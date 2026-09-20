"""
Design system for Sensitor Portfolio Intelligence.

Single source of truth for colour, spacing, typography and chart chrome.
Everything visual in the app should read its values from here — never hardcode a
hex in a page or component.

Palette provenance
------------------
The categorical series palette is the validated 8-slot dark set, checked against
this app's own chart surface (#0E1522) with the data-viz validator:

    Lightness band      PASS  all 8 inside L 0.48-0.67
    Chroma floor        PASS  all 8 >= 0.1
    CVD separation      PASS  worst adjacent dE 8.4 (protan)
    Normal-vision floor PASS  worst adjacent dE 19.3
    Contrast vs surface PASS  all 8 >= 3:1

Slots are assigned in fixed order and never cycled. Past 8 series, fold the tail
into "Other" rather than generating a 9th hue.
"""

import re
import streamlit as st

# =============================================================================
# TOKENS
# =============================================================================

# --- Surfaces (deep fintech dark) -------------------------------------------
BG_DEEP = "#070B14"        # page plane
SURFACE = "#0E1522"        # card / chart surface  (palette validated against this)
SURFACE_2 = "#141C2B"      # raised surface, table headers, hovered rows
SURFACE_3 = "#1B2435"      # input backgrounds, chips

# --- Ink ---------------------------------------------------------------------
INK = "#EDF2F9"            # primary text
INK_2 = "#9AA8BF"          # secondary text
INK_MUTED = "#6B7A93"      # axis labels, captions
INK_FAINT = "#465065"      # disabled, hairline text

# --- Lines -------------------------------------------------------------------
BORDER = "rgba(154,168,191,0.14)"
BORDER_STRONG = "rgba(154,168,191,0.26)"
GRID = "rgba(154,168,191,0.08)"
AXIS = "rgba(154,168,191,0.20)"

# --- Brand -------------------------------------------------------------------
ACCENT = "#3987E5"         # Sensitor blue — primary action, portfolio series
ACCENT_SOFT = "rgba(57,135,229,0.14)"
ACCENT_GLOW = "rgba(57,135,229,0.30)"

# --- Status (fixed roles, never reused as a series colour) -------------------
# Each always ships with an icon + label so hue never carries meaning alone.
GOOD = "#16B979"
WARNING = "#E8A317"
SERIOUS = "#E8894A"
CRITICAL = "#E2504F"

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
POS = "#16B979"
NEG = "#E2504F"
FLAT = INK_MUTED

# =============================================================================
# CATEGORICAL SERIES PALETTE — fixed order, never cycled
# =============================================================================

PALETTE = [
    "#3987E5",  # 1 blue
    "#D95926",  # 2 orange
    "#199E70",  # 3 aqua
    "#C98500",  # 4 yellow
    "#D55181",  # 5 magenta
    "#008300",  # 6 green
    "#9085E9",  # 7 violet
    "#E66767",  # 8 red
]

# Scatter / bubble / small-multiple forms use the all-pairs-safe head of the list.
PALETTE_ALLPAIRS = PALETTE[:3]

# Sequential ramp (single hue, light -> dark) for magnitude encodings.
SEQ_BLUE = [
    "#CDE2FB", "#9EC5F4", "#6DA7EC", "#3987E5",
    "#256ABF", "#1C5CAB", "#184F95", "#104281",
]

# Diverging pair for correlation / polarity: red <-> neutral <-> blue.
DIVERGING = [
    [0.0, "#E2504F"],
    [0.25, "#C97F7E"],
    [0.5, "#2A3444"],   # neutral midpoint — not a hue
    [0.75, "#4E7FBE"],
    [1.0, "#3987E5"],
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

RADIUS = "14px"
RADIUS_SM = "9px"
RADIUS_PILL = "999px"
FONT = "'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif"
MONO = "'JetBrains Mono', 'SF Mono', Menlo, monospace"

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
    "Other": INK_MUTED,
    "Unknown": INK_MUTED,
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
    "displayModeBar": True,
    "displaylogo": False,
    "modeBarButtonsToRemove": [
        "select2d", "lasso2d", "autoScale2d", "toggleSpikelines",
    ],
    "responsive": True,
}


# =============================================================================
# CSS THEME
# =============================================================================

def inject_theme() -> None:
    """Inject the full app stylesheet. Call once, early, in main()."""
    st.markdown(
        f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* ---------- Base plane ---------- */
.stApp {{
  background:
    radial-gradient(1200px 700px at 12% -8%, rgba(57,135,229,0.10), transparent 60%),
    radial-gradient(900px 600px at 100% 0%, rgba(144,133,233,0.07), transparent 55%),
    {BG_DEEP} !important;
}}
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

{MAIN} h1, {MAIN} h2, {MAIN} h3, {MAIN} h4 {{
  color: {INK} !important;
  letter-spacing: -0.025em !important;
  font-weight: 700 !important;
}}
{MAIN} p, {MAIN} li, {MAIN} label {{ color: {INK_2} !important; }}

/* Numbers align in columns; headline figures stay proportional. */
.snr-num {{ font-variant-numeric: tabular-nums; }}

/* ---------- Page header ---------- */
.snr-page-head {{ margin: 0 0 22px 0; }}
.snr-eyebrow {{
  font-size: 0.68rem; font-weight: 700; letter-spacing: 0.16em;
  text-transform: uppercase; color: {ACCENT}; margin-bottom: 6px;
}}
.snr-title {{
  font-size: 1.85rem; font-weight: 800; color: {INK};
  letter-spacing: -0.035em; line-height: 1.1;
}}
.snr-sub {{ font-size: 0.9rem; color: {INK_MUTED}; margin-top: 6px; }}

/* ---------- Section header ---------- */
.snr-section {{
  display: flex; align-items: baseline; gap: 10px;
  margin: 30px 0 14px 0; padding-bottom: 10px;
  border-bottom: 1px solid {BORDER};
}}
.snr-section-t {{
  font-size: 0.78rem; font-weight: 700; letter-spacing: 0.14em;
  text-transform: uppercase; color: {INK};
}}
.snr-section-s {{ font-size: 0.8rem; color: {INK_MUTED}; }}

/* ---------- Cards ---------- */
.snr-card {{
  height: 100%;
  box-sizing: border-box;
  background: linear-gradient(180deg, rgba(255,255,255,0.028), rgba(255,255,255,0.008)), {SURFACE};
  border: 1px solid {BORDER};
  border-radius: {RADIUS};
  padding: 16px 18px;
  transition: border-color .18s ease, transform .18s ease, box-shadow .18s ease;
}}
.snr-card:hover {{
  border-color: {BORDER_STRONG};
  transform: translateY(-1px);
  box-shadow: 0 10px 30px -14px rgba(0,0,0,0.75);
}}

/* ---------- Metric card ---------- */
.snr-metric {{ position: relative; overflow: hidden; }}
.snr-metric-label {{
  font-size: 0.66rem; font-weight: 700; letter-spacing: 0.13em;
  text-transform: uppercase; color: {INK_MUTED};
  display: flex; align-items: center; gap: 6px;
}}
.snr-metric-value {{
  font-size: 1.85rem; font-weight: 800; color: {INK};
  letter-spacing: -0.035em; line-height: 1.15; margin-top: 8px;
}}
.snr-metric-value.sm {{ font-size: 1.35rem; }}
.snr-metric-foot {{
  display: flex; align-items: center; justify-content: space-between;
  gap: 8px; margin-top: 10px; font-size: 0.74rem; color: {INK_MUTED};
  min-height: 30px;   /* reserved so cards in a row stay the same height */
}}
.snr-delta {{ font-weight: 700; font-variant-numeric: tabular-nums; }}

/* progress track */
.snr-track {{
  height: 5px; border-radius: 3px; background: rgba(154,168,191,0.13);
  margin-top: 11px; overflow: hidden;
}}
.snr-fill {{ height: 100%; border-radius: 3px; transition: width .5s cubic-bezier(.22,1,.36,1); }}

/* segmented meter — the "██████░░░░" idea, done properly */
.snr-meter {{ display: flex; gap: 2px; margin-top: 11px; }}
.snr-seg {{ flex: 1; height: 6px; border-radius: 1.5px; background: rgba(154,168,191,0.13); }}

/* ---------- Pills & badges ---------- */
.snr-pill {{
  display: inline-flex; align-items: center; gap: 5px;
  padding: 3px 10px; border-radius: {RADIUS_PILL};
  font-size: 0.68rem; font-weight: 700; letter-spacing: 0.05em;
  white-space: nowrap;
}}

/* ---------- Alerts ---------- */
.snr-alert {{
  display: flex; gap: 12px; align-items: flex-start;
  background: {SURFACE}; border: 1px solid {BORDER};
  border-left-width: 3px; border-radius: {RADIUS_SM};
  padding: 13px 15px; margin-bottom: 9px;
}}
.snr-alert-t {{ font-size: 0.86rem; font-weight: 700; color: {INK}; margin-bottom: 3px; }}
.snr-alert-b {{ font-size: 0.8rem; color: {INK_2}; line-height: 1.55; }}

/* ---------- Data table ---------- */
.snr-table {{ width: 100%; border-collapse: collapse; font-size: 0.82rem; }}
.snr-table th {{
  text-align: left; padding: 9px 12px;
  font-size: 0.64rem; font-weight: 700; letter-spacing: 0.11em;
  text-transform: uppercase; color: {INK_MUTED};
  border-bottom: 1px solid {BORDER};
}}
.snr-table td {{
  padding: 10px 12px; color: {INK_2};
  border-bottom: 1px solid rgba(154,168,191,0.06);
  font-variant-numeric: tabular-nums;
}}
.snr-table tr:hover td {{ background: rgba(154,168,191,0.04); }}
.snr-table td.k {{ color: {INK}; font-weight: 600; }}
.snr-table td.r {{ text-align: right; }}

/* ---------- Tooltip ---------- */
.snr-tip {{ position: relative; display: inline-flex; cursor: help; margin-left: 5px; }}
.snr-tip-i {{
  width: 13px; height: 13px; border-radius: 50%;
  border: 1px solid {INK_FAINT}; color: {INK_MUTED};
  font-size: 9px; font-weight: 700; line-height: 11px; text-align: center;
}}
.snr-tip-body {{
  visibility: hidden; opacity: 0; position: absolute; bottom: 130%; left: -8px;
  width: 244px; padding: 10px 12px; z-index: 99;
  background: {SURFACE_2}; border: 1px solid {BORDER_STRONG};
  border-radius: {RADIUS_SM}; box-shadow: 0 14px 38px -12px rgba(0,0,0,0.85);
  font-size: 0.74rem; font-weight: 400; line-height: 1.55;
  color: {INK_2}; text-transform: none; letter-spacing: 0;
  transition: opacity .16s ease, visibility .16s ease;
}}
.snr-tip:hover .snr-tip-body {{ visibility: visible; opacity: 1; }}

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {{
  background: linear-gradient(180deg, #0A101C 0%, {BG_DEEP} 100%) !important;
  border-right: 1px solid {BORDER};
}}
[data-testid="stSidebar"] * {{ color: {INK_2}; }}
[data-testid="stSidebar"] .stButton > button {{
  background: transparent !important;
  border: 1px solid transparent !important;
  color: {INK_2} !important;
  border-radius: {RADIUS_SM} !important;
  font-weight: 500 !important; font-size: 0.84rem !important;
  text-align: left !important; justify-content: flex-start !important;
  padding: 7px 12px !important;
  transition: background .15s ease, color .15s ease;
}}
[data-testid="stSidebar"] .stButton > button:hover {{
  background: rgba(154,168,191,0.07) !important; color: {INK} !important;
}}
[data-testid="stSidebar"] .stButton > button[kind="primary"] {{
  background: {ACCENT_SOFT} !important;
  border-color: rgba(57,135,229,0.30) !important;
  color: {INK} !important; font-weight: 600 !important;
}}

/* ---------- Inputs ---------- */
/* Streamlit has migrated its inputs from BaseWeb to react-aria: the control is
   now `.react-aria-ComboBox > div[role="group"]`, which paints its own light
   surface. Both generations are covered so the theme holds either way. */
:is([data-testid="stSelectbox"], [data-testid="stTextInput"],
    [data-testid="stNumberInput"], [data-testid="stDateInput"],
    [data-testid="stTimeInput"], [data-testid="stMultiSelect"]) div[role="group"] {{
  background: {SURFACE_3} !important;
  border: 1px solid {BORDER} !important;
  border-radius: {RADIUS_SM} !important;
}}
:is([data-testid="stSelectbox"], [data-testid="stTextInput"],
    [data-testid="stNumberInput"], [data-testid="stMultiSelect"])
    :is(input, button, span, div) {{
  color: {INK} !important;
}}
/* The chips a multiselect shows for chosen values. Streamlit's default paints
   them in its own red, which on this palette reads as an error state — three
   instruments chosen in a filter looked like three validation failures. The
   chip is `span[data-tag]`, two levels inside the tags container. */
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
   and paints a light surface on the wrapper rather than on the group. Without
   this it is the one white control on a dark form — which is exactly how it
   looked until the journal form was opened in a browser. */
[data-testid="stTimeInput"] [data-testid="stTimeInputTimeDisplay"],
[data-testid="stTimeInput"] [data-testid="stTimeInputTimeDisplay"] > div {{
  background: {SURFACE_3} !important;
  border-color: {BORDER} !important;
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
[data-testid="stWidgetLabel"] p {{ color: {INK_MUTED} !important; }}

/* Dropdown panels. Targeted by role as well as by class: this build emits no
   `.react-aria-Popover` class on the multiselect's panel, only an emotion hash,
   so a class-only rule left it white — visible as a white "No results" box
   hanging under a dark filter panel. The `:has()` rule catches the panel that
   wraps the list, which is what actually paints the surface. */
.react-aria-Popover, .react-aria-ListBox,
[role="listbox"], div:has(> [role="listbox"]) {{
  background: {SURFACE_2} !important;
  border-color: {BORDER} !important;
  border-radius: {RADIUS_SM} !important;
  box-shadow: 0 16px 40px -14px rgba(0,0,0,0.85) !important;
}}
[role="listbox"] {{ color: {INK_2} !important; }}
:is(.react-aria-ListBox, [role="listbox"]) [role="option"] {{
  color: {INK_2} !important; background: transparent !important;
}}
:is(.react-aria-ListBox, [role="listbox"]) [role="option"][data-focused],
:is(.react-aria-ListBox, [role="listbox"]) [role="option"]:hover {{
  background: rgba(154,168,191,0.10) !important;
}}
:is(.react-aria-ListBox, [role="listbox"]) [role="option"][data-selected] {{
  background: {ACCENT_SOFT} !important; color: {INK} !important;
}}

div[data-baseweb="select"] > div,
div[data-baseweb="select"] div[role="button"],
.stTextInput input, .stNumberInput input {{
  background: {SURFACE_3} !important;
  border-color: {BORDER} !important;
  border-radius: {RADIUS_SM} !important;
  color: {INK} !important;
}}
div[data-baseweb="select"] * {{ color: {INK} !important; }}
div[data-baseweb="select"] svg {{ fill: {INK_MUTED} !important; }}
div[data-baseweb="popover"] div[data-baseweb="menu"],
div[data-baseweb="popover"] ul {{
  background: {SURFACE_2} !important;
  border: 1px solid {BORDER} !important;
  border-radius: {RADIUS_SM} !important;
}}
div[data-baseweb="popover"] li {{ background: transparent !important; color: {INK_2} !important; }}
div[data-baseweb="popover"] li:hover {{ background: rgba(154,168,191,0.08) !important; }}
.stTextInput input:focus, .stNumberInput input:focus {{
  border-color: {ACCENT} !important;
  box-shadow: 0 0 0 3px {ACCENT_SOFT} !important;
}}

/* ---------- Main buttons ---------- */
/* A form's submit button is `kind="primaryFormSubmit"`, not `primary`, and so
   fell through to Streamlit's own red default — a scarlet "Save trade" in the
   middle of a blue product. Styled alongside the ordinary primary button so the
   two cannot drift apart. */
{MAIN} .stFormSubmitButton > button[kind="primaryFormSubmit"] {{
  background: linear-gradient(135deg, {ACCENT}, #2A6FC4) !important;
  border: none !important; border-radius: {RADIUS_SM} !important;
  color: #FFFFFF !important;
  font-weight: 600 !important; letter-spacing: -0.01em !important;
  box-shadow: 0 6px 20px -8px {ACCENT_GLOW} !important;
  transition: transform .15s ease, box-shadow .15s ease;
}}
{MAIN} .stFormSubmitButton > button[kind="primaryFormSubmit"]:hover {{
  transform: translateY(-1px);
  box-shadow: 0 10px 26px -8px {ACCENT_GLOW} !important;
}}
{MAIN} .stFormSubmitButton > button[kind="secondaryFormSubmit"] {{
  background: {SURFACE_3} !important;
  border: 1px solid {BORDER} !important;
  color: {INK_2} !important; border-radius: {RADIUS_SM} !important;
  font-weight: 500 !important;
}}
{MAIN} .stButton > button[kind="primary"] {{
  background: linear-gradient(135deg, {ACCENT}, #2A6FC4) !important;
  border: none !important; border-radius: {RADIUS_SM} !important;
  font-weight: 600 !important; letter-spacing: -0.01em !important;
  box-shadow: 0 6px 20px -8px {ACCENT_GLOW} !important;
  transition: transform .15s ease, box-shadow .15s ease;
}}
{MAIN} .stButton > button[kind="primary"]:hover {{
  transform: translateY(-1px);
  box-shadow: 0 10px 26px -8px {ACCENT_GLOW} !important;
}}
{MAIN} .stButton > button[kind="secondary"] {{
  background: {SURFACE_3} !important;
  border: 1px solid {BORDER} !important;
  color: {INK_2} !important; border-radius: {RADIUS_SM} !important;
  font-weight: 500 !important;
}}

/* ---------- Tabs ---------- */
.stTabs [data-baseweb="tab-list"] {{
  gap: 4px; border-bottom: 1px solid {BORDER};
  background: transparent; padding-bottom: 0;
}}
.stTabs [data-baseweb="tab"] {{
  background: transparent !important; border: none !important;
  color: {INK_MUTED} !important; font-size: 0.8rem !important;
  font-weight: 600 !important; letter-spacing: 0.02em;
  padding: 9px 14px !important; border-radius: 0 !important;
}}
.stTabs [aria-selected="true"] {{
  color: {INK} !important;
  box-shadow: inset 0 -2px 0 0 {ACCENT} !important;
}}
/* Streamlit's own selected-tab bar, which it paints in its default red. The
   tab underneath already carries an accent underline, so left alone the two
   stack into a red line over a blue one. Predates the trading pages; fixed
   here because it is two lines and it is visibly wrong. */
.stTabs .react-aria-SelectionIndicator {{ background: {ACCENT} !important; }}
::selection {{ background: {ACCENT_GLOW}; color: {INK}; }}

/* ---------- Expanders ---------- */
/* Untouched, an open expander paints a white header and body — the journal's
   trade form and the trading filter panel both live in one, so a light slab
   opened in the middle of a dark page. Styled as a card so an expander reads
   like the rest of the surface rather than like a different application. */
[data-testid="stExpander"] details {{
  background: {SURFACE} !important;
  border: 1px solid {BORDER} !important;
  border-radius: {RADIUS_SM} !important;
  overflow: hidden;
}}
[data-testid="stExpander"] summary {{
  background: {SURFACE_3} !important;
  color: {INK_2} !important;
  font-size: 0.83rem !important; font-weight: 600 !important;
}}
[data-testid="stExpander"] summary:hover {{ background: {SURFACE_2} !important; }}
[data-testid="stExpander"] summary :is(p, span, div) {{ color: {INK_2} !important; }}
[data-testid="stExpander"] details > div {{ background: transparent !important; }}

/* ---------- Radio pills (period selector) ---------- */
div[role="radiogroup"] {{ gap: 4px !important; flex-wrap: wrap; }}
div[role="radiogroup"] label {{
  background: {SURFACE_3} !important; border: 1px solid {BORDER} !important;
  border-radius: {RADIUS_PILL} !important; padding: 4px 13px !important;
  margin: 0 !important; transition: all .15s ease;
}}
div[role="radiogroup"] label:hover {{ border-color: {BORDER_STRONG} !important; }}
div[role="radiogroup"] label > div > div:first-child {{ display: none !important; }}
div[role="radiogroup"] label p {{
  font-size: 0.75rem !important; font-weight: 600 !important; color: {INK_MUTED} !important;
}}
div[role="radiogroup"] label:has(input:checked) {{
  background: {ACCENT_SOFT} !important; border-color: rgba(57,135,229,0.45) !important;
}}
div[role="radiogroup"] label:has(input:checked) p {{ color: {INK} !important; }}

/* ---------- Misc chrome ---------- */
hr {{ border-color: {BORDER} !important; }}
.streamlit-expanderHeader {{
  background: {SURFACE} !important; border: 1px solid {BORDER} !important;
  border-radius: {RADIUS_SM} !important; color: {INK_2} !important;
}}
[data-testid="stMetricValue"] {{ color: {INK} !important; }}
::-webkit-scrollbar {{ width: 9px; height: 9px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: rgba(154,168,191,0.18); border-radius: 5px; }}
::-webkit-scrollbar-thumb:hover {{ background: rgba(154,168,191,0.30); }}

/* No horizontal overflow at any width. */
[data-testid="stMainBlockContainer"], .snr-card {{ max-width: 100%; overflow-x: auto; }}
</style>""",
        unsafe_allow_html=True,
    )
