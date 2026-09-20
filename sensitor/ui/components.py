"""
Visual component library for Sensitor Portfolio Intelligence.

The governing rule: a metric is a visual component, never a line of text.
`Volatility: 18.4%` is a failure; a metric card carrying the figure, a fill meter
showing where it sits in its range, a benchmark delta and a sparkline is the
minimum bar.

Every component renders through `design.html()`, which collapses inter-tag
whitespace before handing the markup to Streamlit. Indented multi-line HTML gets
parsed as a markdown code block and rendered as literal text — that single quirk
is behind most "raw HTML showing on screen" bugs, and routing everything through
one helper removes the whole class of failure.

Delta and status colours always ship alongside a glyph (▲ ▼ ● ■), so hue never
carries meaning on its own.
"""

from __future__ import annotations

import html as _html

from .themes import (
    ACCENT, BORDER, FLAT, INK, INK_2, INK_FAINT, INK_MUTED, NEG, POS,
    RADIUS_SM, STATUS, STATUS_ICON, html,
)

# =============================================================================
# FORMATTERS
# =============================================================================

def pct(x, decimals: int = 1, sign: bool = False) -> str:
    if x is None:
        return "—"
    return f"{x * 100:{'+' if sign else ''}.{decimals}f}%"


def num(x, decimals: int = 2, sign: bool = False) -> str:
    if x is None:
        return "—"
    return f"{x:{'+' if sign else ''}.{decimals}f}"


def money(x, currency: str = "$", decimals: int = 0) -> str:
    if x is None:
        return "—"
    if abs(x) >= 1_000_000:
        return f"{currency}{x / 1_000_000:.2f}M"
    if abs(x) >= 10_000:
        return f"{currency}{x:,.0f}"
    return f"{currency}{x:,.{decimals}f}"


def _esc(s) -> str:
    return _html.escape(str(s), quote=True)


# =============================================================================
# PRIMITIVES
# =============================================================================

def tooltip_html(text: str) -> str:
    """Inline help marker. Returned as a string so it can sit inside a label."""
    if not text:
        return ""
    return (
        f'<span class="snr-tip"><span class="snr-tip-i">?</span>'
        f'<span class="snr-tip-body">{_esc(text)}</span></span>'
    )


def sparkline_svg(values, color: str = ACCENT, width: int = 108, height: int = 30,
                  fill: bool = True) -> str:
    """
    Inline SVG sparkline.

    Drawn as SVG rather than a Plotly figure because a dashboard renders dozens of
    these: an inline path costs nothing, while dozens of Plotly instances make the
    page crawl.
    """
    series = [float(v) for v in values if v is not None]
    if len(series) < 2:
        return f'<svg width="{width}" height="{height}"></svg>'

    # Downsample so the path stays small regardless of history length.
    if len(series) > 90:
        step = len(series) / 90
        series = [series[int(i * step)] for i in range(90)]

    lo, hi = min(series), max(series)
    span = (hi - lo) or 1.0
    pad = 3
    inner_h = height - 2 * pad
    n = len(series)

    points = [
        (i * width / (n - 1), pad + inner_h - ((v - lo) / span) * inner_h)
        for i, v in enumerate(series)
    ]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)

    area = ""
    if fill:
        uid = abs(hash((line, color))) % 10_000_000
        area = (
            f'<defs><linearGradient id="g{uid}" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0%" stop-color="{color}" stop-opacity="0.28"/>'
            f'<stop offset="100%" stop-color="{color}" stop-opacity="0"/>'
            f'</linearGradient></defs>'
            f'<polygon points="0,{height} {line} {width},{height}" fill="url(#g{uid})"/>'
        )

    end_x, end_y = points[-1]
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'preserveAspectRatio="none" style="display:block;overflow:visible;">'
        f'{area}'
        f'<polyline points="{line}" fill="none" stroke="{color}" stroke-width="2" '
        f'stroke-linejoin="round" stroke-linecap="round"/>'
        f'<circle cx="{end_x:.1f}" cy="{end_y:.1f}" r="2.6" fill="{color}"/>'
        f'</svg>'
    )


def meter_html(fraction: float, color: str = ACCENT, segments: int = 18) -> str:
    """Segmented fill meter — the readable form of `██████████░░░░`."""
    fraction = max(0.0, min(1.0, float(fraction or 0.0)))
    filled = round(fraction * segments)
    cells = "".join(
        f'<div class="snr-seg" style="background:{color};"></div>' if i < filled
        else '<div class="snr-seg"></div>'
        for i in range(segments)
    )
    return f'<div class="snr-meter">{cells}</div>'


def track_html(fraction: float, color: str = ACCENT) -> str:
    """Continuous progress track."""
    fraction = max(0.0, min(1.0, float(fraction or 0.0)))
    return (
        f'<div class="snr-track"><div class="snr-fill" '
        f'style="width:{fraction * 100:.1f}%;background:{color};"></div></div>'
    )


def pill_html(text: str, tone: str = "neutral", icon: bool = True) -> str:
    color = STATUS.get(tone, INK_2)
    glyph = f"{STATUS_ICON.get(tone, '')} " if icon and tone in STATUS_ICON else ""
    return (
        f'<span class="snr-pill" style="background:{color}1F;color:{color};">'
        f'{glyph}{_esc(text)}</span>'
    )


def delta_html(value, label: str = "", as_pct: bool = True, decimals: int = 1,
               higher_is_better: bool = True) -> str:
    """Signed delta with an arrow glyph, so direction never rests on colour alone."""
    if value is None:
        return f'<span style="color:{INK_FAINT};">—</span>'
    good = (value > 0) if higher_is_better else (value < 0)
    color = FLAT if abs(value) < 1e-12 else (POS if good else NEG)
    arrow = "▲" if value > 0 else ("▼" if value < 0 else "■")
    text = pct(value, decimals, sign=True) if as_pct else num(value, decimals, sign=True)
    # The space before the label is a non-breaking entity on purpose: design.html()
    # collapses whitespace between tags, so a literal space here would be eaten and
    # the delta would run into its label ("+17.2%vs S&P 500").
    suffix = (f'<span style="color:{INK_FAINT};font-weight:500;">&nbsp;{_esc(label)}</span>'
              if label else "")
    return f'<span class="snr-delta" style="color:{color};">{arrow} {text}</span>{suffix}'


# =============================================================================
# HEADERS
# =============================================================================

def page_header(title: str, subtitle: str = "", eyebrow: str = "") -> None:
    eyebrow_html = f'<div class="snr-eyebrow">{_esc(eyebrow)}</div>' if eyebrow else ""
    sub_html = f'<div class="snr-sub">{_esc(subtitle)}</div>' if subtitle else ""
    html(f'<div class="snr-page-head">{eyebrow_html}'
         f'<div class="snr-title">{_esc(title)}</div>{sub_html}</div>')


def section(title: str, subtitle: str = "") -> None:
    sub_html = f'<div class="snr-section-s">{_esc(subtitle)}</div>' if subtitle else ""
    html(f'<div class="snr-section"><div class="snr-section-t">{_esc(title)}</div>'
         f'{sub_html}</div>')


# =============================================================================
# THE METRIC CARD
# =============================================================================

def metric_card(
    label: str,
    value: str,
    *,
    delta=None,
    delta_label: str = "",
    delta_as_pct: bool = True,
    higher_is_better: bool = True,
    bar: float | None = None,
    bar_color: str | None = None,
    bar_style: str = "meter",          # "meter" | "track" | None
    spark=None,
    spark_color: str | None = None,
    tooltip: str = "",
    status: str | None = None,
    caption: str = "",
    compact: bool = False,
) -> None:
    """
    The atomic unit of the dashboard.

    A single call produces: label + help marker, the headline figure, a fill meter
    positioning it in its range, a signed benchmark delta, and a sparkline of its
    history. Every argument past `value` is optional, so a card degrades gracefully
    when a portfolio is too short or too small to support the full treatment — but
    a card should never be left with only a number.
    """
    accent = STATUS.get(status, bar_color or ACCENT)

    parts = ['<div class="snr-card snr-metric">']

    parts.append(
        f'<div class="snr-metric-label">{_esc(label)}{tooltip_html(tooltip)}</div>'
    )
    value_class = "snr-metric-value snr-num" + (" sm" if compact else "")
    parts.append(f'<div class="{value_class}">{_esc(value)}</div>')

    if bar is not None and bar_style:
        parts.append(
            meter_html(bar, accent) if bar_style == "meter" else track_html(bar, accent)
        )

    foot_left = ""
    if delta is not None:
        foot_left = delta_html(delta, delta_label, delta_as_pct,
                               higher_is_better=higher_is_better)
    elif caption:
        foot_left = f'<span style="color:{INK_MUTED};">{_esc(caption)}</span>'

    foot_right = ""
    if spark is not None and len(list(spark)) > 1:
        foot_right = sparkline_svg(spark, spark_color or accent)
    elif delta is not None and caption:
        foot_right = f'<span style="color:{INK_FAINT};">{_esc(caption)}</span>'

    # The footer row is always emitted, even when empty. Cards sit side by side in
    # a column row, and one card without a footer would be visibly shorter than
    # its neighbours — the reserved row keeps a KPI row flush.
    parts.append(
        f'<div class="snr-metric-foot"><div>{foot_left}</div>'
        f'<div>{foot_right}</div></div>'
    )

    parts.append("</div>")
    html("".join(parts))


def stat_card(label: str, value: str, sub: str = "", tone: str | None = None,
              tooltip: str = "") -> None:
    """Compact figure for dense grids where a full metric card would crowd."""
    color = STATUS.get(tone, INK) if tone else INK
    sub_html = (f'<div style="font-size:0.72rem;color:{INK_MUTED};margin-top:4px;">'
                f'{_esc(sub)}</div>') if sub else ""
    html(
        f'<div class="snr-card" style="padding:13px 15px;">'
        f'<div class="snr-metric-label">{_esc(label)}{tooltip_html(tooltip)}</div>'
        f'<div class="snr-num" style="font-size:1.28rem;font-weight:700;color:{color};'
        f'letter-spacing:-0.03em;margin-top:6px;">{_esc(value)}</div>'
        f'{sub_html}</div>'
    )


# =============================================================================
# SCORES
# =============================================================================

def score_bar(label: str, score: float, max_score: float = 100,
              tooltip: str = "", detail: str = "") -> None:
    """One component of a composite score, shown with its own fill."""
    fraction = max(0.0, min(1.0, score / max_score if max_score else 0))
    tone = "good" if fraction >= 0.75 else ("warning" if fraction >= 0.5 else "critical")
    color = STATUS[tone]
    detail_html = (f'<div style="font-size:0.7rem;color:{INK_FAINT};margin-top:5px;">'
                   f'{_esc(detail)}</div>') if detail else ""
    html(
        f'<div style="margin-bottom:15px;">'
        f'<div style="display:flex;justify-content:space-between;align-items:baseline;'
        f'margin-bottom:6px;">'
        f'<span style="font-size:0.8rem;color:{INK_2};font-weight:600;">'
        f'{_esc(label)}{tooltip_html(tooltip)}</span>'
        f'<span class="snr-num" style="font-size:0.85rem;font-weight:700;color:{color};">'
        f'{score:.0f}<span style="color:{INK_FAINT};font-weight:500;">/{max_score:.0f}</span></span>'
        f'</div>{track_html(fraction, color)}{detail_html}</div>'
    )


# =============================================================================
# ALERTS
# =============================================================================

def alert(level: str, title: str, body: str, footnote: str = "") -> None:
    """
    Threshold-based observation.

    Phrased as an observation about the data, never as advice. `footnote` carries
    the threshold that triggered it, so the reader can see why it fired.
    """
    color = STATUS.get(level, INK_2)
    icon = STATUS_ICON.get(level, "●")
    foot = (f'<div style="font-size:0.7rem;color:{INK_FAINT};margin-top:6px;">'
            f'{_esc(footnote)}</div>') if footnote else ""
    html(
        f'<div class="snr-alert" style="border-left-color:{color};">'
        f'<div style="color:{color};font-size:0.82rem;line-height:1.5;">{icon}</div>'
        f'<div style="flex:1;"><div class="snr-alert-t">{_esc(title)}</div>'
        f'<div class="snr-alert-b">{_esc(body)}</div>{foot}</div></div>'
    )


# =============================================================================
# TABLES
# =============================================================================

def data_table(headers: list[str], rows: list[list], align: str | None = None,
               bars: dict | None = None) -> None:
    """
    Dense data table with optional inline bars.

    `align` is a per-column string of 'l'/'r'. `bars` maps a column index to
    (max_value, colour); those cells render a value plus a proportional bar, which
    turns a wall of numbers into something scannable. Cell contents are escaped —
    pass plain values, not markup.
    """
    ncols = len(headers)
    align = align or ("l" + "r" * (ncols - 1))
    bars = bars or {}

    head = "".join(
        f'<th style="text-align:{"right" if align[i] == "r" else "left"};">{_esc(h)}</th>'
        for i, h in enumerate(headers)
    )

    body = []
    for row in rows:
        cells = []
        for i, cell in enumerate(row):
            klass = "k" if i == 0 else ""
            klass += " r" if align[i] == "r" else ""
            if i in bars:
                max_value, color = bars[i]
                raw = row[i][1] if isinstance(row[i], tuple) else 0
                text = row[i][0] if isinstance(row[i], tuple) else str(cell)
                frac = max(0.0, min(1.0, abs(raw) / max_value)) if max_value else 0
                cells.append(
                    f'<td class="{klass}"><div style="display:flex;align-items:center;'
                    f'gap:8px;justify-content:flex-end;">'
                    f'<span>{_esc(text)}</span>'
                    f'<div style="width:54px;height:5px;border-radius:3px;'
                    f'background:rgba(154,168,191,0.13);overflow:hidden;flex:none;">'
                    f'<div style="width:{frac * 100:.0f}%;height:100%;background:{color};'
                    f'border-radius:3px;"></div></div></div></td>'
                )
            else:
                cells.append(f'<td class="{klass}">{_esc(cell)}</td>')
        body.append(f"<tr>{''.join(cells)}</tr>")

    html(
        f'<div class="snr-card" style="padding:4px 6px;overflow-x:auto;">'
        f'<table class="snr-table"><thead><tr>{head}</tr></thead>'
        f'<tbody>{"".join(body)}</tbody></table></div>'
    )


# =============================================================================
# LAYOUT HELPERS
# =============================================================================

def spacer(height: int = 16) -> None:
    html(f'<div style="height:{height}px;"></div>')


def note(text: str, icon: str = "ⓘ") -> None:
    """Methodology footnote — where approximations and assumptions get stated."""
    html(
        f'<div style="display:flex;gap:8px;align-items:flex-start;padding:9px 12px;'
        f'background:rgba(154,168,191,0.04);border:1px solid {BORDER};'
        f'border-radius:{RADIUS_SM};margin-top:10px;">'
        f'<span style="color:{INK_FAINT};font-size:0.75rem;">{icon}</span>'
        f'<span style="font-size:0.73rem;color:{INK_MUTED};line-height:1.55;">'
        f'{_esc(text)}</span></div>'
    )


def empty_state(title: str, body: str, icon: str = "◎") -> None:
    html(
        f'<div class="snr-card" style="text-align:center;padding:44px 26px;">'
        f'<div style="font-size:2rem;color:{INK_FAINT};margin-bottom:12px;">{icon}</div>'
        f'<div style="font-size:1rem;font-weight:700;color:{INK};margin-bottom:6px;">'
        f'{_esc(title)}</div>'
        f'<div style="font-size:0.85rem;color:{INK_MUTED};max-width:430px;margin:0 auto;'
        f'line-height:1.6;">{_esc(body)}</div></div>'
    )
