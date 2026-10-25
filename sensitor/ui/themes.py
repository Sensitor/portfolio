"""
Design system for Sensitor Portfolio Intelligence.

Single source of truth for colour, spacing, typography and chart chrome.
Everything visual in the app should read its values from here — never hardcode a
hex in a page or component; a tint of a token is `fade(TOKEN, alpha)`.

The analytics app wears the platform's « Carnet de bord » direction (see
docs/DIRECTION_ARTISTIQUE.md): paper and sheet surfaces, ink text, the plan's
blue for actions and the portfolio, green and brick for gains and losses, ochre
for warnings, Newsreader titles and Schibsted Grotesk for the interface and
every figure. The navy sidebar is the binding, the one place with the grid.

Palette provenance
------------------
The categorical series palette is an 8-slot set in the direction's hues,
checked against the chart surface (#FFFDF8) with the data-viz validator
(validate_palette.js, light mode):

    Lightness band      PASS  all 8 inside L 0.43-0.77
    Chroma floor        PASS  all 8 >= 0.1
    CVD separation      PASS  worst adjacent dE 9.5 (deutan)
    Normal-vision floor PASS  worst adjacent dE 17.6
    Contrast vs surface PASS  all 8 >= 3:1

The first three slots also pass with every pair compared (scatter forms): worst
CVD dE 9.5, normal-vision dE 18.9. The sequential ramp passes the ordinal
checks (monotone, steps >= 0.06 L, light end >= 2:1).

Slots are assigned in fixed order and never cycled. Past 8 series, fold the tail
into "Other" rather than generating a 9th hue.
"""

import re
import streamlit as st

# =============================================================================
# TOKENS
# =============================================================================

# --- Surfaces (the platform's paper, sheet and margin) ----------------------
BG_DEEP = "#F3F0E8"        # page plane: paper
SURFACE = "#FFFDF8"        # card / chart surface: sheet (palette validated against this)
SURFACE_2 = "#EEE9DD"      # margin: table headers, hovered rows, notes
SURFACE_3 = "#FFFDF8"      # input backgrounds, chips

# --- Ink ---------------------------------------------------------------------
INK = "#0F1B26"            # primary text            15.3:1 on paper
INK_2 = "#33414D"          # secondary text           9.2:1
INK_MUTED = "#59636B"      # axis labels, captions    5.4:1
INK_FAINT = "#737B82"      # placeholders, hairline text

# --- Lines -------------------------------------------------------------------
BORDER = "#D8D2C3"
BORDER_STRONG = "#B7B0A0"
GRID = "rgba(15,27,38,0.07)"
AXIS = "#B7B0A0"

# --- Brand -------------------------------------------------------------------
ACCENT = "#1F4A72"         # the plan's blue: primary action, portfolio series
ACCENT_SOFT = "#E1E9F1"
ACCENT_GLOW = "rgba(31,74,114,0.18)"   # selection only: no halos

# --- Status (fixed roles, never reused as a series colour) -------------------
# Each always ships with an icon + label so hue never carries meaning alone.
GOOD = "#22604A"
WARNING = "#855615"
SERIOUS = "#9C5A1E"
CRITICAL = "#9A3A2C"

STATUS = {
    "good": GOOD,
    "warning": WARNING,
    "serious": SERIOUS,
    "critical": CRITICAL,
    "neutral": INK_2,
}

STATUS_ICON = {
    "good": "●",       # ●
    "warning": "▲",    # ▲
    "serious": "▲",
    "critical": "■",   # ■
    "neutral": "○",    # ○
}

# --- Directional (P&L) -------------------------------------------------------
POS = "#22604A"
NEG = "#9A3A2C"
FLAT = INK_MUTED
NEUTRAL = "#59636B"        # the grey of « not significant », « other », reference marks

# =============================================================================
# CATEGORICAL SERIES PALETTE — fixed order, never cycled
# =============================================================================

PALETTE = [
    "#2F6A9E",  # 1 ink blue
    "#B85C2B",  # 2 copper
    "#13A07A",  # 3 sea green
    "#B8861B",  # 4 ochre
    "#A8507A",  # 5 plum
    "#5E8B2C",  # 6 olive
    "#5A5AA8",  # 7 indigo
    "#C0473F",  # 8 brick red
]

# Scatter / bubble / small-multiple forms use the all-pairs-safe head of the list.
PALETTE_ALLPAIRS = PALETTE[:3]

# Sequential ramp (single hue, light -> dark) for magnitude encodings.
SEQ_BLUE = [
    "#96B4D1", "#7397BC", "#5A82AE", "#44709E",
    "#2F5B87", "#22476D", "#173553", "#0E253B",
]

# Diverging pair for correlation / polarity: brick <-> neutral <-> blue.
DIVERGING = [
    [0.0, "#9A3A2C"],
    [0.25, "#C98F84"],
    [0.5, "#EEE9DD"],   # neutral midpoint, the margin's paper, not a hue
    [0.75, "#7397BC"],
    [1.0, "#2F5B87"],
]

# =============================================================================
# GEOMETRY & TYPE
# =============================================================================

# Streamlit renamed the main content wrapper: recent builds emit
# `[data-testid="stMain"]` and no longer carry the `.main` class that older
# versions did. Selectors target both so the theme holds across versions.
# Wrapped in :is() so it stays a single compound selector — a bare comma-separated
# list would break the descendant combinator in `{MAIN} h1`.
MAIN = ':is([data-testid="stMain"], .main)'

RADIUS = "3px"
RADIUS_SM = "2px"
RADIUS_PILL = "2px"
FONT = "'Schibsted Grotesk', 'DM Sans', system-ui, -apple-system, 'Segoe UI', sans-serif"
TITLE = "'Newsreader', Georgia, 'Times New Roman', serif"
MONO = "'DM Mono', 'SF Mono', Menlo, monospace"
ISO = ("repeating-linear-gradient(30deg, rgba(169,198,226,.055) 0 1px, transparent 1px 34px),"
       "repeating-linear-gradient(150deg, rgba(169,198,226,.055) 0 1px, transparent 1px 34px),"
       "repeating-linear-gradient(90deg, rgba(169,198,226,.035) 0 1px, transparent 1px 58.9px)")


def fade(color: str, alpha: float) -> str:
    """A token at an opacity, as rgba(): the one way a page or chart tints a colour."""
    value = color.lstrip("#")
    r, g, b = (int(value[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


# Asset-class colours — stable identity across every chart in the app, so a class
# never changes colour when the filter changes the series count.
ASSET_CLASS_COLORS = {
    "Equity": PALETTE[0],
    "Stock": PALETTE[0],
    "ETF": PALETTE[0],
    "Bond": PALETTE[2],
    "Bonds": PALETTE[2],
    "Crypto": PALETTE[1],
    "Commodity": PALETTE[3],
    "Commodities": PALETTE[3],
    "Real Estate": PALETTE[4],
    "Cash": PALETTE[6],
    "Other": NEUTRAL,
    "Unknown": NEUTRAL,
}


def series_color(i: int) -> str:
    """Categorical slot i, folding past the 8th into muted 'Other' ink."""
    return PALETTE[i] if i < len(PALETTE) else INK_MUTED


def class_color(name: str) -> str:
    return ASSET_CLASS_COLORS.get(name, INK_MUTED)


def delta_color(value: float) -> str:
    if value is None:
        return FLAT
    return POS if value > 0 else (NEG if value < 0 else FLAT)


# =============================================================================
# HTML HELPER
# =============================================================================

_TAG_GAP = re.compile(r">\s+<")
_WS = re.compile(r"\s*\n\s*")


def html(markup: str) -> None:
    """
    Render raw HTML through Streamlit safely.

    Streamlit's markdown parser turns any line indented by 4+ spaces into a code
    block, which is what makes multi-line HTML blocks render as literal text.
    Collapsing inter-tag whitespace into a single line removes that whole class of
    bug, so components can be written readably and still render correctly.
    """
    compact = _TAG_GAP.sub("><", markup.strip())
    compact = _WS.sub(" ", compact)
    st.markdown(compact, unsafe_allow_html=True)


# =============================================================================
# PLOTLY THEME
# =============================================================================

def plotly_layout(height: int = 320, showlegend: bool = False, **overrides) -> dict:
    """Base layout every chart in the app starts from."""
    layout = dict(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, size=12, color=INK_2),
        margin=dict(l=8, r=8, t=8, b=8),
        showlegend=showlegend,
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="left", x=0,
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=11, color=INK_2),
        ),
        hoverlabel=dict(
            bgcolor=SURFACE_2,
            bordercolor=BORDER_STRONG,
            font=dict(family=FONT, size=12, color=INK),
            align="left",
        ),
        hovermode="x unified",
        modebar=dict(bgcolor=fade(BG_DEEP, 0.9), color=INK_FAINT, activecolor=ACCENT),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            linecolor=AXIS,
            tickfont=dict(size=11, color=INK_MUTED),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=GRID,
            gridwidth=1,
            zeroline=False,
            linecolor="rgba(0,0,0,0)",
            tickfont=dict(size=11, color=INK_MUTED),
        ),
    )
    for key, value in overrides.items():
        if key in layout and isinstance(layout[key], dict) and isinstance(value, dict):
            layout[key] = {**layout[key], **value}
        else:
            layout[key] = value
    return layout


PLOTLY_CONFIG = {
    "displayModeBar": False,
    "scrollZoom": False,
    "responsive": True,
}

PLOTLY_CONFIG_ZOOM = {
    # On hover (or tap) only: shown all the time it sat over the legend on a phone.
    "displayModeBar": "hover",
    "displaylogo": False,
    "modeBarButtonsToRemove": [
        "select2d", "lasso2d", "autoScale2d", "toggleSpikelines",
    ],
    "responsive": True,
}


# =============================================================================
# CSS THEME
# =============================================================================

def components_css() -> str:
    """
    The stylesheet of the analysis components alone: page and section headers,
    cards, metric cards, pills, alerts, the « Lecture » margin, the risk hatch,
    ledger tables and tooltips. No page plane, sidebar or widget rule: this is
    what the Sensitor platform injects to host the analysis pages inside its
    own shell (`inject_components`), and what `inject_theme` builds on.
    """
    return f"""
/* Figures: proportional. The tabular set of Schibsted widens the comma, which
   opens a gap in French decimals (« 12 ,5 »); columns align on the right. */
.snr-num {{ font-variant-numeric: normal; }}

/* ---------- Page header: a rubric, a direct title ---------- */
.snr-page-head {{ margin: 0 0 22px 0; padding-bottom: 14px; border-bottom: 1px solid {BORDER}; }}
.snr-eyebrow {{
  font-size: 0.72rem; font-weight: 600; letter-spacing: 0.08em;
  text-transform: uppercase; color: {INK_MUTED}; margin-bottom: 6px;
}}
.snr-title {{
  font-family: {TITLE}; font-size: 2.15rem; font-weight: 600; color: {INK};
  letter-spacing: -0.02em; line-height: 1.1;
}}
.snr-sub {{ font-size: 0.95rem; color: {INK_2}; margin-top: 8px; line-height: 1.55; max-width: 760px; }}

/* ---------- Section header: a hairline and a question ---------- */
.snr-section {{
  display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap;
  margin: 30px 0 14px 0; padding-top: 12px;
  border-top: 1px solid {BORDER_STRONG};
}}
.snr-section-t {{
  font-family: {TITLE}; font-size: 1.3rem; font-weight: 600; letter-spacing: -0.01em;
  text-transform: none; color: {INK};
}}
.snr-section-s {{ font-size: 0.86rem; color: {INK_MUTED}; }}

/* ---------- Cards: a sheet with its rule ---------- */
.snr-card {{
  height: 100%;
  box-sizing: border-box;
  background: {SURFACE};
  border: 1px solid {BORDER};
  border-top: 2px solid {INK};
  border-radius: 0;
  padding: 16px 18px;
  transition: border-color .18s ease;
}}
.snr-card:hover {{ border-color: {BORDER_STRONG}; border-top-color: {INK}; }}

/* ---------- Metric card ---------- */
.snr-metric {{ position: relative; overflow: hidden; }}
.snr-metric-label {{
  font-size: 0.8rem; font-weight: 500; letter-spacing: 0;
  text-transform: none; color: {INK_MUTED};
  display: flex; align-items: center; gap: 6px;
}}
.snr-metric-value {{
  font-size: 1.8rem; font-weight: 600; color: {INK};
  letter-spacing: -0.025em; line-height: 1.15; margin-top: 6px;
}}
.snr-metric-value.sm {{ font-size: 1.35rem; }}
.snr-metric-foot {{
  display: flex; align-items: center; justify-content: space-between;
  gap: 8px; margin-top: 10px; font-size: 0.8rem; color: {INK_MUTED};
  min-height: 30px;   /* reserved so cards in a row stay the same height */
}}
.snr-delta {{ font-weight: 600; }}

/* progress track */
.snr-track {{
  height: 4px; border-radius: 0; background: {fade(INK, 0.08)};
  margin-top: 11px; overflow: hidden;
}}
.snr-fill {{ height: 100%; border-radius: 0; transition: width .5s cubic-bezier(.22,1,.36,1); }}

/* segmented meter: one mark per step, like the platform's record */
.snr-meter {{ display: flex; gap: 2px; margin-top: 11px; }}
.snr-seg {{ flex: 1; height: 6px; border-radius: 0; background: {fade(INK, 0.08)}; }}

/* ---------- Pills & badges ---------- */
.snr-pill {{
  display: inline-flex; align-items: center; gap: 5px;
  padding: 3px 9px; border-radius: {RADIUS_PILL};
  font-size: 0.72rem; font-weight: 600; letter-spacing: 0.02em;
  white-space: nowrap;
}}

/* ---------- Alerts: a note in the margin ---------- */
.snr-alert {{
  display: flex; gap: 12px; align-items: flex-start;
  background: {SURFACE_2}; border: 0;
  border-left: 3px solid {BORDER_STRONG}; border-radius: 0;
  padding: 13px 15px; margin-bottom: 9px;
}}
.snr-alert-t {{ font-size: 0.9rem; font-weight: 600; color: {INK}; margin-bottom: 3px; }}
.snr-alert-b {{ font-size: 0.86rem; color: {INK_2}; line-height: 1.55; }}

/* ---------- Lecture: the margin beside a chart ---------- */
.snr-reading {{
  border-left: 2px solid {WARNING}; padding: 4px 0 4px 16px; margin: 6px 0 0 0;
}}
.snr-reading-l {{
  font-size: 0.72rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase;
  color: {WARNING}; margin-bottom: 10px;
}}
.snr-reading p {{
  font-family: {TITLE}; font-style: italic; font-size: 1.02rem; line-height: 1.5;
  color: {INK_2}; margin: 0 0 10px 0;
}}
.snr-reading-f {{ font-size: 0.74rem; color: {INK_MUTED}; line-height: 1.5; margin-top: 4px; }}

/* ---------- Risk zones: the 30° hatch ----------
   Patterns are used for risk zones only. Plotly draws its "-" pattern flat; the
   rotation turns it into the Carnet hatch. A browser that ignores a CSS transform
   on <pattern> keeps a horizontal hatch, which still reads as a zone. */
.js-plotly-plot pattern {{ transform: rotate(-30deg); }}

/* ---------- Data table: a ledger ---------- */
.snr-table {{ width: 100%; border-collapse: collapse; font-size: 0.86rem; border-top: 2px solid {INK}; }}
.snr-table th {{
  text-align: left; padding: 9px 12px 9px 0;
  font-size: 0.76rem; font-weight: 600; letter-spacing: 0.01em;
  text-transform: none; color: {INK_MUTED};
  border-bottom: 1px solid {BORDER_STRONG};
}}
.snr-table td {{
  padding: 10px 12px 10px 0; color: {INK_2};
  border-bottom: 1px solid {BORDER};
}}
.snr-table tr:hover td {{ background: {SURFACE_2}; }}
.snr-table td.k {{ color: {INK}; font-weight: 600; }}
.snr-table td.r {{ text-align: right; }}

/* ---------- Tooltip ---------- */
.snr-tip {{ position: relative; display: inline-flex; cursor: help; margin-left: 5px; }}
.snr-tip-i {{
  width: 13px; height: 13px; border-radius: 50%;
  border: 1px solid {INK_FAINT}; color: {INK_MUTED};
  font-size: 9px; font-weight: 600; line-height: 11px; text-align: center;
}}
.snr-tip-body {{
  visibility: hidden; opacity: 0; position: absolute; bottom: 130%; left: -8px;
  width: 244px; padding: 10px 12px; z-index: 99;
  background: {SURFACE}; border: 1px solid {BORDER_STRONG};
  border-radius: {RADIUS_SM}; box-shadow: 0 10px 28px -14px {fade(INK, 0.35)};
  font-size: 0.8rem; font-weight: 400; line-height: 1.55;
  color: {INK_2}; text-transform: none; letter-spacing: 0;
  transition: opacity .16s ease, visibility .16s ease;
}}
.snr-tip:hover .snr-tip-body {{ visibility: visible; opacity: 1; }}

"""


def inject_components() -> None:
    """Inject `components_css()` alone, for a host app that styles its own page and widgets."""
    st.markdown(f"<style>{components_css()}</style>", unsafe_allow_html=True)


def inject_theme() -> None:
    """Inject the full app stylesheet. Call once, early, in main()."""
    st.markdown(
        f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400;1,6..72,500&family=Schibsted+Grotesk:wght@400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

/* ---------- Base plane: paper, no halo ---------- */
.stApp {{ background: {BG_DEEP} !important; }}
html, body, [class*="css"] {{ font-family: {FONT} !important; }}

:is([data-testid="stMainBlockContainer"], .block-container) {{
  padding: 1.5rem 2rem 4rem 2rem !important;
  max-width: 1480px !important;
}}
@media (max-width: 900px) {{
  :is([data-testid="stMainBlockContainer"], .block-container) {{
    padding: 0.9rem 0.9rem 3rem 0.9rem !important;
  }}
}}
/* The chrome header is hidden but still reserves 60px of page height, which
   pushed every page down by a header's worth of empty space. */
[data-testid="stHeader"] {{ height: 0 !important; min-height: 0 !important; }}
[data-testid="stToolbar"], [data-testid="stDecoration"] {{ display: none !important; }}

{MAIN} h1, {MAIN} h2 {{
  color: {INK} !important; font-family: {TITLE} !important;
  letter-spacing: -0.015em !important; font-weight: 600 !important;
}}
{MAIN} h3 {{
  color: {INK} !important; font-family: {TITLE} !important;
  letter-spacing: -0.01em !important; font-weight: 600 !important;
}}
{MAIN} h4 {{
  color: {INK} !important; letter-spacing: -0.01em !important; font-weight: 600 !important;
}}
{MAIN} p, {MAIN} li, {MAIN} label {{ color: {INK_2} !important; }}

{components_css()}
/* ---------- Sidebar: the navy binding, the one place with the grid ---------- */
[data-testid="stSidebar"] {{
  background-color: {INK} !important; background-image: {ISO} !important;
  border-right: 1px solid #1d2c3b;
}}
[data-testid="stSidebar"] > div {{ background: transparent !important; }}
[data-testid="stSidebar"] * {{ color: #A9B7C4; }}
[data-testid="stSidebar"] :is(h1, h2, h3, h4, b, strong) {{ color: #E9EEF2 !important; }}
[data-testid="stSidebar"] .stButton > button {{
  background: transparent !important;
  border: 1px solid transparent !important;
  color: #E9EEF2 !important;
  border-radius: {RADIUS_SM} !important;
  font-weight: 500 !important; font-size: 0.86rem !important;
  text-align: left !important; justify-content: flex-start !important;
  padding: 7px 12px !important;
  transition: background .15s ease, color .15s ease;
}}
[data-testid="stSidebar"] .stButton > button * {{ color: inherit !important; }}
[data-testid="stSidebar"] .stButton > button:hover {{
  background: rgba(255,255,255,0.06) !important; color: #FFFFFF !important;
}}
[data-testid="stSidebar"] .stButton > button[kind="primary"] {{
  background: #223548 !important;
  border-color: transparent !important; box-shadow: inset 3px 0 #A9C6E2 !important;
  color: #FFFFFF !important; font-weight: 600 !important;
}}
[data-testid="stSidebar"] hr {{ border-color: rgba(255,255,255,0.10) !important; }}

/* ---------- Inputs ---------- */
/* Streamlit has migrated its inputs from BaseWeb to react-aria: the control is
   now `.react-aria-ComboBox > div[role="group"]`, which paints its own surface.
   Both generations are covered so the theme holds either way. */
:is([data-testid="stSelectbox"], [data-testid="stTextInput"],
    [data-testid="stNumberInput"], [data-testid="stDateInput"],
    [data-testid="stTimeInput"], [data-testid="stMultiSelect"]) div[role="group"],
/* The text input's inner wrapper carries no role, so the rule above misses it.
   A password input leaves a strip beside it for the reveal button, and that
   strip would keep Streamlit's own default. */
.react-aria-TextField > div {{
  background: {SURFACE_3} !important;
  border: 1px solid {BORDER_STRONG} !important;
  border-radius: {RADIUS_SM} !important;
}}
.react-aria-TextField > div > input {{ border: none !important; }}
.react-aria-TextField button {{ background: transparent !important; }}
.react-aria-TextField button :is(span, svg) {{
  color: {INK_MUTED} !important; fill: {INK_MUTED} !important;
}}
:is([data-testid="stSelectbox"], [data-testid="stTextInput"],
    [data-testid="stNumberInput"], [data-testid="stMultiSelect"])
    :is(input, button, span, div) {{
  color: {INK} !important;
}}
/* The chips a multiselect shows for chosen values. Streamlit's default paints
   them in its own red, which reads as an error state. */
[data-testid="stMultiSelectTagsContainer"] span[data-tag],
[data-testid="stMultiSelectTagsContainer"] [data-baseweb="tag"] {{
  background: {ACCENT_SOFT} !important;
  border: 1px solid {BORDER} !important;
  border-radius: {RADIUS_PILL} !important;
  color: {INK} !important;
}}
[data-testid="stMultiSelectTagsContainer"] span[data-tag] :is(span, svg) {{
  color: {INK} !important; fill: {INK_2} !important;
}}
/* The time input nests its segmented spinbuttons two levels below the group,
   and paints its surface on the wrapper rather than on the group. */
[data-testid="stTimeInput"] [data-testid="stTimeInputTimeDisplay"],
[data-testid="stTimeInput"] [data-testid="stTimeInputTimeDisplay"] > div {{
  background: {SURFACE_3} !important;
  border-color: {BORDER_STRONG} !important;
  border-radius: {RADIUS_SM} !important;
}}
[data-testid="stTimeInput"] :is(span[role="spinbutton"], span[data-type="literal"]) {{
  color: {INK} !important;
}}
[data-testid="stTimeInput"] span[role="spinbutton"]:focus {{
  background: {ACCENT_SOFT} !important; color: {INK} !important;
}}
[data-testid="stDateInput"] :is(input, span, div[role="spinbutton"]) {{
  color: {INK} !important;
}}
:is([data-testid="stSelectbox"], [data-testid="stTextInput"],
    [data-testid="stMultiSelect"]) input::placeholder {{
  color: {INK_FAINT} !important;
}}
[data-testid="stSelectbox"] svg,
[data-testid="stMultiSelect"] svg,
[data-testid="stNumberInput"] svg {{ fill: {INK_MUTED} !important; color: {INK_MUTED} !important; }}
[data-testid="stWidgetLabel"] p {{ color: {INK_MUTED} !important; font-weight: 500 !important; }}

/* Dropdown panels. Targeted by role as well as by class: this build emits no
   `.react-aria-Popover` class on the multiselect's panel, only an emotion hash. */
.react-aria-Popover, .react-aria-ListBox,
[role="listbox"], div:has(> [role="listbox"]) {{
  background: {SURFACE} !important;
  border-color: {BORDER_STRONG} !important;
  border-radius: {RADIUS_SM} !important;
  box-shadow: 0 12px 30px -16px {fade(INK, 0.35)} !important;
}}
[role="listbox"] {{ color: {INK_2} !important; }}
:is(.react-aria-ListBox, [role="listbox"]) [role="option"] {{
  color: {INK_2} !important; background: transparent !important;
}}
:is(.react-aria-ListBox, [role="listbox"]) [role="option"][data-focused],
:is(.react-aria-ListBox, [role="listbox"]) [role="option"]:hover {{
  background: {SURFACE_2} !important;
}}
:is(.react-aria-ListBox, [role="listbox"]) [role="option"][data-selected] {{
  background: {ACCENT_SOFT} !important; color: {INK} !important;
}}

div[data-baseweb="select"] > div,
div[data-baseweb="select"] div[role="button"],
.stTextInput input, .stNumberInput input {{
  background: {SURFACE_3} !important;
  border-color: {BORDER_STRONG} !important;
  border-radius: {RADIUS_SM} !important;
  color: {INK} !important;
}}
div[data-baseweb="select"] * {{ color: {INK} !important; }}
div[data-baseweb="select"] svg {{ fill: {INK_MUTED} !important; }}
div[data-baseweb="popover"] div[data-baseweb="menu"],
div[data-baseweb="popover"] ul {{
  background: {SURFACE} !important;
  border: 1px solid {BORDER_STRONG} !important;
  border-radius: {RADIUS_SM} !important;
}}
div[data-baseweb="popover"] li {{ background: transparent !important; color: {INK_2} !important; }}
div[data-baseweb="popover"] li:hover {{ background: {SURFACE_2} !important; }}
.stTextInput input:focus, .stNumberInput input:focus {{
  border-color: {ACCENT} !important;
  box-shadow: 0 0 0 2px {ACCENT_SOFT} !important;
}}

/* Inputs placed on the navy binding stay dark, so they read as part of it. */
[data-testid="stSidebar"] :is(div[role="group"], .react-aria-TextField > div,
    div[data-baseweb="select"] > div, div[data-baseweb="select"] div[role="button"]) {{
  background: #18293A !important; border-color: #2B3F52 !important;
}}
[data-testid="stSidebar"] :is([data-testid="stSelectbox"], [data-testid="stTextInput"],
    [data-testid="stNumberInput"], [data-testid="stMultiSelect"]) :is(input, button, span, div),
[data-testid="stSidebar"] div[data-baseweb="select"] * {{ color: #E9EEF2 !important; }}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {{ color: #A9B7C4 !important; }}

/* ---------- Sliders ---------- */
/* Streamlit's slider ships red, and red means « lost money » on every other
   surface in this app. The filled portion and the thumb take the accent. */
[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"],
[data-testid="stSlider"] div[role="slider"] {{
  background: {ACCENT} !important;
  border-color: {ACCENT} !important;
  box-shadow: 0 0 0 3px {ACCENT_SOFT} !important;
}}
/* The track is painted by the two inner divs of the BaseWeb slider: the first
   is the filled run, the second the remainder. There is no semantic hook here. */
[data-testid="stSlider"] [data-baseweb="slider"] > div > div:first-child {{
  background: {ACCENT} !important;
}}
[data-testid="stSlider"] [data-baseweb="slider"] > div > div:nth-child(2) {{
  background: {fade(INK, 0.14)} !important;
}}
[data-testid="stSlider"] [data-testid="stThumbValue"],
[data-testid="stSlider"] [data-testid="stTickBar"],
[data-testid="stSlider"] [data-testid="stTickBarMin"],
[data-testid="stSlider"] [data-testid="stTickBarMax"] {{
  color: {INK_MUTED} !important;
}}

/* ---------- Main buttons: flat ink, the plan's blue on hover ---------- */
/* A form's submit button is `kind="primaryFormSubmit"`, not `primary`, and so
   fell through to Streamlit's own red default. Styled alongside the ordinary
   primary button so the two cannot drift apart. */
{MAIN} .stFormSubmitButton > button[kind="primaryFormSubmit"],
{MAIN} .stButton > button[kind="primary"] {{
  background: {INK} !important;
  border: 1px solid {INK} !important; border-radius: {RADIUS_SM} !important;
  color: {BG_DEEP} !important;
  font-weight: 600 !important; letter-spacing: 0 !important;
  box-shadow: none !important;
  transition: background .15s ease, border-color .15s ease;
}}
{MAIN} :is(.stFormSubmitButton > button[kind="primaryFormSubmit"], .stButton > button[kind="primary"]) * {{
  color: {BG_DEEP} !important;
}}
{MAIN} .stFormSubmitButton > button[kind="primaryFormSubmit"]:hover,
{MAIN} .stButton > button[kind="primary"]:hover {{
  background: {ACCENT} !important; border-color: {ACCENT} !important;
}}
{MAIN} .stFormSubmitButton > button[kind="secondaryFormSubmit"],
{MAIN} .stButton > button[kind="secondary"] {{
  background: transparent !important;
  border: 1px solid {INK} !important;
  color: {INK} !important; border-radius: {RADIUS_SM} !important;
  font-weight: 500 !important;
}}
{MAIN} .stButton > button[kind="secondary"]:hover {{ background: {INK} !important; color: {BG_DEEP} !important; }}
{MAIN} .stButton > button[kind="secondary"]:hover * {{ color: {BG_DEEP} !important; }}

/* ---------- Tabs ---------- */
/* Both DOM generations are targeted. Streamlit moved tabs from BaseWeb to
   react-aria; the selectors carry the tab's testid so they outrank Streamlit's
   own selected-tab rule rather than racing it in the cascade. */
.stTabs :is([data-baseweb="tab-list"], [role="tablist"]) {{
  gap: 4px; border-bottom: 1px solid {BORDER};
  background: transparent !important; padding: 0 !important;
  border-radius: 0 !important;
}}
.stTabs :is([data-baseweb="tab"], [data-testid="stTab"]) {{
  background: none !important; background-color: transparent !important;
  border: none !important; box-shadow: none !important;
  color: {INK_MUTED} !important; font-size: 0.86rem !important;
  font-weight: 500 !important; letter-spacing: 0;
  padding: 9px 14px !important; border-radius: 0 !important;
}}
.stTabs :is([data-baseweb="tab"], [data-testid="stTab"])[aria-selected="true"] {{
  background: none !important; background-color: transparent !important;
  color: {INK} !important; font-weight: 600 !important;
  box-shadow: inset 0 -2px 0 0 {ACCENT} !important;
}}
.stTabs [data-testid="stTab"] :is(p, div, span) {{ color: inherit !important; }}
/* Streamlit's own selected-tab bar, which it paints in its default red. */
.stTabs .react-aria-SelectionIndicator {{ background: {ACCENT} !important; }}
::selection {{ background: {ACCENT_SOFT}; color: {INK}; }}

/* ---------- Checkboxes, toggles and the download button ---------- */
/* Streamlit paints a checked box and a download button in its own red default.
   Neither carries a `kind` attribute or a testid on the painted element, so
   they are reached by structure. */
[data-testid="stCheckbox"] div[class]:not([data-testid]),
[data-testid="stToggle"] div[class]:not([data-testid]) {{
  background-color: {ACCENT} !important;
  border-color: {ACCENT} !important;
}}
[data-testid="stCheckbox"] label {{ color: {INK_2} !important; }}
[data-testid="stCheckbox"] :is(p, span) {{ color: {INK_2} !important; }}

{MAIN} [data-testid="stDownloadButton"] > button {{
  background: transparent !important;
  border: 1px solid {INK} !important;
  color: {INK} !important;
  border-radius: {RADIUS_SM} !important;
  font-weight: 600 !important;
}}
{MAIN} [data-testid="stDownloadButton"] > button:hover {{
  background: {INK} !important; color: {BG_DEEP} !important;
}}
{MAIN} [data-testid="stDownloadButton"] :is(p, span, div) {{ color: inherit !important; }}

/* ---------- Expanders: a sheet ---------- */
[data-testid="stExpander"] details {{
  background: {SURFACE} !important;
  border: 1px solid {BORDER} !important;
  border-radius: 0 !important;
  overflow: hidden;
}}
[data-testid="stExpander"] summary {{
  background: {SURFACE} !important;
  color: {INK} !important;
  font-size: 0.88rem !important; font-weight: 600 !important;
}}
[data-testid="stExpander"] summary:hover {{ background: {SURFACE_2} !important; }}
[data-testid="stExpander"] summary :is(p, span, div) {{ color: {INK} !important; }}
[data-testid="stExpander"] details > div {{ background: transparent !important; }}

/* ---------- Radio chips (period selector): square, quiet ---------- */
div[role="radiogroup"] {{ gap: 4px !important; flex-wrap: wrap; }}
div[role="radiogroup"] label {{
  background: {SURFACE} !important; border: 1px solid {BORDER} !important;
  border-radius: {RADIUS_PILL} !important; padding: 4px 12px !important;
  margin: 0 !important; transition: all .15s ease;
}}
div[role="radiogroup"] label:hover {{ border-color: {BORDER_STRONG} !important; }}
div[role="radiogroup"] label > div > div:first-child {{ display: none !important; }}
div[role="radiogroup"] label p {{
  font-size: 0.8rem !important; font-weight: 500 !important; color: {INK_MUTED} !important;
}}
div[role="radiogroup"] label:has(input:checked) {{
  background: {ACCENT_SOFT} !important; border-color: {ACCENT} !important;
}}
div[role="radiogroup"] label:has(input:checked) p {{ color: {INK} !important; font-weight: 600 !important; }}
[data-testid="stSidebar"] div[role="radiogroup"] label {{ background: transparent !important; border-color: #2B3F52 !important; }}
[data-testid="stSidebar"] div[role="radiogroup"] label p {{ color: #A9B7C4 !important; }}
[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {{ background: #223548 !important; border-color: #A9C6E2 !important; }}
[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p {{ color: #FFFFFF !important; }}

/* ---------- Misc chrome ---------- */
hr {{ border-color: {BORDER} !important; }}
.streamlit-expanderHeader {{
  background: {SURFACE} !important; border: 1px solid {BORDER} !important;
  border-radius: 0 !important; color: {INK} !important;
}}
[data-testid="stMetricValue"] {{ color: {INK} !important; }}
[data-testid="stAlert"] {{ border-radius: 0 !important; }}
::-webkit-scrollbar {{ width: 9px; height: 9px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: {fade(INK, 0.18)}; border-radius: 0; }}
::-webkit-scrollbar-thumb:hover {{ background: {fade(INK, 0.32)}; }}

/* No horizontal overflow at any width. */
[data-testid="stMainBlockContainer"], .snr-card {{ max-width: 100%; overflow-x: auto; }}
</style>""",
        unsafe_allow_html=True,
    )


# =============================================================================
# LEGACY COMPONENTS
# =============================================================================

def inject_legacy() -> None:
    """
    The classes of the first-generation pages (Build, Workspace, Account), in the
    same direction. Only components: the widgets, the sidebar and the page are
    styled once, by `inject_theme`. Call before it.
    """
    st.markdown(
        f"""<style>
/* Health score: the page's one strong block. Navy, no glow, no grid. */
.score-card {{
  background: {INK}; border: 0; border-radius: 0;
  padding: 28px 32px; margin: 16px 0; position: relative; overflow: hidden;
}}
.score-card::before, .score-card::after {{ display: none; }}
.score-num {{ font-family: {TITLE}; font-size: 4.4rem; font-weight: 600; color: #F6F3EC; line-height: 1;
  letter-spacing: -0.03em; text-shadow: none; }}
.score-label {{ font-size: 0.74rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase;
  color: #A9C6E2; margin-bottom: 8px; }}
.score-badge {{ display: inline-block; background: transparent; border: 1px solid #3D5468; border-radius: {RADIUS_PILL};
  padding: 4px 12px; font-size: 0.76rem; font-weight: 600; letter-spacing: 0.04em; color: #E9EEF2; margin-top: 10px; }}
.bar-bg {{ background: rgba(255,255,255,0.14); border-radius: 0; height: 5px; overflow: hidden; margin-top: 5px; }}
.bar-fill {{ height: 100%; border-radius: 0; background: #A9C6E2; transition: width 0.7s ease-out; }}

/* Figures and cards: a sheet with its rule. */
.metric-card, .kpi-card, .asset-card, .model-card {{
  background: {SURFACE}; border: 1px solid {BORDER}; border-top: 2px solid {INK}; border-radius: 0;
  padding: 18px 22px; margin: 6px 0; transition: border-color .2s ease;
}}
.metric-card:hover, .kpi-card:hover, .asset-card:hover, .model-card:hover {{
  border-color: {BORDER_STRONG}; border-top-color: {INK}; transform: none; box-shadow: none; background: {SURFACE};
}}
.kpi-card::before {{ display: none; }}
.asset-card :is(p, span, div) {{ color: {INK_2} !important; }}
.metric-label, .kpi-label {{ font-size: 0.8rem; font-weight: 500; letter-spacing: 0; text-transform: none;
  color: {INK_MUTED}; margin-bottom: 6px; }}
.metric-value, .kpi-value {{ font-size: 1.9rem; font-weight: 600; color: {INK}; line-height: 1.05;
  letter-spacing: -0.025em; margin-bottom: 6px; }}
.kpi-icon {{ display: none; }}
.kpi-sub {{ font-size: 0.8rem; color: {INK_MUTED}; line-height: 1.45; }}
.kpi-positive {{ color: {POS}; }} .kpi-negative {{ color: {NEG}; }}
.kpi-neutral {{ color: {ACCENT}; }} .kpi-warning {{ color: {WARNING}; }}

/* Recommendations: notes in the margin, the rule says the status. */
.rec-card {{
  background: {SURFACE_2}; border: 0; border-left: 3px solid {ACCENT}; border-radius: 0;
  padding: 14px 18px; margin: 10px 0; transition: background .2s ease;
}}
.rec-card:hover {{ background: {SURFACE_2}; transform: none; box-shadow: none; }}
.rec-card h4 {{ color: {INK} !important; margin: 0 0 6px 0; font-size: 0.95rem; font-weight: 600; }}
.rec-card p {{ color: {INK_2} !important; margin: 4px 0; line-height: 1.6; font-size: 0.88rem; }}
.rec-card.critical {{ border-left-color: {CRITICAL} !important; }}
.rec-card.warning {{ border-left-color: {WARNING} !important; }}
.rec-card.success {{ border-left-color: {GOOD} !important; }}
.rec-card.info {{ border-left-color: {ACCENT} !important; }}

/* Badges: square, quiet. */
.asset-class-badge, .risk-badge {{ display: inline-block; padding: 3px 9px; border-radius: {RADIUS_PILL};
  font-size: 0.72rem; font-weight: 600; letter-spacing: 0.02em; text-transform: none; }}

/* Bars */
.progress-bar-bg {{ background: {fade(INK, 0.08)}; border-radius: 0; height: 6px; overflow: hidden; margin-top: 4px; }}
.progress-bar-fill {{ height: 100%; border-radius: 0; transition: width 0.6s ease-out; }}
.stProgress > div > div {{ background: {ACCENT} !important; }}

/* Offers and locked features: a note, not a banner. */
.upgrade-card, .paywall-block {{
  background: {SURFACE_2}; border: 0; border-left: 3px solid {WARNING}; border-radius: 0;
  padding: 22px 26px; text-align: left; margin: 16px 0;
}}
.upgrade-card h3 {{ color: {INK} !important; margin: 0 0 8px 0; }}
.upgrade-card p {{ color: {INK_2} !important; font-size: 0.92rem; }}

/* Section headers: a hairline and a title, no icon tile. */
.section-header {{ display: flex; align-items: baseline; gap: 12px; margin: 30px 0 16px; padding-top: 12px;
  border-top: 1px solid {BORDER_STRONG}; }}
.section-icon {{ display: none; }}
.section-title {{ font-family: {TITLE}; font-size: 1.3rem; font-weight: 600; color: {INK}; }}
.section-sub {{ font-size: 0.86rem; color: {INK_MUTED}; margin-top: 2px; }}

.tooltip-hint {{ background: {SURFACE_2}; border: 0; border-left: 3px solid {BORDER_STRONG}; border-radius: 0;
  padding: 10px 14px; font-size: 0.86rem; color: {INK_2}; line-height: 1.55; }}
.tooltip-hint strong {{ color: {ACCENT}; }}
.ft-divider {{ height: 1px; background: {BORDER}; margin: 26px 0; border: none; }}

[data-testid="stMetricValue"] {{ font-size: 1.9rem !important; font-weight: 600 !important; color: {INK} !important; }}
[data-testid="stMetricLabel"] {{ font-size: 0.8rem !important; color: {INK_MUTED} !important; font-weight: 500 !important;
  text-transform: none !important; letter-spacing: 0 !important; }}
#MainMenu, footer, header {{ visibility: hidden; }}
</style>""",
        unsafe_allow_html=True,
    )
