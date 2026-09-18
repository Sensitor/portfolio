"""
PORTFOLIO X-RAY — what you actually own.

A portfolio of index funds looks like three tickers and is in fact several hundred
companies with a definite sector, geography, cap and style profile. This page
resolves each holding into its underlying exposures and shows the result next to
the naive ticker view, so the gap between the two is the headline rather than a
footnote.

The reference data behind the resolution is approximate and clearly labelled as
such on the page; see `sensitor/xray.py` for its provenance.
"""

from __future__ import annotations

import streamlit as st

from .. import charts as C
from .. import xray as X
from ..components import data_table, metric_card, note, page_header, pct, section
from ..design import ACCENT, PLOTLY_CONFIG, class_color
from ..i18n import define, tr
from ._shared import guard


def render_xray(ctx) -> None:
    lang = ctx.lang if ctx else st.session_state.get("language", "en")

    page_header(tr("nav_xray", lang), tr("xray_sub", lang), eyebrow=tr("product_short", lang))
    if not guard(ctx, lang):
        return

    xray = ctx.xray
    weights = ctx.weights

    # ── Headline exposures — the "you own more of this than you think" row ───
    section(tr("headline_exposures", lang).upper())

    headlines = X.headline_exposures(xray)
    if headlines:
        cols = st.columns(len(headlines), gap="medium")
        for col, headline in zip(cols, headlines):
            share = headline["share"]
            with col:
                # Deliberately neutral. A US large-cap tilt is a description of the
                # portfolio, not a defect, and painting it with the critical status
                # colour would assert a judgement the data does not support. Only
                # the signal engine, which has documented thresholds, flags things.
                metric_card(
                    headline["label_fr"] if lang == "fr" else headline["label_en"],
                    headline["bucket"],
                    bar=share,
                    bar_color=ACCENT,
                    caption=f"{share * 100:.1f}% {'of portfolio' if lang == 'en' else 'du portefeuille'}",
                    tooltip=define("lookthrough", lang),
                    compact=True,
                )
    note(tr("xray_note", lang))

    # ── Direct holdings versus resolved exposure ─────────────────────────────
    section(tr("hidden_exposure", lang).upper(), tr("hidden_exposure_sub", lang))

    col_direct, col_resolved = st.columns(2, gap="large")
    with col_direct:
        st.markdown(f"**{tr('direct_holdings', lang)}**")
        direct = dict(sorted(weights.items(), key=lambda kv: -kv[1]))
        st.plotly_chart(
            C.exposure_bars(direct, max_items=10, height=max(180, 33 * len(direct) + 34)),
            width='stretch', config=PLOTLY_CONFIG, key="xray_direct",
        )
    with col_resolved:
        st.markdown(f"**{tr('lookthrough', lang)} — {X.DIMENSION_LABELS['sector'][lang]}**")
        st.plotly_chart(
            C.exposure_bars(xray.get("sector", {}), max_items=10,
                            height=max(180, 33 * min(len(xray.get("sector", {})), 10) + 34)),
            width='stretch', config=PLOTLY_CONFIG, key="xray_sector_compare",
        )

    # ── Every dimension ──────────────────────────────────────────────────────
    section(tr("lookthrough", lang).upper())

    tab_labels = [X.DIMENSION_LABELS[d][lang] for d in X.DIMENSIONS]
    tabs = st.tabs(tab_labels)

    for tab, dimension in zip(tabs, X.DIMENSIONS):
        with tab:
            buckets = xray.get(dimension, {})
            if not buckets:
                note(tr("no_data_body", lang))
                continue

            chart_col, table_col = st.columns([1.35, 1], gap="large")
            with chart_col:
                st.plotly_chart(
                    C.exposure_bars(
                        buckets,
                        color_map=class_color if dimension == "asset_class" else None,
                        max_items=10,
                        height=max(190, 33 * min(len(buckets), 10) + 40),
                    ),
                    width='stretch', config=PLOTLY_CONFIG,
                    key=f"xray_{dimension}",
                )
            with table_col:
                rows = [[bucket, pct(share, 1)] for bucket, share in buckets.items()]
                data_table(
                    [X.DIMENSION_LABELS[dimension][lang], tr("weight", lang)],
                    rows, align="lr",
                )

    # ── Per-holding resolution ───────────────────────────────────────────────
    section(tr("holdings", lang).upper(),
            "Resolved per holding" if lang == "en" else "Résolu par position")

    rows = []
    for ticker, weight in sorted(weights.items(), key=lambda kv: -kv[1]):
        profile = X.resolve_profile(ticker, ctx.asset_info, ctx.sector_map, ctx.geo_map)
        rows.append([
            ticker,
            pct(weight, 1),
            _top_bucket(profile, "asset_class"),
            _top_bucket(profile, "sector"),
            _top_bucket(profile, "geography"),
            _top_bucket(profile, "style"),
        ])
    data_table(
        [tr("assets", lang), tr("weight", lang)]
        + [X.DIMENSION_LABELS[d][lang] for d in ("asset_class", "sector", "geography", "style")],
        rows, align="lrllll",
    )
    note(f"{X.DATA_VINTAGE}. {tr('xray_note', lang)}")


def _top_bucket(profile: dict, dimension: str) -> str:
    """Largest bucket of a dimension, annotated when the holding is a blend."""
    buckets = profile.get(dimension) or {}
    if not buckets:
        return "—"
    bucket, share = max(buckets.items(), key=lambda kv: kv[1])
    return bucket if share > 0.95 else f"{bucket} ({share * 100:.0f}%)"
