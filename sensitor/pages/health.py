"""
PORTFOLIO HEALTH — the score, and why it is what it is.

The score is useless if the reader cannot see inside it. This page puts the dial
next to the five components that produced it, each showing its own fill, the
metric that drove it, the reference level it was measured against and its weight
in the total. The methodology is stated on the page rather than buried.
"""

from __future__ import annotations

import streamlit as st

from .. import charts as C
from ..components import (
    metric_card, note, num, page_header, pct, score_bar, section, spacer, stat_card,
)
from ..design import INK_2, INK_MUTED, PLOTLY_CONFIG, STATUS, html
from ..health import WEIGHTS
from ..i18n import define, tr
from ._shared import guard, period_selector, single_asset_note

_COMPONENT_ORDER = ["performance", "risk", "diversification", "concentration", "liquidity"]


def render_health(ctx) -> None:
    lang = ctx.lang if ctx else st.session_state.get("language", "en")

    page_header(tr("nav_health", lang), tr("health_sub", lang),
                eyebrow=tr("product_short", lang))
    if not guard(ctx, lang):
        return

    period_selector(ctx, "health_period")

    health = ctx.health
    components = health["components"]

    # ── The dial and the breakdown, side by side ─────────────────────────────
    col_gauge, col_break = st.columns([1, 1.45], gap="large")

    with col_gauge:
        st.plotly_chart(
            C.health_gauge(health["total"], height=278, tone=health["tone"]),
            width='stretch', config=PLOTLY_CONFIG, key="health_gauge",
        )
        tone_color = STATUS[health["tone"]]
        band_label = tr("band_" + health["band"], lang)
        weakest_label = tr("c_" + health["weakest"], lang)
        html(
            f'<div style="text-align:center;margin-top:-18px;">'
            f'<div style="display:inline-block;background:{tone_color}1F;color:{tone_color};'
            f'padding:5px 16px;border-radius:999px;font-size:0.78rem;font-weight:700;'
            f'letter-spacing:0.08em;text-transform:uppercase;">'
            f'{band_label}</div>'
            f'<div style="font-size:0.75rem;color:{INK_MUTED};margin-top:10px;">'
            f'{tr("weakest", lang)}: '
            f'<b style="color:{INK_2};">{weakest_label}</b></div></div>'
        )

    with col_break:
        section(tr("score_breakdown", lang).upper(), tr("why_this_score", lang))
        for key in _COMPONENT_ORDER:
            component = components[key]
            detail = (
                f"{tr('measured', lang)}: {component['metric_text']}  ·  "
                f"{tr('reference', lang)}: {component['reference']}  ·  "
                f"{tr('weight', lang)}: {component['weight']}%"
            )
            score_bar(
                tr(f"c_{key}", lang),
                component["score"],
                100,
                tooltip=_component_tooltip(key, lang),
                detail=detail,
            )

    note(tr("health_method", lang))

    # ── Component contributions to the total ─────────────────────────────────
    section("CONTRIBUTION",
            "Component score × weight" if lang == "en"
            else "Score de la composante × pondération")

    cols = st.columns(5, gap="small")
    for col, key in zip(cols, _COMPONENT_ORDER):
        component = components[key]
        with col:
            stat_card(
                tr(f"c_{key}", lang),
                f"{component['score']:.0f}",
                sub=f"→ {component['contribution']:.1f} / {WEIGHTS[key]}",
                tone=component["tone"],
                tooltip=_component_tooltip(key, lang),
            )

    # ── Portfolio DNA ────────────────────────────────────────────────────────
    section(tr("portfolio_dna", lang).upper(), tr("dna_sub", lang))

    dna = ctx.dna
    axes = ["growth", "risk", "diversification", "liquidity", "income", "defensive"]
    labels = [tr(f"dna_{a}", lang) for a in axes]
    values = [dna[a] for a in axes]

    col_radar, col_axes = st.columns([1.15, 1], gap="large")
    with col_radar:
        st.plotly_chart(
            C.radar(labels, values, height=340, name=tr("portfolio", lang)),
            width='stretch', config=PLOTLY_CONFIG, key="health_dna",
        )
    with col_axes:
        spacer(14)
        for axis in axes:
            score_bar(tr(f"dna_{axis}", lang), dna[axis], 100)

    # ── Underlying statistics ────────────────────────────────────────────────
    section(tr("risk_metrics", lang).upper())
    stats = ctx.stats
    conc = ctx.concentration

    m1, m2, m3, m4 = st.columns(4, gap="medium")
    with m1:
        metric_card(tr("sharpe_ratio", lang), num(stats["sharpe"], 2),
                    bar=min(max((stats["sharpe"] + 0.5) / 3.0, 0), 1),
                    tooltip=define("sharpe", lang))
    with m2:
        metric_card(tr("volatility", lang), pct(stats["volatility"], 1),
                    bar=min(stats["volatility"] / 0.45, 1),
                    higher_is_better=False, tooltip=define("volatility", lang))
    with m3:
        metric_card(tr("avg_correlation", lang), num(ctx.avg_correlation, 2),
                    bar=min(max((ctx.avg_correlation + 1) / 2, 0), 1),
                    higher_is_better=False, tooltip=define("avg_correlation", lang))
    with m4:
        metric_card(tr("effective_assets", lang),
                    f"{conc.get('effective_assets', 0):.1f}",
                    bar=min(conc.get("effective_assets", 0) / 12, 1),
                    caption=f"/ {conc.get('n_assets', 0)} {tr('holdings', lang).lower()}",
                    tooltip=define("effective_assets", lang))

    single_asset_note(ctx)


def _component_tooltip(key: str, lang: str) -> str:
    mapping = {
        "performance": "sharpe",
        "risk": "volatility",
        "diversification": "diversification_ratio",
        "concentration": "effective_assets",
    }
    if key in mapping:
        return define(mapping[key], lang)
    return (
        "Weight-averaged liquidity of the holdings, from the asset library's 0-100 "
        "liquidity field. Holdings with no entry are assumed reasonably liquid."
        if lang == "en" else
        "Liquidité moyenne pondérée des positions, issue du champ liquidité 0-100 de la "
        "bibliothèque d'actifs. Les positions sans donnée sont supposées raisonnablement liquides."
    )
