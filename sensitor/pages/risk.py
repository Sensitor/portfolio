"""
RISK LAB — how much risk, and where it comes from.

Four blocks, in the order the questions get asked:

1. **How much** — volatility, downside volatility, the risk-adjusted ratios.
2. **How bad can a day be** — VaR, CVaR, and the shape of the return distribution.
3. **Where does it come from** — Euler risk contribution, correlation, concentration.
4. **What did it feel like** — the drawdown record.

The risk-contribution block is the one that pays for the page: it shows that a
position's share of the capital and its share of the risk are different numbers.
"""

from __future__ import annotations

import streamlit as st

from .. import analytics as A
from .. import charts as C
from ..components import (
    data_table, metric_card, note, num, page_header, pct, section, spacer, stat_card,
)
from ..design import INK_MUTED, PALETTE, PLOTLY_CONFIG, PLOTLY_CONFIG_ZOOM, STATUS
from ..i18n import define, tr
from ._shared import guard, period_selector, single_asset_note


def render_risk(ctx) -> None:
    lang = ctx.lang if ctx else st.session_state.get("language", "en")

    page_header(tr("nav_risk", lang), tr("risk_sub", lang), eyebrow=tr("product_short", lang))
    if not guard(ctx, lang):
        return

    period_selector(ctx, "risk_period")

    stats = ctx.stats
    var95, var99 = ctx.var, ctx.var99

    # ── 1. How much risk ─────────────────────────────────────────────────────
    section(tr("risk_metrics", lang).upper())

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    with c1:
        metric_card(tr("volatility", lang), pct(stats["volatility"], 1),
                    bar=min(stats["volatility"] / 0.45, 1), higher_is_better=False,
                    bar_color=(STATUS["good"] if stats["volatility"] < 0.15 else
                               STATUS["warning"] if stats["volatility"] < 0.25 else STATUS["critical"]),
                    tooltip=define("volatility", lang))
    with c2:
        metric_card(tr("downside_volatility", lang), pct(stats["downside_vol"], 1),
                    bar=min(stats["downside_vol"] / 0.35, 1), higher_is_better=False,
                    tooltip=define("downside_vol", lang))
    with c3:
        metric_card(tr("sortino_ratio", lang), num(stats["sortino"], 2),
                    bar=min(max((stats["sortino"] + 0.5) / 3.5, 0), 1),
                    tooltip=define("sortino", lang))
    with c4:
        metric_card(tr("calmar_ratio", lang), num(stats["calmar"], 2),
                    bar=min(max((stats["calmar"] + 0.5) / 2.5, 0), 1),
                    tooltip=define("calmar", lang))

    # ── 2. Tail risk ─────────────────────────────────────────────────────────
    section(tr("return_distribution", lang).upper(),
            "1-day horizon" if lang == "en" else "horizon 1 jour")

    if var95:
        v1, v2, v3, v4 = st.columns(4, gap="medium")
        with v1:
            metric_card(tr("var_95", lang), pct(var95["historical_var"], 2),
                        bar=min(var95["historical_var"] / 0.08, 1),
                        bar_color=STATUS["warning"], higher_is_better=False,
                        tooltip=define("var", lang), caption=tr("historical", lang))
        with v2:
            metric_card(tr("cvar_95", lang), pct(var95["historical_cvar"], 2),
                        bar=min(var95["historical_cvar"] / 0.10, 1),
                        bar_color=STATUS["serious"], higher_is_better=False,
                        tooltip=define("cvar", lang), caption=tr("historical", lang))
        with v3:
            metric_card(tr("var_99", lang), pct(var99["historical_var"], 2),
                        bar=min(var99["historical_var"] / 0.12, 1),
                        bar_color=STATUS["critical"], higher_is_better=False,
                        tooltip=define("var", lang), caption=tr("historical", lang))
        with v4:
            gap = var95["historical_var"] - var95["parametric_var"]
            metric_card(f"{tr('var_95', lang)} — {tr('parametric', lang)}",
                        pct(var95["parametric_var"], 2),
                        bar=min(var95["parametric_var"] / 0.08, 1),
                        bar_color=INK_MUTED, higher_is_better=False,
                        tooltip=define("var", lang),
                        caption=(f"{'gap' if lang == 'en' else 'écart'} "
                                 f"{gap * 100:+.2f}pp {tr('vs', lang)} "
                                 f"{tr('historical', lang).lower()}"))

        spacer(10)
        dist_col, stats_col = st.columns([1.7, 1], gap="large")
        with dist_col:
            st.plotly_chart(
                C.return_distribution(ctx.portfolio_returns,
                                      var95["historical_var"], var95["historical_cvar"]),
                width='stretch', config=PLOTLY_CONFIG, key="risk_dist",
            )
        with stats_col:
            dist = ctx.distribution
            if dist:
                spacer(6)
                g1, g2 = st.columns(2, gap="small")
                with g1:
                    stat_card(tr("median", lang), pct(dist["median"], 3))
                    stat_card(tr("skewness", lang), num(dist["skewness"], 2),
                              tone="warning" if dist["skewness"] < -0.3 else None,
                              tooltip=define("skewness", lang))
                with g2:
                    stat_card(tr("worst_day", lang), pct(stats["worst_day"], 2), tone="critical")
                    stat_card(tr("kurtosis", lang), num(dist["kurtosis"], 2),
                              tone="warning" if dist["kurtosis"] > 3 else None,
                              tooltip=define("kurtosis", lang))
        note(tr("var_method_note", lang))

    # ── 3. Where the risk comes from ─────────────────────────────────────────
    section(tr("risk_contribution", lang).upper(), tr("risk_contribution_sub", lang))
    single_asset_note(ctx)

    rc = ctx.risk_contribution
    if rc is not None and not rc.empty:
        st.plotly_chart(
            C.weight_vs_risk(rc, label_weight=tr("weight", lang),
                             label_risk=tr("risk_contribution", lang)),
            width='stretch', config=PLOTLY_CONFIG, key="risk_wvr",
        )
        max_risk = float(rc["pct_contribution"].max()) or 1.0
        rows = [
            [row["ticker"], pct(row["weight"], 1), pct(row["asset_volatility"], 1),
             num(row["marginal"], 3),
             (f"{row['pct_contribution'] * 100:.1f}%", float(row["pct_contribution"])),
             f"{row['risk_ratio']:.2f}x"]
            for _, row in rc.iterrows()
        ]
        data_table(
            [tr("assets", lang), tr("weight", lang), tr("volatility", lang),
             "MCTR", tr("risk_contribution", lang), "Risk / Weight"],
            rows, align="lrrrrr", bars={4: (max_risk, PALETTE[1])},
        )
        note(define("risk_contribution", lang) + " " + define("marginal_risk", lang))

    # ── Correlation ──────────────────────────────────────────────────────────
    if not ctx.is_single_asset:
        section(tr("correlation_matrix", lang).upper())

        k1, k2, k3 = st.columns(3, gap="medium")
        conc = ctx.concentration
        with k1:
            metric_card(tr("avg_correlation", lang), num(ctx.avg_correlation, 2),
                        bar=min(max((ctx.avg_correlation + 1) / 2, 0), 1),
                        higher_is_better=False,
                        bar_color=(STATUS["good"] if ctx.avg_correlation < 0.35 else
                                   STATUS["warning"] if ctx.avg_correlation < 0.6 else STATUS["critical"]),
                        tooltip=define("avg_correlation", lang))
        with k2:
            metric_card(tr("effective_assets", lang),
                        f"{conc.get('effective_assets', 0):.1f}",
                        bar=conc.get("diversification_efficiency", 0),
                        caption=(f"{tr('diversification_efficiency', lang)}: "
                                 f"{conc.get('diversification_efficiency', 0) * 100:.0f}%"),
                        tooltip=define("effective_assets", lang))
        with k3:
            div_ratio = ctx.diversification_ratio
            metric_card(tr("diversification_ratio", lang), num(div_ratio, 2),
                        bar=min(max((div_ratio - 1) / 1.0, 0), 1),
                        bar_color=STATUS["good"] if div_ratio >= 1.35 else STATUS["warning"],
                        tooltip=define("diversification_ratio", lang))

        spacer(10)
        st.plotly_chart(
            C.correlation_heatmap(ctx.correlation),
            width='stretch', config=PLOTLY_CONFIG, key="risk_corr",
        )
        note(define("correlation", lang))

        # ── Concentration ────────────────────────────────────────────────────
        section(tr("concentration_analysis", lang).upper())
        n1, n2, n3, n4 = st.columns(4, gap="medium")
        with n1:
            metric_card(tr("top1", lang), pct(conc.get("top1", 0), 1),
                        bar=conc.get("top1", 0), higher_is_better=False,
                        bar_color=(STATUS["critical"] if conc.get("top1", 0) >= 0.30 else
                                   STATUS["warning"] if conc.get("top1", 0) >= 0.20 else STATUS["good"]))
        with n2:
            metric_card(tr("top3", lang), pct(conc.get("top3", 0), 1),
                        bar=conc.get("top3", 0), higher_is_better=False)
        with n3:
            metric_card(tr("top5", lang), pct(conc.get("top5", 0), 1),
                        bar=conc.get("top5", 0), higher_is_better=False)
        with n4:
            metric_card(tr("hhi", lang), num(conc.get("hhi", 0), 3),
                        bar=conc.get("hhi", 0), higher_is_better=False,
                        tooltip=define("hhi", lang))

        spacer(10)
        st.plotly_chart(
            C.concentration_curve(conc.get("sorted_weights", [])),
            width='stretch', config=PLOTLY_CONFIG, key="risk_conc",
        )

    # ── 4. Drawdown record ───────────────────────────────────────────────────
    section(tr("drawdown_analysis", lang).upper())
    dd = ctx.drawdown
    if dd:
        d1, d2, d3, d4 = st.columns(4, gap="medium")
        with d1:
            metric_card(tr("current_drawdown", lang), pct(dd["current_drawdown"], 1),
                        bar=min(abs(dd["current_drawdown"]) / 0.4, 1),
                        bar_color=STATUS["critical"] if dd["current_drawdown"] < -0.1 else STATUS["good"],
                        tooltip=define("current_drawdown", lang))
        with d2:
            metric_card(tr("max_drawdown", lang), pct(dd["max_drawdown"], 1),
                        bar=min(abs(dd["max_drawdown"]) / 0.6, 1),
                        bar_color=STATUS["critical"], tooltip=define("max_drawdown", lang))
        with d3:
            metric_card(tr("time_underwater", lang), pct(dd["time_underwater_pct"], 0),
                        bar=dd["time_underwater_pct"], higher_is_better=False,
                        tooltip=define("time_underwater", lang))
        with d4:
            recovery = dd.get("avg_recovery_days")
            metric_card(tr("avg_recovery", lang),
                        f"{recovery:.0f} {tr('days', lang)}" if recovery else "—",
                        bar=min((recovery or 0) / 365, 1), higher_is_better=False,
                        caption=f"{dd['n_episodes']} episodes" if lang == "en"
                                else f"{dd['n_episodes']} épisodes")

        spacer(10)
        st.plotly_chart(
            C.underwater(dd["series"]),
            width='stretch', config=PLOTLY_CONFIG_ZOOM, key="risk_uw",
        )

        episodes = A.drawdown_episodes(ctx.portfolio_returns, top=5)
        if episodes:
            spacer(8)
            rows = []
            for episode in episodes:
                recovery_text = (
                    f"{episode['recovery_days']} {tr('days', lang)}"
                    if episode["recovered"] else tr("ongoing", lang)
                )
                rows.append([
                    pct(episode["depth"], 1),
                    episode["peak_date"].strftime("%Y-%m-%d"),
                    episode["trough_date"].strftime("%Y-%m-%d"),
                    f"{episode['decline_days']} {tr('days', lang)}",
                    recovery_text,
                ])
            data_table(
                [tr("depth", lang), tr("peak", lang), tr("trough", lang),
                 "Decline" if lang == "en" else "Baisse", tr("recovery", lang)],
                rows, align="lllll",
            )
