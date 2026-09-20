"""
Shared page furniture: guards, the period selector, and the benchmark selector.

Keeping these in one place means every Sensitor page handles an empty portfolio,
a two-week history or a single holding the same way — the edge cases that
otherwise produce a stack trace or, worse, a confident number computed from four
data points.
"""

from __future__ import annotations

import streamlit as st

from .. import market
from ..components import empty_state, note
from ..i18n import tr


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
    return tickers[labels.index(chosen)]


def load_benchmark(ctx, ticker: str):
    """
    Fetch and align a benchmark to the portfolio's window.

    Returns (portfolio_returns, benchmark_returns) aligned on shared dates, or
    (None, None) when the data is unavailable — callers render portfolio-only
    figures in that case rather than failing.
    """
    portfolio = ctx.portfolio_returns
    if portfolio is None or len(portfolio) < 20:
        return None, None
    start = portfolio.index[0].strftime("%Y-%m-%d")
    raw = market.fetch_returns(ticker, start)
    if raw is None:
        return None, None
    return market.align(portfolio, raw)


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
        from ..storage import Store
        return Store()
    except Exception:                                   # noqa: BLE001
        return None


def current_user_email() -> str:
    """Whoever is signed in, normalised. Empty string when nobody is."""
    return (st.session_state.get("user_email") or "").strip().lower()


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
