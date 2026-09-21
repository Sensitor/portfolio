"""
REPORTS — generate the documents.

Two of them, in two tabs: the client portfolio report and the weekly trading
review. They live together because they are the same kind of thing — a
self-contained HTML file you print or send — and they are built from the same
primitives in `core.document`, so they look like one product.

The tabs guard separately. A portfolio report needs a loaded portfolio; a
trading review needs a journal and nothing else. Guarding the page as a whole
would hide the review from anyone who only trades.

See `core/document.py` for why HTML rather than a generated PDF; the page says
the same thing in one line so nobody has to read the source to find out.
"""

from __future__ import annotations

import streamlit as st

from ..investment import analytics as A
from ..integrations import market_data as market
from ..investment import report as R
from ..investment import stress as S
from ..trading import report as WR
from ..ui.components import empty_state, metric_card, note, page_header, section, spacer
from ..core.i18n import tr
from ._shared import benchmark_selector, guard, load_benchmark, period_selector
from ._trading_shared import trading_context

_HISTORY_START = "1999-01-01"


def render_reports(ctx) -> None:
    lang = ctx.lang if ctx else st.session_state.get("language", "en")

    page_header(tr("nav_reports", lang), tr("reports_sub", lang),
                eyebrow=tr("product_short", lang))

    portfolio_tab, trading_tab = st.tabs(
        [tr("nav_investment", lang), tr("weekly_review", lang)])
    with portfolio_tab:
        _portfolio_report(ctx, lang)
    with trading_tab:
        _weekly_review(lang)


# =============================================================================
# PORTFOLIO REPORT
# =============================================================================

def _portfolio_report(ctx, lang) -> None:
    if not guard(ctx, lang):
        return

    period_selector(ctx, "rep_period")

    # ── Document settings ────────────────────────────────────────────────────
    section(tr("generate_report", lang).upper())

    loaded = st.session_state.get("sensitor_loaded_portfolio") or {}
    default_title = loaded.get("name") or tr("portfolio", lang)

    title_col, client_col, by_col = st.columns(3, gap="medium")
    with title_col:
        title = st.text_input(tr("report_title", lang), value=default_title, key="rep_title")
    with client_col:
        client = st.text_input(tr("client_name", lang), key="rep_client")
    with by_col:
        prepared_by = st.text_input(
            tr("prepared_by", lang),
            value=st.session_state.get("user_email", ""), key="rep_by",
        )

    bench_ticker = benchmark_selector(ctx, "rep_bench")

    # ── Section picker ───────────────────────────────────────────────────────
    st.markdown(f"**{tr('include_sections', lang)}**")
    chosen = []
    columns = st.columns(3, gap="medium")
    for index, key in enumerate(R.SECTIONS):
        with columns[index % 3]:
            if st.checkbox(tr(f"s_{key}", lang), value=True, key=f"rep_s_{key}"):
                chosen.append(key)

    spacer(10)
    generate = st.button(tr("generate_report", lang), key="rep_go",
                         type="primary", width="stretch")

    if generate:
        st.session_state["sensitor_report_html"] = _build(
            ctx, lang, title, client, prepared_by, bench_ticker, chosen
        )

    html_doc = st.session_state.get("sensitor_report_html")
    if not html_doc:
        note(tr("report_format_note", lang))
        return

    # ── Result ───────────────────────────────────────────────────────────────
    section(tr("report_ready", lang).upper())

    info_col, download_col = st.columns([2, 1], gap="medium")
    with info_col:
        metric_card(
            tr("report_ready", lang), f"{len(html_doc) / 1024:.0f} KB",
            bar=1.0,
            caption=f"{len(chosen)} {tr('include_sections', lang).lower()} · "
                    f"{'self-contained HTML' if lang == 'en' else 'HTML autonome'}",
            compact=True,
        )
    with download_col:
        spacer(18)
        safe_title = "".join(
            c if c.isalnum() or c in "-_ " else "_" for c in (title or "report")
        ).strip().replace(" ", "_") or "report"
        st.download_button(
            tr("download_report", lang),
            data=html_doc.encode("utf-8"),
            file_name=f"sensitor_{safe_title}.html",
            mime="text/html",
            width="stretch",
            key="rep_download",
        )

    note(tr("report_format_note", lang))

    with st.expander(tr("report_preview", lang), expanded=True):
        st.components.v1.html(html_doc, height=900, scrolling=True)


# =============================================================================
# WEEKLY TRADING REVIEW
# =============================================================================

def _weekly_review(lang) -> None:
    """
    A week of trading as a printable document.

    Which week is a control rather than an assumption: on a Monday morning the
    week anyone wants to review is the one that just ended, and a page that only
    ever offered "this week" would be useless on the day it is most wanted.
    """
    tctx = trading_context(lang)
    if tctx is None:
        return
    if not tctx.has_trades:
        empty_state(tr("no_trades_title", lang), tr("no_trades_body", lang), icon="◌")
        return

    trades = list(tctx.journal)
    weeks = _recent_weeks(trades)
    if not weeks:
        empty_state(tr("no_trades_title", lang), tr("no_closed_trades", lang), icon="◷")
        return

    labels = [_week_label(start, end, count) for start, end, count in weeks]

    pick_col, name_col = st.columns([2, 1.4], gap="medium")
    with pick_col:
        chosen_label = st.selectbox(tr("review_week", lang), labels, index=0,
                                    key="rev_week")
    with name_col:
        trader = st.text_input(tr("prepared_by", lang),
                               value=st.session_state.get("user_email", ""),
                               key="rev_by")

    start = weeks[labels.index(chosen_label)][0]

    st.markdown(f"**{tr('review_sections', lang)}**")
    chosen = []
    columns = st.columns(3, gap="medium")
    for index, key in enumerate(WR.SECTIONS):
        with columns[index % 3]:
            title = WR.TITLES[key][lang]
            if st.checkbox(title, value=True, key=f"rev_s_{key}"):
                chosen.append(key)

    spacer(10)
    if st.button(tr("generate_review", lang), key="rev_go", type="primary",
                 width="stretch"):
        st.session_state["sensitor_review_html"] = WR.build_weekly_html(
            trades, week_of=start, lang=lang, currency=tctx.currency or "$",
            sections=chosen, trader_name=trader or None,
            account_label=tctx.account_id,
        )

    html_doc = st.session_state.get("sensitor_review_html")
    if not html_doc:
        note(tr("report_format_note", lang))
        return

    section(tr("report_ready", lang).upper())
    info_col, download_col = st.columns([2, 1], gap="medium")
    with info_col:
        metric_card(
            tr("weekly_review", lang), f"{len(html_doc) / 1024:.0f} KB",
            bar=1.0,
            caption=f"{len(chosen)} {tr('review_sections', lang).lower()} · "
                    f"{'self-contained HTML' if lang == 'en' else 'HTML autonome'}",
            compact=True,
        )
    with download_col:
        spacer(18)
        st.download_button(
            tr("download_review", lang),
            data=html_doc.encode("utf-8"),
            file_name=f"sensitor_review_{start.strftime('%Y-%m-%d')}.html",
            mime="text/html", width="stretch", key="rev_download",
        )

    note(tr("review_ready", lang))
    with st.expander(tr("report_preview", lang), expanded=True):
        st.components.v1.html(html_doc, height=900, scrolling=True)


def _recent_weeks(trades, limit: int = 12):
    """The weeks that actually contain closed trades, newest first."""
    from ..trading import analytics as TA

    seen = {}
    for trade in TA.closed(trades):
        if not trade.closed_at:
            continue
        start, end = WR.week_bounds(trade.closed_at)
        seen[start] = (start, end, seen.get(start, (None, None, 0))[2] + 1)
    return [seen[key] for key in sorted(seen, reverse=True)][:limit]


def _week_label(start, end, count) -> str:
    from datetime import timedelta
    last = end - timedelta(days=1)
    return (f"{start.strftime('%Y-%m-%d')} → {last.strftime('%m-%d')}  "
            f"({count})")


def _build(ctx, lang, title, client, prepared_by, bench_ticker, chosen) -> str:
    """Assemble everything the report needs, then render it."""
    benchmark_stats = None
    benchmark_name = market.benchmark_label(bench_ticker, lang)
    _, bench_returns = load_benchmark(ctx, bench_ticker)
    if bench_returns is not None:
        benchmark_stats = A.perf_stats(bench_returns)

    stress_results = None
    if "stress" in chosen:
        prices = market.fetch_many_prices(tuple(ctx.tickers), _HISTORY_START)
        if prices:
            bench_prices = market.fetch_prices(bench_ticker, _HISTORY_START)
            stress_results = S.run_all_scenarios(prices, ctx.weights, bench_prices)

    return R.build_html(
        ctx, sections=chosen, lang=lang, title=title or None,
        client_name=client or None, prepared_by=prepared_by or None,
        benchmark_stats=benchmark_stats, benchmark_name=benchmark_name,
        stress_results=stress_results,
    )
