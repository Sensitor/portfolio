"""
STRESS LAB — what breaks, and by how much.

Two blocks with deliberately different epistemics, kept visually distinct so the
reader never confuses them:

* **Historical scenarios** replay real prices over real crisis windows. No model.
  The only caveat is coverage, which is shown on every card.
* **Custom shocks** propagate user-chosen driver moves through regression betas.
  That is a model, calibrated on ordinary conditions, and the page says so.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ..ui import charts as C
from ..integrations import market_data as market
from ..investment import stress as S
from ..ui.components import (
    alert, data_table, metric_card, money, note, num, page_header, pct, pill_html,
    section, spacer,
)
from ..ui.themes import INK, INK_2, INK_FAINT, INK_MUTED, PLOTLY_CONFIG, STATUS, html
from ..core.i18n import tr
from ..integrations.market_data import benchmark_label
from ._shared import benchmark_selector, guard

# Crisis windows reach back to 2000, well before any portfolio's own window.
_HISTORY_START = "1999-01-01"


def render_stress(ctx) -> None:
    lang = ctx.lang if ctx else st.session_state.get("language", "en")

    page_header(tr("nav_stress", lang), tr("stress_sub", lang),
                eyebrow=tr("product_short", lang))
    if not guard(ctx, lang):
        return

    _historical_block(ctx, lang)
    _custom_block(ctx, lang)


# =============================================================================
# HISTORICAL
# =============================================================================

def _historical_block(ctx, lang: str) -> None:
    section(tr("historical_scenarios", lang).upper(), tr("historical_sub", lang))

    bench_ticker = benchmark_selector(ctx, "stress_bench")
    bench_name = benchmark_label(bench_ticker, lang)

    with st.spinner(""):
        prices = market.fetch_many_prices(tuple(ctx.tickers), _HISTORY_START)
        bench_prices = market.fetch_prices(bench_ticker, _HISTORY_START)

    if not prices:
        note(tr("benchmark_unavailable", lang))
        return

    results = S.run_all_scenarios(prices, ctx.weights, bench_prices)
    if not results:
        note(tr("no_history_window", lang))
        return

    # ── Scenario cards ───────────────────────────────────────────────────────
    for row in range(0, len(results), 4):
        chunk = results[row:row + 4]
        cols = st.columns(len(chunk), gap="medium")
        for col, result in zip(cols, chunk):
            with col:
                _scenario_card(result, lang)

    spacer(12)

    # ── Comparison chart ─────────────────────────────────────────────────────
    rows = [
        {"label": S.scenario_label(r["key"], lang),
         "portfolio": r["portfolio_return"],
         "benchmark": r.get("benchmark_return")}
        for r in results if r.get("reliable")
    ]
    if rows:
        st.plotly_chart(
            C.scenario_bars(rows, label_portfolio=tr("portfolio", lang),
                            label_benchmark=bench_name),
            width="stretch", config=PLOTLY_CONFIG, key="stress_scenarios",
        )

    # ── Detail table ─────────────────────────────────────────────────────────
    table_rows = []
    for result in results:
        bench = result.get("benchmark_return")
        table_rows.append([
            S.scenario_label(result["key"], lang),
            f"{result['start']} → {result['end']}",
            pct(result["portfolio_return"], 1),
            pct(bench, 1) if bench is not None else "—",
            pct(result["relative"], 1) if result.get("relative") is not None else "—",
            f"{result['coverage'] * 100:.0f}%",
            result.get("worst_asset") or "—",
        ])
    data_table(
        [tr("historical_scenarios", lang), tr("period", lang), tr("portfolio", lang),
         bench_name, "Δ", tr("coverage", lang), tr("worst_contributor", lang)],
        table_rows, align="llrrrrl",
    )
    note(tr("historical_note", lang))


def _scenario_card(result: dict, lang: str) -> None:
    """One crisis, with its coverage stated on the face of the card."""
    key = result["key"]
    label = S.scenario_label(key, lang)
    coverage = result["coverage"]
    reliable = result.get("reliable", False)

    portfolio_return = result["portfolio_return"]
    tone = ("critical" if portfolio_return <= -0.30 else
            "serious" if portfolio_return <= -0.15 else
            "warning" if portfolio_return < 0 else "good")

    coverage_pill = pill_html(
        f"{tr('coverage', lang)} {coverage * 100:.0f}%",
        "good" if reliable else "warning",
    )
    bench = result.get("benchmark_return")
    bench_line = (
        f'<div style="font-size:0.72rem;color:{INK_MUTED};margin-top:8px;">'
        f'{tr("benchmark_impact", lang)}: '
        f'<b style="color:{INK_2};">{pct(bench, 1)}</b></div>'
    ) if bench is not None else ""

    html(
        f'<div class="snr-card" style="border-left:3px solid {STATUS[tone]};">'
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px;">'
        f'<div class="snr-metric-label" style="text-transform:none;letter-spacing:0;'
        f'font-size:0.82rem;color:{INK};font-weight:700;">{label}</div>'
        f'</div>'
        f'<div class="snr-num" style="font-size:1.7rem;font-weight:800;color:{STATUS[tone]};'
        f'letter-spacing:-0.035em;margin-top:10px;">{pct(portfolio_return, 1)}</div>'
        f'{bench_line}'
        f'<div style="margin-top:10px;">{coverage_pill}</div>'
        f'<div style="font-size:0.7rem;color:{INK_FAINT};margin-top:10px;line-height:1.5;">'
        f'{S.scenario_description(key, lang)}</div>'
        f'</div>'
    )

    if not reliable:
        missing = ", ".join(result.get("missing", [])[:4]) or "—"
        alert("warning", tr("coverage_warning", lang).split(".")[0],
              f"{tr('missing_holdings', lang)}: {missing}",
              footnote=f"{tr('coverage', lang)} {coverage * 100:.0f}% "
                       f"< {S.MIN_COVERAGE * 100:.0f}%")


# =============================================================================
# CUSTOM SHOCKS
# =============================================================================

def _custom_block(ctx, lang: str) -> None:
    section(tr("custom_stress", lang).upper(), tr("custom_stress_sub", lang))

    driver_returns = _load_drivers(ctx)
    if driver_returns is None or driver_returns.empty:
        note(tr("benchmark_unavailable", lang))
        return

    # ── Shock inputs ─────────────────────────────────────────────────────────
    shocks = {}
    cols = st.columns(len(S.DRIVER_ORDER), gap="medium")
    for col, ticker in zip(cols, S.DRIVER_ORDER):
        if ticker not in driver_returns.columns:
            continue
        with col:
            default = int(S.DRIVERS[ticker]["default"] * 100)
            value = st.slider(
                S.driver_label(ticker, lang),
                min_value=-80, max_value=50, value=default, step=5,
                key=f"shock_{ticker}", format="%d%%",
            )
            shocks[ticker] = value / 100

    if not shocks:
        note(tr("benchmark_unavailable", lang))
        return

    betas = S.estimate_betas(
        market.normalise_index(ctx.returns_df), driver_returns[list(shocks)]
    )
    if not betas:
        note(tr("short_history_body", lang))
        return

    result = S.custom_shock(ctx.weights, betas, shocks, ctx.end_value)
    if not result.get("covered"):
        note(tr("short_history_body", lang))
        return

    shock = result["portfolio_shock"]
    metrics = S.stressed_metrics(ctx.portfolio_returns, shock, ctx.stats)

    spacer(10)

    # ── Before / after ───────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4, gap="medium")
    with c1:
        metric_card(
            tr("estimated_impact", lang), pct(shock, 1),
            bar=min(abs(shock) / 0.6, 1), higher_is_better=False,
            bar_color=STATUS["critical"] if shock < -0.2 else STATUS["warning"],
            caption=f"{tr('coverage', lang)} {result['coverage'] * 100:.0f}%",
        )
    with c2:
        metric_card(
            tr("portfolio_value", lang),
            money(result["value_after"], ctx.currency),
            delta=shock, delta_label=tr("stressed", lang), higher_is_better=False,
            caption=f"{tr('before', lang)} {money(result['value_before'], ctx.currency)}",
        )
    with c3:
        after_dd = metrics["after"]["max_drawdown"]
        metric_card(
            tr("max_drawdown", lang), pct(after_dd, 1),
            bar=min(abs(after_dd) / 0.6, 1), higher_is_better=False,
            bar_color=STATUS["critical"],
            caption=f"{tr('before', lang)} {pct(metrics['before']['max_drawdown'], 1)}",
        )
    with c4:
        metric_card(
            tr("fit_quality", lang), num(result["mean_r_squared"], 2),
            bar=result["mean_r_squared"],
            bar_color=(STATUS["good"] if result["mean_r_squared"] >= 0.7 else
                       STATUS["warning"] if result["mean_r_squared"] >= 0.4 else STATUS["critical"]),
            caption="R² " + ("of the beta model" if lang == "en" else "du modèle de bêtas"),
        )

    spacer(10)

    # ── Before / after comparison ────────────────────────────────────────────
    comparison = [
        {"label": tr("portfolio_value", lang),
         "before": abs(result["value_before"] or 0), "after": abs(result["value_after"] or 0),
         "before_text": money(result["value_before"], ctx.currency),
         "after_text": money(result["value_after"], ctx.currency), "tone": "critical"},
        {"label": tr("total_return", lang),
         "before": metrics["before"]["total_return"], "after": metrics["after"]["total_return"],
         "before_text": pct(metrics["before"]["total_return"], 1),
         "after_text": pct(metrics["after"]["total_return"], 1), "tone": "serious"},
        {"label": tr("max_drawdown", lang),
         "before": metrics["before"]["max_drawdown"], "after": metrics["after"]["max_drawdown"],
         "before_text": pct(metrics["before"]["max_drawdown"], 1),
         "after_text": pct(metrics["after"]["max_drawdown"], 1), "tone": "critical"},
    ]
    st.plotly_chart(
        C.before_after_bars(comparison, label_before=tr("before", lang),
                            label_after=tr("after", lang)),
        width="stretch", config=PLOTLY_CONFIG, key="stress_before_after",
    )

    # ── Per-holding response ─────────────────────────────────────────────────
    ordered = sorted(result["per_asset"].items(), key=lambda kv: kv[1]["contribution"])
    st.plotly_chart(
        C.contribution_bars([t for t, _ in ordered],
                            [v["contribution"] for _, v in ordered]),
        width="stretch", config=PLOTLY_CONFIG, key="stress_contrib",
    )

    rows = [
        [ticker, pct(v["weight"], 1), pct(v["shock"], 1), pct(v["contribution"], 2),
         num(v["r_squared"], 2)]
        for ticker, v in sorted(result["per_asset"].items(),
                                key=lambda kv: kv[1]["contribution"])
    ]
    data_table(
        [tr("assets", lang), tr("weight", lang),
         "Asset response" if lang == "en" else "Réaction de l'actif",
         tr("attribution", lang), "R²"],
        rows, align="lrrrr",
    )
    note(tr("shock_note", lang))


def _load_drivers(ctx):
    """
    Driver return series, reusing the portfolio's own data where it overlaps.

    A book that already holds SPY needs no extra download for the equity driver,
    which keeps the request count (and the rate-limit risk) down.
    """
    local = market.normalise_index(ctx.returns_df)
    have = {t: local[t] for t in S.DRIVER_ORDER if t in local.columns}
    need = tuple(t for t in S.DRIVER_ORDER if t not in have)

    if need:
        start = local.index[0].strftime("%Y-%m-%d")
        for ticker, series in market.fetch_many_returns(need, start).items():
            normalised = market.normalise_index(series)
            overlap = normalised.index.intersection(local.index)
            if len(overlap) >= 60:
                have[ticker] = normalised

    if not have:
        return None
    frame = pd.DataFrame(have).dropna()
    return frame if len(frame) >= 60 else None
