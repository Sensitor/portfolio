"""
Design tokens and the stylesheet for the Academy app.

Editorial rather than dashboard: ivory paper for reading, ink-navy for the
sidebar and the few emphatic surfaces, one restrained blue, green and red kept
for right / wrong feedback. Playfair Display for headings, DM Sans for text,
DM Mono for labels and figures.

Every colour Streamlit would otherwise take from its theme is set explicitly,
so the app looks the same whether the visitor's system is in light or dark mode.
Muted text colours were chosen to keep at least 4.5:1 contrast on their surface.
"""

from __future__ import annotations

import streamlit as st

TOKENS = {
    "ink": "#14202b",
    "ink-2": "#1c2a37",
    "text": "#26323c",
    "muted": "#59636a",
    "paper": "#f4f2ec",
    "paper-2": "#ebe8df",
    "card": "#fbfaf6",
    "white": "#fffefa",
    "line": "#e0dcd1",
    "line-strong": "#c9c4b7",
    "blue": "#284764",
    "blue-2": "#3b5a74",
    "blue-soft": "#e2e8ed",
    "green": "#355b48",
    "green-soft": "#e3ece5",
    "red": "#8a4038",
    "red-soft": "#f3e4df",
    "gold": "#7d6337",
    "gold-soft": "#efe6d4",
    "side": "#101a24",
    "side-2": "#172431",
    "side-text": "#d3dbe2",
    "side-muted": "#8e9cab",
    "side-accent": "#9db8d2",
}

FONTS = ("https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500"
         "&family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700"
         "&family=Playfair+Display:wght@500;600&display=swap")

_VARS = "".join(f"--{k}:{v};" for k, v in TOKENS.items())

CSS = f"""
@import url('{FONTS}');
:root {{ {_VARS}
  --serif: 'Playfair Display', Georgia, 'Times New Roman', serif;
  --sans: 'DM Sans', -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif;
  --mono: 'DM Mono', 'SFMono-Regular', Consolas, monospace;
}}

/* ── Canvas ─────────────────────────────────────────────────────────────── */
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
  background: var(--paper) !important; color: var(--text);
  font-family: var(--sans);
}}
[data-testid="stHeader"] {{ background: transparent !important; }}
[data-testid="stDecoration"], [data-testid="stAppDeployButton"],
[data-testid="stMainMenu"], [data-testid="stStatusWidget"] {{ display: none !important; }}
[data-testid="stHeaderActionElements"] {{ display: none !important; }}
[data-testid="stMainBlockContainer"] {{
  max-width: 1160px; padding: 2.4rem 2.6rem 4.5rem;
}}
.stApp [data-testid="stVerticalBlock"] {{ gap: 0.9rem; }}
/* Streamlit pulls every Markdown block up by 1rem; the custom fragments are laid
   out with their own margins, so they opt out. */
.stApp [data-testid="stMarkdownContainer"]:has(> [class*="ac-"]),
.stApp [data-testid="stMarkdownContainer"]:has(> figure),
.stApp [data-testid="stMarkdownContainer"]:has(> table) {{ margin-bottom: 0 !important; }}

/* ── Type ───────────────────────────────────────────────────────────────── */
.stApp [data-testid="stMarkdownContainer"] {{ color: var(--text); }}
.stApp [data-testid="stMarkdownContainer"] p,
.stApp [data-testid="stMarkdownContainer"] li {{
  color: var(--text); font-size: 15.5px; line-height: 1.75;
}}
.stApp [data-testid="stMarkdownContainer"] strong {{ color: var(--ink); font-weight: 650; }}
.stApp [data-testid="stMarkdownContainer"] h1:not([class]),
.stApp [data-testid="stMarkdownContainer"] h2:not([class]),
.stApp [data-testid="stMarkdownContainer"] h3:not([class]) {{
  font-family: var(--serif); color: var(--ink); font-weight: 500;
  letter-spacing: -0.012em; padding: 0;
}}
.stApp [data-testid="stMarkdownContainer"] h2:not([class]) {{ font-size: 1.62rem; margin: 1.6rem 0 .4rem; }}
.stApp [data-testid="stMarkdownContainer"] h3:not([class]) {{ font-size: 1.25rem; margin: 1.2rem 0 .3rem; }}
.stApp [data-testid="stMarkdownContainer"] code {{
  font-family: var(--mono); font-size: .86em; color: var(--blue);
  background: var(--blue-soft); padding: .1em .35em; border-radius: 3px;
}}
.stApp [data-testid="stMarkdownContainer"] table {{
  border-collapse: collapse; width: 100%; margin: .6rem 0 1rem; font-size: 14px;
  background: var(--card); border: 1px solid var(--line);
}}
.stApp [data-testid="stMarkdownContainer"] th {{
  font: 500 10.5px var(--mono); letter-spacing: .08em; text-transform: uppercase;
  color: var(--muted); text-align: left; padding: 10px 12px;
  border-bottom: 1px solid var(--line-strong); background: var(--paper);
}}
.stApp [data-testid="stMarkdownContainer"] td {{
  padding: 10px 12px; border-bottom: 1px solid var(--line); color: var(--text);
  font-variant-numeric: tabular-nums; vertical-align: top; line-height: 1.55;
}}
.stApp .katex {{ color: var(--ink); font-size: 1.12em; }}
.stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stCaptionContainer"] p {{
  color: var(--muted) !important; font-size: 13px;
}}

/* ── Sidebar ────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {{ background: var(--side) !important; border-right: 1px solid #1e2b38; }}
[data-testid="stSidebar"] > div {{ background: var(--side) !important; }}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span {{ color: var(--side-text); }}
[data-testid="stSidebarHeader"] {{ padding-bottom: 0; }}
[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] button,
[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] svg {{ color: var(--side-muted) !important; }}
[data-testid="stExpandSidebarButton"], [data-testid="stExpandSidebarButton"] svg {{
  color: var(--ink) !important;
}}
[data-testid="stSidebar"] .stButton > button {{
  width: 100%; justify-content: flex-start; background: transparent; border: 0;
  border-radius: 6px; padding: .58rem .8rem; min-height: 0; color: var(--side-text);
  font-weight: 500; font-size: 14px; box-shadow: none;
}}
[data-testid="stSidebar"] .stButton > button * {{ color: inherit !important; }}
[data-testid="stSidebar"] .stButton > button > div {{ justify-content: flex-start; width: 100%; }}
[data-testid="stSidebar"] .stButton > button p {{ text-align: left; }}
[data-testid="stSidebar"] .stButton > button:hover {{ background: #ffffff0f; color: #fff; }}
[data-testid="stSidebar"] .stButton > button:focus-visible {{ outline: 2px solid var(--side-accent); }}
[data-testid="stSidebar"] .stButton > button[kind="primary"],
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {{
  background: var(--side-2) !important; color: #fff !important;
  box-shadow: inset 2px 0 var(--side-accent);
}}
[data-testid="stSidebar"] .stButton {{ margin: 0; }}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{ gap: .15rem; }}

/* ── Buttons ────────────────────────────────────────────────────────────── */
.stApp [data-testid="stMain"] .stButton > button,
.stApp [data-testid="stMain"] .stDownloadButton > button,
.stApp [data-testid="stMain"] [data-testid="stFormSubmitButton"] > button {{
  border-radius: 4px; border: 1px solid var(--line-strong); background: var(--white);
  color: var(--ink); font-weight: 600; font-size: 13.5px; padding: .55rem 1.05rem;
  box-shadow: none; min-height: 2.5rem; transition: border-color .15s, background .15s;
}}
.stApp [data-testid="stMain"] .stButton > button *,
.stApp [data-testid="stMain"] .stDownloadButton > button *,
.stApp [data-testid="stMain"] [data-testid="stFormSubmitButton"] > button * {{
  color: inherit !important; font-weight: inherit; font-size: inherit;
}}
.stApp [data-testid="stMain"] .stButton > button:hover,
.stApp [data-testid="stMain"] .stDownloadButton > button:hover {{
  border-color: var(--ink); background: var(--white); color: var(--ink);
}}
.stApp [data-testid="stMain"] button[data-testid="stBaseButton-primary"],
.stApp [data-testid="stMain"] button[data-testid="stBaseButton-primaryFormSubmit"] {{
  background: var(--ink) !important; border-color: var(--ink) !important; color: var(--paper) !important;
}}
.stApp [data-testid="stMain"] button[data-testid="stBaseButton-primary"]:hover,
.stApp [data-testid="stMain"] button[data-testid="stBaseButton-primaryFormSubmit"]:hover {{
  background: var(--ink-2) !important;
}}
.stApp [data-testid="stMain"] button[data-testid="stBaseButton-tertiary"] {{
  border: 0 !important; background: transparent !important; padding: .2rem 0 !important;
  min-height: 0; color: var(--blue) !important; text-decoration: underline;
  text-underline-offset: 4px; text-decoration-color: var(--line-strong);
}}
.stApp [data-testid="stMain"] button:disabled {{ opacity: .45; }}
.stApp button:focus-visible {{ outline: 2px solid var(--blue-2) !important; outline-offset: 2px; }}

/* Row buttons: a lesson list, a path list */
.stApp [class*="st-key-row_"] .stButton > button {{
  width: 100%; justify-content: flex-start; text-align: left; background: transparent;
  border: 0; border-bottom: 1px solid var(--line); border-radius: 0; padding: .85rem .3rem;
  font-weight: 500; font-size: 15px; min-height: 0;
}}
.stApp [class*="st-key-row_"] .stButton > button:hover {{ background: var(--card); border-color: var(--line); }}
.stApp [class*="st-key-row_"] .stButton > button > div,
.stApp [class*="st-key-rowcurrent_"] .stButton > button > div {{ justify-content: flex-start; width: 100%; }}
.stApp [class*="st-key-row_"] .stButton > button p,
.stApp [class*="st-key-rowcurrent_"] .stButton > button p {{ text-align: left; }}
.stApp [class*="st-key-rowcurrent_"] .stButton > button {{
  width: 100%; justify-content: flex-start; background: var(--blue-soft) !important; border: 0 !important;
  border-radius: 4px; padding: .7rem .6rem; font-size: 14px; color: var(--ink); font-weight: 600;
}}

/* ── Inputs ─────────────────────────────────────────────────────────────── */
.stApp [data-testid="stWidgetLabel"] p, .stApp [data-testid="stWidgetLabel"] label {{
  color: var(--ink) !important; font-size: 13.5px; font-weight: 600;
}}
.stApp [data-baseweb="input"], .stApp [data-baseweb="base-input"],
.stApp [data-baseweb="select"] > div, .stApp [data-baseweb="textarea"] {{
  background: var(--white) !important; border-color: var(--line-strong) !important;
  border-radius: 4px !important;
}}
.stApp input, .stApp textarea, .stApp [data-baseweb="select"] * {{
  color: var(--ink) !important; -webkit-text-fill-color: var(--ink);
  font-family: var(--sans); font-variant-numeric: tabular-nums;
}}
.stApp input::placeholder {{ color: var(--muted) !important; -webkit-text-fill-color: var(--muted); }}
.stApp [data-testid="stNumberInputContainer"] button {{
  background: var(--paper-2) !important; color: var(--ink) !important; border: 0 !important;
}}
.stApp [data-testid="stNumberInputContainer"] button svg {{ fill: var(--ink) !important; }}
.stApp [data-testid="InputInstructions"] {{ color: var(--muted) !important; }}
[data-baseweb="popover"] li, [data-baseweb="popover"] ul {{ background: var(--white) !important; color: var(--ink) !important; }}

/* Choices — Streamlit 1.64 markup: label[data-testid=stRadioOption] and
   stCheckbox > label, each with a visually hidden input and a drawn box. */
.stApp [data-testid="stRadio"], .stApp [data-testid="stRadio"] > div,
.stApp [data-testid="stRadio"] [role="radiogroup"], .stApp [data-testid="stCheckbox"] {{ width: 100%; }}
.stApp [data-testid="stRadio"] [role="radiogroup"] {{ gap: .5rem; }}
.stApp [data-testid="stRadioOption"],
.stApp [data-testid="stCheckbox"] > label {{
  background: var(--white); border: 1px solid var(--line); border-radius: 6px;
  padding: .75rem .95rem; margin: 0; width: 100%; align-items: flex-start;
  transition: border-color .15s, background .15s;
}}
.stApp [data-testid="stRadioOption"]:hover,
.stApp [data-testid="stCheckbox"] > label:hover {{ border-color: var(--blue-2); }}
.stApp [data-testid="stRadioOption"][data-selected="true"],
.stApp [data-testid="stCheckbox"] > label:has(input:checked) {{
  border-color: var(--blue-2); background: var(--blue-soft);
}}
.stApp [data-testid="stRadioOption"] p, .stApp [data-testid="stCheckbox"] label p {{
  color: var(--text) !important; font-size: 14.5px; line-height: 1.5; font-weight: 400 !important;
}}
.stApp [data-testid="stRadioOption"] > div > div:first-child {{
  background: var(--white) !important; box-shadow: inset 0 0 0 1.5px var(--blue-2) !important;
  margin-top: 3px;
}}
.stApp [data-testid="stRadioOption"][data-selected="true"] > div > div:first-child {{
  background: var(--blue-2) !important;
}}
.stApp [data-testid="stRadioOption"][data-selected="true"] > div > div:first-child > div {{
  background: var(--white) !important;
}}
.stApp [data-testid="stCheckbox"] > label > div:first-of-type {{
  border-color: var(--blue-2) !important; background-color: var(--white) !important; margin-top: 3px;
}}
.stApp [data-testid="stCheckbox"] > label:has(input:checked) > div:first-of-type {{
  background-color: var(--blue-2) !important;
}}
.stApp [class*="st-key-inline_"] [data-testid="stRadioOption"] {{ width: auto; padding: .5rem .85rem; }}
.stApp [class*="st-key-inline_"] [data-testid="stRadio"] [role="radiogroup"] {{ width: auto; }}
.stApp [data-testid="stRadioOption"]:has(input:disabled),
.stApp [data-testid="stCheckbox"] > label:has(input:disabled) {{ opacity: .78; cursor: default; }}
.stApp [data-testid="stNumberInputContainer"] {{
  background: var(--white) !important; border: 1px solid var(--line-strong) !important; border-radius: 4px;
}}
.stApp [data-testid="stNumberInputContainer"] input {{ background: transparent !important; }}

/* Expanders, tabs, forms */
.stApp [data-testid="stExpander"] details {{
  border: 1px solid var(--line) !important; border-radius: 6px; background: var(--card);
}}
.stApp [data-testid="stExpander"] summary, .stApp [data-testid="stExpander"] summary * {{
  color: var(--ink) !important; font-weight: 600;
}}
.stApp [data-testid="stExpander"] summary:hover {{ color: var(--blue) !important; }}
.stApp [data-baseweb="tab-list"] {{ gap: 1.4rem; border-bottom: 1px solid var(--line); }}
.stApp [data-baseweb="tab"] {{ background: transparent !important; padding: .6rem 0; }}
.stApp [data-baseweb="tab"] p {{ color: var(--muted) !important; font-weight: 600; font-size: 14px; }}
.stApp [data-baseweb="tab"][aria-selected="true"] p {{ color: var(--ink) !important; }}
.stApp [data-baseweb="tab-highlight"] {{ background: var(--ink) !important; }}
.stApp [data-baseweb="tab-border"] {{ display: none; }}
.stApp [data-testid="stForm"] {{
  border: 1px solid var(--line); background: var(--card); border-radius: 8px; padding: 1.4rem 1.5rem;
}}
.stApp [data-testid="stAlert"] {{ border-radius: 6px; }}
.stApp [data-testid="stAlertContentWarning"] p, .stApp [data-testid="stAlertContentError"] p,
.stApp [data-testid="stAlertContentInfo"] p, .stApp [data-testid="stAlertContentSuccess"] p {{
  color: var(--ink) !important;
}}
.stApp hr {{ border-color: var(--line); }}
.stApp [data-testid="stToast"] {{ background: var(--ink) !important; }}
.stApp [data-testid="stToast"] * {{ color: var(--paper) !important; }}

/* ── Callouts (keyed containers) ───────────────────────────────────────── */
.stApp [class*="st-key-callout_"] {{
  border-left: 2px solid var(--blue-2); background: #e9ece9; padding: 1rem 1.3rem .35rem;
  border-radius: 0 6px 6px 0; margin: .4rem 0 .6rem; gap: .2rem;
}}
.stApp [class*="st-key-callout_definition"] {{ background: var(--card); border-left-color: var(--ink); border: 1px solid var(--line); border-left: 2px solid var(--ink); }}
.stApp [class*="st-key-callout_example"] {{ background: var(--gold-soft); border-left-color: var(--gold); }}
.stApp [class*="st-key-callout_warning"] {{ background: var(--red-soft); border-left-color: var(--red); }}
.stApp [class*="st-key-callout_mistake"] {{ background: var(--red-soft); border-left-color: var(--red); }}
.stApp [class*="st-key-callout_recap"] {{ background: var(--ink); border-left-color: var(--side-accent); }}
.stApp [class*="st-key-callout_recap"] p, .stApp [class*="st-key-callout_recap"] li,
.stApp [class*="st-key-callout_recap"] strong {{ color: #e6ebef !important; }}
.stApp [class*="st-key-callout_recap"] .ac-callout-title {{ color: var(--side-accent); }}
.stApp [class*="st-key-callout_method"] {{ background: var(--blue-soft); border-left-color: var(--blue); }}
.stApp [class*="st-key-callout_"] p, .stApp [class*="st-key-callout_"] li {{ font-size: 15px; }}

/* Exercise solutions */
.stApp [class*="st-key-solution_"] {{
  border-left: 2px solid var(--line-strong); background: var(--paper-2); padding: .75rem 1.1rem .1rem;
  border-radius: 0 6px 6px 0; gap: .1rem; margin-bottom: .4rem;
}}
.stApp [class*="st-key-solution_correct"] {{ background: var(--green-soft); border-left-color: var(--green); }}
.stApp [class*="st-key-solution_correct"] .ac-callout-title {{ color: var(--green); }}
.stApp [class*="st-key-solution_incorrect"] {{ background: var(--red-soft); border-left-color: var(--red); }}
.stApp [class*="st-key-solution_incorrect"] .ac-callout-title {{ color: var(--red); }}
.stApp [class*="st-key-solution_"] p {{ font-size: 14.5px; }}

/* Question blocks and panels */
.stApp [class*="st-key-panel_"] {{
  background: var(--card); border: 1px solid var(--line); border-radius: 8px; padding: 1.3rem 1.4rem 1.1rem;
}}
.stApp [class*="st-key-dark_"] {{
  background: var(--ink); border-radius: 10px; padding: 2.2rem 2.3rem 2rem;
}}
.stApp [class*="st-key-dark_"] p {{ color: #c4ccd3 !important; }}
.stApp [class*="st-key-dark_"] .stButton > button[data-testid="stBaseButton-primary"] {{
  background: var(--paper) !important; color: var(--ink) !important; border-color: var(--paper) !important;
}}
.stApp [class*="st-key-dark_"] .stButton > button[data-testid="stBaseButton-secondary"] {{
  background: transparent !important; color: var(--paper) !important; border-color: #4a5966 !important;
}}

/* ── Custom HTML ───────────────────────────────────────────────────────── */
.stApp .ac-eyebrow {{
  font: 500 11px var(--mono); letter-spacing: .16em; text-transform: uppercase; color: var(--muted);
}}
.stApp .ac-eyebrow b {{ color: var(--blue); font-weight: 500; }}
.stApp .ac-h1 {{
  padding: 0 !important; font: 500 2.6rem/1.12 var(--serif); color: var(--ink); letter-spacing: -0.022em; margin: .45rem 0 .6rem;
}}
.stApp .ac-h2 {{ padding: 0 !important; font: 500 1.6rem/1.2 var(--serif); color: var(--ink); letter-spacing: -0.015em; margin: 0; }}
.stApp .ac-h3 {{ padding: 0 !important; font: 500 1.2rem/1.3 var(--serif); color: var(--ink); margin: 0 0 .25rem; }}
.stApp .ac-lead {{ font-size: 17px; line-height: 1.7; color: var(--muted); max-width: 680px; margin: 0; }}
.stApp .ac-sub {{ font-size: 14px; color: var(--muted); margin: .25rem 0 0; line-height: 1.6; }}
.stApp .ac-meta {{ display: flex; flex-wrap: wrap; gap: .4rem 1.4rem; margin-top: 1rem;
  font: 400 12px var(--mono); color: var(--muted); letter-spacing: .04em; }}
.stApp .ac-meta span b {{ color: var(--ink); font-weight: 500; }}
.stApp .ac-section {{ display: flex; justify-content: space-between; align-items: flex-end; gap: 1rem;
  border-bottom: 1px solid var(--line); padding-bottom: .7rem; margin: 2.2rem 0 .3rem; }}
.stApp .ac-rule {{ border: 0; border-top: 1px solid var(--line); margin: 1.6rem 0; }}
.stApp .ac-tag {{ display: inline-block; font: 500 10px var(--mono); letter-spacing: .1em; text-transform: uppercase;
  padding: 3px 7px; border-radius: 3px; border: 1px solid var(--line-strong); color: var(--muted);
  vertical-align: middle; white-space: nowrap; }}
.stApp .ac-tag.open {{ color: var(--green); border-color: #b8cbbd; background: var(--green-soft); }}
.stApp .ac-tag.member {{ color: var(--blue); border-color: #c3d0db; background: var(--blue-soft); }}
.stApp .ac-tag.done {{ color: var(--green); border-color: #b8cbbd; }}
.stApp .ac-tag.soon {{ color: var(--gold); border-color: #ddcfb4; background: var(--gold-soft); }}
.stApp .ac-progress {{ height: 3px; background: var(--line); border-radius: 3px; overflow: hidden; }}
.stApp .ac-progress > i {{ display: block; height: 100%; background: var(--blue-2); }}
.stApp .ac-progress-row {{ display: flex; align-items: center; gap: .8rem; font: 12px var(--mono); color: var(--muted); }}
.stApp .ac-progress-row .ac-progress {{ flex: 1; }}
.stApp .ac-stats {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line); }}
.stApp .ac-stat {{ padding: 1.1rem 1.2rem 1rem 0; }}
.stApp .ac-stat + .ac-stat {{ border-left: 1px solid var(--line); padding-left: 1.2rem; }}
.stApp .ac-stat .label {{ font: 500 10.5px var(--mono); letter-spacing: .12em; text-transform: uppercase; color: var(--muted); }}
.stApp .ac-stat .value {{ font: 500 1.75rem var(--serif); color: var(--ink); margin-top: .35rem; font-variant-numeric: tabular-nums; }}
.stApp .ac-stat .value small {{ font: 400 .9rem var(--sans); color: var(--muted); }}
.stApp .ac-stat .detail {{ font-size: 12.5px; color: var(--muted); margin-top: .15rem; }}
.stApp .ac-figures {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 0;
  border: 1px solid var(--line); background: var(--card); border-radius: 8px; overflow: hidden; }}
.stApp .ac-figure-cell {{ padding: 1rem 1.1rem; border-right: 1px solid var(--line); border-bottom: 1px solid var(--line); margin: 0 -1px -1px 0; }}
.stApp .ac-figure-cell .label {{ font: 500 10.5px var(--mono); letter-spacing: .1em; text-transform: uppercase; color: var(--muted); }}
.stApp .ac-figure-cell .value {{ font: 500 1.35rem var(--mono); color: var(--ink); margin-top: .35rem; letter-spacing: -.02em;
  font-variant-numeric: tabular-nums; white-space: nowrap; }}
.stApp .ac-figure-cell .detail {{ font-size: 12.5px; color: var(--muted); margin-top: .2rem; }}
.stApp .ac-figure-cell.emph {{ background: var(--ink); }}
.stApp .ac-figure-cell.emph .label {{ color: var(--side-muted); }}
.stApp .ac-figure-cell.emph .value {{ color: #fff; }}
.stApp .ac-figure-cell.emph .detail {{ color: #c4ccd3; }}
.stApp .ac-diagram {{ margin: .6rem 0 1rem; background: var(--card); border: 1px solid var(--line);
  border-radius: 8px; padding: 1.1rem 1.2rem .8rem; }}
.stApp .ac-diagram svg {{ width: 100%; height: auto; display: block; max-height: 340px; }}
.stApp .ac-diagram figcaption {{ font-size: 13px; color: var(--muted); line-height: 1.55; margin-top: .7rem;
  border-top: 1px solid var(--line); padding-top: .6rem; }}
.stApp .ac-callout-title {{ font: 500 10.5px var(--mono); letter-spacing: .14em; text-transform: uppercase; color: var(--blue); margin-bottom: .1rem; }}
.stApp .ac-objectives {{ border: 1px solid var(--line); background: var(--card); border-radius: 8px; padding: 1rem 1.3rem; margin: 1.3rem 0 .4rem; }}
.stApp .ac-objectives ul {{ margin: .45rem 0 0; padding-left: 1.1rem; }}
.stApp .ac-objectives li {{ color: var(--text); font-size: 14.5px; line-height: 1.65; }}
.stApp .ac-list {{ list-style: none; padding: 0; margin: 0; }}
.stApp .ac-list li {{ display: grid; grid-template-columns: 2.4rem 1fr auto; gap: .8rem; align-items: baseline;
  padding: .85rem 0; border-bottom: 1px solid var(--line); }}
.stApp .ac-list li .n {{ font: 12px var(--mono); color: var(--muted); }}
.stApp .ac-list li .t {{ color: var(--ink); font-size: 15px; }}
.stApp .ac-list li .t small {{ display: block; color: var(--muted); font-size: 13px; margin-top: .15rem; line-height: 1.5; }}
.stApp .ac-list li.muted .t {{ color: var(--muted); }}
.stApp .ac-note {{ font-size: 13px; color: var(--muted); line-height: 1.6; border-left: 2px solid var(--line-strong); padding-left: .9rem; }}
.stApp .ac-feedback {{ border-radius: 6px; padding: .9rem 1.1rem; margin-top: .2rem; font-size: 14px; line-height: 1.6; }}
.stApp .ac-feedback.correct {{ background: var(--green-soft); border: 1px solid #c3d4c7; }}
.stApp .ac-feedback.incorrect {{ background: var(--red-soft); border: 1px solid #e3c9c2; }}
.stApp .ac-feedback.unanswered {{ background: var(--paper-2); border: 1px solid var(--line); }}
.stApp .ac-feedback .status {{ font: 500 11px var(--mono); letter-spacing: .12em; text-transform: uppercase; }}
.stApp .ac-feedback.correct .status {{ color: var(--green); }}
.stApp .ac-feedback.incorrect .status {{ color: var(--red); }}
.stApp .ac-feedback.unanswered .status {{ color: var(--muted); }}
.stApp .ac-feedback ul {{ margin: .5rem 0 0; padding: 0; list-style: none; }}
.stApp .ac-feedback li {{ margin: .45rem 0; color: var(--text); padding-left: 1.4rem; position: relative; }}
.stApp .ac-feedback li .mark {{ position: absolute; left: 0; font-weight: 700; }}
.stApp .ac-feedback li.ok .mark {{ color: var(--green); }}
.stApp .ac-feedback li.ko .mark {{ color: var(--red); }}
.stApp .ac-feedback li b {{ color: var(--ink); font-weight: 600; }}
.stApp .ac-feedback li span.why {{ display: block; color: var(--muted); font-size: 13.5px; }}
.stApp .ac-question {{ font: 500 1.08rem/1.5 var(--sans); color: var(--ink); margin: .2rem 0 .1rem; }}
.stApp .ac-score {{ display: flex; align-items: baseline; gap: 1rem; flex-wrap: wrap; }}
.stApp .ac-score .big {{ font: 500 2.6rem var(--serif); color: var(--ink); font-variant-numeric: tabular-nums; }}
.stApp .ac-locked {{ border: 1px dashed var(--line-strong); border-radius: 8px; padding: 1.6rem 1.5rem; background: var(--card); }}
.stApp .ac-hero-kicker {{ font: 500 11px var(--mono); letter-spacing: .16em; text-transform: uppercase; color: var(--side-accent); }}
.stApp .ac-hero-title {{ padding: 0 !important; font: 500 clamp(2.1rem, 4vw, 3.1rem)/1.1 var(--serif); color: #f4f2ec; letter-spacing: -0.022em; margin: 1rem 0 .9rem; }}
.stApp .ac-hero-title em {{ font-style: normal; color: var(--side-accent); }}
.stApp .ac-hero-text {{ font-size: 15.5px; line-height: 1.75; color: #b9c3cb; max-width: 520px; }}
.stApp .ac-hero-art svg {{ width: 100%; height: auto; display: block; }}
.stApp .ac-brand {{ display: flex; align-items: center; gap: .75rem; padding: .2rem .5rem 1.1rem; }}
.stApp .ac-brand-name {{ font: 700 15px var(--sans); letter-spacing: .2em; color: #f2f4f6; }}
.stApp .ac-brand-sub {{ font: 500 9.5px var(--mono); letter-spacing: .22em; color: var(--side-muted); margin-top: 2px; }}
.stApp .ac-side-label {{ font: 500 10px var(--mono); letter-spacing: .16em; color: var(--side-muted); padding: .9rem .8rem .35rem; }}
.stApp .ac-side-user {{ border-top: 1px solid #ffffff14; margin-top: 1.4rem; padding: 1rem .8rem 0; font-size: 12.5px; color: var(--side-muted); line-height: 1.5; }}
.stApp .ac-side-user b {{ display: block; color: var(--side-text); font-weight: 600; font-size: 13px; word-break: break-all; }}
.stApp .ac-side-foot {{ font-size: 11.5px; color: var(--side-muted); line-height: 1.55; padding: 1rem .8rem 0; }}
.stApp .ac-footer {{ border-top: 1px solid var(--line); margin-top: 3rem; padding-top: 1rem; display: flex; flex-wrap: wrap;
  justify-content: space-between; gap: .6rem 1.4rem; font: 11px var(--mono); color: var(--muted); letter-spacing: .04em; }}
.stApp .ac-cols {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0; }}
.stApp .ac-col {{ padding: 1.3rem 1.4rem 1.2rem 0; }}
.stApp .ac-col + .ac-col {{ border-left: 1px solid var(--line); padding-left: 1.4rem; }}
.stApp .ac-col .num {{ font: 12px var(--mono); color: var(--muted); }}
.stApp .ac-col h4 {{ font: 500 1.15rem var(--serif); color: var(--ink); margin: .6rem 0 .4rem; padding: 0; }}
.stApp .ac-col p {{ font-size: 14px; color: var(--muted); line-height: 1.65; margin: 0; }}
.stApp .ac-resource-cover {{ width: 46px; height: 60px; background: var(--ink); color: #dfe5e8; display: grid; place-items: center;
  font: 500 18px var(--serif); box-shadow: 3px 3px 0 var(--line-strong); flex-shrink: 0; }}
.stApp .ac-resource {{ display: flex; gap: 1rem; align-items: flex-start; }}
.stApp .ac-resource .kind {{ font: 500 10.5px var(--mono); letter-spacing: .1em; text-transform: uppercase; color: var(--muted); }}

@media (max-width: 900px) {{
  [data-testid="stMainBlockContainer"] {{ padding: 1.4rem 1.1rem 3.5rem; }}
  .stApp .ac-h1 {{ font-size: 2.05rem; }}
  .stApp .ac-stats, .stApp .ac-cols {{ grid-template-columns: 1fr; }}
  .stApp .ac-stat + .ac-stat, .stApp .ac-col + .ac-col {{ border-left: 0; padding-left: 0; border-top: 1px solid var(--line); }}
  .stApp [class*="st-key-dark_"] {{ padding: 1.6rem 1.3rem; }}
  .stApp .ac-list li {{ grid-template-columns: 2rem 1fr; }}
  .stApp .ac-list li > :last-child {{ grid-column: 2; }}
}}
"""


def inject() -> None:
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)
