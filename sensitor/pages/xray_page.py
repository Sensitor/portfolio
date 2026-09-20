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

from ..ui import charts as C
from ..investment import xray as X
from ..ui.components import (
    data_table, metric_card, note, page_header, pct, section, spacer,
)
from ..ui.themes import ACCENT, PLOTLY_CONFIG, STATUS, class_color
from ..core.i18n import define, tr
from ._shared import guard

STATUS_GOOD = STATUS["good"]
STATUS_WARNING = STATUS["warning"]


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

    _factor_block(ctx, lang)


def _top_bucket(profile: dict, dimension: str) -> str:
    """Largest bucket of a dimension, annotated when the holding is a blend."""
    buckets = profile.get(dimension) or {}
    if not buckets:
        return "—"
    bucket, share = max(buckets.items(), key=lambda kv: kv[1])
    return bucket if share > 0.95 else f"{bucket} ({share * 100:.0f}%)"


# =============================================================================
# FACTOR EXPOSURE
# =============================================================================

def _factor_block(ctx, lang: str) -> None:
    """
    Systematic risk exposures, estimated against liquid ETF proxies.

    Sits on the X-Ray page because it answers the same question as look-through —
    what you actually own — in the language of risk premia rather than sectors.
    """
    from ..ui import charts as C
    from ..investment import factors as FA
    from ..integrations import market_data as market
    from ..ui.components import metric_card, num

    section(tr("factor_exposure", lang).upper(), tr("factor_sub", lang))

    returns = ctx.portfolio_returns
    if returns is None or len(returns) < 90:
        note(tr("short_history_body", lang))
        return

    start = returns.index[0].strftime("%Y-%m-%d")
    with st.spinner(""):
        proxies = market.fetch_many_returns(tuple(FA.required_tickers()), start)

    factor_matrix = FA.build_factors(proxies)
    if factor_matrix.empty:
        note(tr("factor_unavailable", lang))
        return

    result = FA.factor_exposure(market.normalise_index(returns), factor_matrix)
    if not result:
        note(tr("factor_unavailable", lang))
        return

    significant = [item for item in result["loadings"] if item["significant"]]

    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        metric_card(
            tr("explained_variance", lang), pct(result["r_squared"], 0),
            bar=result["r_squared"],
            bar_color=(STATUS_GOOD if result["r_squared"] >= 0.7 else STATUS_WARNING),
            caption=f"adj. R² {result['adj_r_squared']:.2f} · {result['n_days']} {tr('days', lang)}",
        )
    with c2:
        metric_card(
            tr("alpha", lang), pct(result["alpha"], 2),
            bar=min(max((result["alpha"] + 0.1) / 0.2, 0), 1),
            tooltip=define("alpha", lang),
            caption=f"t = {result['alpha_t']:+.2f}",
        )
    with c3:
        top = significant[0] if significant else None
        metric_card(
            "Dominant factor" if lang == "en" else "Facteur dominant",
            FA.factor_label(top["factor"], lang) if top else "—",
            bar=min(abs(top["loading"]) / 1.2, 1) if top else 0,
            caption=(f"{tr('factor_loading', lang)} {top['loading']:+.2f}" if top
                     else tr("not_significant", lang)),
            compact=True,
        )

    spacer(10)
    chart_col, table_col = st.columns([1.3, 1], gap="large")
    with chart_col:
        st.plotly_chart(
            C.factor_bars(result["loadings"],
                          label_fn=lambda k: FA.factor_label(k, lang),
                          ns_suffix=tr("not_significant", lang)),
            width="stretch", config=PLOTLY_CONFIG, key="xray_factors",
        )
    with table_col:
        rows = [
            [FA.factor_label(item["factor"], lang),
             num(item["loading"], 2),
             num(item["t_stat"], 1),
             "✓" if item["significant"] else "—"]
            for item in result["loadings"]
        ]
        data_table(
            [tr("factor_exposure", lang), tr("factor_loading", lang), "t",
             "sig." if lang == "en" else "signif."],
            rows, align="lrrr",
        )

    note(tr("factor_note", lang))
