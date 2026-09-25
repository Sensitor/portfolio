"""
Shared page furniture: guards, the period selector, and the benchmark selector.

Keeping these in one place means every Sensitor page handles an empty portfolio,
a two-week history or a single holding the same way — the edge cases that
otherwise produce a stack trace or, worse, a confident number computed from four
data points.
"""

from __future__ import annotations

import streamlit as st

from ..integrations import market_data as market
from ..investment import currency as FX
from ..ui.components import empty_state, note
from ..core.i18n import tr


def guard(ctx, lang: str) -> bool:
    """
    Return True when the page has enough data to render.

    Two distinct failures get two distinct messages: no portfolio at all, and a
    portfolio whose history is too short for the statistics to mean anything.
    """
    if ctx is None:
        empty_state(tr("no_data_title", lang), tr("no_data_body", lang))
        return False
    if not ctx.has_history:
        empty_state(tr("short_history_title", lang), tr("short_history_body", lang), icon="◷")
        return False
    return True


def period_selector(ctx, key: str) -> str:
    """
    Horizontal period pills.

    Changing the period re-slices the returns and clears every derived value, so
    the metrics and the charts always describe the same window — a period control
    that only moved the chart would be worse than none.
    """
    options = ctx.available_periods
    current = ctx.period if ctx.period in options else options[-1]
    selected = st.radio(
        tr("period", ctx.lang),
        options,
        index=options.index(current),
        horizontal=True,
        key=key,
        label_visibility="collapsed",
    )
    ctx.set_period(selected)
    return selected


def benchmark_selector(ctx, key: str, default: str = market.DEFAULT_BENCHMARK) -> str:
    """Benchmark picker, labelled in the active language."""
    tickers = list(market.BENCHMARKS)
    labels = [market.benchmark_label(t, ctx.lang) for t in tickers]
    index = tickers.index(default) if default in tickers else 0
    chosen = st.selectbox(
        tr("benchmark", ctx.lang), labels, index=index, key=key,
        label_visibility="collapsed",
    )
    ticker = tickers[labels.index(chosen)]

    # Said where the choice is made. Every benchmark here is dollar-quoted, so
    # against a euro portfolio the comparison line is converted — and a reader
    # checking it against the index they see quoted elsewhere should know that
    # before they conclude the app is wrong.
    base = (getattr(ctx.analyzer, "base_currency", None) or "USD").upper()
    if FX.settlement_currency(FX.quote_currency(ticker))[0].upper() != base:
        st.caption(
            f"Converted to {base} — compared like for like with the portfolio."
            if ctx.lang == "en" else
            f"Converti en {base} — comparé à la même échelle que le portefeuille."
        )
    return ticker


def load_benchmark(ctx, ticker: str):
    """
    Fetch and align a benchmark to the portfolio's window, in its currency.

    Returns (portfolio_returns, benchmark_returns) aligned on shared dates, or
    (None, None) when the data is unavailable — callers render portfolio-only
    figures in that case rather than failing.

    The benchmark is converted into the portfolio's base currency for the same
    reason the holdings are. Every benchmark in the list is dollar-quoted; a
    euro-denominated portfolio compared against a dollar S&P 500 is being
    measured against a line that includes a currency move the portfolio's own
    figures already account for, and the alpha, beta and tracking error that
    come out of that comparison are all about the euro rather than about the
    portfolio.

    A benchmark whose rate cannot be sourced is treated as unavailable rather
    than compared unconverted: a portfolio-only page is a smaller loss than a
    confident comparison against the wrong thing.
    """
    portfolio = ctx.portfolio_returns
    if portfolio is None or len(portfolio) < 20:
        return None, None
    start = portfolio.index[0].strftime("%Y-%m-%d")

    base = (getattr(ctx.analyzer, "base_currency", None) or "USD").upper()
    quote = FX.quote_currency(ticker)
    if FX.settlement_currency(quote)[0].upper() == base:
        raw = market.fetch_returns(ticker, start)
        if raw is None:
            return None, None
        return market.align(portfolio, raw)

    # Converted on the price level, then differenced — the same ordering the
    # analyzer uses, and for the same reason: a return and a rate compound.
    prices = market.fetch_prices(ticker, start)
    if prices is None:
        return None, None
    rate = _benchmark_rate(quote, base, start)
    if rate is None:
        return None, None
    converted, report = FX.convert_prices(
        prices.to_frame(ticker), base, {quote: rate})
    if ticker not in converted.columns:
        return None, None
    raw = converted[ticker].pct_change().dropna()
    if len(raw) < 20:
        return None, None
    return market.align(portfolio, raw)


def _benchmark_rate(quote: str, base: str, start: str):
    """The exchange rate series a benchmark needs, oriented for multiplication."""
    for symbol, invert in FX.fx_candidates(quote, base):
        series = market.fetch_prices(symbol, start)
        if series is None or len(series) == 0:
            continue
        return (1.0 / series) if invert else series
    return None


def single_asset_note(ctx) -> None:
    if ctx.is_single_asset:
        note(tr("single_asset_note", ctx.lang))


@st.cache_resource(show_spinner=False)
def get_store():
    """
    The shared persistence layer.

    Cached as a resource, not data: one SQLite connection per app process, reused
    across reruns and sessions. Returns None if the database cannot be opened —
    a read-only filesystem, for instance — so the pages can degrade to a clear
    message instead of failing on import.
    """
    try:
        from ..database import Store
        return Store()
    except Exception:                                   # noqa: BLE001
        return None


def get_auth():
    """
    The authentication service, over the shared store.

    Cheap to build — it holds no state of its own — so it is constructed per
    call rather than cached. Caching it would be caching a thing whose only
    field is the store that is already cached.
    """
    from ..core.auth import Auth
    store = get_store()
    return Auth(store) if store is not None else None


def current_user_email() -> str:
    """
    Whoever is signed in, verified. Empty string when nobody is.

    Resolved from the session token, never from the email in session state. The
    email is what the person typed; the token is what the app issued after
    checking it. Reading the typed value here is the whole vulnerability: with
    the data layer scoped by user, an unverified email *is* the authorisation.

    The resolved address is mirrored back into `user_email` for the legacy
    pages, which still read it directly — but it is written by this function
    from a verified session, never by a widget.
    """
    auth = get_auth()
    if auth is None:
        return ""

    token = st.session_state.get("session_token")
    email = auth.resolve(token) if token else None

    if not email:
        # A token that no longer resolves — expired, revoked, or from a database
        # that has since been replaced — must not leave a stale identity behind.
        if st.session_state.get("user_email"):
            st.session_state.user_email = ""
            st.session_state.authenticated = False
        return ""

    st.session_state.user_email = email
    st.session_state.authenticated = True
    return email


def require_store_and_user(lang: str):
    """
    Guard for the pages that persist things.

    Returns (store, email) or (None, None) after rendering the reason. Saved
    portfolios are filed under an email address, so an anonymous session has
    nowhere to file them.
    """
    store = get_store()
    if store is None:
        note(tr("storage_note", lang))
        return None, None
    email = current_user_email()
    if not email:
        empty_state(tr("sign_in_required", lang), tr("sign_in_body", lang), icon="◔")
        return None, None
    return store, email


def snapshot_metrics(ctx) -> dict:
    """
    The figures worth freezing in a snapshot.

    Deliberately a small, flat set: enough to draw a history chart and an advisor
    row without storing series that would balloon the database.
    """
    stats = ctx.stats
    health = ctx.health
    concentration = ctx.concentration
    return {
        "total_return": stats["total_return"],
        "cagr": stats["cagr"],
        "volatility": stats["volatility"],
        "sharpe": stats["sharpe"],
        "max_drawdown": stats["max_drawdown"],
        "health": health["total"],
        "health_band": health["band"],
        "effective_assets": concentration.get("effective_assets"),
        "n_assets": len(ctx.tickers),
        "period": ctx.period,
    }


def currency_notice(analyzer, lang: str) -> None:
    """
    What the exchange rates and the shared window did to this portfolio.

    Rendered under a page's own header rather than above it. The first version
    printed from the router, before any page had drawn anything, which put a
    grey line of caveat above the product name — legible, and visibly not part
    of the page it was describing.

    Only the captions live here. The *failure* — an asset dropped for want of a
    rate — stays in the router, because it changes every number on every page
    and belongs above all of them.
    """
    report = getattr(analyzer, "currency_report", None) or {}
    base = getattr(analyzer, "base_currency", "USD")
    converted = report.get("converted") or {}

    if converted:
        names = ", ".join(sorted(converted))
        currencies = ", ".join(sorted(set(converted.values())))
        st.caption(
            f"Converted to {base} at the daily rate: {names} ({currencies}). "
            f"Returns include the currency move."
            if lang == "en" else
            f"Converti en {base} au taux du jour : {names} ({currencies}). "
            f"Les rendements incluent le mouvement de change."
        )

    window = getattr(analyzer, "window_report", None) or {}
    limited_by = window.get("limited_by")
    start = window.get("start")
    if window.get("shortened") and limited_by and start is not None:
        try:
            since = start.strftime("%d %b %Y")
        except Exception:                               # noqa: BLE001
            since = str(start)[:10]
        st.caption(
            f"Measured from {since} — the first date every holding traded. "
            f"{limited_by} has the shortest history, and a correlation over a period "
            f"when an asset did not exist is not a weaker figure, it is not a figure."
            if lang == "en" else
            f"Mesuré depuis le {since} — la première date où toutes les lignes cotaient. "
            f"{limited_by} a l'historique le plus court, et une corrélation sur une "
            f"période où un actif n'existait pas n'est pas un chiffre moins fiable, "
            f"ce n'est pas un chiffre."
        )
