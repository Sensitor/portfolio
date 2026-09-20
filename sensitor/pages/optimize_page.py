"""
OPTIMIZE — the efficient frontier, and where you sit on it.

Shows the risk/return geometry of the holdings, the two portfolios worth naming
(minimum volatility and maximum Sharpe), and the weight moves that would take the
current allocation to either of them.

The page states plainly what the frontier is: a picture of one past window, from
estimates that mean-variance optimisation is notoriously sensitive to. A position
cap is exposed as a control rather than hidden, because the cap is the single
biggest determinant of how sane the output looks.
"""

from __future__ import annotations

import streamlit as st

from ..ui import charts as C
from ..investment import optimize as O
from ..ui.components import (
    data_table, empty_state, metric_card, note, num, page_header, pct, section, spacer,
)
from ..ui.themes import PLOTLY_CONFIG, PLOTLY_CONFIG_ZOOM, STATUS
from ..core.i18n import define, tr
from ._shared import guard, period_selector


def render_optimize(ctx) -> None:
    lang = ctx.lang if ctx else st.session_state.get("language", "en")

    page_header(tr("nav_optimize", lang), tr("optimize_sub", lang),
                eyebrow=tr("product_short", lang))
    if not guard(ctx, lang):
        return

    left, right = st.columns([3, 1.4])
    with left:
        period_selector(ctx, "opt_period")
    with right:
        cap = st.slider(
            tr("max_position", lang), min_value=10, max_value=100,
            value=int(ctx.frontier_bounds[1] * 100), step=5,
            key="opt_cap", format="%d%%",
        )
    ctx.set_frontier_bounds((0.0, cap / 100))

    result = ctx.frontier
    if not result or not result.get("frontier"):
        empty_state(tr("efficient_frontier", lang), tr("frontier_unavailable", lang), icon="◫")
        return

    current = result["current"]
    max_sharpe = result.get("max_sharpe")
    min_vol = result.get("min_volatility")

    # ── Named portfolios ─────────────────────────────────────────────────────
    section(tr("efficient_frontier", lang).upper(),
            f"{len(result['tickers'])} {tr('assets', lang).lower()} · {ctx.period}")

    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        metric_card(
            tr("current_portfolio", lang), num(current["sharpe"], 2),
            bar=min(max((current["sharpe"] + 0.5) / 3.0, 0), 1),
            tooltip=define("sharpe", lang),
            caption=(f"{pct(current['return'], 1)} {tr('expected_return', lang).lower()} · "
                     f"{pct(current['volatility'], 1)} vol"),
        )
    with c2:
        if max_sharpe:
            metric_card(
                tr("max_sharpe_portfolio", lang), num(max_sharpe["sharpe"], 2),
                delta=max_sharpe["sharpe"] - current["sharpe"],
                delta_label=tr("vs", lang) + " " + tr("current_portfolio", lang).lower(),
                delta_as_pct=False,
                bar=min(max((max_sharpe["sharpe"] + 0.5) / 3.0, 0), 1),
                bar_color=STATUS["good"],
                caption=(f"{pct(max_sharpe['return'], 1)} · "
                         f"{pct(max_sharpe['volatility'], 1)} vol"),
            )
    with c3:
        if min_vol:
            metric_card(
                tr("min_vol_portfolio", lang), pct(min_vol["volatility"], 1),
                delta=min_vol["volatility"] - current["volatility"],
                delta_label=tr("vs", lang) + " " + tr("current_portfolio", lang).lower(),
                higher_is_better=False,
                bar=min(min_vol["volatility"] / 0.45, 1),
                caption=(f"{pct(min_vol['return'], 1)} {tr('expected_return', lang).lower()} · "
                         f"Sharpe {min_vol['sharpe']:.2f}"),
            )

    spacer(10)
    st.plotly_chart(
        C.frontier_scatter(result, lang=lang),
        width="stretch", config=PLOTLY_CONFIG_ZOOM, key="opt_frontier",
    )
    note(tr("frontier_note", lang))

    # ── Move to a target allocation ──────────────────────────────────────────
    section(tr("allocation_change", lang).upper())

    targets = {}
    if max_sharpe:
        targets[tr("max_sharpe_portfolio", lang)] = max_sharpe
    if min_vol:
        targets[tr("min_vol_portfolio", lang)] = min_vol
    if not targets:
        return

    target_name = st.radio(
        tr("target_allocation", lang), list(targets), horizontal=True,
        key="opt_target", label_visibility="collapsed",
    )
    target = targets[target_name]
    changes = O.weight_changes(current["weights"], target["weights"])

    chart_col, table_col = st.columns([1.2, 1], gap="large")
    with chart_col:
        if changes:
            st.plotly_chart(
                C.allocation_change_bars(changes),
                width="stretch", config=PLOTLY_CONFIG, key="opt_changes",
            )
        else:
            note(tr("no_signals_body", lang))
    with table_col:
        rows = [
            [tr("expected_return", lang), pct(current["return"], 1), pct(target["return"], 1),
             pct(target["return"] - current["return"], 1)],
            [tr("volatility", lang), pct(current["volatility"], 1), pct(target["volatility"], 1),
             pct(target["volatility"] - current["volatility"], 1)],
            [tr("sharpe_ratio", lang), num(current["sharpe"], 2), num(target["sharpe"], 2),
             num(target["sharpe"] - current["sharpe"], 2)],
        ]
        data_table(
            ["", tr("current_portfolio", lang), target_name, "Δ"], rows, align="lrrr",
        )

    # ── Full target weights ──────────────────────────────────────────────────
    spacer(8)
    weight_rows = [
        [ticker,
         pct(current["weights"].get(ticker, 0.0), 1),
         pct(target["weights"].get(ticker, 0.0), 1),
         pct(target["weights"].get(ticker, 0.0) - current["weights"].get(ticker, 0.0), 1)]
        for ticker in sorted(target["weights"], key=lambda t: -target["weights"][t])
    ]
    data_table(
        [tr("assets", lang), tr("current_portfolio", lang), target_name, "Δ"],
        weight_rows, align="lrrr",
    )
