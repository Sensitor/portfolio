"""
TRADING ANALYTICS — slice the history by anything that was recorded.

Two halves. The top is **Trading DNA**: the strongest instrument, setup and
session in the book, each drawn only from buckets with enough trades to compare.
The bottom is the free-form slicer: pick a dimension, pick a metric, and read the
breakdown against the filter.

The discipline that makes this page trustworthy is refusing to promote a small
bucket. A table sorted by win rate always puts a two-trade bucket on top;
`performance.best()` will not return one below the threshold, and every bucket in
every chart and table here carries its `n`. The alternative — a "best setup" card
backed by three trades — is how a journal teaches someone the wrong lesson and
then watches them size up on it.
"""

from __future__ import annotations

import streamlit as st

from ..core.i18n import tr
from ..trading import performance as P
from ..trading.analytics import MIN_MEANINGFUL_SAMPLE
from ..ui import charts as C
from ..ui.components import (
    alert, data_table, metric_card, money, note, page_header, pct, pill_html,
    section, spacer, stat_card,
)
from ..ui.themes import INK_FAINT, INK_MUTED, PALETTE, PLOTLY_CONFIG, STATUS, html
from ._trading_shared import (
    account_selector, duration_text, filter_panel, guard, period_selector,
    pf_text, r_text, sample_pill, trading_context,
)

DIMENSIONS = ["symbol", "setup", "combination", "session", "weekday", "hour",
              "month", "timeframe", "direction", "regime", "risk_band"]
METRICS = ["net_pnl", "expectancy", "win_rate", "avg_r", "total_r"]


def render_trading_analytics(ctx=None) -> None:
    lang = st.session_state.get("language", "en")
    page_header(
        f"{tr('nav_trading', lang)} · {tr('nav_trading_analytics', lang)}",
        tr("trading_analytics_sub", lang),
        eyebrow=tr("product_trading", lang),
    )

    tctx = trading_context(lang)
    if not guard(tctx, lang):
        return

    left, right = st.columns([3, 1.4])
    with left:
        period_selector(tctx, "tan_period")
    with right:
        account_selector(tctx, "tan_account")

    filter_panel(tctx, "tan_filter")

    _dna_block(tctx, lang)
    _slicer_block(tctx, lang)
    _comparison_block(tctx, lang)


# =============================================================================
# TRADING DNA
# =============================================================================

def _dna_block(tctx, lang) -> None:
    section(tr("trading_dna", lang).upper(), tr("trading_dna_sub", lang))

    currency = tctx.currency
    symbols = tctx.breakdown("symbol")
    setups = tctx.breakdown("setup")
    sessions = tctx.breakdown("session")
    risk = tctx.risk.get("profile", {})

    c1, c2, c3, c4 = st.columns(4, gap="medium")

    with c1:
        most = max(symbols, key=lambda r: r["n"]) if symbols else None
        total = sum(r["n"] for r in symbols) or 1
        metric_card(
            tr("most_traded", lang),
            most["label"] if most else "—",
            bar=(most["n"] / total) if most else None,
            bar_color=PALETTE[0],
            caption=(f"{most['n']} {tr('trades', lang).lower()} · "
                     f"{pct(most['n'] / total, 0)}" if most else "—"),
            compact=True,
        )

    with c2:
        _best_card(tr("best_instrument", lang), symbols, currency, lang)
    with c3:
        _best_card(tr("best_setup", lang), setups, currency, lang)
    with c4:
        _best_card(tr("best_session", lang), sessions, currency, lang)

    spacer(12)
    d1, d2, d3, d4 = st.columns(4, gap="medium")
    holding = tctx.holding_time
    metrics = tctx.metrics

    with d1:
        median_risk = risk.get("median_risk")
        metric_card(
            tr("typical_risk", lang),
            money(median_risk, currency, decimals=2) if median_risk is not None else "—",
            bar=risk.get("coverage"),
            bar_color=STATUS["good"] if (risk.get("coverage") or 0) >= 0.9
            else STATUS["warning"],
            caption=(f"{pct(risk.get('coverage', 0), 0)} {tr('with_stop', lang)}"),
            compact=True,
        )
    with d2:
        # The median leads and the mean follows: one trade held over a weekend
        # moves the average by hours and the median not at all.
        metric_card(
            tr("median_holding", lang),
            duration_text(holding.get("median"), lang),
            caption=f"{tr('mean_word', lang)} "
                    f"{duration_text(holding.get('average'), lang)}",
            compact=True,
        )
    with d3:
        n_symbols = metrics["symbols"]
        metric_card(
            tr("total_trades", lang), f"{metrics['n']}",
            caption=f"{n_symbols} "
                    f"{tr('instrument_one' if n_symbols == 1 else 'instrument_many', lang)}",
            compact=True,
        )
    with d4:
        metric_card(
            tr("total_r", lang), r_text(metrics["total_r"]),
            caption=f"{metrics['n_with_r']} {tr('trades', lang).lower()}",
            compact=True,
        )

    note(tr("dna_note", lang))


def _best_card(label, rows, currency, lang) -> None:
    """
    The strongest bucket on a dimension — or nothing, when none qualifies.

    `P.best` refuses a bucket below the sample threshold, so on a short history
    this card shows a dash and says why. That is the honest answer: with eleven
    trades spread over four setups, there is no best setup yet.
    """
    winner = P.best(rows, "expectancy")
    if not winner:
        metric_card(label, "—", caption=tr("not_enough_data", lang), compact=True)
        return

    span = max(abs(r["expectancy"]) for r in rows if r["expectancy"] is not None) or 1
    metric_card(
        label, winner["label"],
        bar=min(max(winner["expectancy"] / span, 0), 1),
        bar_color=STATUS["good"] if winner["expectancy"] >= 0 else STATUS["critical"],
        caption=(f"{money(winner['expectancy'], currency, decimals=2)} "
                 f"{tr('per_trade', lang)} · n={winner['n']}"),
        compact=True,
    )


# =============================================================================
# SLICER
# =============================================================================

def _slicer_block(tctx, lang) -> None:
    section(tr("performance_by", lang).upper())

    dim_labels = [tr(f"d_{d}", lang) for d in DIMENSIONS]
    metric_labels = [tr(_metric_key(m), lang) for m in METRICS]

    c1, c2 = st.columns(2, gap="medium")
    with c1:
        dim_choice = st.selectbox(tr("performance_by", lang), dim_labels, index=0,
                                  key="tan_dim")
    with c2:
        metric_choice = st.selectbox(tr("metric", lang), metric_labels, index=0,
                                     key="tan_metric")

    dimension = DIMENSIONS[dim_labels.index(dim_choice)]
    metric = METRICS[metric_labels.index(metric_choice)]

    rows = tctx.breakdown(dimension)
    if not rows:
        note(tr("not_enough_data", lang))
        return

    st.plotly_chart(
        C.trading_breakdown(rows, metric=metric, currency=tctx.currency, lang=lang),
        width="stretch", config=PLOTLY_CONFIG, key=f"tan_bd_{dimension}_{metric}",
    )

    _breakdown_table(rows, dim_choice, tctx, lang)
    note(tr("sample_note", lang))


def _metric_key(metric: str) -> str:
    return {"net_pnl": "net_pnl", "expectancy": "expectancy", "win_rate": "win_rate",
            "avg_r": "average_r", "total_r": "total_r"}[metric]


def _breakdown_table(rows, dim_label, tctx, lang) -> None:
    currency = tctx.currency
    max_n = max(r["n"] for r in rows) or 1
    table = []
    for row in rows:
        table.append([
            row["label"],
            (str(row["n"]), float(row["n"])),
            pct(row["win_rate"], 0) if row["win_rate"] is not None else "—",
            money(row["net_pnl"], currency),
            money(row["expectancy"], currency, decimals=2)
            if row["expectancy"] is not None else "—",
            pf_text(row["profit_factor"], lang),
            r_text(row["avg_r"]),
        ])
    data_table(
        [dim_label, tr("trades", lang), tr("win_rate", lang), tr("net_pnl", lang),
         tr("expectancy", lang), tr("profit_factor", lang), tr("average_r", lang)],
        table, align="lrrrrrr",
        bars={1: (max_n, PALETTE[1])},
    )


# =============================================================================
# BEST / WORST WITH CONCENTRATION
# =============================================================================

def _comparison_block(tctx, lang) -> None:
    currency = tctx.currency
    setups = tctx.breakdown("setup")
    symbols = tctx.breakdown("symbol")

    concentration = P.concentration(symbols)
    if not concentration:
        return

    section(tr("where_the_result_comes_from", lang).upper())

    profit_share = concentration.get("profit_share")
    busiest_share = concentration.get("busiest_share")
    c1, c2 = st.columns([1, 1.3], gap="large")

    with c1:
        metric_card(
            tr("top_contributor_share", lang),
            pct(profit_share, 0) if profit_share is not None else "—",
            bar=min(max(profit_share or 0, 0), 1),
            bar_color=(STATUS["warning"] if (profit_share or 0) >= 0.6
                       else STATUS["neutral"]),
            caption=(f"{concentration.get('most_profitable', '—')} · "
                     f"{concentration.get('reliable_buckets', 0)}/"
                     f"{concentration.get('n_buckets', 0)} "
                     f"{tr('reliable_buckets', lang)}"),
            compact=True,
        )
        spacer(10)
        metric_card(
            tr("busiest_instrument", lang),
            concentration.get("busiest", "—"),
            bar=min(max(busiest_share or 0, 0), 1),
            bar_color=PALETTE[0],
            caption=(f"{pct(busiest_share, 0)} {tr('of_trades_share', lang)}"
                     if busiest_share is not None else "—"),
            compact=True,
        )
        # Concentration is stated, never judged. One instrument carrying most of
        # the profit is what a specialist's book looks like; it is also what a
        # book carried by a single lucky run looks like. The page cannot tell
        # them apart, so it reports the share and says what it would take to.
        if profit_share is not None and profit_share >= 0.6:
            alert(
                "warning",
                tr("concentrated_result", lang),
                tr("concentrated_result_body", lang).format(
                    label=concentration.get("most_profitable", "—"),
                    share=f"{profit_share * 100:.0f}%"),
                footnote=tr("concentrated_footnote", lang),
            )

    with c2:
        if setups:
            st.plotly_chart(
                C.trading_breakdown(setups, metric="expectancy", currency=currency,
                                    lang=lang, height=max(200, 32 * len(setups) + 44)),
                width="stretch", config=PLOTLY_CONFIG, key="tan_setup_exp",
            )
        else:
            note(tr("not_enough_data", lang))
