"""
PERFORMANCE — how it performed, and what drove it.

Three questions in order: what did it return, how did that return behave over time
(rolling metrics), and which holdings produced it (attribution). The benchmark
comparison sits alongside rather than on a second axis — both series are indexed
to the same base so one scale carries them.
"""

from __future__ import annotations

import numpy as np
import streamlit as st

from ..investment import analytics as A
from ..ui import charts as C
from ..ui.components import (
    data_table, metric_card, note, num, page_header, pct, section, spacer, stat_card,
)
from ..ui.themes import PLOTLY_CONFIG, PLOTLY_CONFIG_ZOOM, STATUS
from ..core.i18n import define, tr
from ..integrations.market_data import benchmark_label
from ._shared import benchmark_selector, guard, load_benchmark, period_selector

_MONTHS = {
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "fr": ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sep", "Oct", "Nov", "Déc"],
}


def render_performance(ctx) -> None:
    lang = ctx.lang if ctx else st.session_state.get("language", "en")

    page_header(tr("nav_performance", lang), tr("performance_sub", lang),
                eyebrow=tr("product_short", lang))
    if not guard(ctx, lang):
        return

    left, right = st.columns([3, 1.4])
    with left:
        period_selector(ctx, "perf_period")
    with right:
        bench_ticker = benchmark_selector(ctx, "perf_bench")

    port_aligned, bench_aligned = load_benchmark(ctx, bench_ticker)
    bench_name = benchmark_label(bench_ticker, lang)
    stats = ctx.stats

    # ── Headline figures ─────────────────────────────────────────────────────
    values = ctx.values
    c1, c2, c3, c4 = st.columns(4, gap="medium")
    with c1:
        metric_card(tr("total_return", lang), pct(stats["total_return"], 1),
                    spark=values.to_numpy().tolist(),
                    bar=min(max((stats["total_return"] + 0.5) / 1.5, 0), 1),
                    bar_color=STATUS["good"] if stats["total_return"] >= 0 else STATUS["critical"])
    with c2:
        metric_card(tr("annualized_return", lang), pct(stats["cagr"], 1),
                    bar=min(max((stats["cagr"] + 0.2) / 0.6, 0), 1),
                    caption=f"{stats['years']:.1f} {'years' if lang == 'en' else 'ans'}")
    with c3:
        metric_card(tr("best_day", lang), pct(stats["best_day"], 2),
                    bar=min(stats["best_day"] / 0.12, 1), bar_color=STATUS["good"])
    with c4:
        metric_card(tr("positive_days", lang), pct(stats["hit_rate"], 1),
                    bar=stats["hit_rate"],
                    bar_color=STATUS["good"] if stats["hit_rate"] >= 0.5 else STATUS["warning"],
                    caption=f"{stats['n_days']} {tr('days', lang)}")

    # ── Cumulative performance ───────────────────────────────────────────────
    section(tr("cumulative_performance", lang).upper(),
            f"{tr('portfolio', lang)} {tr('vs', lang)} {bench_name} — {ctx.period}")

    series_map = {tr("portfolio", lang): values}
    if bench_aligned is not None:
        series_map[bench_name] = A.cumulative(bench_aligned) * ctx.start_value
    st.plotly_chart(
        C.cumulative_performance(series_map, height=400, value_prefix=ctx.currency),
        width='stretch', config=PLOTLY_CONFIG_ZOOM, key="perf_cum",
    )

    # ── Benchmark analysis ───────────────────────────────────────────────────
    section(tr("benchmark_analysis", lang).upper(), bench_name)
    if bench_aligned is None:
        note(tr("benchmark_unavailable", lang))
    else:
        bench = A.benchmark_stats(port_aligned, bench_aligned)
        b1, b2, b3, b4 = st.columns(4, gap="medium")
        with b1:
            metric_card(tr("beta", lang), num(bench["beta"], 2),
                        bar=min(abs(bench["beta"]) / 2, 1),
                        tooltip=define("beta", lang), caption=f"{tr('vs', lang)} {bench_name}")
        with b2:
            metric_card(tr("alpha", lang), pct(bench["alpha"], 2),
                        bar=min(max((bench["alpha"] + 0.1) / 0.2, 0), 1),
                        bar_color=STATUS["good"] if bench["alpha"] >= 0 else STATUS["critical"],
                        tooltip=define("alpha", lang), caption="annualised" if lang == "en" else "annualisé")
        with b3:
            metric_card(tr("r_squared", lang), num(bench["r_squared"], 2),
                        bar=bench["r_squared"], tooltip=define("r_squared", lang))
        with b4:
            metric_card(tr("information_ratio", lang), num(bench["information_ratio"], 2),
                        bar=min(max((bench["information_ratio"] + 1) / 3, 0), 1),
                        tooltip=define("information_ratio", lang))

        spacer(12)
        e1, e2, e3, e4 = st.columns(4, gap="medium")
        with e1:
            stat_card(tr("active_return", lang), pct(bench["active_return"], 2),
                      tone="good" if bench["active_return"] >= 0 else "critical")
        with e2:
            stat_card(tr("tracking_error", lang), pct(bench["tracking_error"], 2),
                      tooltip=define("tracking_error", lang))
        with e3:
            stat_card(tr("up_capture", lang), pct(bench["up_capture"], 0),
                      tone="good" if bench["up_capture"] >= 1 else None,
                      tooltip=define("capture", lang))
        with e4:
            stat_card(tr("down_capture", lang), pct(bench["down_capture"], 0),
                      tone="good" if bench["down_capture"] <= 1 else "warning",
                      tooltip=define("capture", lang))

        spacer(10)
        rows = [
            [tr("total_return", lang), pct(bench["portfolio"]["total_return"], 1),
             pct(bench["benchmark"]["total_return"], 1),
             pct(bench["portfolio"]["total_return"] - bench["benchmark"]["total_return"], 1)],
            [tr("annualized_return", lang), pct(bench["portfolio"]["cagr"], 1),
             pct(bench["benchmark"]["cagr"], 1),
             pct(bench["portfolio"]["cagr"] - bench["benchmark"]["cagr"], 1)],
            [tr("volatility", lang), pct(bench["portfolio"]["volatility"], 1),
             pct(bench["benchmark"]["volatility"], 1),
             pct(bench["portfolio"]["volatility"] - bench["benchmark"]["volatility"], 1)],
            [tr("sharpe_ratio", lang), num(bench["portfolio"]["sharpe"], 2),
             num(bench["benchmark"]["sharpe"], 2),
             num(bench["portfolio"]["sharpe"] - bench["benchmark"]["sharpe"], 2)],
            [tr("max_drawdown", lang), pct(bench["portfolio"]["max_drawdown"], 1),
             pct(bench["benchmark"]["max_drawdown"], 1),
             pct(bench["portfolio"]["max_drawdown"] - bench["benchmark"]["max_drawdown"], 1)],
        ]
        data_table(["", tr("portfolio", lang), bench_name, "Δ"], rows, align="lrrr")

    # ── Attribution ──────────────────────────────────────────────────────────
    section(tr("attribution", lang).upper(), tr("attribution_sub", lang))
    attribution = ctx.attribution
    if attribution is not None and not attribution.empty:
        st.plotly_chart(
            C.contribution_bars(attribution["ticker"].tolist(),
                                attribution["contribution"].tolist()),
            width='stretch', config=PLOTLY_CONFIG, key="perf_attr",
        )
        rows = [
            [row["ticker"], pct(row["weight"], 1), pct(row["asset_return"], 1),
             pct(row["contribution"], 2)]
            for _, row in attribution.iterrows()
        ]
        rows.append(["Σ " + tr("portfolio", lang), "100.0%", "—", pct(stats["total_return"], 2)])
        data_table(
            [tr("assets", lang), tr("weight", lang),
             "Asset return" if lang == "en" else "Rendement actif",
             tr("attribution", lang)],
            rows, align="lrrr",
        )
        note(define("attribution", lang))

    # ── Rolling metrics ──────────────────────────────────────────────────────
    section(tr("rolling_metrics", lang).upper(), "63-day window")
    rolling = A.rolling_stats(ctx.portfolio_returns, window=63)
    if rolling.empty:
        note(tr("short_history_body", lang))
    else:
        r1, r2 = st.columns(2, gap="large")
        with r1:
            st.markdown(f"**{tr('rolling_volatility', lang)}**")
            st.plotly_chart(
                C.rolling_metric(rolling, "volatility", height=210,
                                 reference=float(rolling["volatility"].mean())),
                width='stretch', config=PLOTLY_CONFIG, key="perf_rvol",
            )
        with r2:
            st.markdown(f"**{tr('rolling_sharpe', lang)}**")
            st.plotly_chart(
                C.rolling_metric(rolling, "sharpe", height=210, as_pct=False, reference=1.0),
                width='stretch', config=PLOTLY_CONFIG, key="perf_rsharpe",
            )

    # ── Monthly returns ──────────────────────────────────────────────────────
    monthly = A.monthly_returns(ctx.portfolio_returns)
    if not monthly.empty:
        section(tr("monthly_returns", lang).upper())
        months = _MONTHS.get(lang, _MONTHS["en"])
        headers = [""] + [months[m - 1] for m in monthly.columns] + ["Σ"]
        rows = []
        for year, row in monthly.iterrows():
            cells = [str(year)]
            for month in monthly.columns:
                value = row[month]
                cells.append("—" if (value is None or np.isnan(value)) else f"{value * 100:+.1f}")
            year_total = np.nanprod([1 + v for v in row.to_numpy() if not np.isnan(v)]) - 1
            cells.append(f"{year_total * 100:+.1f}")
            rows.append(cells)
        data_table(headers, rows, align="l" + "r" * (len(headers) - 1))
