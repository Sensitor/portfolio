"""
TRADING JOURNAL — every trade, with the context and the state of mind behind it.

The one page in the trading section that writes. Everything else reads what is
recorded here, which makes the recording the product: a journal that is tedious
to fill in is a journal nobody fills in, so the form asks for the execution
fields first, keeps strategy and psychology behind their own expanders, and
requires only what the engine genuinely cannot work without.

Three things this page does deliberately:

* **It shows what is missing.** A trade with no stop is marked on its own card,
  because that trade is silently absent from every R statistic in the product.
* **It shows what is wrong without refusing it.** `journal.validate()` finds
  trades whose numbers would make their own statistics incorrect. They are kept
  and listed so they can be corrected, not rejected on entry.
* **It never recomputes anything itself.** P&L, R, risk and duration come off
  the `Trade` model. A second implementation here would drift from the engine's
  within a release.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, time, timezone

import streamlit as st

from ..core.i18n import tr
from ..trading import setups as taxonomy
from ..trading.models import Direction, Trade, session_label, validate
from ..ui.components import (
    alert, data_table, empty_state, metric_card, money, note, page_header,
    pct, pill_html, section, spacer,
)
from ..ui.themes import BORDER, INK, INK_2, INK_FAINT, INK_MUTED, RADIUS_SM, STATUS, html
from ._trading_shared import (
    account_selector, duration_text, filter_panel, guard, outcome_tone,
    period_selector, r_text, store_and_user, trade_flags, trading_context,
)

PAGE_SIZE = 25
EDIT_KEY = "trading_editing_id"


def render_trading_journal(ctx=None) -> None:
    lang = st.session_state.get("language", "en")
    page_header(
        f"{tr('nav_trading', lang)} · {tr('nav_trading_journal', lang)}",
        tr("trading_journal_sub", lang),
        eyebrow=tr("product_trading", lang),
    )

    store, email = store_and_user(lang)
    if store is None:
        return

    tctx = trading_context(lang)
    if tctx is None:
        return

    _entry_form(lang, store, email, tctx)

    # The journal is useful with a single open position in it, so unlike the
    # analytics pages it does not require a closed trade.
    if not guard(tctx, lang, need_closed=False):
        return

    left, right = st.columns([3, 1.4])
    with left:
        period_selector(tctx, "tjr_period")
    with right:
        account_selector(tctx, "tjr_account")

    filter_panel(tctx, "tjr_filter")

    _open_positions(tctx, lang)
    _problems(tctx, lang)
    _trade_list(tctx, lang, store, email)


# =============================================================================
# ENTRY
# =============================================================================

def _entry_form(lang, store, email, tctx) -> None:
    editing = st.session_state.get(EDIT_KEY)
    existing = tctx.journal.get(editing) if editing else None

    label = tr("edit_trade", lang) if existing else tr("add_trade", lang)
    with st.expander(f"＋ {label}", expanded=bool(existing)):
        _form_body(lang, store, email, existing)


def _form_body(lang, store, email, existing) -> None:
    prefix = "tjf"
    directions = [tr("long", lang), tr("short", lang)]

    with st.form(f"{prefix}_form", clear_on_submit=existing is None):
        section(tr("execution", lang).upper())

        c1, c2, c3, c4 = st.columns(4, gap="medium")
        with c1:
            symbol = st.text_input(tr("symbol", lang),
                                   value=existing.symbol if existing else "",
                                   key=f"{prefix}_symbol", placeholder="EURUSD")
        with c2:
            direction = st.radio(
                tr("direction_label", lang), directions, horizontal=True,
                key=f"{prefix}_dir",
                index=0 if not existing or existing.direction is Direction.LONG else 1,
            )
        with c3:
            size = st.number_input(tr("position_size", lang), min_value=0.0,
                                   value=float(existing.size) if existing else 1.0,
                                   step=0.01, format="%.4f", key=f"{prefix}_size")
        with c4:
            account = st.text_input(tr("account", lang),
                                    value=(existing.account_id if existing else "") or "",
                                    key=f"{prefix}_account")

        p1, p2, p3, p4 = st.columns(4, gap="medium")
        with p1:
            entry_price = st.number_input(
                tr("entry_price", lang), min_value=0.0, step=0.0001, format="%.5f",
                value=float(existing.entry_price) if existing else 0.0,
                key=f"{prefix}_entry")
        with p2:
            exit_price = st.number_input(
                tr("exit_price", lang), min_value=0.0, step=0.0001, format="%.5f",
                value=float(existing.exit_price) if existing and existing.exit_price
                else 0.0, key=f"{prefix}_exit")
        with p3:
            stop_loss = st.number_input(
                tr("stop_loss", lang), min_value=0.0, step=0.0001, format="%.5f",
                value=float(existing.stop_loss) if existing and existing.stop_loss
                else 0.0, key=f"{prefix}_stop")
        with p4:
            take_profit = st.number_input(
                tr("take_profit", lang), min_value=0.0, step=0.0001, format="%.5f",
                value=float(existing.take_profit) if existing and existing.take_profit
                else 0.0, key=f"{prefix}_tp")

        t1, t2, t3, t4 = st.columns(4, gap="medium")
        today = date.today()
        with t1:
            open_date = st.date_input(
                tr("opened_at", lang),
                value=existing.opened_at.date() if existing else today,
                key=f"{prefix}_odate")
        with t2:
            # A real label, hidden rather than blanked: the space stays reserved
            # so the control lines up with the date beside it, and a screen
            # reader gets "Opened — time" instead of a space.
            open_time = st.time_input(
                f"{tr('opened_at', lang)} — {tr('time_label', lang)}",
                value=existing.opened_at.time() if existing else time(9, 0),
                key=f"{prefix}_otime", label_visibility="hidden")
        with t3:
            close_date = st.date_input(
                tr("closed_at", lang),
                value=existing.closed_at.date() if existing and existing.closed_at
                else today, key=f"{prefix}_cdate")
        with t4:
            close_time = st.time_input(
                f"{tr('closed_at', lang)} — {tr('time_label', lang)}",
                value=existing.closed_at.time() if existing and existing.closed_at
                else time(11, 0),
                key=f"{prefix}_ctime", label_visibility="hidden")

        m1, m2, m3 = st.columns(3, gap="medium")
        with m1:
            commission = st.number_input(
                tr("commission", lang), value=float(existing.commission) if existing
                else 0.0, step=0.01, format="%.2f", key=f"{prefix}_comm")
        with m2:
            swap = st.number_input(
                tr("swap", lang), value=float(existing.swap) if existing else 0.0,
                step=0.01, format="%.2f", key=f"{prefix}_swap")
        with m3:
            currency = st.selectbox(
                tr("currency", lang), ["USD", "EUR", "GBP", "JPY", "CHF"],
                index=["USD", "EUR", "GBP", "JPY", "CHF"].index(
                    existing.account_currency if existing
                    and existing.account_currency in ("USD", "EUR", "GBP", "JPY", "CHF")
                    else "USD"),
                key=f"{prefix}_ccy")

        # ── Strategy ─────────────────────────────────────────────────────────
        with st.expander(tr("strategy", lang), expanded=False):
            s1, s2, s3 = st.columns(3, gap="medium")
            setup_keys = taxonomy.known_setups()
            setup_labels = [taxonomy.setup_label(k, lang) for k in setup_keys]
            with s1:
                chosen_setups = st.multiselect(
                    tr("setups_label", lang), setup_labels,
                    default=[taxonomy.setup_label(k, lang)
                             for k in taxonomy.canonical_setups(
                                 existing.setups if existing else [])
                             if k in setup_keys],
                    key=f"{prefix}_setups")
                timeframe = st.selectbox(
                    tr("timeframe", lang), [""] + taxonomy.TIMEFRAMES,
                    index=(taxonomy.TIMEFRAMES.index(existing.timeframe) + 1
                           if existing and existing.timeframe in taxonomy.TIMEFRAMES
                           else 0),
                    key=f"{prefix}_tf")
            with s2:
                regime_keys = [""] + list(taxonomy.MARKET_REGIMES)
                regime_labels = [""] + [taxonomy.MARKET_REGIMES[k][lang]
                                        for k in taxonomy.MARKET_REGIMES]
                regime = st.selectbox(
                    tr("market_regime", lang), regime_labels,
                    index=(regime_keys.index(existing.market_regime)
                           if existing and existing.market_regime in regime_keys else 0),
                    key=f"{prefix}_regime")
                quality = st.slider(tr("setup_quality", lang), 1, 5,
                                    value=existing.setup_quality if existing
                                    and existing.setup_quality else 3,
                                    key=f"{prefix}_quality")
            with s3:
                confidence = st.slider(tr("confidence_label", lang), 1, 5,
                                       value=existing.confidence if existing
                                       and existing.confidence else 3,
                                       key=f"{prefix}_conf")
            entry_reason = st.text_input(
                tr("entry_reason", lang),
                value=(existing.entry_reason if existing else "") or "",
                key=f"{prefix}_ereason")
            exit_reason = st.text_input(
                tr("exit_reason", lang),
                value=(existing.exit_reason if existing else "") or "",
                key=f"{prefix}_xreason")

        # ── Psychology ───────────────────────────────────────────────────────
        with st.expander(tr("psychology_section", lang), expanded=False):
            emotion_keys = [""] + list(taxonomy.EMOTIONS)
            emotion_labels = [""] + [taxonomy.EMOTIONS[k][lang] for k in taxonomy.EMOTIONS]
            e1, e2, e3, e4 = st.columns(4, gap="medium")
            with e1:
                before = st.selectbox(
                    tr("emotion_before", lang), emotion_labels,
                    index=(emotion_keys.index(existing.emotion_before)
                           if existing and existing.emotion_before in emotion_keys else 0),
                    key=f"{prefix}_before")
            with e2:
                during = st.selectbox(
                    tr("emotion_during", lang), emotion_labels,
                    index=(emotion_keys.index(existing.emotion_during)
                           if existing and existing.emotion_during in emotion_keys else 0),
                    key=f"{prefix}_during")
            with e3:
                after = st.selectbox(
                    tr("emotion_after", lang), emotion_labels,
                    index=(emotion_keys.index(existing.emotion_after)
                           if existing and existing.emotion_after in emotion_keys else 0),
                    key=f"{prefix}_after")
            with e4:
                discipline = st.slider(tr("discipline_label", lang), 1, 5,
                                       value=existing.discipline if existing
                                       and existing.discipline else 3,
                                       key=f"{prefix}_disc")

            mistake_keys = list(taxonomy.MISTAKES)
            mistake_labels = [taxonomy.mistake_label(k, lang) for k in mistake_keys]
            chosen_mistakes = st.multiselect(
                tr("mistakes_label", lang), mistake_labels,
                default=[taxonomy.mistake_label(k, lang)
                         for k in taxonomy.canonical_mistakes(
                             existing.mistakes if existing else [])
                         if k in mistake_keys],
                key=f"{prefix}_mistakes")
            notes = st.text_area(tr("trade_notes", lang),
                                 value=(existing.notes if existing else "") or "",
                                 key=f"{prefix}_notes", height=80)

        submitted = st.form_submit_button(tr("save_trade", lang), type="primary")

    if not submitted:
        return

    if not symbol.strip() or entry_price <= 0 or size <= 0:
        st.warning(tr("trade_required_fields", lang))
        return

    opened_at = datetime.combine(open_date, open_time)
    closed_at = datetime.combine(close_date, close_time) if exit_price > 0 else None

    trade = Trade(
        id=existing.id if existing else uuid.uuid4().hex[:16],
        symbol=symbol.strip().upper(),
        direction=Direction.LONG if direction == directions[0] else Direction.SHORT,
        entry_price=float(entry_price),
        size=float(size),
        opened_at=opened_at,
        exit_price=float(exit_price) if exit_price > 0 else None,
        closed_at=closed_at,
        stop_loss=float(stop_loss) if stop_loss > 0 else None,
        take_profit=float(take_profit) if take_profit > 0 else None,
        commission=float(commission),
        swap=float(swap),
        account_id=account.strip() or None,
        account_currency=currency,
        setups=[setup_keys[setup_labels.index(s)] for s in chosen_setups],
        timeframe=timeframe or None,
        market_regime=regime_keys[regime_labels.index(regime)] or None,
        setup_quality=int(quality),
        confidence=int(confidence),
        entry_reason=entry_reason.strip() or None,
        exit_reason=exit_reason.strip() or None,
        emotion_before=emotion_keys[emotion_labels.index(before)] or None,
        emotion_during=emotion_keys[emotion_labels.index(during)] or None,
        emotion_after=emotion_keys[emotion_labels.index(after)] or None,
        discipline=int(discipline),
        mistakes=[mistake_keys[mistake_labels.index(m)] for m in chosen_mistakes],
        notes=notes.strip() or None,
        source=existing.source if existing else "manual",
    )

    problems = validate(trade)
    if problems:
        # Saved anyway, then flagged. A journal that refuses a row on entry is a
        # journal whose owner stops using it mid-import.
        st.warning(" · ".join(problems))

    store.save_trade(email, trade)
    st.session_state.pop(EDIT_KEY, None)
    st.success(tr("trade_saved", lang))
    st.rerun()


# =============================================================================
# OPEN POSITIONS
# =============================================================================

def _open_positions(tctx, lang) -> None:
    open_trades = list(tctx.open_trades)
    if not open_trades:
        return

    section(tr("open_position", lang).upper(), f"{len(open_trades)}")
    rows = []
    for trade in open_trades:
        rows.append([
            trade.symbol,
            tr("long", lang) if trade.direction is Direction.LONG else tr("short", lang),
            f"{trade.entry_price:g}",
            f"{trade.stop_loss:g}" if trade.stop_loss else "—",
            f"{trade.size:g}",
            trade.opened_at.strftime("%Y-%m-%d %H:%M"),
        ])
    data_table(
        [tr("symbol", lang), tr("direction_label", lang), tr("entry_price", lang),
         tr("stop_loss", lang), tr("position_size", lang), tr("opened_at", lang)],
        rows, align="llrrrl",
    )
    note(tr("open_excluded_note", lang))


# =============================================================================
# DATA PROBLEMS
# =============================================================================

def _problems(tctx, lang) -> None:
    problems = tctx.scoped.validate()
    if not problems:
        return

    section(tr("data_problems", lang).upper(), f"{len(problems)}")
    for entry in problems[:10]:
        alert("warning", f"{entry['symbol']} · {entry['id'][:8]}",
              " · ".join(entry["problems"]))
    note(tr("data_problems_body", lang))


# =============================================================================
# THE LIST
# =============================================================================

def _trade_list(tctx, lang, store, email) -> None:
    trades = list(tctx.scoped.closed().sorted_by("closed_at"))
    section(tr("trades", lang).upper(), f"{len(trades)}")

    if not trades:
        empty_state(tr("no_trades_title", lang), tr("no_trades_body", lang), icon="◌")
        return

    pages = max(1, (len(trades) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = 1
    if pages > 1:
        # Narrow: a full-width stepper above a list of cards reads as a filter
        # over the list rather than a position in it.
        picker, _ = st.columns([1, 4])
        with picker:
            page = st.number_input(f"{tr('page', lang)} (1–{pages})", min_value=1,
                                   max_value=pages, value=1, step=1, key="tjr_page")
    start = (int(page) - 1) * PAGE_SIZE
    for trade in trades[start:start + PAGE_SIZE]:
        _trade_card(trade, tctx, lang, store, email)


def _trade_card(trade, tctx, lang, store, email) -> None:
    currency = tctx.currency
    pnl = trade.pnl
    tone = outcome_tone(pnl)
    colour = STATUS[tone]

    header = (
        f'<div style="display:flex;justify-content:space-between;align-items:baseline;'
        f'gap:12px;flex-wrap:wrap;">'
        f'<div style="display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;">'
        f'<span style="font-size:0.95rem;font-weight:700;color:{INK};">{trade.symbol}</span>'
        f'<span style="font-size:0.72rem;color:{INK_MUTED};text-transform:uppercase;'
        f'letter-spacing:0.08em;">'
        f'{tr("long", lang) if trade.direction is Direction.LONG else tr("short", lang)}'
        f'</span>'
        f'<span style="font-size:0.72rem;color:{INK_FAINT};">'
        f'{trade.closed_at.strftime("%Y-%m-%d %H:%M") if trade.closed_at else ""}'
        f'&nbsp;·&nbsp;{session_label(trade.session, lang)}</span>'
        f'{trade_flags(trade, lang)}</div>'
        f'<div style="text-align:right;">'
        f'<span class="snr-num" style="font-size:1.05rem;font-weight:700;color:{colour};">'
        f'{money(pnl, currency, decimals=2) if pnl is not None else "—"}</span>'
        f'<span style="font-size:0.78rem;color:{INK_2};margin-left:10px;">'
        f'{r_text(trade.r_multiple)}</span></div></div>'
    )

    facts = [
        (tr("entry_price", lang), f"{trade.entry_price:g}"),
        (tr("exit_price", lang), f"{trade.exit_price:g}" if trade.exit_price else "—"),
        (tr("stop_loss", lang), f"{trade.stop_loss:g}" if trade.stop_loss else "—"),
        (tr("position_size", lang), f"{trade.size:g}"),
        (tr("duration", lang), duration_text(trade.duration_minutes, lang)),
        (tr("costs", lang), money(trade.costs, currency, decimals=2)),
    ]
    fact_html = "".join(
        f'<div><div style="font-size:0.63rem;color:{INK_FAINT};text-transform:uppercase;'
        f'letter-spacing:0.09em;">{label}</div>'
        f'<div class="snr-num" style="font-size:0.82rem;color:{INK_2};margin-top:2px;">'
        f'{value}</div></div>'
        for label, value in facts
    )

    tags = []
    for setup in taxonomy.canonical_setups(trade.setups):
        tags.append(pill_html(taxonomy.setup_label(setup, lang), "neutral", icon=False))
    if trade.timeframe:
        tags.append(pill_html(trade.timeframe, "neutral", icon=False))
    if trade.emotion_before:
        tags.append(pill_html(
            taxonomy.EMOTIONS.get(trade.emotion_before, {}).get(lang, trade.emotion_before),
            "neutral", icon=False))
    tag_html = (f'<div style="margin-top:10px;display:flex;gap:6px;flex-wrap:wrap;">'
                f'{"".join(tags)}</div>') if tags else ""

    note_html = ""
    if trade.notes:
        note_html = (
            f'<div style="margin-top:10px;font-size:0.76rem;color:{INK_MUTED};'
            f'line-height:1.55;border-left:2px solid {BORDER};padding-left:10px;">'
            f'{trade.notes[:400]}</div>'
        )

    html(
        f'<div class="snr-card" style="padding:14px 16px;margin-bottom:10px;'
        f'border-left:3px solid {colour};">{header}'
        f'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(84px,1fr));'
        f'gap:10px;margin-top:12px;">{fact_html}</div>{tag_html}{note_html}</div>'
    )

    edit_col, delete_col, _ = st.columns([1, 1, 9])
    with edit_col:
        if st.button(tr("edit_trade", lang), key=f"tjr_edit_{trade.id}"):
            st.session_state[EDIT_KEY] = trade.id
            st.rerun()
    with delete_col:
        if st.button(tr("delete_trade", lang), key=f"tjr_del_{trade.id}"):
            store.delete_trade(email, trade.id)
            st.session_state.pop(EDIT_KEY, None)
            st.success(tr("trade_deleted", lang))
            st.rerun()
