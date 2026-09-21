"""
Document primitives for printable reports.

The palette, the formatters, the inline-SVG charts and the stylesheet that both
the portfolio report and the weekly trading review are built from. Neutral
about either domain: it knows how to draw a line chart and lay out a KPI row,
and nothing about what a Sharpe ratio or an R multiple is.

Extracted rather than duplicated. Two hand-written SVG renderers would drift,
and the one that drifted would be whichever had fewer readers — so the trading
review and the portfolio report would slowly stop looking like the same
product, which is the one thing a client-facing document cannot afford.

Why HTML rather than a generated PDF
------------------------------------
A native PDF would mean a rendering dependency (reportlab, or kaleido to turn
Plotly figures into images). Kaleido in particular is heavy and routinely fails
on hosted Streamlit. A self-contained HTML file with a print stylesheet reaches
the same destination — the browser's "Save as PDF" produces a clean, paginated
document — without a dependency that breaks the deploy. The trade-off is that
the user presses Ctrl+P, and that is stated in the UI rather than hidden.

Why these documents are light and the app is dark
-------------------------------------------------
The app is a screen instrument; a report is a document that gets printed and
handed over. A dark background wastes ink, greys out on most printers and reads
as a screenshot rather than a deliverable. The accents carry over so the two
still look like one product.

No Streamlit import, and no engine import: this module is only ever a renderer.
"""

from __future__ import annotations

import html as _html

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


# Roughly the width of one character at font-size 10 in the document's face.
# Used to shorten a label that would otherwise run off the left edge of the
# canvas — an SVG has no overflow to clip against, so a long label does not get
# truncated, it gets *drawn outside the picture* and silently loses its first
# few characters. "Break of Structure" became "reak of Structure".
_CHAR_PX = 5.4


def _fit(label: str, available: float) -> str:
    """Shorten a label to what fits, with an ellipsis rather than a clean cut."""
    budget = int(max(4, (available - 8) / _CHAR_PX))
    return label if len(label) <= budget else label[: budget - 1] + "…"


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
                     f'font-size="10" fill="{INK_2}">{_esc(_fit(label, label_width))}</text>')
        parts.append(f'<rect x="{label_width}" y="{y + 3}" width="{bar_w:.1f}" '
                     f'height="12" rx="3" fill="{color}"/>')
        text = _pct(value, 1) if as_pct else f"{value:,.2f}"
        parts.append(f'<text x="{label_width + bar_w + 6:.1f}" y="{y + 13}" '
                     f'font-size="10" fill="{INK_2}">{text}</text>')
    parts.append("</svg>")
    return "".join(parts)


def svg_diverging_bars(items, width: int = 360, label_width: int = 92,
                       row_height: int = 22, as_pct: bool = True,
                       currency: str = "$") -> str:
    """
    Bars diverging from a centre line, for contributions and impacts.

    `as_pct` decides the value label. It defaults to True because this chart was
    built for weight and contribution deltas, which are fractions — but the
    trading review plots money through it, and a dollar amount formatted as a
    percentage reads "+142893.0%". The parameter exists so neither caller has to
    know what the other assumed.
    """
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
                     f'font-size="10" fill="{INK_2}">{_esc(_fit(label, label_width))}</text>')
        parts.append(f'<rect x="{x:.1f}" y="{y + 3}" width="{bar_w:.1f}" height="12" '
                     f'rx="3" fill="{color}"/>')
        anchor = centre + bar_w + 6 if value >= 0 else centre - bar_w - 6
        align = "start" if value >= 0 else "end"
        text = (_pct(value, 1, sign=True) if as_pct
                else f"{'+' if value >= 0 else '-'}{currency}{abs(value):,.0f}")
        parts.append(f'<text x="{anchor:.1f}" y="{y + 13}" text-anchor="{align}" '
                     f'font-size="10" fill="{INK_2}">{_esc(text)}</text>')
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
