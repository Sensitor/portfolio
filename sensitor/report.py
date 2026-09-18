"""
Client-ready portfolio report.

Produces one self-contained HTML document: no JavaScript, no external requests,
every chart drawn as inline SVG. Open it anywhere, print it to PDF from the
browser, email the file — it works offline and it looks the same everywhere.

Why HTML rather than a generated PDF
------------------------------------
A native PDF would mean a rendering dependency (reportlab, or kaleido to turn
Plotly figures into images). Kaleido in particular is heavy and routinely fails
on hosted Streamlit. A self-contained HTML file with a print stylesheet reaches
the same destination — the browser's "Save as PDF" produces a clean, paginated
document — without a dependency that breaks the deploy. The trade-off is that
the user presses Ctrl+P, and that is stated in the UI rather than hidden.

Why the report is light and the app is dark
-------------------------------------------
The app is a screen instrument; the report is a document that gets printed and
handed over. A dark background wastes ink, greys out on most printers and reads
as a screenshot rather than a deliverable. The palette's accents carry over so
the two still look like one product.

No Streamlit import. `build_html` takes the same `Context` the pages use.
"""

from __future__ import annotations

import html as _html
from datetime import datetime

from . import xray as X
from .i18n import tr

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

# Light-document palette. Hues match the app's series colours so the two read as
# one product; the surfaces are inverted for print.
INK = "#14181F"
INK_2 = "#4A5668"
INK_3 = "#7A8798"
RULE = "#E2E6EC"
SURFACE = "#FFFFFF"
SURFACE_2 = "#F6F8FA"
ACCENT = "#2A6FC4"
POS = "#0F8F5F"
NEG = "#C43A39"
SERIES = ["#2A6FC4", "#C4501F", "#12805C", "#A86E00", "#B8446E",
          "#006B00", "#6F62C8", "#C45050"]

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


def _esc(value) -> str:
    return _html.escape(str(value), quote=True)


def _pct(value, decimals=1, sign=False) -> str:
    if value is None:
        return "—"
    return f"{value * 100:{'+' if sign else ''}.{decimals}f}%"


def _num(value, decimals=2) -> str:
    return "—" if value is None else f"{value:.{decimals}f}"


def _money(value, currency="$") -> str:
    if value is None:
        return "—"
    if abs(value) >= 1_000_000:
        return f"{currency}{value / 1_000_000:.2f}M"
    return f"{currency}{value:,.0f}"


# =============================================================================
# INLINE SVG CHARTS
# =============================================================================

def svg_lines(series_map: dict, width: int = 720, height: int = 230) -> str:
    """
    Multi-series line chart.

    Drawn by hand rather than exported from Plotly because the report must stay
    self-contained and script-free: an SVG path prints correctly and needs no
    runtime, whereas an exported image needs a rendering dependency.
    """
    series_map = {k: v for k, v in series_map.items() if v is not None and len(v) > 1}
    if not series_map:
        return ""

    all_values = [float(v) for series in series_map.values() for v in series]
    lo, hi = min(all_values), max(all_values)
    span = (hi - lo) or 1.0
    pad_left, pad_bottom, pad_top = 54, 22, 10
    plot_w = width - pad_left - 8
    plot_h = height - pad_top - pad_bottom

    parts = [f'<svg viewBox="0 0 {width} {height}" width="100%" '
             f'style="max-width:{width}px;font-family:inherit;">']

    # Horizontal guides with value labels.
    for i in range(4):
        y = pad_top + plot_h * i / 3
        value = hi - span * i / 3
        parts.append(f'<line x1="{pad_left}" y1="{y:.1f}" x2="{width - 8}" y2="{y:.1f}" '
                     f'stroke="{RULE}" stroke-width="1"/>')
        parts.append(f'<text x="{pad_left - 8}" y="{y + 3.5:.1f}" text-anchor="end" '
                     f'font-size="9" fill="{INK_3}">{value:,.0f}</text>')

    for index, (name, series) in enumerate(series_map.items()):
        values = [float(v) for v in series]
        # Downsample: a 900-point path bloats the file and prints identically.
        if len(values) > 300:
            step = len(values) / 300
            values = [values[int(i * step)] for i in range(300)]
        n = len(values)
        points = " ".join(
            f"{pad_left + i * plot_w / (n - 1):.1f},"
            f"{pad_top + plot_h - ((v - lo) / span) * plot_h:.1f}"
            for i, v in enumerate(values)
        )
        color = ACCENT if index == 0 else SERIES[index % len(SERIES)]
        parts.append(f'<polyline points="{points}" fill="none" stroke="{color}" '
                     f'stroke-width="{2 if index == 0 else 1.4}" stroke-linejoin="round"/>')

    # Legend beneath the plot.
    x = pad_left
    for index, name in enumerate(series_map):
        color = ACCENT if index == 0 else SERIES[index % len(SERIES)]
        parts.append(f'<rect x="{x}" y="{height - 11}" width="10" height="3" rx="1.5" fill="{color}"/>')
        parts.append(f'<text x="{x + 14}" y="{height - 6}" font-size="9" fill="{INK_2}">'
                     f'{_esc(name)}</text>')
        x += 16 + len(str(name)) * 5.4
    parts.append("</svg>")
    return "".join(parts)


def svg_bars(items, width: int = 340, label_width: int = 92,
             colors=None, as_pct: bool = True, row_height: int = 22) -> str:
    """Horizontal bars with direct labels — the report's workhorse chart."""
    items = [(str(k), float(v)) for k, v in items]
    if not items:
        return ""
    height = row_height * len(items) + 6
    largest = max(abs(v) for _, v in items) or 1.0
    bar_area = width - label_width - 54

    parts = [f'<svg viewBox="0 0 {width} {height}" width="100%" '
             f'style="max-width:{width}px;font-family:inherit;">']
    for i, (label, value) in enumerate(items):
        y = i * row_height + 3
        bar_w = abs(value) / largest * bar_area
        color = (colors[i] if colors and i < len(colors)
                 else (SERIES[i % len(SERIES)] if as_pct else (POS if value >= 0 else NEG)))
        parts.append(f'<text x="{label_width - 8}" y="{y + 12}" text-anchor="end" '
                     f'font-size="10" fill="{INK_2}">{_esc(label)}</text>')
        parts.append(f'<rect x="{label_width}" y="{y + 3}" width="{bar_w:.1f}" '
                     f'height="12" rx="3" fill="{color}"/>')
        text = _pct(value, 1) if as_pct else f"{value:,.2f}"
        parts.append(f'<text x="{label_width + bar_w + 6:.1f}" y="{y + 13}" '
                     f'font-size="10" fill="{INK_2}">{text}</text>')
    parts.append("</svg>")
    return "".join(parts)


def svg_diverging_bars(items, width: int = 360, label_width: int = 92,
                       row_height: int = 22) -> str:
    """Bars diverging from a centre line, for contributions and impacts."""
    items = [(str(k), float(v)) for k, v in items]
    if not items:
        return ""
    height = row_height * len(items) + 6
    largest = max(abs(v) for _, v in items) or 1.0
    half = (width - label_width - 48) / 2
    centre = label_width + half

    parts = [f'<svg viewBox="0 0 {width} {height}" width="100%" '
             f'style="max-width:{width}px;font-family:inherit;">']
    parts.append(f'<line x1="{centre}" y1="0" x2="{centre}" y2="{height - 6}" '
                 f'stroke="{RULE}" stroke-width="1"/>')
    for i, (label, value) in enumerate(items):
        y = i * row_height + 3
        bar_w = abs(value) / largest * half
        x = centre if value >= 0 else centre - bar_w
        color = POS if value >= 0 else NEG
        parts.append(f'<text x="{label_width - 8}" y="{y + 12}" text-anchor="end" '
                     f'font-size="10" fill="{INK_2}">{_esc(label)}</text>')
        parts.append(f'<rect x="{x:.1f}" y="{y + 3}" width="{bar_w:.1f}" height="12" '
                     f'rx="3" fill="{color}"/>')
        anchor = centre + bar_w + 6 if value >= 0 else centre - bar_w - 6
        align = "start" if value >= 0 else "end"
        parts.append(f'<text x="{anchor:.1f}" y="{y + 13}" text-anchor="{align}" '
                     f'font-size="10" fill="{INK_2}">{_pct(value, 1, sign=True)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def svg_gauge(score: float, size: int = 130) -> str:
    """Semicircular score dial."""
    score = max(0.0, min(100.0, float(score)))
    radius = size / 2 - 12
    cx, cy = size / 2, size / 2 + 6
    color = (POS if score >= 65 else "#C08A00" if score >= 50 else NEG)
    circumference = 3.14159 * radius

    return (
        f'<svg viewBox="0 0 {size} {size * 0.68}" width="{size}" '
        f'style="font-family:inherit;">'
        f'<path d="M {cx - radius} {cy} A {radius} {radius} 0 0 1 {cx + radius} {cy}" '
        f'fill="none" stroke="{RULE}" stroke-width="10" stroke-linecap="round"/>'
        f'<path d="M {cx - radius} {cy} A {radius} {radius} 0 0 1 {cx + radius} {cy}" '
        f'fill="none" stroke="{color}" stroke-width="10" stroke-linecap="round" '
        f'stroke-dasharray="{circumference * score / 100:.1f} {circumference:.1f}"/>'
        f'<text x="{cx}" y="{cy - 6}" text-anchor="middle" font-size="26" '
        f'font-weight="700" fill="{INK}">{score:.0f}</text>'
        f'</svg>'
    )


def svg_radar(labels, values, size: int = 230, max_value: float = 100) -> str:
    """Profile radar for the DNA section."""
    import math
    n = len(labels)
    if n < 3:
        return ""
    cx = cy = size / 2
    radius = size / 2 - 34

    def point(index, fraction):
        angle = -math.pi / 2 + 2 * math.pi * index / n
        r = radius * max(0.0, min(1.0, fraction))
        return cx + r * math.cos(angle), cy + r * math.sin(angle)

    parts = [f'<svg viewBox="0 0 {size} {size}" width="{size}" style="font-family:inherit;">']
    for ring in (0.25, 0.5, 0.75, 1.0):
        ring_points = " ".join(f"{x:.1f},{y:.1f}" for x, y in
                               (point(i, ring) for i in range(n)))
        parts.append(f'<polygon points="{ring_points}" fill="none" stroke="{RULE}" '
                     f'stroke-width="1"/>')

    shape = " ".join(f"{x:.1f},{y:.1f}" for x, y in
                     (point(i, v / max_value) for i, v in enumerate(values)))
    parts.append(f'<polygon points="{shape}" fill="{ACCENT}22" stroke="{ACCENT}" '
                 f'stroke-width="2"/>')

    for i, label in enumerate(labels):
        x, y = point(i, 1.20)
        anchor = "middle" if abs(x - cx) < 12 else ("start" if x > cx else "end")
        parts.append(f'<text x="{x:.1f}" y="{y + 3:.1f}" text-anchor="{anchor}" '
                     f'font-size="9" fill="{INK_2}">{_esc(label)}</text>')
    parts.append("</svg>")
    return "".join(parts)


# =============================================================================
# HTML BUILDING BLOCKS
# =============================================================================

def _kpi(label: str, value: str, sub: str = "") -> str:
    sub_html = f'<div class="kpi-sub">{_esc(sub)}</div>' if sub else ""
    return (f'<div class="kpi"><div class="kpi-label">{_esc(label)}</div>'
            f'<div class="kpi-value">{_esc(value)}</div>{sub_html}</div>')


def _table(headers, rows, align=None) -> str:
    align = align or ("l" + "r" * (len(headers) - 1))
    head = "".join(
        f'<th style="text-align:{"right" if align[i] == "r" else "left"}">{_esc(h)}</th>'
        for i, h in enumerate(headers)
    )
    body = "".join(
        "<tr>" + "".join(
            f'<td style="text-align:{"right" if align[i] == "r" else "left"}">{_esc(c)}</td>'
            for i, c in enumerate(row)
        ) + "</tr>"
        for row in rows
    )
    return f'<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>'


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


_STYLE = f"""
@page {{ size: A4; margin: 16mm 14mm; }}
* {{ box-sizing: border-box; }}
body {{
  font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
  color: {INK}; background: {SURFACE}; margin: 0;
  padding: 28px 32px 40px 32px; max-width: 900px; margin: 0 auto;
  font-size: 13px; line-height: 1.55; -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}}
header {{ border-bottom: 2px solid {INK}; padding-bottom: 14px; margin-bottom: 26px; }}
.brand {{
  font-size: 9px; font-weight: 700; letter-spacing: 0.18em;
  text-transform: uppercase; color: {ACCENT}; margin-bottom: 6px;
}}
h1 {{ font-size: 26px; margin: 0; letter-spacing: -0.03em; font-weight: 800; }}
h2 {{
  font-size: 12px; font-weight: 700; letter-spacing: 0.13em; text-transform: uppercase;
  color: {INK}; margin: 0 0 14px 0; padding-bottom: 7px; border-bottom: 1px solid {RULE};
}}
h3 {{ font-size: 12px; font-weight: 700; margin: 20px 0 8px 0; color: {INK}; }}
h4 {{ font-size: 10px; font-weight: 700; margin: 0 0 6px 0; color: {INK_2};
     text-transform: uppercase; letter-spacing: 0.08em; }}
.meta {{ font-size: 11px; color: {INK_3}; margin-top: 8px; }}
.section {{ margin-bottom: 30px; }}
.kpi-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 18px; }}
.kpi {{ background: {SURFACE_2}; border: 1px solid {RULE}; border-radius: 8px; padding: 11px 13px; }}
.kpi-label {{ font-size: 8.5px; font-weight: 700; letter-spacing: 0.11em;
             text-transform: uppercase; color: {INK_3}; }}
.kpi-value {{ font-size: 20px; font-weight: 800; letter-spacing: -0.03em; margin-top: 4px;
             font-variant-numeric: tabular-nums; }}
.kpi-sub {{ font-size: 9.5px; color: {INK_3}; margin-top: 2px; }}
table {{ width: 100%; border-collapse: collapse; font-size: 11.5px; margin: 10px 0; }}
th {{ font-size: 8.5px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase;
     color: {INK_3}; padding: 7px 9px; border-bottom: 1.5px solid {RULE}; }}
td {{ padding: 7px 9px; border-bottom: 1px solid {RULE}; font-variant-numeric: tabular-nums; }}
tbody tr:last-child td {{ border-bottom: none; }}
.chart {{ margin: 14px 0; }}
.chart-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 18px; margin-top: 14px; }}
.two-col {{ display: grid; grid-template-columns: 1.4fr 1fr; gap: 22px; align-items: start; }}
.gauge-wrap, .radar-wrap {{ text-align: center; padding-top: 8px; }}
.gauge-label {{ font-size: 9px; font-weight: 700; letter-spacing: 0.11em;
               text-transform: uppercase; color: {INK_3}; margin-top: 2px; }}
.gauge-band {{ font-size: 12px; font-weight: 700; color: {INK}; margin-top: 3px; }}
.obs {{ border-left: 3px solid {INK_3}; background: {SURFACE_2}; padding: 10px 13px;
       margin-bottom: 9px; border-radius: 0 6px 6px 0; }}
.obs-title {{ font-size: 12px; font-weight: 700; margin-bottom: 3px; }}
.obs-body {{ font-size: 11.5px; color: {INK_2}; }}
.obs-foot {{ font-size: 9.5px; color: {INK_3}; margin-top: 5px; }}
.note {{ font-size: 10px; color: {INK_3}; line-height: 1.6; margin: 10px 0 0 0; }}
footer {{ margin-top: 34px; padding-top: 14px; border-top: 1px solid {RULE}; }}
.disclaimer {{ font-size: 9px; color: {INK_3}; line-height: 1.65; }}
.footer-brand {{ font-size: 9px; color: {INK_3}; margin-top: 10px; font-weight: 600; }}
@media print {{
  body {{ padding: 0; max-width: none; }}
  .section.break {{ page-break-before: always; }}
  .section {{ page-break-inside: avoid; }}
  table, .obs, .kpi-grid {{ page-break-inside: avoid; }}
}}
@media (max-width: 720px) {{
  .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }}
  .two-col, .chart-grid {{ grid-template-columns: 1fr; }}
}}
"""
