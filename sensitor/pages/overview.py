"""
OVERVIEW — the hero dashboard.

The first screen anyone sees. Its job is that within a few seconds the reader
knows what the portfolio is worth, how it has performed, how much risk it carries,
where that risk sits, and what crossed a threshold. Every figure is a visual
component: a number alone is never enough.
"""

from __future__ import annotations

import streamlit as st

from ..ui import charts as C
from ..ui.components import (
    alert, data_table, metric_card, money, note, num, page_header, pct,
    section, spacer,
)
from ..ui.themes import (
    ACCENT, PALETTE, PLOTLY_CONFIG, PLOTLY_CONFIG_ZOOM, STATUS, class_color,
)
from ..core.i18n import define, tr
from ..integrations.market_data import benchmark_label
from ._shared import (
    benchmark_selector, currency_notice, guard, load_benchmark, period_selector,
    single_asset_note,
)


def render_overview(ctx) -> None:
    lang = ctx.lang if ctx else st.session_state.get("language", "en")

    page_header(
        tr("nav_overview", lang),
        tr("overview_sub", lang),
        eyebrow=tr("product", lang),
    )
    if not guard(ctx, lang):
        return

    # Said once, on the page carrying the headline figures, and under the header
    # rather than above it.
    currency_notice(ctx.analyzer, lang)

    # ── Controls ─────────────────────────────────────────────────────────────
    left, right = st.columns([3, 1.4])
    with left:
        period_selector(ctx, "ov_period")
    with right:
        bench_ticker = benchmark_selector(ctx, "ov_bench")

    port_aligned, bench_aligned = load_benchmark(ctx, bench_ticker)
    bench_name = benchmark_label(bench_ticker, lang)

    stats = ctx.stats
    bench_stats = None
    if bench_aligned is not None:
        from ..investment import analytics as A
        bench_stats = A.perf_stats(bench_aligned)


    # ── Hero KPI row ─────────────────────────────────────────────────────────
    values = ctx.values
    value_spark = values.to_numpy().tolist()

    c1, c2, c3, c4 = st.columns(4, gap="medium")

    with c1:
        change = ctx.end_value - ctx.start_value
        metric_card(
            tr("portfolio_value", lang),
            money(ctx.end_value, ctx.currency),
            delta=stats["total_return"],
            delta_label=tr("period", lang).lower(),
            spark=value_spark,
            spark_color=ACCENT if change >= 0 else STATUS["critical"],
            caption=f"{money(change, ctx.currency)}",
        )

    with c2:
        delta_vs_bench = (
            stats["total_return"] - bench_stats["total_return"] if bench_stats else None
        )
        metric_card(
            tr("total_return", lang),
            pct(stats["total_return"], 1),
            delta=delta_vs_bench,
            delta_label=f"{tr('vs', lang)} {bench_name}",
            bar=min(max((stats["total_return"] + 0.5) / 1.5, 0), 1),
            bar_color=STATUS["good"] if stats["total_return"] >= 0 else STATUS["critical"],
            caption=f"{stats['n_days']} {tr('days', lang)}",
        )

    with c3:
        metric_card(
            tr("annualized_return", lang),
            pct(stats["cagr"], 1),
            delta=(stats["cagr"] - bench_stats["cagr"]) if bench_stats else None,
            delta_label=f"{tr('vs', lang)} {bench_name}",
            bar=min(max((stats["cagr"] + 0.2) / 0.6, 0), 1),
            bar_color=STATUS["good"] if stats["cagr"] >= 0 else STATUS["critical"],
            caption=f"{stats['years']:.1f} {'years' if lang == 'en' else 'ans'}",
        )

    with c4:
        vol = stats["volatility"]
        metric_card(
            tr("volatility", lang),
            pct(vol, 1),
            delta=(vol - bench_stats["volatility"]) if bench_stats else None,
            delta_label=f"{tr('vs', lang)} {bench_name}",
            higher_is_better=False,
            bar=min(vol / 0.45, 1),
            bar_color=(STATUS["good"] if vol < 0.15 else
                       STATUS["warning"] if vol < 0.25 else STATUS["critical"]),
            tooltip=define("volatility", lang),
            caption="annualised" if lang == "en" else "annualisée",
        )

    spacer(14)

    # ── Second KPI row ───────────────────────────────────────────────────────
    d1, d2, d3, d4 = st.columns(4, gap="medium")

    with d1:
        sharpe = stats["sharpe"]
        metric_card(
            tr("sharpe_ratio", lang),
            num(sharpe, 2),
            delta=(sharpe - bench_stats["sharpe"]) if bench_stats else None,
            delta_label=f"{tr('vs', lang)} {bench_name}",
            delta_as_pct=False,
            bar=min(max((sharpe + 0.5) / 3.0, 0), 1),
            bar_color=(STATUS["good"] if sharpe >= 1 else
                       STATUS["warning"] if sharpe >= 0.4 else STATUS["critical"]),
            tooltip=define("sharpe", lang),
            caption="rf 4%",
        )

    with d2:
        max_dd = stats["max_drawdown"]
        dd_series = ctx.drawdown.get("series") if ctx.drawdown else None
        metric_card(
            tr("max_drawdown", lang),
            pct(max_dd, 1),
            bar=min(abs(max_dd) / 0.6, 1),
            bar_color=(STATUS["good"] if abs(max_dd) < 0.15 else
                       STATUS["warning"] if abs(max_dd) < 0.30 else STATUS["critical"]),
            spark=dd_series.to_numpy().tolist() if dd_series is not None else None,
            spark_color=STATUS["critical"],
            tooltip=define("max_drawdown", lang),
        )

    with d3:
        health = ctx.health
        metric_card(
            tr("health_score", lang),
            f"{health['total']:.0f}",
            bar=health["total"] / 100,
            status=health["tone"],
            tooltip=define("health_score", lang),
            caption=tr(f"band_{health['band']}", lang),
        )

    with d4:
        rc = ctx.risk_contribution
        if rc is not None and not rc.empty:
            top = rc.iloc[0]
            metric_card(
                tr("top_risk_driver", lang),
                str(top["ticker"]),
                bar=float(top["pct_contribution"]),
                bar_color=(STATUS["critical"] if top["pct_contribution"] >= 0.40 else
                           STATUS["warning"] if top["pct_contribution"] >= 0.28 else STATUS["good"]),
                tooltip=define("risk_contribution", lang),
                caption=(f"{top['pct_contribution'] * 100:.0f}% {tr('of_risk', lang)} · "
                         f"{top['weight'] * 100:.0f}% {tr('weight', lang).lower()}"),
                compact=True,
            )
        else:
            metric_card(tr("top_risk_driver", lang), "—", caption=tr("assets", lang))

    # ── Hero chart ───────────────────────────────────────────────────────────
    section(tr("growth_of_capital", lang).upper(),
            f"{tr('portfolio', lang)} {tr('vs', lang)} {bench_name} — {ctx.period}")

    series_map = {tr("portfolio", lang): values}
    if bench_aligned is not None:
        from ..investment import analytics as A
        bench_curve = A.cumulative(bench_aligned) * ctx.start_value
        series_map[bench_name] = bench_curve

    st.plotly_chart(
        C.cumulative_performance(series_map, height=390, value_prefix=ctx.currency),
        width='stretch', config=PLOTLY_CONFIG_ZOOM,
        key="ov_cumulative",
    )

    # ── Signals + composition ────────────────────────────────────────────────
    spacer(8)
    col_signals, col_own = st.columns([1.25, 1], gap="large")

    with col_signals:
        section(tr("things_to_review", lang).upper())
        signals = ctx.signals[:4]
        if signals:
            for signal in signals:
                alert(
                    signal["level"],
                    signal["title"][lang],
                    signal["body"][lang],
                    footnote=signal["footnote"][lang],
                )
        else:
            alert("good", tr("no_signals", lang), tr("no_signals_body", lang))

    with col_own:
        section(tr("what_you_own", lang).upper())
        xray = ctx.xray
        st.plotly_chart(
            C.exposure_bars(xray.get("asset_class", {}), color_map=class_color, height=150),
            width='stretch', config=PLOTLY_CONFIG, key="ov_class",
        )
        st.plotly_chart(
            C.exposure_bars(xray.get("sector", {}), max_items=8, height=268),
            width='stretch', config=PLOTLY_CONFIG, key="ov_sector",
        )
        note(tr("xray_note", lang))

    # ── Holdings table ───────────────────────────────────────────────────────
    section(tr("holdings", lang).upper(), f"{len(ctx.tickers)} {tr('assets', lang).lower()}")
    single_asset_note(ctx)

    rc = ctx.risk_contribution
    weights = ctx.weights
    rows = []
    if rc is not None and not rc.empty:
        max_risk = float(rc["pct_contribution"].max()) or 1.0
        for _, row in rc.iterrows():
            ticker = row["ticker"]
            rows.append([
                ticker,
                pct(row["weight"], 1),
                money(ctx.end_value * row["weight"], ctx.currency),
                pct(row["asset_volatility"], 1),
                (f"{row['pct_contribution'] * 100:.1f}%", float(row["pct_contribution"])),
                f"{row['risk_ratio']:.2f}x",
            ])
        data_table(
            [tr("assets", lang), tr("weight", lang), tr("value", lang),
             tr("volatility", lang), tr("risk_contribution", lang), "Risk / Weight"],
            rows,
            align="lrrrrr",
            bars={4: (max_risk, PALETTE[1])},
        )
    else:
        for ticker, weight in sorted(weights.items(), key=lambda kv: -kv[1]):
            rows.append([ticker, pct(weight, 1), money(ctx.end_value * weight, ctx.currency)])
        data_table([tr("assets", lang), tr("weight", lang), tr("value", lang)],
                   rows, align="lrr")
