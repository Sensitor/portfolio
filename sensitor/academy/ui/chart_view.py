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
FONT = "DM Sans, -apple-system, Segoe UI, Helvetica, Arial, sans-serif"
MONO = "DM Mono, SFMono-Regular, Consolas, monospace"


def _fr(value) -> str:
    if isinstance(value, float):
        text = f"{value:,.4f}".rstrip("0").rstrip(".")
        return text.replace(",", " ").replace(".", ",")
    if isinstance(value, int):
        return f"{value:,}".replace(",", " ")
    return str(value)


def figure(chart: Chart, dataset: Dataset) -> go.Figure:
    rows = list(dataset.rows)
    xs = [r[chart.x] for r in rows]
    flags = [bool(r.get(chart.highlight)) for r in rows] if chart.highlight else [False] * len(rows)
    fig = go.Figure()
    for i, (column, label) in enumerate(chart.series):
        color = PALETTE[i % len(PALETTE)]
        ys = [r[column] for r in rows]
        text = [f"{_fr(y)} {dataset.unit}".strip() + (" · estimation" if f else "") for y, f in zip(ys, flags)]
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
    axis = dict(gridcolor=TOKENS["line"], zerolinecolor=TOKENS["line-strong"], linecolor=TOKENS["line-strong"],
                automargin=True, tickformat=",~r",
                tickfont=dict(family=MONO, size=11, color=TOKENS["muted"]),
                title_font=dict(family=FONT, size=12, color=TOKENS["muted"]))
    fig.update_layout(
        separators=", ", font=dict(family=FONT, size=13, color=TOKENS["text"]),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=14, b=10), height=380, bargap=0.25,
        barmode="stack" if chart.stacked else "group",
        showlegend=len(chart.series) > 1, legend=dict(orientation="h", y=1.08, x=0),
        hoverlabel=dict(bgcolor=TOKENS["white"], bordercolor=TOKENS["line-strong"],
                        font=dict(family=FONT, color=TOKENS["ink"])),
        xaxis=dict({k: v for k, v in axis.items() if k != "tickformat"},
                   title=dict(text=chart.x_label, standoff=12)),
        yaxis=dict(axis, title=dict(text=chart.y_label, standoff=14),
                                                       type="log" if chart.y_log else "linear"),
    )
    return fig


def render(chart: Chart, dataset: Dataset, *, caption: str = "", number: int | None = None, key: str) -> None:
    with st.container(key=f"chart_{key}"):
        if chart.title:
            html(f'<div class="sx-chart-title">{esc(chart.title)}</div>')
        st.plotly_chart(figure(chart, dataset), key=f"plot_{key}", theme=None,
                        config={"displayModeBar": False, "responsive": True})
        label = f"Figure {number}" if number else "Figure"
        flag = '<span class="sx-pill soon">Exemple synthétique</span> ' if dataset.synthetic else ""
        estimate = ' <span class="sx-chart-key">Points clairs : estimations.</span>' if chart.highlight and any(
            r.get(chart.highlight) for r in dataset.rows) else ""
        link = (f' <a href="{esc(dataset.url)}" target="_blank" rel="noopener">référence</a>'
                if dataset.url and not dataset.synthetic else "")
        html(f'<div class="sx-chart-foot">{f"<b>{label}</b><span>{esc(caption)}</span>" if caption else ""}'
             f'<p class="sx-chart-credit">{flag}{esc(dataset.credit)}{link}{estimate}</p></div>')
