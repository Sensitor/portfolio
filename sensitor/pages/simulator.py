"""
SIMULATOR — change the allocation, watch every number move.

Three blocks:

* **What-if** — a slider per holding, with every metric recomputed on the same
  history and shown as before/after. The point is the trade-off: almost no change
  improves everything at once, and the page is built so that shows.
* **Comparison** — the current book against the optimiser's two portfolios and an
  equal-weight alternative, on identical history and one shared equity chart.
* **Monte Carlo** — forward projection from this portfolio's own return
  distribution, as a percentile fan.

Nothing on this page writes to the saved portfolio. The simulated weights live in
session state under their own key and are discarded on reset.
"""

from __future__ import annotations

import streamlit as st

from .. import charts as C
from .. import montecarlo as MC
from .. import simulate as SI
from ..components import (
    alert, data_table, metric_card, money, note, num, page_header, pct, section,
    spacer,
)
from ..design import PLOTLY_CONFIG, PLOTLY_CONFIG_ZOOM, STATUS
from ..i18n import define, tr
from ._shared import guard, period_selector

SIM_KEY = "sensitor_sim_weights"

_METRIC_LABELS = {
    "total_return": "total_return", "cagr": "annualized_return",
    "volatility": "volatility", "sharpe": "sharpe_ratio",
    "sortino": "sortino_ratio", "max_drawdown": "max_drawdown",
    "var_95": "var_95", "effective_assets": "effective_assets",
    "health": "health_score",
}


def render_simulator(ctx) -> None:
    lang = ctx.lang if ctx else st.session_state.get("language", "en")

    page_header(tr("nav_simulator", lang), tr("simulator_sub", lang),
                eyebrow=tr("product_short", lang))
    if not guard(ctx, lang):
        return

    period_selector(ctx, "sim_period")

    current = ctx.weights
    simulated = _simulated_weights(current)

    bundle_kwargs = dict(
        asset_info=ctx.asset_info, sector_map=ctx.sector_map,
        geo_map=ctx.geo_map, profile=ctx.profile,
    )
    before = SI.evaluate_weights(ctx.returns_df, current, **bundle_kwargs)
    after = SI.evaluate_weights(ctx.returns_df, simulated, **bundle_kwargs)

    _what_if_block(ctx, lang, current, simulated, before, after)
    _comparison_block(ctx, lang, before, after, bundle_kwargs)
    _monte_carlo_block(ctx, lang, after or before)


# =============================================================================
# WHAT-IF
# =============================================================================

def _simulated_weights(current: dict) -> dict:
    """Session-held simulated weights, seeded from the live portfolio."""
    stored = st.session_state.get(SIM_KEY)
    if not stored or set(stored) != set(current):
        stored = dict(current)
        st.session_state[SIM_KEY] = stored
    return stored


def _what_if_block(ctx, lang, current, simulated, before, after) -> None:
    section(tr("what_if", lang).upper(), tr("what_if_sub", lang))

    head, reset_col = st.columns([4, 1])
    with reset_col:
        if st.button(tr("reset_allocation", lang), key="sim_reset",
                     width="stretch"):
            st.session_state[SIM_KEY] = dict(current)
            for ticker in current:
                st.session_state.pop(f"sim_w_{ticker}", None)
            st.rerun()

    tickers = sorted(current, key=lambda t: -current[t])
    columns = st.columns(min(len(tickers), 4), gap="medium")
    raw = {}
    for i, ticker in enumerate(tickers):
        with columns[i % len(columns)]:
            raw[ticker] = st.slider(
                ticker, min_value=0.0, max_value=100.0,
                value=float(round(simulated.get(ticker, 0.0) * 100, 1)),
                step=0.5, key=f"sim_w_{ticker}", format="%.1f%%",
            ) / 100

    normalised = SI.normalise(raw, drop_zero=False)
    if not normalised:
        note(tr("no_data_body", lang))
        return
    st.session_state[SIM_KEY] = normalised

    changed = any(abs(normalised.get(t, 0) - current.get(t, 0)) > 0.001 for t in current)
    note(tr("normalise_note", lang))

    if not changed:
        alert("good", tr("no_change_yet", lang).split(".")[0],
              tr("no_change_yet", lang))
        return
    if not after:
        note(tr("short_history_body", lang))
        return

    spacer(8)
    _impact_cards(lang, before, after, ctx.currency, ctx.end_value)

    # Allocation delta
    changes = [
        {"ticker": t, "before": current.get(t, 0.0), "after": normalised.get(t, 0.0),
         "delta": normalised.get(t, 0.0) - current.get(t, 0.0)}
        for t in sorted(set(current) | set(normalised))
        if abs(normalised.get(t, 0.0) - current.get(t, 0.0)) >= 0.005
    ]
    changes.sort(key=lambda c: abs(c["delta"]), reverse=True)

    if changes:
        chart_col, risk_col = st.columns([1, 1.15], gap="large")
        with chart_col:
            st.plotly_chart(
                C.allocation_change_bars(changes),
                width="stretch", config=PLOTLY_CONFIG, key="sim_changes",
            )
        with risk_col:
            rc = after.get("risk_contribution")
            if rc is not None and not rc.empty:
                st.plotly_chart(
                    C.weight_vs_risk(rc, label_weight=tr("weight", lang),
                                     label_risk=tr("risk_contribution", lang)),
                    width="stretch", config=PLOTLY_CONFIG, key="sim_risk",
                )
    note(tr("simulation_note", lang))


def _impact_cards(lang, before, after, currency, value) -> None:
    """Six headline metrics, each as before -> after with direction applied."""
    rows = [
        ("cagr", before["stats"]["cagr"], after["stats"]["cagr"], True, True),
        ("volatility", before["stats"]["volatility"], after["stats"]["volatility"], True, False),
        ("sharpe", before["stats"]["sharpe"], after["stats"]["sharpe"], False, True),
        ("max_drawdown", before["stats"]["max_drawdown"], after["stats"]["max_drawdown"],
         True, True),
        ("var_95", -before["var"].get("historical_var", 0.0),
         -after["var"].get("historical_var", 0.0), True, True),
        ("health", before.get("health", {}).get("total", 0.0),
         after.get("health", {}).get("total", 0.0), False, True),
    ]

    for start in (0, 3):
        cols = st.columns(3, gap="medium")
        for col, (key, b, a, is_pct, higher) in zip(cols, rows[start:start + 3]):
            delta = a - b
            improved = (delta > 0) if higher else (delta < 0)
            with col:
                metric_card(
                    tr(_METRIC_LABELS.get(key, key), lang),
                    pct(a, 1) if is_pct else (f"{a:.0f}" if key == "health" else num(a, 2)),
                    delta=delta if abs(delta) > 1e-9 else None,
                    delta_label=f"{tr('vs', lang)} {tr('current', lang).lower()}",
                    delta_as_pct=is_pct,
                    higher_is_better=higher,
                    bar=min(max(a / 100 if key == "health" else abs(a) / 0.5, 0), 1),
                    bar_color=STATUS["good"] if improved else STATUS["warning"],
                    caption=(f"{tr('current', lang)} "
                             f"{pct(b, 1) if is_pct else (f'{b:.0f}' if key == 'health' else num(b, 2))}"),
                    tooltip=define(key if key != "var_95" else "var", lang),
                )
        spacer(10)


# =============================================================================
# COMPARISON
# =============================================================================

def _comparison_block(ctx, lang, before, after, bundle_kwargs) -> None:
    section(tr("comparison", lang).upper(), tr("comparison_sub", lang))

    bundles = {tr("current", lang): before}

    frontier = ctx.frontier
    if frontier:
        for key, label_key in (("max_sharpe", "max_sharpe_portfolio"),
                               ("min_volatility", "min_vol_portfolio")):
            point = frontier.get(key)
            if point:
                bundle = SI.evaluate_weights(ctx.returns_df, point["weights"], **bundle_kwargs)
                if bundle:
                    bundles[tr(label_key, lang)] = bundle

    equal = {t: 1 / len(ctx.weights) for t in ctx.weights}
    equal_bundle = SI.evaluate_weights(ctx.returns_df, equal, **bundle_kwargs)
    if equal_bundle:
        bundles[tr("equal_weight", lang)] = equal_bundle

    if after and st.session_state.get(SIM_KEY) != ctx.weights:
        bundles[tr("simulated", lang)] = after

    if len(bundles) < 2:
        note(tr("frontier_unavailable", lang))
        return

    curves = SI.equity_curves(bundles, base=ctx.start_value or 100_000)
    st.plotly_chart(
        C.cumulative_performance(curves, height=360, value_prefix=ctx.currency),
        width="stretch", config=PLOTLY_CONFIG_ZOOM, key="sim_compare",
    )

    labels = list(bundles)
    rows = []
    for row in SI.compare(bundles):
        key = row["metric"]
        cells = [tr(_METRIC_LABELS.get(key, key), lang)]
        for label in labels:
            value = row["values"].get(label)
            if value is None:
                cells.append("—")
                continue
            if row["is_pct"]:
                text = pct(value, 1)
            elif key == "health":
                text = f"{value:.0f}"
            else:
                text = num(value, 2)
            cells.append(f"{text}  ●" if row["best"] == label else text)
        rows.append(cells)

    data_table([""] + labels, rows, align="l" + "r" * len(labels))
    note("● = " + tr("best", lang) + ". " + tr("simulation_note", lang))


# =============================================================================
# MONTE CARLO
# =============================================================================

def _monte_carlo_block(ctx, lang, bundle) -> None:
    section(tr("monte_carlo", lang).upper(), tr("monte_carlo_sub", lang))

    if not bundle:
        note(tr("short_history_body", lang))
        return

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    with c1:
        years = st.slider(tr("horizon", lang), 1, 30, 10, key="mc_years",
                          format="%d " + tr("years_label", lang))
    with c2:
        simulations = st.select_slider(
            tr("simulations", lang), options=[500, 1000, 2000, 5000, 10000],
            value=2000, key="mc_sims",
        )
    with c3:
        contribution = st.number_input(
            tr("annual_contribution", lang), min_value=0, max_value=1_000_000,
            value=0, step=1000, key="mc_contrib",
        )
    with c4:
        method_labels = {tr("method_bootstrap", lang): "bootstrap",
                         tr("method_parametric", lang): "parametric"}
        method = method_labels[st.selectbox(
            tr("method", lang), list(method_labels), key="mc_method",
        )]

    result = MC.simulate(
        bundle["returns"], initial_value=ctx.end_value or 100_000,
        years=years, simulations=simulations, method=method,
        contribution_per_year=float(contribution),
    )
    if not result:
        note(tr("short_history_body", lang))
        return

    if result["horizon_days"] > result["history_days"] * 4:
        alert("warning", tr("mc_history_warning", lang).split(",")[0],
              tr("mc_history_warning", lang),
              footnote=f"{result['history_days']} {tr('days', lang)} → "
                       f"{result['horizon_days']} {tr('days', lang)}")

    spacer(8)
    terminals = result["terminal_percentiles"]
    m1, m2, m3, m4 = st.columns(4, gap="medium")
    with m1:
        metric_card(tr("median_outcome", lang), money(result["median"], ctx.currency),
                    bar=0.5, caption=f"{tr('current', lang)} "
                                     f"{money(result['initial_value'], ctx.currency)}")
    with m2:
        metric_card(tr("pessimistic", lang), money(terminals[10], ctx.currency),
                    bar=0.1, bar_color=STATUS["critical"],
                    caption=f"10% {'of paths below' if lang == 'en' else 'des trajectoires en dessous'}")
    with m3:
        metric_card(tr("optimistic", lang), money(terminals[90], ctx.currency),
                    bar=0.9, bar_color=STATUS["good"],
                    caption=f"10% {'of paths above' if lang == 'en' else 'des trajectoires au-dessus'}")
    with m4:
        metric_card(tr("prob_loss", lang), pct(result["prob_loss"], 0),
                    bar=result["prob_loss"], higher_is_better=False,
                    bar_color=(STATUS["good"] if result["prob_loss"] < 0.15 else
                               STATUS["warning"] if result["prob_loss"] < 0.35 else STATUS["critical"]),
                    caption=f"{tr('vs', lang)} {money(result['invested'], ctx.currency)} "
                            f"{'invested' if lang == 'en' else 'investi'}")

    spacer(10)
    st.plotly_chart(
        C.fan_chart(result, currency=ctx.currency, lang=lang),
        width="stretch", config=PLOTLY_CONFIG_ZOOM, key="mc_fan",
    )

    dist_col, prob_col = st.columns([1.4, 1], gap="large")
    with dist_col:
        st.markdown(f"**{tr('terminal_values', lang)}**")
        st.plotly_chart(
            C.terminal_distribution(result, currency=ctx.currency, lang=lang),
            width="stretch", config=PLOTLY_CONFIG, key="mc_terminal",
        )
    with prob_col:
        st.markdown(f"**{tr('prob_targets', lang)}**")
        targets = MC.suggest_targets(result)
        probabilities = MC.probability_of_reaching(result, targets)
        if probabilities:
            st.plotly_chart(
                C.probability_bars(probabilities, currency=ctx.currency),
                width="stretch", config=PLOTLY_CONFIG, key="mc_probs",
            )

    annualised = MC.annualised_outcomes(result)
    if annualised:
        rows = [[f"P{p}", money(terminals[p], ctx.currency), pct(annualised[p], 1)]
                for p in sorted(annualised)]
        data_table(
            ["", tr("terminal_values", lang), tr("annualized_return", lang)],
            rows, align="lrr",
        )

    note(tr("mc_note", lang))
