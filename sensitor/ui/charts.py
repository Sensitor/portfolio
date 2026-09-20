"""
Themed Plotly chart factories for Sensitor Portfolio Intelligence.

Every chart in the app is built here so that grid, ink, hover styling and colour
assignment stay identical across pages. Pages call a factory and render it; they
never build a `go.Figure` themselves.

Rules enforced in this module
-----------------------------
* One y-axis per chart. Two measures of different scale get two charts or a
  common index — never a second axis.
* Categorical colour comes from the validated fixed-order palette and follows the
  entity, so filtering the series list never repaints the survivors.
* Sequential encodings use one hue; the correlation scale is the diverging pair
  with a neutral (non-hue) midpoint.
* Every chart carries a hover layer; a legend appears whenever there are two or
  more series.
* Grid and axes stay recessive; marks are thin.
"""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from .themes import (
    ACCENT, AXIS, BORDER_STRONG, DIVERGING, GRID, INK, INK_2, INK_FAINT,
    INK_MUTED, NEG, PALETTE, PALETTE_ALLPAIRS, POS, STATUS, SURFACE, SURFACE_2,
    plotly_layout, series_color,
)

_BAR_RADIUS = 4


def _bar_marker(color, **kw):
    """Bar marker with rounded data-ends, degrading if the Plotly build lacks it."""
    marker = dict(color=color, **kw)
    try:
        go.Bar(marker=dict(cornerradius=_BAR_RADIUS))
        marker["cornerradius"] = _BAR_RADIUS
    except Exception:
        pass
    return marker


# =============================================================================
# PERFORMANCE
# =============================================================================

def cumulative_performance(series_map: dict, height: int = 380,
                           value_prefix: str = "", fill: bool = True) -> go.Figure:
    """
    Growth-of-capital lines, portfolio first.

    `series_map` is {name: Series}. All series are indexed to the same base by the
    caller, so one axis carries them all.

    `fill=False` drops the area under a single series and lets the y-axis scale to
    the data. A filled area has to reach zero, which is right for a growth curve
    starting at a known base and wrong for a value history sampled at a few
    points — there it flattens the line against the top of the plot.
    """
    fig = go.Figure()
    for i, (name, series) in enumerate(series_map.items()):
        if series is None or len(series) < 2:
            continue
        color = ACCENT if i == 0 else series_color(i)
        width = 2.4 if i == 0 else 1.8
        fig.add_trace(go.Scatter(
            x=series.index, y=series.to_numpy(),
            name=name, mode="lines",
            line=dict(color=color, width=width),
            fill="tozeroy" if fill and i == 0 and len(series_map) == 1 else None,
            fillcolor=("rgba(57,135,229,0.10)"
                       if fill and i == 0 and len(series_map) == 1 else None),
            hovertemplate=f"<b>{name}</b>  {value_prefix}%{{y:,.2f}}<extra></extra>",
        ))

    fig.update_layout(**plotly_layout(
        height=height,
        showlegend=len(series_map) > 1,
        margin=dict(l=8, r=8, t=28 if len(series_map) > 1 else 8, b=8),
        xaxis=dict(showspikes=True, spikecolor=BORDER_STRONG,
                   spikethickness=1, spikemode="across", spikedash="dot"),
    ))
    return fig


def underwater(dd_series, height: int = 240) -> go.Figure:
    """Drawdown depth over time — the shape of every decline, not just the worst."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dd_series.index, y=dd_series.to_numpy() * 100,
        mode="lines", name="Drawdown",
        line=dict(color=NEG, width=1.6),
        fill="tozeroy", fillcolor="rgba(226,80,79,0.16)",
        hovertemplate="<b>%{y:.2f}%</b><extra></extra>",
    ))
    fig.update_layout(**plotly_layout(
        height=height,
        yaxis=dict(ticksuffix="%", rangemode="tozero"),
        xaxis=dict(showspikes=True, spikecolor=BORDER_STRONG,
                   spikethickness=1, spikemode="across", spikedash="dot"),
    ))
    return fig


def rolling_metric(rolling_df, column: str, height: int = 220,
                   as_pct: bool = True, reference: float | None = None) -> go.Figure:
    """A single rolling series, with an optional reference line for context."""
    fig = go.Figure()
    values = rolling_df[column].to_numpy() * (100 if as_pct else 1)
    fig.add_trace(go.Scatter(
        x=rolling_df.index, y=values, mode="lines",
        line=dict(color=ACCENT, width=2),
        fill="tozeroy", fillcolor="rgba(57,135,229,0.09)",
        hovertemplate=("<b>%{y:.2f}" + ("%" if as_pct else "") + "</b><extra></extra>"),
        name=column,
    ))
    if reference is not None:
        fig.add_hline(
            y=reference * (100 if as_pct else 1),
            line=dict(color=INK_FAINT, width=1, dash="dot"),
        )
    fig.update_layout(**plotly_layout(
        height=height,
        yaxis=dict(ticksuffix="%" if as_pct else ""),
    ))
    return fig


def contribution_bars(labels, values, height: int | None = None,
                      as_pct: bool = True, title_suffix: str = "") -> go.Figure:
    """
    Horizontal contribution chart — who added and who subtracted.

    Positive and negative use the directional pair, and each bar is direct-labelled,
    so the sign is carried by position and text as well as colour.
    """
    values = list(values)
    labels = list(labels)
    height = height or max(180, 34 * len(labels) + 40)
    colors = [POS if v >= 0 else NEG for v in values]
    scaled = [v * 100 if as_pct else v for v in values]
    text = [f"{v:+.2f}%" if as_pct else f"{v:+.2f}" for v in scaled]

    fig = go.Figure(go.Bar(
        x=scaled, y=labels, orientation="h",
        marker=_bar_marker(colors),
        text=text, textposition="outside",
        textfont=dict(size=11, color=INK_2),
        hovertemplate="<b>%{y}</b>  %{x:+.2f}" + ("%" if as_pct else "") + "<extra></extra>",
        width=0.62,
    ))
    span = max(abs(min(scaled)), abs(max(scaled))) if scaled else 1
    fig.update_layout(**plotly_layout(
        height=height, hovermode="closest",
        xaxis=dict(showgrid=True, gridcolor=GRID, zeroline=True,
                   zerolinecolor=AXIS, zerolinewidth=1,
                   range=[-span * 1.35, span * 1.35],
                   ticksuffix="%" if as_pct else ""),
        yaxis=dict(showgrid=False, type="category", autorange="reversed",
                   tickfont=dict(size=11, color=INK_2)),
        margin=dict(l=8, r=8, t=6, b=6),
    ))
    return fig


# =============================================================================
# RISK
# =============================================================================

def weight_vs_risk(rc_df, height: int | None = None,
                   label_weight: str = "Weight",
                   label_risk: str = "Risk contribution") -> go.Figure:
    """
    The signature risk chart: capital weight beside share of total volatility.

    Both series are percentages of the same whole, so one axis carries them, and
    the gap between the pair is the message — a small position can own a large
    share of the risk.
    """
    tickers = rc_df["ticker"].tolist()
    height = height or max(200, 40 * len(tickers) + 48)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=rc_df["weight"] * 100, y=tickers, orientation="h",
        name=label_weight,
        marker=_bar_marker(PALETTE[0], opacity=0.55),
        hovertemplate="<b>%{y}</b> — " + label_weight + " %{x:.1f}%<extra></extra>",
        width=0.34, offset=-0.34,
    ))
    fig.add_trace(go.Bar(
        x=rc_df["pct_contribution"] * 100, y=tickers, orientation="h",
        name=label_risk,
        marker=_bar_marker(PALETTE[1]),
        text=[f"{v * 100:.0f}%" for v in rc_df["pct_contribution"]],
        textposition="outside", textfont=dict(size=11, color=INK_2),
        hovertemplate="<b>%{y}</b> — " + label_risk + " %{x:.1f}%<extra></extra>",
        width=0.34, offset=0.0,
    ))

    top = max(rc_df["pct_contribution"].max(), rc_df["weight"].max()) * 100
    fig.update_layout(**plotly_layout(
        height=height, showlegend=True, hovermode="closest",
        barmode="overlay", bargap=0.30,
        xaxis=dict(showgrid=True, gridcolor=GRID, ticksuffix="%",
                   range=[0, top * 1.28]),
        yaxis=dict(showgrid=False, type="category", autorange="reversed",
                   tickfont=dict(size=11, color=INK_2)),
        margin=dict(l=8, r=8, t=30, b=6),
    ))
    return fig


def correlation_heatmap(corr_df, height: int | None = None) -> go.Figure:
    """
    Correlation matrix on the diverging scale, fixed to [-1, 1].

    The scale is pinned so colour means the same thing across every portfolio, and
    cells are direct-labelled so the exact value never depends on reading a hue.
    """
    tickers = list(corr_df.columns)
    n = len(tickers)
    height = height or max(280, 46 * n + 70)
    values = corr_df.to_numpy().astype(float).copy()

    # Mask the diagonal. Every asset correlates 1.00 with itself, so those cells
    # carry no information while taking the strongest colour on the scale and
    # pulling the eye away from the pairs that matter.
    labels = [[f"{v:.2f}" for v in row] for row in values]
    np.fill_diagonal(values, np.nan)
    for i in range(n):
        labels[i][i] = ""

    fig = go.Figure(go.Heatmap(
        z=values, x=tickers, y=tickers,
        colorscale=DIVERGING, zmid=0, zmin=-1, zmax=1,
        xgap=2, ygap=2,
        text=labels,
        texttemplate="%{text}",
        textfont=dict(size=10 if n <= 10 else 9, color=INK),
        hovertemplate="<b>%{y} ↔ %{x}</b><br>Correlation %{z:.3f}<extra></extra>",
        hoverongaps=False,
        colorbar=dict(
            thickness=9, len=0.62, outlinewidth=0,
            tickfont=dict(size=10, color=INK_MUTED),
            tickvals=[-1, -0.5, 0, 0.5, 1],
        ),
    ))
    fig.update_layout(**plotly_layout(
        height=height, hovermode="closest",
        xaxis=dict(side="bottom", showgrid=False, tickfont=dict(size=11, color=INK_2)),
        yaxis=dict(autorange="reversed", showgrid=False,
                   tickfont=dict(size=11, color=INK_2)),
        margin=dict(l=8, r=8, t=8, b=8),
    ))
    return fig


def return_distribution(returns, var_level: float | None = None,
                        cvar_level: float | None = None, height: int = 280) -> go.Figure:
    """
    Daily return histogram with the loss tail shaded.

    Bars beyond the VaR threshold take the critical colour, which is what makes
    "5% of days" a visible region rather than an abstract number.
    """
    values = returns.dropna().to_numpy() * 100
    threshold = -var_level * 100 if var_level else None

    counts, edges = np.histogram(values, bins=60)
    centers = (edges[:-1] + edges[1:]) / 2
    colors = [
        STATUS["critical"] if (threshold is not None and c <= threshold) else ACCENT
        for c in centers
    ]

    fig = go.Figure(go.Bar(
        x=centers, y=counts,
        marker=_bar_marker(colors),
        hovertemplate="Return %{x:.2f}%<br>%{y} days<extra></extra>",
        width=(edges[1] - edges[0]) * 0.88,
    ))

    if threshold is not None:
        fig.add_vline(x=threshold, line=dict(color=STATUS["critical"], width=1.5, dash="dash"),
                      annotation_text=f"VaR {threshold:.2f}%",
                      annotation_position="top right",
                      annotation_font=dict(size=10, color=STATUS["critical"]))
    if cvar_level is not None:
        fig.add_vline(x=-cvar_level * 100, line=dict(color=STATUS["serious"], width=1.2, dash="dot"),
                      annotation_text=f"CVaR {-cvar_level * 100:.2f}%",
                      annotation_position="top left",
                      annotation_font=dict(size=10, color=STATUS["serious"]))

    fig.update_layout(**plotly_layout(
        height=height, hovermode="closest", bargap=0.04,
        xaxis=dict(ticksuffix="%", showgrid=False, zeroline=True,
                   zerolinecolor=AXIS, zerolinewidth=1),
        yaxis=dict(title=None),
    ))
    return fig


def concentration_curve(sorted_weights, height: int = 260) -> go.Figure:
    """
    Cumulative weight by rank, against the equal-weight diagonal.

    Distance from the diagonal is concentration: a flat 45-degree line is perfectly
    even, a curve that reaches the ceiling in two steps is a two-position book.
    """
    n = len(sorted_weights)
    ranks = list(range(1, n + 1))
    cumulative = np.cumsum(sorted_weights) * 100
    equal = [(i / n) * 100 for i in ranks]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ranks, y=equal, mode="lines", name="Equal weight",
        line=dict(color=INK_FAINT, width=1.5, dash="dot"),
        hovertemplate="Equal weight %{y:.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=ranks, y=cumulative, mode="lines+markers", name="Portfolio",
        line=dict(color=ACCENT, width=2.4),
        marker=dict(size=8, color=ACCENT, line=dict(width=2, color=SURFACE)),
        fill="tonexty", fillcolor="rgba(57,135,229,0.12)",
        hovertemplate="Top %{x} positions = %{y:.1f}%<extra></extra>",
    ))
    fig.update_layout(**plotly_layout(
        height=height, showlegend=True, hovermode="x unified",
        xaxis=dict(title=None, dtick=1, tickfont=dict(size=11, color=INK_MUTED)),
        yaxis=dict(ticksuffix="%", range=[0, 105]),
        margin=dict(l=8, r=8, t=30, b=8),
    ))
    return fig


# =============================================================================
# COMPOSITION
# =============================================================================

def exposure_bars(breakdown: dict, height: int | None = None, max_items: int = 9,
                  color_map=None, other_label: str = "Other") -> go.Figure:
    """
    Horizontal allocation bars — the default for composition.

    Preferred over a pie because bars are read by length against a shared baseline,
    which stays accurate at ten buckets where a pie stops being legible. Past
    `max_items` the tail folds into one bucket rather than generating new hues.
    """
    items = list(breakdown.items())
    folded = len(items) > max_items
    if folded:
        head, tail = items[:max_items - 1], items[max_items - 1:]
        items = head + [(other_label, sum(v for _, v in tail))]

    labels = [k for k, _ in items]
    values = [v * 100 for _, v in items]
    colors = (
        [color_map(label) for label in labels] if callable(color_map)
        else [series_color(i) for i in range(len(labels))]
    )
    # The residual bucket is not a category — giving it a series hue makes a
    # leftover look like the portfolio's biggest real exposure.
    if folded:
        colors[-1] = INK_MUTED
    height = height or max(180, 33 * len(labels) + 34)

    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker=_bar_marker(colors),
        text=[f"{v:.1f}%" for v in values],
        textposition="outside", textfont=dict(size=11, color=INK_2),
        hovertemplate="<b>%{y}</b>  %{x:.2f}%<extra></extra>",
        width=0.64,
    ))
    fig.update_layout(**plotly_layout(
        height=height, hovermode="closest",
        xaxis=dict(showgrid=True, gridcolor=GRID, ticksuffix="%",
                   range=[0, max(values) * 1.24 if values else 100]),
        yaxis=dict(showgrid=False, type="category", autorange="reversed",
                   tickfont=dict(size=11, color=INK_2)),
        margin=dict(l=8, r=8, t=6, b=6),
    ))
    return fig


# =============================================================================
# SCORES
# =============================================================================

def health_gauge(score: float, height: int = 250, label: str = "",
                 tone: str | None = None) -> go.Figure:
    """
    Radial score dial.

    A gauge is used here because the number is a single bounded headline on a fixed
    0-100 scale — the one case where a dial beats a bar. Gauges are not used for
    anything else in the app.

    `tone` should be passed by callers that already have the score's band (from
    `health._band`), so the arc colour and the band label never disagree about the
    same number. The local fallback exists only for callers without one.
    """
    score = max(0.0, min(100.0, float(score)))
    if tone is None:
        tone = ("good" if score >= 65 else
                "warning" if score >= 50 else
                "serious" if score >= 35 else "critical")
    color = STATUS[tone]

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number=dict(font=dict(size=46, color=INK, family="Inter"),
                    valueformat=".0f", suffix=""),
        gauge=dict(
            axis=dict(range=[0, 100], tickwidth=1, tickcolor=INK_FAINT,
                      tickfont=dict(size=10, color=INK_MUTED),
                      tickvals=[0, 25, 50, 75, 100]),
            bar=dict(color=color, thickness=0.30),
            bgcolor="rgba(154,168,191,0.07)",
            borderwidth=0,
            # Band edges mirror health._band exactly, so the background zones,
            # the arc colour and the band label all agree.
            steps=[
                dict(range=[0, 35], color="rgba(226,80,79,0.10)"),
                dict(range=[35, 50], color="rgba(232,137,74,0.10)"),
                dict(range=[50, 65], color="rgba(232,163,23,0.10)"),
                dict(range=[65, 100], color="rgba(22,185,121,0.10)"),
            ],
            threshold=dict(line=dict(color=INK, width=2), thickness=0.78, value=score),
        ),
        domain=dict(x=[0, 1], y=[0, 1]),
    ))
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color=INK_2),
        margin=dict(l=24, r=24, t=18, b=8),
    )
    return fig


def radar(labels, values, height: int = 320, max_value: float = 100,
          name: str = "Portfolio", compare=None, compare_name: str = "") -> go.Figure:
    """
    Profile radar (Portfolio DNA / score breakdown).

    Radar is used only for a small fixed set of axes on one common 0-100 scale,
    where the shape itself is the takeaway. It is never used for unrelated measures.
    """
    closed_labels = list(labels) + [labels[0]]
    closed_values = list(values) + [values[0]]

    fig = go.Figure()
    if compare is not None:
        closed_compare = list(compare) + [compare[0]]
        fig.add_trace(go.Scatterpolar(
            r=closed_compare, theta=closed_labels, fill="toself",
            name=compare_name or "Reference",
            line=dict(color=INK_FAINT, width=1.5, dash="dot"),
            fillcolor="rgba(154,168,191,0.07)",
            hovertemplate="<b>%{theta}</b>  %{r:.0f}<extra></extra>",
        ))
    fig.add_trace(go.Scatterpolar(
        r=closed_values, theta=closed_labels, fill="toself", name=name,
        line=dict(color=ACCENT, width=2.2),
        fillcolor="rgba(57,135,229,0.20)",
        marker=dict(size=8, color=ACCENT, line=dict(width=2, color=SURFACE)),
        hovertemplate="<b>%{theta}</b>  %{r:.0f}<extra></extra>",
    ))
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", size=11, color=INK_2),
        showlegend=compare is not None,
        legend=dict(orientation="h", y=-0.08, x=0, font=dict(size=11, color=INK_2)),
        margin=dict(l=52, r=52, t=24, b=34),
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(range=[0, max_value], showticklabels=True,
                            tickfont=dict(size=9, color=INK_FAINT),
                            gridcolor=GRID, linecolor="rgba(0,0,0,0)"),
            angularaxis=dict(gridcolor=GRID, linecolor=GRID,
                             tickfont=dict(size=11, color=INK_2)),
        ),
        hoverlabel=dict(bgcolor=SURFACE_2, bordercolor=BORDER_STRONG,
                        font=dict(family="Inter", size=12, color=INK)),
    )
    return fig


# =============================================================================
# FACTORS
# =============================================================================

def factor_bars(loadings, height: int | None = None, label_fn=None,
                ns_suffix: str = "n.s.") -> go.Figure:
    """
    Factor loadings diverging from zero.

    Statistically weak loadings (|t| < 2) are drawn faded *and* suffixed in their
    label, so the distinction survives for a reader who cannot separate the two
    opacities — opacity alone would be a colour-only encoding.
    """
    loadings = list(loadings)
    if not loadings:
        return go.Figure()

    labels, values, colors, texts = [], [], [], []
    for item in loadings:
        name = label_fn(item["factor"]) if label_fn else item["factor"]
        significant = item.get("significant", True)
        labels.append(name if significant else f"{name}  ({ns_suffix})")
        values.append(item["loading"])
        base = POS if item["loading"] >= 0 else NEG
        colors.append(base if significant else "rgba(154,168,191,0.45)")
        texts.append(f"{item['loading']:+.2f}")

    height = height or max(200, 32 * len(labels) + 40)
    span = max(abs(v) for v in values) or 1

    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker=_bar_marker(colors),
        text=texts, textposition="outside",
        textfont=dict(size=11, color=INK_2),
        customdata=[[item.get("t_stat", 0.0), item.get("stderr", 0.0)] for item in loadings],
        hovertemplate=("<b>%{y}</b><br>Loading %{x:+.3f}"
                       "<br>t = %{customdata[0]:+.2f}  ·  s.e. %{customdata[1]:.3f}"
                       "<extra></extra>"),
        width=0.6,
    ))
    fig.update_layout(**plotly_layout(
        height=height, hovermode="closest",
        xaxis=dict(showgrid=True, gridcolor=GRID, zeroline=True,
                   zerolinecolor=AXIS, zerolinewidth=1,
                   range=[-span * 1.3, span * 1.3]),
        yaxis=dict(showgrid=False, type="category", autorange="reversed",
                   tickfont=dict(size=11, color=INK_2)),
        margin=dict(l=8, r=8, t=6, b=6),
    ))
    return fig


# =============================================================================
# STRESS
# =============================================================================

def scenario_bars(rows, height: int | None = None,
                  label_portfolio: str = "Portfolio",
                  label_benchmark: str = "Benchmark") -> go.Figure:
    """
    Portfolio versus benchmark impact per crisis scenario.

    Both series are returns over the same window, so one axis carries them. Rows
    arrive worst-first, which puts the scenarios that matter at the top.
    """
    rows = list(rows)
    if not rows:
        return go.Figure()
    labels = [r["label"] for r in rows]
    height = height or max(220, 42 * len(labels) + 46)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[r["portfolio"] * 100 for r in rows], y=labels, orientation="h",
        name=label_portfolio,
        marker=_bar_marker([NEG if r["portfolio"] < 0 else POS for r in rows]),
        text=[f"{r['portfolio'] * 100:+.1f}%" for r in rows],
        textposition="outside", textfont=dict(size=11, color=INK_2),
        hovertemplate="<b>%{y}</b> — " + label_portfolio + " %{x:+.1f}%<extra></extra>",
        width=0.34, offset=-0.34,
    ))
    has_bench = any(r.get("benchmark") is not None for r in rows)
    if has_bench:
        fig.add_trace(go.Bar(
            x=[(r.get("benchmark") or 0) * 100 for r in rows], y=labels, orientation="h",
            name=label_benchmark,
            marker=_bar_marker("rgba(154,168,191,0.42)"),
            hovertemplate="<b>%{y}</b> — " + label_benchmark + " %{x:+.1f}%<extra></extra>",
            width=0.34, offset=0.0,
        ))

    values = [r["portfolio"] * 100 for r in rows] + \
             [(r.get("benchmark") or 0) * 100 for r in rows]
    # Each side gets its own headroom. A single asymmetric range assumed losses
    # dominate, which clipped the bars of any scenario the portfolio gained in.
    low = min(min(values), 0.0)
    high = max(max(values), 0.0)
    pad = max(abs(low), abs(high), 1) * 0.16
    fig.update_layout(**plotly_layout(
        height=height, showlegend=has_bench, hovermode="closest",
        barmode="overlay", bargap=0.3,
        xaxis=dict(showgrid=True, gridcolor=GRID, zeroline=True,
                   zerolinecolor=AXIS, zerolinewidth=1, ticksuffix="%",
                   range=[low - pad * 1.5, high + pad * 1.5]),
        yaxis=dict(showgrid=False, type="category", autorange="reversed",
                   tickfont=dict(size=11, color=INK_2)),
        margin=dict(l=8, r=8, t=30 if has_bench else 6, b=6),
    ))
    return fig


def before_after_bars(rows, height: int | None = None,
                      label_before: str = "Before", label_after: str = "After") -> go.Figure:
    """
    Paired before/after values for a small set of metrics, each on its own row.

    Values are normalised to a common 0-1 scale per row before plotting, because
    a Sharpe ratio and a drawdown percentage cannot share an axis; the readable
    figures are carried by the direct labels.
    """
    rows = list(rows)
    if not rows:
        return go.Figure()
    height = height or max(200, 44 * len(rows) + 40)
    labels = [r["label"] for r in rows]

    def norm(row, key):
        span = max(abs(row["before"]), abs(row["after"])) or 1
        return abs(row[key]) / span

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[norm(r, "before") for r in rows], y=labels, orientation="h",
        name=label_before,
        marker=_bar_marker("rgba(154,168,191,0.40)"),
        text=[r["before_text"] for r in rows],
        textposition="outside", textfont=dict(size=11, color=INK_MUTED),
        hovertemplate="<b>%{y}</b> — " + label_before + " %{text}<extra></extra>",
        width=0.32, offset=-0.34,
    ))
    fig.add_trace(go.Bar(
        x=[norm(r, "after") for r in rows], y=labels, orientation="h",
        name=label_after,
        marker=_bar_marker([STATUS[r.get("tone", "warning")] for r in rows]),
        text=[r["after_text"] for r in rows],
        textposition="outside", textfont=dict(size=11, color=INK),
        hovertemplate="<b>%{y}</b> — " + label_after + " %{text}<extra></extra>",
        width=0.32, offset=0.02,
    ))
    fig.update_layout(**plotly_layout(
        height=height, showlegend=True, hovermode="closest",
        barmode="overlay", bargap=0.34,
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False,
                   range=[0, 1.42]),
        yaxis=dict(showgrid=False, type="category", autorange="reversed",
                   tickfont=dict(size=11, color=INK_2)),
        margin=dict(l=8, r=8, t=30, b=6),
    ))
    return fig


# =============================================================================
# OPTIMISATION
# =============================================================================

def frontier_scatter(result: dict, height: int = 430, lang: str = "en") -> go.Figure:
    """
    Risk/return scatter with the efficient frontier and the named portfolios.

    A scatter is an all-pairs colour form, so only the three all-pairs-safe slots
    carry identity here; each named portfolio is additionally given its own marker
    shape and a direct label, and the individual assets stay muted so they read as
    context rather than as a fourth series.
    """
    frontier = result.get("frontier") or []
    fig = go.Figure()

    if frontier:
        fig.add_trace(go.Scatter(
            x=[p["volatility"] * 100 for p in frontier],
            y=[p["return"] * 100 for p in frontier],
            mode="lines", name="Efficient frontier" if lang == "en" else "Frontière efficiente",
            line=dict(color=PALETTE_ALLPAIRS[0], width=2.4),
            hovertemplate="Vol %{x:.1f}%  ·  Return %{y:.1f}%<extra></extra>",
        ))

    assets = result.get("assets") or []
    if assets:
        fig.add_trace(go.Scatter(
            x=[a["volatility"] * 100 for a in assets],
            y=[a["return"] * 100 for a in assets],
            mode="markers+text", name="Holdings" if lang == "en" else "Positions",
            marker=dict(size=9, color="rgba(154,168,191,0.55)", symbol="circle",
                        line=dict(width=1.5, color=SURFACE)),
            text=[a["ticker"] for a in assets],
            textposition="top center",
            textfont=dict(size=10, color=INK_MUTED),
            hovertemplate="<b>%{text}</b><br>Vol %{x:.1f}%  ·  Return %{y:.1f}%<extra></extra>",
        ))

    named = [
        ("current", "Current" if lang == "en" else "Actuel",
         PALETTE_ALLPAIRS[1], "diamond", 15),
        ("max_sharpe", "Max Sharpe", PALETTE_ALLPAIRS[2], "star", 17),
        ("min_volatility", "Min volatility" if lang == "en" else "Vol. minimale",
         STATUS["warning"], "square", 13),
    ]
    for key, label, color, symbol, size in named:
        point = result.get(key)
        if not point:
            continue
        # No direct label on these three. They routinely land within a couple of
        # percent of one another, and their labels collided into unreadable mush;
        # the legend carries each one's own marker shape, so identity survives
        # without depending on colour alone.
        fig.add_trace(go.Scatter(
            x=[point["volatility"] * 100], y=[point["return"] * 100],
            mode="markers", name=label,
            marker=dict(size=size, color=color, symbol=symbol,
                        line=dict(width=2, color=SURFACE)),
            hovertemplate=(f"<b>{label}</b><br>Vol %{{x:.1f}}%  ·  Return %{{y:.1f}}%"
                           f"<br>Sharpe {point['sharpe']:.2f}<extra></extra>"),
        ))

    fig.update_layout(**plotly_layout(
        height=height, showlegend=True, hovermode="closest",
        xaxis=dict(showgrid=True, gridcolor=GRID, ticksuffix="%",
                   title=dict(text="Volatility" if lang == "en" else "Volatilité",
                              font=dict(size=11, color=INK_MUTED))),
        yaxis=dict(ticksuffix="%",
                   title=dict(text="Expected return" if lang == "en" else "Rendement attendu",
                              font=dict(size=11, color=INK_MUTED))),
        margin=dict(l=8, r=8, t=30, b=34),
    ))
    return fig


def allocation_change_bars(changes, height: int | None = None) -> go.Figure:
    """Weight moves between two allocations, largest first."""
    changes = list(changes)
    if not changes:
        return go.Figure()
    height = height or max(180, 32 * len(changes) + 40)
    deltas = [c["delta"] * 100 for c in changes]
    span = max(abs(d) for d in deltas) or 1

    fig = go.Figure(go.Bar(
        x=deltas, y=[c["ticker"] for c in changes], orientation="h",
        marker=_bar_marker([POS if d >= 0 else NEG for d in deltas]),
        text=[f"{c['before'] * 100:.0f}% → {c['after'] * 100:.0f}%" for c in changes],
        textposition="outside", textfont=dict(size=11, color=INK_2),
        hovertemplate="<b>%{y}</b>  %{x:+.1f}pp<extra></extra>",
        width=0.6,
    ))
    fig.update_layout(**plotly_layout(
        height=height, hovermode="closest",
        xaxis=dict(showgrid=True, gridcolor=GRID, zeroline=True,
                   zerolinecolor=AXIS, zerolinewidth=1, ticksuffix="pp",
                   range=[-span * 1.7, span * 1.7]),
        yaxis=dict(showgrid=False, type="category", autorange="reversed",
                   tickfont=dict(size=11, color=INK_2)),
        margin=dict(l=8, r=8, t=6, b=6),
    ))
    return fig


# =============================================================================
# MONTE CARLO
# =============================================================================

def fan_chart(result: dict, height: int = 420, currency: str = "$",
              lang: str = "en") -> go.Figure:
    """
    Percentile fan of simulated paths.

    Bands are drawn as nested fills of one hue at increasing opacity, so the
    encoding reads as a single probability gradient rather than as four unrelated
    categories. The median is the only line with real weight; the band edges stay
    recessive because the space between them is the message, not the edges.
    """
    percentiles = result.get("paths_percentiles") or {}
    if not percentiles:
        return go.Figure()

    horizon = len(next(iter(percentiles.values())))

    # A ten-year projection is ~2500 daily points per band. Sent whole, the filled
    # polygons alone push the figure past 400 KB of JSON for no visible gain —
    # the bands are smooth by construction. Subsample to a few hundred points,
    # always keeping the final day so the terminal values stay exact.
    max_points = 240
    if horizon > max_points:
        keep = np.unique(np.concatenate([
            np.linspace(0, horizon - 1, max_points).astype(int), [horizon - 1],
        ]))
        percentiles = {p: np.asarray(v)[keep] for p, v in percentiles.items()}
        x = keep / 252.0
    else:
        x = np.arange(horizon) / 252.0

    fig = go.Figure()
    band_label = "confidence band" if lang == "en" else "intervalle"

    # Outer band first so the inner one paints over it.
    for lower, upper, opacity in ((10, 90, 0.10), (25, 75, 0.20)):
        if lower not in percentiles or upper not in percentiles:
            continue
        fig.add_trace(go.Scatter(
            x=np.concatenate([x, x[::-1]]),
            y=np.concatenate([percentiles[upper], percentiles[lower][::-1]]),
            fill="toself", fillcolor=f"rgba(57,135,229,{opacity})",
            line=dict(width=0), hoverinfo="skip",
            name=f"{lower}–{upper}% {band_label}",
        ))

    for p, width, dash in ((10, 1, "dot"), (90, 1, "dot")):
        if p in percentiles:
            fig.add_trace(go.Scatter(
                x=x, y=percentiles[p], mode="lines", name=f"P{p}",
                line=dict(color="rgba(57,135,229,0.55)", width=width, dash=dash),
                hovertemplate=f"P{p}  {currency}%{{y:,.0f}}<extra></extra>",
            ))

    if 50 in percentiles:
        fig.add_trace(go.Scatter(
            x=x, y=percentiles[50], mode="lines",
            name="Median" if lang == "en" else "Médiane",
            line=dict(color=ACCENT, width=2.6),
            hovertemplate=f"Median  {currency}%{{y:,.0f}}<extra></extra>",
        ))

    initial = result.get("initial_value")
    if initial:
        fig.add_hline(y=initial, line=dict(color=INK_FAINT, width=1, dash="dash"))

    fig.update_layout(**plotly_layout(
        height=height, showlegend=True, hovermode="x unified",
        xaxis=dict(title=dict(text="Years" if lang == "en" else "Années",
                              font=dict(size=11, color=INK_MUTED)),
                   showspikes=True, spikecolor=BORDER_STRONG,
                   spikethickness=1, spikemode="across", spikedash="dot"),
        yaxis=dict(tickprefix=currency, tickformat=",.0f"),
        margin=dict(l=8, r=8, t=30, b=34),
    ))
    return fig


def terminal_distribution(result: dict, height: int = 240, currency: str = "$",
                          lang: str = "en") -> go.Figure:
    """
    Distribution of simulated terminal values, with the break-even point marked.

    Bars below the amount invested take the critical colour, which turns
    "probability of losing money" from a number into a visible region.
    """
    terminal = result.get("terminal")
    if terminal is None or len(terminal) == 0:
        return go.Figure()

    invested = result.get("invested") or result.get("initial_value") or 0
    # Trim the extreme right tail so the bulk of the distribution stays readable.
    upper = float(np.percentile(terminal, 99))
    clipped = terminal[terminal <= upper]

    counts, edges = np.histogram(clipped, bins=55)
    centers = (edges[:-1] + edges[1:]) / 2
    colors = [STATUS["critical"] if c < invested else ACCENT for c in centers]

    fig = go.Figure(go.Bar(
        x=centers, y=counts, marker=_bar_marker(colors),
        hovertemplate=f"{currency}%{{x:,.0f}}<br>%{{y}} paths<extra></extra>",
        width=(edges[1] - edges[0]) * 0.9,
    ))
    fig.add_vline(
        x=invested, line=dict(color=INK, width=1.5, dash="dash"),
        annotation_text=("invested" if lang == "en" else "investi"),
        annotation_position="top right",
        annotation_font=dict(size=10, color=INK_2),
    )
    fig.update_layout(**plotly_layout(
        height=height, hovermode="closest", bargap=0.04,
        xaxis=dict(tickprefix=currency, tickformat=",.0f", showgrid=False),
        yaxis=dict(title=None),
    ))
    return fig


def probability_bars(rows, height: int | None = None, currency: str = "$") -> go.Figure:
    """Probability of reaching each target — a simple, direct-labelled bar row."""
    rows = list(rows)
    if not rows:
        return go.Figure()
    height = height or max(160, 34 * len(rows) + 36)
    labels = [f"{currency}{r['target']:,.0f}" for r in rows]
    values = [r["probability"] * 100 for r in rows]

    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker=_bar_marker([
            STATUS["good"] if v >= 60 else STATUS["warning"] if v >= 30 else STATUS["critical"]
            for v in values
        ]),
        text=[f"{v:.0f}%" for v in values],
        textposition="outside", textfont=dict(size=11, color=INK_2),
        hovertemplate="<b>%{y}</b>  %{x:.1f}%<extra></extra>",
        width=0.6,
    ))
    fig.update_layout(**plotly_layout(
        height=height, hovermode="closest",
        xaxis=dict(showgrid=True, gridcolor=GRID, ticksuffix="%", range=[0, 118]),
        # Explicitly categorical. Currency labels like "$700,000" get coerced to a
        # numeric axis otherwise, which collapses every bar to a hairline and
        # reformats the labels as plain numbers.
        yaxis=dict(showgrid=False, type="category", autorange="reversed",
                   tickfont=dict(size=11, color=INK_2)),
        margin=dict(l=8, r=8, t=6, b=6),
    ))
    return fig
