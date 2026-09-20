"""
Shared furniture for the five trading pages.

The counterpart to `_shared.py`, which does the same job for the investment
pages: guards, the selectors, and the one place the journal is loaded. Keeping
them here means all five pages handle an empty journal, an unsigned-in session
and a journal of open positions only the same way — and it means the period,
the account and the filter are read from one place, so the metrics at the top of
a page can never describe a different set of trades than the table below them.

Two rules are enforced here rather than left to each page:

* **Trades are read per user, per rerun, and never cached across users.** The
  journal is keyed by the signed-in email at read time. A `@st.cache_data` on
  the journal would be keyed by the argument list, and one wrong key would serve
  one person's book to another.
* **The filter vocabulary comes from the unfiltered journal.** A dropdown that
  only offers what survives the current filter cannot be widened again.
"""

from __future__ import annotations

from datetime import date, datetime

import streamlit as st

from ..core.i18n import tr
from ..trading import setups as taxonomy
from ..trading.analytics import format_duration
from ..trading.context import build_context
from ..trading.journal import TradeFilter, TradeJournal
from ..trading.models import Direction, Session, session_label
from ..ui.components import empty_state, money, note, num, pct, pill_html, spacer
from ..ui.themes import INK_FAINT, INK_MUTED, STATUS, html
from ._shared import current_user_email, get_store

# Session-state keys. Prefixed so they cannot collide with the investment
# pages' own period, which is a different window over different data.
STATE_PERIOD = "trading_period"
STATE_ACCOUNT = "trading_account"
STATE_FILTER = "trading_filter"
STATE_BALANCE = "trading_starting_balance"


# =============================================================================
# LOADING
# =============================================================================

def trading_context(lang: str):
    """
    The context every trading page reads, or None after rendering the reason.

    Returns None in three distinct situations, each with its own message:
    no database, nobody signed in, and no trades yet. Collapsing them into one
    "nothing to show" would leave a reader who simply has not signed in hunting
    for a data problem that does not exist.
    """
    store = get_store()
    if store is None:
        note(tr("storage_note", lang))
        return None

    email = current_user_email()
    if not email:
        empty_state(tr("sign_in_trading", lang), tr("sign_in_trading_body", lang), icon="◔")
        return None

    journal = TradeJournal(store.list_trades(email))

    return build_context(
        journal,
        lang=lang,
        period=st.session_state.get(STATE_PERIOD, "ALL"),
        currency=_currency_of(journal),
        account_id=st.session_state.get(STATE_ACCOUNT) or None,
        criteria=st.session_state.get(STATE_FILTER) or TradeFilter(),
        starting_balance=float(st.session_state.get(STATE_BALANCE) or 0.0),
    )


def _currency_of(journal) -> str:
    """
    The account currency to label figures with.

    Taken from the trades themselves rather than a setting: a journal imported
    from a EUR account should not be labelled in dollars because nobody changed
    a dropdown. Mixed currencies fall back to the symbol-free default, since
    adding P&L across currencies is wrong whatever symbol is printed on it.
    """
    found = {t.account_currency for t in journal if t.account_currency}
    if len(found) != 1:
        return ""
    currency = found.pop()
    return {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥"}.get(currency, f"{currency} ")


def store_and_user(lang: str):
    """(store, email) for the pages that write, or (None, None) with the reason."""
    store = get_store()
    if store is None:
        note(tr("storage_note", lang))
        return None, None
    email = current_user_email()
    if not email:
        empty_state(tr("sign_in_trading", lang), tr("sign_in_trading_body", lang), icon="◔")
        return None, None
    return store, email


# =============================================================================
# GUARDS
# =============================================================================

def guard(ctx, lang: str, *, need_closed: bool = True) -> bool:
    """
    Whether the page has enough to render.

    `need_closed` separates the journal — which is useful with a single open
    position in it — from every analytics page, where an open position has no
    result to measure and would either be skipped silently or counted as a zero.
    Saying so is better than either.
    """
    if ctx is None:
        return False
    if not ctx.has_trades:
        empty_state(tr("no_trades_title", lang), tr("no_trades_body", lang), icon="◌")
        return False
    if need_closed and not ctx.has_closed:
        empty_state(tr("no_trades_title", lang), tr("no_closed_trades", lang), icon="◷")
        return False
    return True


# =============================================================================
# SELECTORS
# =============================================================================

def period_selector(ctx, key: str) -> str:
    """Horizontal period pills, the same control the investment pages use."""
    options = ctx.available_periods
    current = ctx.period if ctx.period in options else options[-1]
    selected = st.radio(
        tr("period", ctx.lang), options, index=options.index(current),
        horizontal=True, key=key, label_visibility="collapsed",
    )
    if selected != ctx.period:
        ctx.set_period(selected)
        st.session_state[STATE_PERIOD] = selected
    return selected


def account_selector(ctx, key: str) -> str | None:
    """
    Account picker, shown only when there is more than one.

    A single-account trader should not have to look at a dropdown with one entry
    to understand that the numbers are theirs.
    """
    accounts = ctx.all_accounts
    if len(accounts) < 2:
        return ctx.account_id

    labels = [tr("all_accounts", ctx.lang)] + accounts
    current = ctx.account_id
    index = labels.index(current) if current in labels else 0
    chosen = st.selectbox(tr("account", ctx.lang), labels, index=index, key=key,
                          label_visibility="collapsed")
    account = None if chosen == labels[0] else chosen
    if account != ctx.account_id:
        ctx.set_account(account)
        st.session_state[STATE_ACCOUNT] = account
    return account


def filter_panel(ctx, key: str) -> TradeFilter:
    """
    The filter panel, in an expander so it does not push the figures below the
    fold on a page whose point is the figures.

    Every dimension offered here is one the engine can already filter on, and
    every option comes from `ctx.all_*`, which reads the unfiltered journal.
    """
    lang = ctx.lang
    criteria = ctx.criteria
    active = criteria.is_active

    title = tr("filters", lang)
    if active:
        title = f"{title} — {len(ctx.scoped)} {tr('of_trades', lang)} {len(ctx.journal)}"

    with st.expander(title, expanded=False):
        c1, c2, c3 = st.columns(3, gap="medium")
        with c1:
            symbols = st.multiselect(tr("symbol", lang), ctx.all_symbols,
                                     default=criteria.symbols or [], key=f"{key}_sym")
            setup_keys = ctx.all_setups
            setup_labels = [taxonomy.setup_label(s, lang) for s in setup_keys]
            chosen_setups = st.multiselect(
                tr("setups_label", lang), setup_labels,
                default=[taxonomy.setup_label(s, lang) for s in (criteria.setups or [])
                         if s in setup_keys],
                key=f"{key}_setup",
            )
        with c2:
            session_keys = list(Session)
            session_labels = [session_label(s, lang) for s in session_keys]
            chosen_sessions = st.multiselect(
                tr("session_label", lang), session_labels,
                default=[session_label(s, lang) for s in (criteria.sessions or [])],
                key=f"{key}_session",
            )
            timeframes = st.multiselect(tr("timeframe", lang), ctx.all_timeframes,
                                        default=criteria.timeframes or [],
                                        key=f"{key}_tf")
        with c3:
            mistake_keys = ctx.all_mistakes
            mistake_labels = [taxonomy.mistake_label(m, lang) for m in mistake_keys]
            chosen_mistakes = st.multiselect(
                tr("mistakes_label", lang), mistake_labels,
                default=[taxonomy.mistake_label(m, lang) for m in (criteria.mistakes or [])
                         if m in mistake_keys],
                key=f"{key}_mistake",
            )
            outcome = st.radio(
                tr("outcome", lang),
                [tr("all", lang), tr("wins", lang), tr("losses", lang)],
                horizontal=True, key=f"{key}_outcome",
                index=1 if criteria.only_wins else (2 if criteria.only_losses else 0),
            )

        search = st.text_input(tr("search", lang), value=criteria.search or "",
                               key=f"{key}_search",
                               placeholder=tr("search_placeholder", lang))

        if st.button(tr("clear_filters", lang), key=f"{key}_clear"):
            _clear_filter_widgets(key)
            st.session_state[STATE_FILTER] = TradeFilter()
            st.rerun()

    outcomes = [tr("all", lang), tr("wins", lang), tr("losses", lang)]
    built = TradeFilter(
        symbols=symbols or None,
        setups=[setup_keys[setup_labels.index(s)] for s in chosen_setups] or None,
        sessions=[session_keys[session_labels.index(s)] for s in chosen_sessions] or None,
        timeframes=timeframes or None,
        mistakes=[mistake_keys[mistake_labels.index(m)] for m in chosen_mistakes] or None,
        only_wins=outcome == outcomes[1],
        only_losses=outcome == outcomes[2],
        search=search.strip() or None,
    )

    if built != criteria:
        ctx.set_filter(built)
        st.session_state[STATE_FILTER] = built

    if built.is_active:
        filtered_badge(ctx)
    return built


def _clear_filter_widgets(key: str) -> None:
    for suffix in ("sym", "setup", "session", "tf", "mistake", "outcome", "search"):
        st.session_state.pop(f"{key}_{suffix}", None)


def filtered_badge(ctx) -> None:
    """A visible marker that the figures describe a subset, not the book."""
    lang = ctx.lang
    html(
        f'<div style="margin:2px 0 10px 0;">'
        f'{pill_html(tr("filtered_notice", lang), "warning")}'
        f'<span style="font-size:0.74rem;color:{INK_MUTED};margin-left:8px;">'
        f'{tr("showing", lang)} {len(ctx.scoped)} {tr("of_trades", lang)} '
        f'{len(ctx.journal)} {tr("trades", lang).lower()}</span></div>'
    )


# =============================================================================
# FORMATTING
# =============================================================================

def r_text(value, decimals: int = 2) -> str:
    """An R multiple, or the em dash that means "no stop, so no R"."""
    return "—" if value is None else f"{value:+.{decimals}f}R"


def pf_text(value, lang: str) -> str:
    """
    Profit factor, or the reason there is not one.

    With no losing trades the ratio has no denominator. Printing "∞" would put a
    meaningless value in a column of meaningful ones.
    """
    return f"{value:.2f}" if value is not None else tr("undefined", lang)


def duration_text(minutes, lang: str) -> str:
    return format_duration(minutes, lang) if minutes is not None else "—"


def outcome_tone(value) -> str:
    if value is None:
        return "neutral"
    return "good" if value > 0 else ("critical" if value < 0 else "neutral")


def sample_pill(n: int, threshold: int, lang: str) -> str:
    """
    The sample size, coloured by whether it clears the threshold.

    Present on every comparison the trading pages draw. A breakdown's most
    dangerous property is that a three-trade bucket looks exactly as
    authoritative as a three-hundred-trade one.
    """
    tone = "neutral" if n >= threshold else "warning"
    return pill_html(f"n = {n}", tone, icon=False)


def trade_flags(trade, lang: str) -> str:
    """Small pills for the things about a trade that change how to read it."""
    parts = []
    if not trade.is_closed:
        parts.append(pill_html(tr("open_position", lang), "neutral"))
    if trade.risk_amount is None:
        parts.append(pill_html(tr("no_stop", lang), "warning"))
    for mistake in trade.mistakes[:3]:
        parts.append(pill_html(taxonomy.mistake_label(mistake, lang), "warning",
                               icon=False))
    return " ".join(parts)
