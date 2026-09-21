"""
Client-ready portfolio report.

Produces one self-contained HTML document: no JavaScript, no external requests,
every chart drawn as inline SVG. Open it anywhere, print it to PDF from the
browser, email the file — it works offline and it looks the same everywhere.

The rendering primitives — palette, formatters, SVG charts, stylesheet — live in
`core.document`, shared with the weekly trading review so the two documents
cannot drift apart. What is here is the portfolio's sections and the order they
go in.

No Streamlit import. `build_html` takes the same `Context` the pages use.
"""

from __future__ import annotations

import html as _html
from datetime import datetime

from . import xray as X
from ..core.i18n import tr
# The palette, the formatters, the SVG charts and the stylesheet live in
# `core.document`, shared with the weekly trading review. Imported by name
# rather than with a star so what this module uses stays readable.
from ..core.document import (  # noqa: F401  (re-exported for callers and tests)
    ACCENT, INK, INK_2, INK_3, NEG, POS, RULE, SERIES, SURFACE, SURFACE_2,
    _STYLE, _esc, _kpi, _money, _num, _pct, _table, svg_bars,
    svg_diverging_bars, svg_gauge, svg_lines, svg_radar,
)

SECTIONS = [
    "overview", "performance", "risk", "diversification",
    "concentration", "stress", "observations", "optimization", "dna",
]

SECTION_TITLES = {
    "overview": {"en": "Portfolio Overview", "fr": "Vue d'Ensemble du Portefeuille"},
    "performance": {"en": "Performance", "fr": "Performance"},
    "risk": {"en": "Risk", "fr": "Risque"},
    "diversification": {"en": "Diversification", "fr": "Diversification"},
    "concentration": {"en": "Concentration", "fr": "Concentration"},
    "stress": {"en": "Stress Tests", "fr": "Tests de Résistance"},
    "observations": {"en": "Key Observations", "fr": "Observations Clés"},
    "optimization": {"en": "Optimization", "fr": "Optimisation"},
    "dna": {"en": "Portfolio DNA", "fr": "ADN du Portefeuille"},
}

DISCLAIMER = {
    "en": (
        "This report is an analysis of historical data for the period stated. It is "
        "not investment advice, not a recommendation to buy or sell any security, and "
        "not a forecast. Every figure describes how this allocation behaved over the "
        "window analysed; past performance does not predict future returns. Fund "
        "look-through data is indicative reference data approximating published fact "
        "sheets, not live holdings. Figures are computed from end-of-day prices and "
        "exclude transaction costs, taxes, spreads and any cash flows other than those "
        "stated."
    ),
    "fr": (
        "Ce rapport est une analyse de données historiques sur la période indiquée. Il "
        "ne constitue ni un conseil en investissement, ni une recommandation d'achat ou "
        "de vente, ni une prévision. Chaque chiffre décrit le comportement de cette "
        "allocation sur la fenêtre analysée ; les performances passées ne préjugent pas "
        "des performances futures. Les données de transparisation des fonds sont des "
        "données de référence indicatives approximant les fiches produits publiées, et "
        "non des positions en temps réel. Les chiffres sont calculés à partir des cours "
        "de clôture et excluent frais de transaction, fiscalité, spreads et tout flux de "
        "trésorerie autre que ceux mentionnés."
    ),
}


# =============================================================================
# HTML BUILDING BLOCKS
# =============================================================================

def _section(key: str, lang: str, body: str, page_break: bool = False) -> str:
    title = SECTION_TITLES.get(key, {}).get(lang, key.title())
    cls = "section break" if page_break else "section"
    return f'<section class="{cls}"><h2>{_esc(title)}</h2>{body}</section>'


# =============================================================================
# SECTIONS
# =============================================================================

def _overview(ctx, lang, currency) -> str:
    stats, health = ctx.stats, ctx.health
    kpis = "".join([
        _kpi(tr("portfolio_value", lang), _money(ctx.end_value, currency),
             f"{tr('period', lang)} {ctx.period}"),
        _kpi(tr("total_return", lang), _pct(stats["total_return"]),
             f"{stats['n_days']} {tr('days', lang)}"),
        _kpi(tr("annualized_return", lang), _pct(stats["cagr"]),
             f"{stats['years']:.1f} {tr('years_label', lang)}"),
        _kpi(tr("volatility", lang), _pct(stats["volatility"]), "annualised"),
        _kpi(tr("sharpe_ratio", lang), _num(stats["sharpe"]), "rf 4%"),
        _kpi(tr("max_drawdown", lang), _pct(stats["max_drawdown"])),
    ])

    rows = [
        [ticker, _pct(weight), _money(ctx.end_value * weight, currency)]
        for ticker, weight in sorted(ctx.weights.items(), key=lambda kv: -kv[1])
    ]
    holdings = _table([tr("assets", lang), tr("weight", lang), tr("value", lang)],
                      rows, align="lrr")

    chart = svg_lines({tr("portfolio", lang): ctx.values.to_numpy().tolist()})

    return (
        f'<div class="kpi-grid">{kpis}</div>'
        f'<div class="chart">{chart}</div>'
        f'<div class="two-col"><div>{holdings}</div>'
        f'<div><div class="gauge-wrap">{svg_gauge(health["total"])}'
        f'<div class="gauge-label">{_esc(tr("health_score", lang))}</div>'
        f'<div class="gauge-band">{_esc(tr("band_" + health["band"], lang))}</div>'
        f'</div></div></div>'
    )


def _performance(ctx, lang, benchmark_stats, benchmark_name) -> str:
    stats = ctx.stats
    rows = [
        [tr("total_return", lang), _pct(stats["total_return"])],
        [tr("annualized_return", lang), _pct(stats["cagr"])],
        [tr("volatility", lang), _pct(stats["volatility"])],
        [tr("sharpe_ratio", lang), _num(stats["sharpe"])],
        [tr("sortino_ratio", lang), _num(stats["sortino"])],
        [tr("max_drawdown", lang), _pct(stats["max_drawdown"])],
        [tr("best_day", lang), _pct(stats["best_day"], 2)],
        [tr("worst_day", lang), _pct(stats["worst_day"], 2)],
        [tr("positive_days", lang), _pct(stats["hit_rate"])],
    ]
    headers = ["", tr("portfolio", lang)]
    align = "lr"
    if benchmark_stats:
        headers.append(benchmark_name)
        align = "lrr"
        bench_values = [
            _pct(benchmark_stats["total_return"]), _pct(benchmark_stats["cagr"]),
            _pct(benchmark_stats["volatility"]), _num(benchmark_stats["sharpe"]),
            _num(benchmark_stats["sortino"]), _pct(benchmark_stats["max_drawdown"]),
            _pct(benchmark_stats["best_day"], 2), _pct(benchmark_stats["worst_day"], 2),
            _pct(benchmark_stats["hit_rate"]),
        ]
        rows = [row + [value] for row, value in zip(rows, bench_values)]

    attribution = ctx.attribution
    attribution_html = ""
    if attribution is not None and not attribution.empty:
        items = [(row["ticker"], row["contribution"]) for _, row in attribution.iterrows()]
        attribution_html = (
            f'<h3>{_esc(tr("attribution", lang))}</h3>'
            f'<div class="chart">{svg_diverging_bars(items)}</div>'
        )

    return f'{_table(headers, rows, align=align)}{attribution_html}'


def _risk(ctx, lang) -> str:
    stats, var = ctx.stats, ctx.var
    drawdown = ctx.drawdown
    rows = [
        [tr("volatility", lang), _pct(stats["volatility"])],
        [tr("downside_volatility", lang), _pct(stats["downside_vol"])],
        [tr("sortino_ratio", lang), _num(stats["sortino"])],
        [tr("calmar_ratio", lang), _num(stats["calmar"])],
        [tr("var_95", lang), _pct(var.get("historical_var"), 2) if var else "—"],
        [tr("cvar_95", lang), _pct(var.get("historical_cvar"), 2) if var else "—"],
        [tr("max_drawdown", lang), _pct(stats["max_drawdown"])],
        [tr("current_drawdown", lang),
         _pct(drawdown.get("current_drawdown")) if drawdown else "—"],
        [tr("time_underwater", lang),
         _pct(drawdown.get("time_underwater_pct"), 0) if drawdown else "—"],
    ]

    rc = ctx.risk_contribution
    contribution_html = ""
    if rc is not None and not rc.empty:
        items = [(row["ticker"], row["pct_contribution"]) for _, row in rc.iterrows()]
        table_rows = [
            [row["ticker"], _pct(row["weight"]), _pct(row["pct_contribution"]),
             f"{row['risk_ratio']:.2f}x"]
            for _, row in rc.iterrows()
        ]
        contribution_html = (
            f'<h3>{_esc(tr("risk_contribution", lang))}</h3>'
            f'<p class="note">{_esc(tr("risk_contribution_sub", lang))}</p>'
            f'<div class="chart">{svg_bars(items)}</div>'
            + _table([tr("assets", lang), tr("weight", lang),
                      tr("risk_contribution", lang), "Risk / Weight"],
                     table_rows, align="lrrr")
        )

    return f'{_table(["", tr("portfolio", lang)], rows)}{contribution_html}'


def _diversification(ctx, lang) -> str:
    conc = ctx.concentration
    rows = [
        [tr("avg_correlation", lang), _num(ctx.avg_correlation)],
        [tr("diversification_ratio", lang), _num(ctx.diversification_ratio)],
        [tr("effective_assets", lang),
         f"{conc.get('effective_assets', 0):.1f} / {conc.get('n_assets', 0)}"],
        [tr("diversification_efficiency", lang),
         _pct(conc.get("diversification_efficiency"), 0)],
    ]
    xray = ctx.xray
    charts = []
    for dimension in ("asset_class", "sector", "geography"):
        buckets = list((xray.get(dimension) or {}).items())[:7]
        if not buckets:
            continue
        charts.append(
            f'<div><h4>{_esc(X.DIMENSION_LABELS[dimension][lang])}</h4>'
            f'{svg_bars(buckets, width=320, label_width=110)}</div>'
        )
    return (f'{_table(["", tr("portfolio", lang)], rows)}'
            f'<div class="chart-grid">{"".join(charts)}</div>')


def _concentration(ctx, lang) -> str:
    conc = ctx.concentration
    rows = [
        [tr("top1", lang), _pct(conc.get("top1"))],
        [tr("top3", lang), _pct(conc.get("top3"))],
        [tr("top5", lang), _pct(conc.get("top5"))],
        [tr("hhi", lang), _num(conc.get("hhi"), 3)],
        [tr("effective_assets", lang), _num(conc.get("effective_assets"), 1)],
    ]
    weights = sorted(ctx.weights.items(), key=lambda kv: -kv[1])
    return (f'{_table(["", tr("portfolio", lang)], rows)}'
            f'<div class="chart">{svg_bars(weights)}</div>')


def _stress(ctx, lang, stress_results, currency) -> str:
    if not stress_results:
        return f'<p class="note">{_esc(tr("no_history_window", lang))}</p>'
    from . import stress as S
    rows = []
    items = []
    for result in stress_results:
        label = S.scenario_label(result["key"], lang)
        rows.append([
            label,
            _pct(result["portfolio_return"]),
            _pct(result.get("benchmark_return")) if result.get("benchmark_return") is not None else "—",
            f"{result['coverage'] * 100:.0f}%",
        ])
        items.append((label, result["portfolio_return"]))
    return (
        f'<div class="chart">{svg_diverging_bars(items, width=420, label_width=150)}</div>'
        + _table([tr("historical_scenarios", lang), tr("portfolio", lang),
                  tr("benchmark", lang), tr("coverage", lang)], rows, align="lrrr")
        + f'<p class="note">{_esc(tr("historical_note", lang))}</p>'
    )


def _observations(ctx, lang) -> str:
    signals = ctx.signals[:6]
    if not signals:
        return f'<p class="note">{_esc(tr("no_signals_body", lang))}</p>'
    blocks = []
    for signal in signals:
        color = {"critical": NEG, "serious": "#C4681F",
                 "warning": "#B08600", "good": POS}.get(signal["level"], INK_3)
        blocks.append(
            f'<div class="obs" style="border-left-color:{color}">'
            f'<div class="obs-title">{_esc(signal["title"][lang])}</div>'
            f'<div class="obs-body">{_esc(signal["body"][lang])}</div>'
            f'<div class="obs-foot">{_esc(signal["footnote"][lang])}</div></div>'
        )
    return "".join(blocks)


def _optimization(ctx, lang) -> str:
    frontier = ctx.frontier
    if not frontier or not frontier.get("frontier"):
        return f'<p class="note">{_esc(tr("frontier_unavailable", lang))}</p>'

    current = frontier["current"]
    rows = [[tr("current_portfolio", lang), _pct(current["return"]),
             _pct(current["volatility"]), _num(current["sharpe"])]]
    for key, label_key in (("max_sharpe", "max_sharpe_portfolio"),
                           ("min_volatility", "min_vol_portfolio")):
        point = frontier.get(key)
        if point:
            rows.append([tr(label_key, lang), _pct(point["return"]),
                         _pct(point["volatility"]), _num(point["sharpe"])])

    return (
        _table(["", tr("expected_return", lang), tr("volatility", lang),
                tr("sharpe_ratio", lang)], rows, align="lrrr")
        + f'<p class="note">{_esc(tr("frontier_note", lang))}</p>'
    )


def _dna(ctx, lang) -> str:
    dna = ctx.dna
    axes = ["growth", "risk", "diversification", "liquidity", "income", "defensive"]
    labels = [tr(f"dna_{axis}", lang) for axis in axes]
    values = [dna[axis] for axis in axes]

    health = ctx.health
    component_rows = [
        [tr(f"c_{key}", lang), f"{component['score']:.0f}",
         f"{component['weight']}%", component["metric_text"]]
        for key, component in health["components"].items()
    ]
    return (
        f'<div class="two-col">'
        f'<div class="radar-wrap">{svg_radar(labels, values)}</div>'
        f'<div>{_table([tr("score_breakdown", lang), "Score", tr("weight", lang), tr("measured", lang)], component_rows, align="lrrr")}</div>'
        f'</div><p class="note">{_esc(tr("health_method", lang))}</p>'
    )


# =============================================================================
# DOCUMENT
# =============================================================================

def build_html(ctx, *, sections=None, lang: str = "en", title: str | None = None,
               client_name: str | None = None, prepared_by: str | None = None,
               benchmark_stats: dict | None = None, benchmark_name: str = "",
               stress_results=None) -> str:
    """
    Render the full report.

    `sections` selects and orders the blocks; unknown keys are ignored so the
    caller can pass a user's checkbox state straight through.
    """
    sections = [s for s in (sections or SECTIONS) if s in SECTIONS]
    currency = ctx.currency
    title = title or tr("product", lang)
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")

    start = ctx.portfolio_returns.index[0].strftime("%Y-%m-%d")
    end = ctx.portfolio_returns.index[-1].strftime("%Y-%m-%d")

    builders = {
        "overview": lambda: _overview(ctx, lang, currency),
        "performance": lambda: _performance(ctx, lang, benchmark_stats, benchmark_name),
        "risk": lambda: _risk(ctx, lang),
        "diversification": lambda: _diversification(ctx, lang),
        "concentration": lambda: _concentration(ctx, lang),
        "stress": lambda: _stress(ctx, lang, stress_results, currency),
        "observations": lambda: _observations(ctx, lang),
        "optimization": lambda: _optimization(ctx, lang),
        "dna": lambda: _dna(ctx, lang),
    }

    body = []
    for index, key in enumerate(sections):
        try:
            content = builders[key]()
        except Exception as error:                       # noqa: BLE001
            # One failing section must not cost the whole report. The gap is
            # labelled rather than silently omitted, so nobody hands a client a
            # document with a section quietly missing.
            content = (f'<p class="note">Section unavailable: '
                       f'{_esc(str(error)[:160])}</p>')
        body.append(_section(key, lang, content, page_break=index > 0))

    meta_bits = [f'{_esc(tr("period", lang))}: {start} → {end}']
    if client_name:
        meta_bits.insert(0, _esc(client_name))
    if prepared_by:
        meta_bits.append(f'{_esc(prepared_by)}')
    meta_bits.append(generated)

    return f"""<!DOCTYPE html>
<html lang="{lang}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(title)}</title>
<style>{_STYLE}</style></head>
<body>
<header>
  <div class="brand">{_esc(tr("product", lang))}</div>
  <h1>{_esc(title)}</h1>
  <div class="meta">{' · '.join(meta_bits)}</div>
</header>
{''.join(body)}
<footer>
  <div class="disclaimer">{_esc(DISCLAIMER.get(lang, DISCLAIMER['en']))}</div>
  <div class="footer-brand">{_esc(tr("product", lang))} · {generated}</div>
</footer>
</body></html>"""
