"""
Interactive charts for lessons, in the platform's design system.

`figure()` builds the Plotly figure from a `Chart` and its `Dataset`; it is pure
and tested on its own. `render()` puts it on the page with the source line the
dataset carries, so no chart can be shown without its origin, licence and date.

Plotly is already a dependency of the portfolio application; nothing new is
installed for this. The mode bar is hidden and zoom is left to the reader's
hover and range selection, which is the interaction that helps in a lesson.
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from ...platform.ui.components import esc, html
from ...platform.ui.theme import TOKENS
from ..datasets import Chart, Dataset

PALETTE = (TOKENS["blue"], TOKENS["gold"], TOKENS["green"], TOKENS["red"], TOKENS["ink-3"])
# The Monnaie et crypto universe leads with its copper accent.
PALETTES = {"trading": PALETTE,
            "monnaie": (TOKENS["copper-2"], TOKENS["blue"], TOKENS["green"], TOKENS["gold"], TOKENS["ink-3"])}
FONT = "DM Sans, -apple-system, Segoe UI, Helvetica, Arial, sans-serif"
MONO = "DM Mono, SFMono-Regular, Consolas, monospace"


_SUPERSCRIPT = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")


def _fr(value) -> str:
    if isinstance(value, float) and value and abs(value) < 1e-4:
        # A probability of 9e-8 must not read as « 0 ».
        mantissa, exponent = f"{value:.2e}".split("e")
        return f"{mantissa.replace('.', ',')} × 10{str(int(exponent)).translate(_SUPERSCRIPT)}"
    if isinstance(value, float):
        text = f"{value:,.4f}".rstrip("0").rstrip(".")
        return text.replace(",", " ").replace(".", ",")
    if isinstance(value, int):
        return f"{value:,}".replace(",", " ")
    return str(value)


def figure(chart: Chart, dataset: Dataset, *, universe: str = "trading") -> go.Figure:
    palette = PALETTES.get(universe, PALETTE)
    rows = list(dataset.rows)
    xs = [r[chart.x] for r in rows]
    flags = [bool(r.get(chart.highlight)) for r in rows] if chart.highlight else [False] * len(rows)
    fig = go.Figure()
    for i, (column, label) in enumerate(chart.series):
        color = palette[i % len(palette)]
        ys = [r[column] for r in rows]
        text = ["" if y is None else f"{_fr(y)} {dataset.unit}".strip() + (" · estimation" if f else "")
                for y, f in zip(ys, flags)]
        if chart.kind == "bar":
            fig.add_trace(go.Bar(x=xs, y=ys, name=label, text=text, hoverinfo="text+x", textposition="none",
                                 marker=dict(color=color, opacity=[0.45 if f else 0.9 for f in flags],
                                             line=dict(width=0))))
        else:
            fig.add_trace(go.Scatter(
                x=xs, y=ys, name=label, text=text, hoverinfo="text+x",
                # Markers help on a handful of points (one per halving); on a monthly
                # series they hide the line.
                mode="lines+markers" if len(rows) <= 40 else "lines", line=dict(color=color, width=2.2, shape="hv" if chart.kind == "step" else "linear"),
                fill="tozeroy" if chart.kind == "area" else None,
                marker=dict(size=[7 if f else 8 for f in flags], color=[TOKENS["white"] if f else color for f in flags],
                            line=dict(color=color, width=1.6))))
    style(fig, x_label=chart.x_label, y_label=chart.y_label, legend=len(chart.series) > 1,
          y_log=chart.y_log, stacked=chart.stacked)
    return fig


def style(fig: go.Figure, *, x_label: str = "", y_label: str = "", legend: bool = True,
          y_log: bool = False, stacked: bool = False, height: int = 380, numeric_x: bool = False) -> go.Figure:
    """The design system applied to any Plotly figure: fonts, colours, grid, French separators."""
    axis = dict(gridcolor=TOKENS["line"], zerolinecolor=TOKENS["line-strong"], linecolor=TOKENS["line-strong"],
                automargin=True, tickformat=",~r",
                tickfont=dict(family=MONO, size=11, color=TOKENS["muted"]),
                title_font=dict(family=FONT, size=12, color=TOKENS["muted"]))
    xaxis = dict(axis) if numeric_x else {k: v for k, v in axis.items() if k != "tickformat"}
    fig.update_layout(
        separators=", ", font=dict(family=FONT, size=13, color=TOKENS["text"]),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        # A legend sits above the plot area; with several series it needs the room.
        margin=dict(l=10, r=10, t=56 if legend else 14, b=10), height=height, bargap=0.25,
        barmode="stack" if stacked else "group",
        showlegend=legend, legend=dict(orientation="h", y=1.02, x=0, yanchor="bottom"),
        hoverlabel=dict(bgcolor=TOKENS["white"], bordercolor=TOKENS["line-strong"],
                        font=dict(family=FONT, color=TOKENS["ink"])),
        xaxis=dict(xaxis, title=dict(text=x_label, standoff=12)),
        yaxis=dict(axis, title=dict(text=y_label, standoff=14), type="log" if y_log else "linear",
                   # On a log axis, powers of ten read better than long decimals.
                   **({"tickformat": "", "exponentformat": "power", "showexponent": "all", "dtick": 2}
                      if y_log else {})),
    )
    return fig


def render(chart: Chart, dataset: Dataset, *, caption: str = "", number: int | None = None, key: str,
           universe: str = "trading") -> None:
    with st.container(key=f"chart_{key}"):
        if chart.title:
            html(f'<div class="sx-chart-title">{esc(chart.title)}</div>')
        st.plotly_chart(figure(chart, dataset, universe=universe), key=f"plot_{key}", theme=None,
                        config={"displayModeBar": False, "responsive": True})
        label = f"Figure {number}" if number else "Figure"
        flag = '<span class="sx-pill soon">Exemple synthétique</span> ' if dataset.synthetic else ""
        estimate = ' <span class="sx-chart-key">Points clairs : estimations.</span>' if chart.highlight and any(
            r.get(chart.highlight) for r in dataset.rows) else ""
        link = (f' <a href="{esc(dataset.url)}" target="_blank" rel="noopener">référence</a>'
                if dataset.url and not dataset.synthetic else "")
        html(f'<div class="sx-chart-foot">{f"<b>{label}</b><span>{esc(caption)}</span>" if caption else ""}'
             f'<p class="sx-chart-credit">{flag}{esc(dataset.credit)}{link}{estimate}</p></div>')
