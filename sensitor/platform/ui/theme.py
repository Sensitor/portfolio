"""
The Sensitor design system: tokens and stylesheet for every space.

Signature
---------
* **Editorial numerals.** Chapters are numbered I, II, III in a large serif;
  sections carry « § 01 » on a strong ink rule with a short blue lead-in.
* **Hexagonal markers**, taken from the mark, give each lesson its state:
  outlined to read, ink for the current one, blue once finished.
* **An isometric grid**, barely visible, textures the navy panels — the same
  30° geometry the monogram is drawn on.

Surfaces alternate on purpose: ivory for the page, white for what is read or
filled in, navy for the few moments that must stand out (a starting point, a
result, a recap). One blue accent; green and red only for right and wrong.

Type contrast does the hierarchy: Playfair Display for titles (italic for the
accent word), DM Sans for reading, DM Mono for every label and figure — so a
title, a chapter, a lesson and its metadata can never be confused.

Streamlit's theme colours are overridden everywhere a widget is used, so the
pages look the same whether the visitor's system is light or dark. Muted text
keeps at least 4.5:1 contrast on its surface.
"""

from __future__ import annotations

import streamlit as st

TOKENS = {
    "ink": "#0f1b26", "ink-2": "#18293a", "ink-3": "#223548",
    "text": "#23303a", "muted": "#56616a", "faint": "#7a838a",
    "paper": "#f3f0e8", "paper-2": "#e9e5da", "white": "#fffdf8",
    "line": "#ddd8cb", "line-strong": "#c3bdae",
    "blue": "#1f4a72", "blue-2": "#3a6993", "blue-soft": "#e0e8f0",
    "on-navy": "#e9eef2", "on-navy-muted": "#a9b7c4", "on-navy-accent": "#a9c6e2",
    "green": "#2c5c45", "green-soft": "#e1ece4", "red": "#8c3a31", "red-soft": "#f4e2dc",
    "gold": "#86672f", "gold-soft": "#efe4ce",
}

FONTS = ("https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500"
         "&family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700"
         "&family=Playfair+Display:ital,wght@0,500;0,600;0,700;1,500;1,600&display=swap")

ISO_GRID = ("repeating-linear-gradient(30deg, rgba(169,198,226,.055) 0 1px, transparent 1px 34px),"
            "repeating-linear-gradient(150deg, rgba(169,198,226,.055) 0 1px, transparent 1px 34px),"
            "repeating-linear-gradient(90deg, rgba(169,198,226,.035) 0 1px, transparent 1px 58.9px)")

CSS = """
@import url('__FONTS__');
:root { __TOKENS__
  --serif: 'Playfair Display', Georgia, 'Times New Roman', serif;
  --sans: 'DM Sans', -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif;
  --mono: 'DM Mono', 'SFMono-Regular', Consolas, monospace;
  --iso: __ISO__;
  --ease: cubic-bezier(.2,.7,.2,1);
}

/* ═══ Canvas ═══════════════════════════════════════════════════════════════ */
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
  background: var(--paper) !important; color: var(--text); font-family: var(--sans);
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stDecoration"], [data-testid="stAppDeployButton"], [data-testid="stMainMenu"],
[data-testid="stStatusWidget"], [data-testid="stHeaderActionElements"] { display: none !important; }
[data-testid="stMainBlockContainer"] { max-width: 1200px; padding: 1.6rem 3rem 5rem; }
.stApp [data-testid="stVerticalBlock"] { gap: 1rem; }
.stApp [data-testid="stMarkdownContainer"]:has(> [class*="sx-"]),
.stApp [data-testid="stMarkdownContainer"]:has(> figure),
.stApp [data-testid="stMarkdownContainer"]:has(> table) { margin-bottom: 0 !important; }
::selection { background: var(--blue-soft); color: var(--ink); }

/* ═══ Reading type (Markdown) ══════════════════════════════════════════════ */
.stApp [data-testid="stMarkdownContainer"] { color: var(--text); }
.stApp [data-testid="stMarkdownContainer"] p,
.stApp [data-testid="stMarkdownContainer"] li { color: var(--text); font-size: 16px; line-height: 1.78; }
.stApp [data-testid="stMarkdownContainer"] strong { color: var(--ink); font-weight: 650; }
.stApp [data-testid="stMarkdownContainer"] em { color: var(--ink); }
.stApp [data-testid="stMarkdownContainer"] h1:not([class]),
.stApp [data-testid="stMarkdownContainer"] h2:not([class]),
.stApp [data-testid="stMarkdownContainer"] h3:not([class]) {
  font-family: var(--serif); color: var(--ink); font-weight: 600; letter-spacing: -.015em; padding: 0;
}
.stApp [data-testid="stMarkdownContainer"] h2:not([class]) { font-size: 1.85rem; line-height: 1.2; margin: 2.2rem 0 .5rem; }
.stApp [data-testid="stMarkdownContainer"] h3:not([class]) { font-size: 1.3rem; margin: 1.4rem 0 .3rem; }
.stApp [data-testid="stMarkdownContainer"] code {
  font-family: var(--mono); font-size: .85em; color: var(--blue); background: var(--blue-soft);
  padding: .1em .35em; border-radius: 3px;
}
.stApp [data-testid="stMarkdownContainer"] table {
  border-collapse: collapse; width: 100%; margin: .8rem 0 1.2rem; font-size: 14.5px;
  background: var(--white); border: 1px solid var(--line);
}
.stApp [data-testid="stMarkdownContainer"] th {
  font: 500 10.5px var(--mono); letter-spacing: .1em; text-transform: uppercase; color: var(--muted);
  text-align: left; padding: 11px 14px; border-bottom: 1px solid var(--ink); background: var(--paper);
}
.stApp [data-testid="stMarkdownContainer"] td {
  padding: 11px 14px; border-bottom: 1px solid var(--line); color: var(--text);
  font-variant-numeric: tabular-nums; vertical-align: top; line-height: 1.55;
}
.stApp [data-testid="stMarkdownContainer"] tr:last-child td { border-bottom: 0; }
.stApp .katex { color: var(--ink); font-size: 1.14em; }
.stApp [data-testid="stCaptionContainer"] p { color: var(--muted) !important; font-size: 13px; }

/* ═══ Sidebar ══════════════════════════════════════════════════════════════ */
[data-testid="stSidebar"] { background: var(--ink) !important; border-right: 1px solid #1d2c3b; }
[data-testid="stSidebar"] > div { background-color: var(--ink) !important; background-image: var(--iso) !important; }
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: .1rem; }
[data-testid="stSidebarHeader"] { padding-bottom: 0; }
[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] svg { color: var(--on-navy-muted) !important; }
[data-testid="stExpandSidebarButton"] svg { color: var(--ink) !important; }
[data-testid="stSidebar"] .stButton { margin: 0; }
[data-testid="stSidebar"] .stButton > button {
  width: 100%; justify-content: flex-start; background: transparent; border: 0; border-radius: 4px;
  padding: .5rem .75rem; min-height: 0; color: var(--on-navy); font-weight: 500; font-size: 14.5px;
  box-shadow: none; transition: background .18s var(--ease), color .18s var(--ease);
}
[data-testid="stSidebar"] .stButton > button * { color: inherit !important; }
[data-testid="stSidebar"] .stButton > button > div { justify-content: flex-start; width: 100%; }
[data-testid="stSidebar"] .stButton > button p { text-align: left; }
[data-testid="stSidebar"] .stButton > button:hover { background: #ffffff10; color: #fff; }
[data-testid="stSidebar"] .stButton > button:focus-visible { outline: 2px solid var(--on-navy-accent); outline-offset: 1px; }
[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] {
  background: var(--ink-3) !important; color: #fff !important; box-shadow: inset 3px 0 var(--on-navy-accent);
}
[data-testid="stSidebar"] [class*="st-key-navprep_"] button,
[data-testid="stSidebar"] [class*="st-key-navsep_"] button { color: var(--on-navy-muted); }
[data-testid="stSidebar"] [class*="st-key-navprep_"] button::after,
[data-testid="stSidebar"] [class*="st-key-navsep_"] button::after {
  content: "Bientôt"; margin-left: auto; font: 500 9.5px var(--mono); letter-spacing: .1em;
  text-transform: uppercase; color: #c9b38a; border: 1px solid #5a4d36; padding: 2px 5px; border-radius: 2px; white-space: nowrap; flex-shrink: 0;
}
[data-testid="stSidebar"] [class*="st-key-navsep_"] button::after { content: "À part"; color: var(--on-navy-muted); border-color: #3a4b5c; }

/* ═══ Buttons ══════════════════════════════════════════════════════════════ */
.stApp [data-testid="stMain"] .stButton > button,
.stApp [data-testid="stMain"] .stDownloadButton > button,
.stApp [data-testid="stMain"] .stLinkButton > a,
.stApp [data-testid="stMain"] [data-testid="stFormSubmitButton"] > button {
  border-radius: 3px; border: 1px solid var(--ink); background: transparent; color: var(--ink);
  font-weight: 600; font-size: 14px; letter-spacing: .01em; padding: .6rem 1.15rem; min-height: 2.6rem;
  box-shadow: none; transition: background .18s var(--ease), color .18s var(--ease), transform .18s var(--ease);
}
.stApp [data-testid="stMain"] .stButton > button *,
.stApp [data-testid="stMain"] .stDownloadButton > button *,
.stApp [data-testid="stMain"] .stLinkButton > a *,
.stApp [data-testid="stMain"] [data-testid="stFormSubmitButton"] > button * { color: inherit !important; font-weight: inherit; font-size: inherit; }
.stApp [data-testid="stMain"] .stButton > button:hover,
.stApp [data-testid="stMain"] .stDownloadButton > button:hover,
.stApp [data-testid="stMain"] .stLinkButton > a:hover { background: var(--ink); color: var(--paper); border-color: var(--ink); }
.stApp [data-testid="stMain"] button[data-testid="stBaseButton-primary"],
.stApp [data-testid="stMain"] button[data-testid="stBaseButton-primaryFormSubmit"] {
  background: var(--ink) !important; border-color: var(--ink) !important; color: var(--paper) !important;
}
.stApp [data-testid="stMain"] button[data-testid="stBaseButton-primary"]:hover,
.stApp [data-testid="stMain"] button[data-testid="stBaseButton-primaryFormSubmit"]:hover { background: var(--blue) !important; border-color: var(--blue) !important; }
.stApp [data-testid="stMain"] button[data-testid="stBaseButton-tertiary"] {
  border: 0 !important; background: transparent !important; padding: .15rem 0 !important; min-height: 0;
  color: var(--blue) !important; font-size: 13.5px;
}
.stApp [data-testid="stMain"] button[data-testid="stBaseButton-tertiary"] p {
  border-bottom: 1px solid var(--line-strong); padding-bottom: 2px; transition: border-color .18s;
}
.stApp [data-testid="stMain"] button[data-testid="stBaseButton-tertiary"]:hover p { border-color: var(--blue); }
.stApp [data-testid="stMain"] button:disabled { opacity: .4; }
.stApp button:focus-visible, .stApp a:focus-visible { outline: 2px solid var(--blue-2) !important; outline-offset: 2px; }

/* Buttons placed on navy */
.stApp [class*="st-key-navy_"] .stButton > button[data-testid="stBaseButton-primary"] {
  background: var(--paper) !important; color: var(--ink) !important; border-color: var(--paper) !important;
}
.stApp [class*="st-key-navy_"] .stButton > button[data-testid="stBaseButton-primary"]:hover { background: #fff !important; }
.stApp [class*="st-key-navy_"] .stButton > button[data-testid="stBaseButton-secondary"] {
  color: var(--on-navy) !important; border-color: #4a5e72 !important; background: transparent !important;
}
.stApp [class*="st-key-navy_"] .stButton > button[data-testid="stBaseButton-secondary"]:hover { border-color: var(--on-navy) !important; }
.stApp [class*="st-key-navy_"] button[data-testid="stBaseButton-tertiary"] { color: var(--on-navy-accent) !important; }

/* ═══ Stretched links: a whole composition is one button ══════════════════ */
.stApp [class*="st-key-tap_"] { position: relative; gap: 0 !important; }
.stApp [class*="st-key-tapbtn_"] { position: absolute !important; inset: 0; z-index: 4; margin: 0 !important; }
.stApp [class*="st-key-tapbtn_"] .stButton, .stApp [class*="st-key-tapbtn_"] .stButton > button {
  width: 100% !important; height: 100% !important; margin: 0;
}
.stApp [class*="st-key-tapbtn_"] .stButton > button {
  opacity: 0; cursor: pointer; border: 0 !important; background: transparent !important; padding: 0 !important;
}
.stApp [class*="st-key-tap_"]:has(button:focus-visible) .sx-tapbody { outline: 2px solid var(--blue-2); outline-offset: 3px; }
.stApp .sx-tapbody { height: 100%; }

/* ═══ Inputs ═══════════════════════════════════════════════════════════════ */
.stApp [data-testid="stWidgetLabel"] p, .stApp [data-testid="stWidgetLabel"] label {
  color: var(--ink) !important; font-size: 13.5px; font-weight: 600;
}
.stApp [data-baseweb="input"], .stApp [data-baseweb="base-input"], .stApp [data-baseweb="select"] > div,
.stApp [data-baseweb="textarea"], .stApp [data-testid="stNumberInputContainer"] {
  background: var(--white) !important; border: 1px solid var(--line-strong) !important; border-radius: 3px !important;
  transition: border-color .18s;
}
.stApp [data-baseweb="input"]:focus-within, .stApp [data-testid="stNumberInputContainer"]:focus-within,
.stApp [data-baseweb="select"] > div:focus-within { border-color: var(--blue-2) !important; box-shadow: 0 0 0 3px var(--blue-soft) !important; }
.stApp input, .stApp textarea, .stApp [data-baseweb="select"] * {
  color: var(--ink) !important; -webkit-text-fill-color: var(--ink); font-family: var(--sans);
  font-variant-numeric: tabular-nums; background: transparent !important;
}
.stApp [data-testid="stSelectbox"] [data-baseweb="select"] > div,
.stApp [data-testid="stSelectbox"] [data-baseweb="select"] > div > div { background-color: var(--white) !important; }
.stApp [data-testid="stTextInputRootElement"], .stApp [data-testid="stTextInputRootElement"] > div {
  background-color: var(--white) !important;
}
.stApp [data-testid="stExpander"] summary { background: var(--white) !important; }
.stApp input::placeholder { color: var(--faint) !important; -webkit-text-fill-color: var(--faint); }
.stApp [data-testid="stNumberInputContainer"] button { background: var(--paper-2) !important; color: var(--ink) !important; border: 0 !important; }
/* "Press Enter to submit form" sits on top of the typed text: hidden. */
.stApp [data-testid="InputInstructions"] { display: none !important; }
/* Whatever wraps an input directly gets the white field, so a Streamlit
   release that renames its wrappers cannot bring back a dark field. */
.stApp div:has(> input[type="text"]), .stApp div:has(> input[type="password"]),
.stApp div:has(> input[type="email"]), .stApp div:has(> input[type="number"]) {
  background-color: var(--white) !important;
}
.stApp [data-testid="stTextInputRootElement"]:focus-within,
.stApp [data-testid="stNumberInputContainer"]:focus-within {
  border-color: var(--blue-2) !important; box-shadow: 0 0 0 3px var(--blue-soft) !important;
}
:root { color-scheme: light; }
[data-baseweb="popover"] li, [data-baseweb="popover"] ul { background: var(--white) !important; color: var(--ink) !important; }

/* Choices — Streamlit 1.64: label[data-testid=stRadioOption], stCheckbox > label */
.stApp [data-testid="stRadio"], .stApp [data-testid="stRadio"] > div,
.stApp [data-testid="stRadio"] [role="radiogroup"], .stApp [data-testid="stCheckbox"] { width: 100%; }
.stApp [data-testid="stRadio"] [role="radiogroup"] { gap: .5rem; }
.stApp [data-testid="stRadioOption"], .stApp [data-testid="stCheckbox"] > label {
  background: var(--white); border: 1px solid var(--line); border-radius: 3px; padding: .85rem 1rem;
  margin: 0; width: 100%; align-items: flex-start; transition: border-color .18s, background .18s, box-shadow .18s;
}
.stApp [data-testid="stRadioOption"]:hover, .stApp [data-testid="stCheckbox"] > label:hover { border-color: var(--blue-2); }
.stApp [data-testid="stRadioOption"][data-selected="true"], .stApp [data-testid="stCheckbox"] > label:has(input:checked) {
  border-color: var(--blue-2); background: var(--blue-soft); box-shadow: inset 3px 0 var(--blue-2);
}
.stApp [data-testid="stRadioOption"] p, .stApp [data-testid="stCheckbox"] label p {
  color: var(--text) !important; font-size: 15px; line-height: 1.5; font-weight: 400 !important;
}
.stApp [data-testid="stRadioOption"] > div > div:first-child {
  background: var(--white) !important; box-shadow: inset 0 0 0 1.5px var(--blue-2) !important; margin-top: 3px;
}
.stApp [data-testid="stRadioOption"][data-selected="true"] > div > div:first-child { background: var(--blue-2) !important; }
.stApp [data-testid="stRadioOption"][data-selected="true"] > div > div:first-child > div { background: var(--white) !important; }
.stApp [data-testid="stCheckbox"] > label > div:first-of-type { border-color: var(--blue-2) !important; background-color: var(--white) !important; margin-top: 3px; border-radius: 2px; }
.stApp [data-testid="stCheckbox"] > label:has(input:checked) > div:first-of-type { background-color: var(--blue-2) !important; }
.stApp [class*="st-key-inline_"] [data-testid="stRadio"] [role="radiogroup"] { width: auto; }
.stApp [class*="st-key-inline_"] [data-testid="stRadioOption"] { width: auto; padding: .5rem .9rem; }
.stApp [data-testid="stRadioOption"]:has(input:disabled), .stApp [data-testid="stCheckbox"] > label:has(input:disabled) { opacity: .8; cursor: default; }

/* Expanders, tabs, forms, alerts */
.stApp [data-testid="stExpander"] details { border: 1px solid var(--line) !important; border-radius: 3px; background: var(--white); }
.stApp [data-testid="stExpander"] summary, .stApp [data-testid="stExpander"] summary * { color: var(--ink) !important; font-weight: 600; }
/* Tabs: Streamlit 1.64 uses react-aria (stTab + SelectionIndicator) */
.stApp [data-testid="stTab"] { color: var(--muted) !important; border-color: transparent !important;
  outline-color: var(--blue-2) !important; }
.stApp [data-testid="stTab"] p { color: var(--muted) !important; font-weight: 600; font-size: 14.5px; }
.stApp [data-testid="stTab"][aria-selected="true"], .stApp [data-testid="stTab"][data-selected="true"],
.stApp [data-testid="stTab"][aria-selected="true"] p, .stApp [data-testid="stTab"][data-selected="true"] p {
  color: var(--ink) !important;
}
.stApp .react-aria-SelectionIndicator { background-color: var(--ink) !important; border-color: var(--ink) !important;
  color: var(--ink) !important; }
.stApp [data-baseweb="tab-list"] { gap: 1.6rem; border-bottom: 1px solid var(--line); }
.stApp [data-baseweb="tab"] { background: transparent !important; padding: .7rem 0; }
.stApp [data-baseweb="tab"] p { color: var(--muted) !important; font-weight: 600; font-size: 14.5px; }
.stApp [data-baseweb="tab"][aria-selected="true"] p { color: var(--ink) !important; }
.stApp [data-baseweb="tab-highlight"] { background: var(--ink) !important; height: 2px; }
.stApp [data-baseweb="tab-border"] { display: none; }
.stApp [data-testid="stForm"] { border: 1px solid var(--line); background: var(--white); border-radius: 3px; padding: 1.6rem 1.7rem; }
.stApp [data-testid="stAlert"] { border-radius: 3px; }
.stApp [data-testid="stAlert"] p { color: var(--ink) !important; }
.stApp [data-testid="stToast"] { background: var(--ink) !important; }
.stApp [data-testid="stToast"] * { color: var(--paper) !important; }

/* ═══ Keyed containers ═════════════════════════════════════════════════════ */
.stApp [class*="st-key-navy_"] {
  background-color: var(--ink); background-image: var(--iso); border-radius: 4px; padding: 2.4rem 2.6rem 2.2rem; position: relative; overflow: hidden;
}
.stApp [class*="st-key-navy_"] p { color: var(--on-navy-muted) !important; }
.stApp [class*="st-key-sheet_"] {
  background: var(--white); border: 1px solid var(--line); border-radius: 4px; padding: 2.6rem 3rem 2.2rem;
  counter-reset: sx-section;
}
.stApp [class*="st-key-sheet_"] [data-testid="stMarkdownContainer"] h2:not([class])::before {
  counter-increment: sx-section; content: counter(sx-section, decimal-leading-zero);
  display: block; font: 500 12px var(--mono); letter-spacing: .14em; color: var(--blue-2); margin-bottom: .45rem;
}
.stApp [class*="st-key-sheet_"] [data-testid="stMarkdownContainer"] h2:not([class]) {
  border-top: 1px solid var(--line); padding-top: 1.4rem !important; margin-top: 2.4rem;
}
.stApp [class*="st-key-sheet_"] > [data-testid="stElementContainer"]:first-child h2:not([class]) {
  border-top: 0; padding-top: 0 !important; margin-top: 0;
}
.stApp [class*="st-key-doc_"] { background: var(--white); border: 1px solid var(--line); border-radius: 4px; padding: 2.6rem 3rem 2.2rem; }
.stApp [class*="st-key-doc_"] [data-testid="stMarkdownContainer"] h1:not([class]) { font-size: 2.2rem; margin: 0 0 .4rem; }
.stApp [class*="st-key-doc_"] [data-testid="stMarkdownContainer"] h2:not([class]) { border-top: 1px solid var(--line); padding-top: 1.2rem !important; font-size: 1.5rem; }
.stApp [class*="st-key-panel_"] {
  background: var(--white); border: 1px solid var(--line); border-radius: 4px; padding: 1.8rem 1.9rem 1.6rem;
}
.stApp [class*="st-key-sheet_"] [class*="st-key-panel_"] { background: var(--paper); border-color: var(--line); }

/* Callouts */
.stApp [class*="st-key-callout_"] {
  border-left: 3px solid var(--blue-2); background: var(--blue-soft); padding: 1.1rem 1.4rem .45rem;
  border-radius: 0 3px 3px 0; margin: .6rem 0 .8rem; gap: .25rem;
}
.stApp [class*="st-key-callout_definition"] { background: var(--paper); border-left-color: var(--ink); }
.stApp [class*="st-key-callout_example"] { background: var(--gold-soft); border-left-color: var(--gold); }
.stApp [class*="st-key-callout_warning"], .stApp [class*="st-key-callout_mistake"] { background: var(--red-soft); border-left-color: var(--red); }
.stApp [class*="st-key-callout_method"] { background: #e7ecef; border-left-color: var(--blue); }
.stApp [class*="st-key-callout_recap"] { background-color: var(--ink); background-image: var(--iso); border-left: 0; border-radius: 4px; padding: 1.5rem 1.8rem .7rem; }
.stApp [class*="st-key-callout_recap"] p, .stApp [class*="st-key-callout_recap"] li,
.stApp [class*="st-key-callout_recap"] strong { color: var(--on-navy) !important; }
.stApp [class*="st-key-callout_"] p, .stApp [class*="st-key-callout_"] li { font-size: 15.5px; }
.stApp .sx-callout-title { font: 500 11px var(--mono); letter-spacing: .16em; text-transform: uppercase; color: var(--blue); }
.stApp [class*="st-key-callout_example"] .sx-callout-title { color: var(--gold); }
.stApp [class*="st-key-callout_warning"] .sx-callout-title, .stApp [class*="st-key-callout_mistake"] .sx-callout-title { color: var(--red); }
.stApp [class*="st-key-callout_definition"] .sx-callout-title { color: var(--ink); }
.stApp [class*="st-key-callout_recap"] .sx-callout-title { color: var(--on-navy-accent); }

/* Exercise solutions */
.stApp [class*="st-key-solution_"] { border-left: 3px solid var(--line-strong); background: var(--paper); padding: .8rem 1.2rem .2rem; border-radius: 0 3px 3px 0; gap: .1rem; }
.stApp [class*="st-key-solution_correct"] { background: var(--green-soft); border-left-color: var(--green); }
.stApp [class*="st-key-solution_correct"] .sx-callout-title { color: var(--green); }
.stApp [class*="st-key-solution_incorrect"] { background: var(--red-soft); border-left-color: var(--red); }
.stApp [class*="st-key-solution_incorrect"] .sx-callout-title { color: var(--red); }
.stApp [class*="st-key-solution_"] p { font-size: 15px; }

/* Lesson outline: a side column on desktop, a collapsible panel on phones */
.stApp [class*="st-key-mobileonly_"] { display: none; }
.stApp [class*="st-key-outline"] { position: sticky; top: 1.2rem; }
.stApp [data-testid="stHorizontalBlock"]:has([class*="st-key-outline"]) { align-items: stretch; }

/* ═══ Composition primitives ═══════════════════════════════════════════════ */
.stApp .sx-crumbs { display: flex; flex-wrap: wrap; align-items: center; gap: .55rem; font: 400 12px var(--mono);
  letter-spacing: .06em; color: var(--muted); padding-bottom: 1.1rem; border-bottom: 1px solid var(--line); margin-bottom: .6rem; }
.stApp .sx-crumbs b { color: var(--ink); font-weight: 500; }
.stApp .sx-crumbs i { font-style: normal; color: var(--line-strong); }
.stApp .sx-kicker { font: 500 11.5px var(--mono); letter-spacing: .18em; text-transform: uppercase; color: var(--blue-2); }
.stApp .sx-kicker.muted { color: var(--muted); }
.stApp .sx-kicker.on-navy { color: var(--on-navy-accent); }
.stApp .sx-display { font: 600 clamp(2.6rem, 5.2vw, 4.4rem)/1.02 var(--serif); letter-spacing: -.032em; color: var(--ink);
  margin: .9rem 0 1.1rem; padding: 0 !important; }
.stApp .sx-display em, .stApp .sx-title em { font-style: italic; font-weight: 500; color: var(--blue-2); }
.stApp .sx-display.on-navy { color: #f6f3ec; }
.stApp .sx-display.on-navy em { color: var(--on-navy-accent); }
.stApp .sx-title { font: 600 clamp(2.2rem, 4vw, 3.3rem)/1.06 var(--serif); letter-spacing: -.028em; color: var(--ink);
  margin: .7rem 0 .9rem; padding: 0 !important; }
.stApp .sx-lead { font-size: 18.5px; line-height: 1.68; color: var(--muted); max-width: 660px; margin: 0; }
.stApp .sx-lead.on-navy { color: var(--on-navy-muted); }
.stApp .sx-body { font-size: 15.5px; line-height: 1.72; color: var(--muted); margin: 0; }
.stApp .sx-meta { display: flex; flex-wrap: wrap; align-items: center; gap: .35rem 0; margin-top: 1.4rem;
  font: 400 12px var(--mono); letter-spacing: .05em; color: var(--muted); }
.stApp .sx-meta > span { display: inline-flex; align-items: center; gap: .4rem; }
.stApp .sx-meta > span + span::before { content: ""; width: 4px; height: 4px; background: var(--line-strong);
  transform: rotate(45deg); margin: 0 .9rem; }
.stApp .sx-meta b { color: var(--ink); font-weight: 500; }
.stApp .sx-meta svg { width: 14px; height: 14px; color: var(--faint); }

/* Section header: § number, strong rule with a blue lead-in, title and intro side by side */
.stApp .sx-section { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 1rem 3rem;
  align-items: end; border-top: 1px solid var(--ink); padding-top: 1.4rem; margin: 3.6rem 0 1.4rem; position: relative; }
.stApp .sx-section::before { content: ""; position: absolute; top: -2px; left: 0; width: 56px; height: 3px; background: var(--blue-2); }
.stApp .sx-section .num { font: 500 12px var(--mono); letter-spacing: .16em; color: var(--blue-2); display: block; margin-bottom: .6rem; }
.stApp .sx-section h2 { font: 600 2.15rem/1.12 var(--serif); letter-spacing: -.02em; color: var(--ink); margin: 0; padding: 0 !important; }
.stApp .sx-section p { font-size: 15.5px; line-height: 1.7; color: var(--muted); margin: 0; max-width: 520px; }
.stApp .sx-section.compact { margin-top: 2.4rem; }

/* Chapter header */
.stApp .sx-chapter { display: grid; grid-template-columns: 6.5rem minmax(0, 1fr); gap: 0 1.6rem; align-items: start;
  margin: 2.6rem 0 .8rem; }
.stApp .sx-chapter .numeral { font: italic 500 4.6rem/0.9 var(--serif); color: var(--blue-2); letter-spacing: -.03em; text-align: right; }
.stApp .sx-chapter .k { font: 500 11px var(--mono); letter-spacing: .16em; text-transform: uppercase; color: var(--muted); }
.stApp .sx-chapter h3 { font: 600 1.95rem/1.15 var(--serif); color: var(--ink); letter-spacing: -.018em; margin: .35rem 0 .45rem; padding: 0 !important; }
.stApp .sx-chapter p { font-size: 15px; line-height: 1.65; color: var(--muted); margin: 0; max-width: 620px; }

/* Lesson rows */
.stApp .sx-lesson { display: grid; grid-template-columns: 3.1rem minmax(0, 1fr) auto 1.6rem; gap: 0 1.3rem; align-items: center;
  padding: 1.15rem 1rem 1.15rem .4rem; margin-left: 8.1rem; border-top: 1px solid var(--line);
  transition: background .2s var(--ease), padding .2s var(--ease); }
.stApp [class*="st-key-tap_"]:last-child .sx-lesson { border-bottom: 1px solid var(--line); }
.stApp .sx-lesson .title { font: 600 1.32rem/1.25 var(--serif); color: var(--ink); letter-spacing: -.01em; }
.stApp .sx-lesson .summary { font-size: 14px; line-height: 1.55; color: var(--muted); margin-top: .3rem; }
.stApp .sx-lesson .side { display: flex; align-items: center; gap: 1rem; font: 400 12px var(--mono); color: var(--faint); white-space: nowrap; }
.stApp .sx-lesson .arrow { color: var(--line-strong); transition: transform .2s var(--ease), color .2s; }
.stApp .sx-lesson .arrow svg { width: 20px; height: 20px; }
.stApp [class*="st-key-tap_"]:hover .sx-lesson { background: var(--white); padding-left: .9rem; }
.stApp [class*="st-key-tap_"]:hover .sx-lesson .arrow { transform: translateX(4px); color: var(--blue-2); }
.stApp .sx-lesson.locked .title { color: var(--text); }
.stApp .sx-lesson.final { background: var(--paper-2); border-top: 1px solid var(--ink); }
.stApp .sx-lesson.flush { margin-left: 0; }

/* Hexagonal markers */
.stApp .sx-hex { width: 46px; height: 46px; display: block; }
.stApp .sx-hex .h { fill: transparent; stroke: var(--line-strong); stroke-width: 1.4; transition: fill .2s, stroke .2s; }
.stApp .sx-hex .t { font: 500 13px var(--mono); fill: var(--ink); }
.stApp .sx-hex.is-current .h { fill: var(--ink); stroke: var(--ink); }
.stApp .sx-hex.is-current .t { fill: #f6f3ec; }
.stApp .sx-hex.is-done .h { fill: var(--blue-2); stroke: var(--blue-2); }
.stApp .sx-hex.is-done .c { stroke: #fff; }
.stApp .sx-hex.is-locked .h { stroke-dasharray: 3 3; }
.stApp .sx-hex.is-locked .t { fill: var(--faint); }
.stApp .sx-hex.is-final .h { fill: var(--gold-soft); stroke: var(--gold); }
.stApp .sx-hex.is-final .t { fill: var(--gold); }
.stApp [class*="st-key-tap_"]:hover .sx-hex:not(.is-done):not(.is-current) .h { stroke: var(--blue-2); }

/* Pills */
.stApp .sx-pill { display: inline-flex; align-items: center; gap: .35rem; font: 500 10.5px var(--mono); letter-spacing: .1em;
  text-transform: uppercase; padding: 4px 8px 4px 7px; border-radius: 2px; border: 1px solid var(--line-strong); color: var(--muted); white-space: nowrap; }
.stApp .sx-pill svg { width: 12px; height: 12px; }
.stApp .sx-pill.free { color: var(--green); border-color: #a9c3b1; }
.stApp .sx-pill.member { color: var(--blue); border-color: #b4c6d7; }
.stApp .sx-pill.done { color: #fff; background: var(--blue-2); border-color: var(--blue-2); }
.stApp .sx-pill.soon { color: var(--gold); border-color: #d6c39c; background: var(--gold-soft); }
.stApp .sx-pill.live { color: var(--green); border-color: #a9c3b1; background: var(--green-soft); }
.stApp .sx-pill.sep { color: var(--muted); }
.stApp .sx-pill.on-navy { color: var(--on-navy-accent); border-color: #3d5468; }

/* Navy start panel (inside a stretched link) */
.stApp .sx-start { background-color: var(--ink); background-image: var(--iso); color: var(--on-navy); border-radius: 4px; padding: 1.7rem 1.8rem 1.5rem;
  display: flex; flex-direction: column; gap: .2rem; min-height: 100%; transition: transform .22s var(--ease), box-shadow .22s var(--ease); }
.stApp [class*="st-key-tap_"]:hover .sx-start { transform: translateY(-2px); box-shadow: 0 18px 40px -22px rgba(15,27,38,.55); }
.stApp .sx-start .t { font: 600 1.7rem/1.18 var(--serif); color: #f6f3ec; margin: .7rem 0 .4rem; letter-spacing: -.015em; }
.stApp .sx-start .s { font-size: 14px; line-height: 1.6; color: var(--on-navy-muted); }
.stApp .sx-start .foot { display: flex; align-items: center; justify-content: space-between; gap: 1rem; margin-top: 1.4rem;
  padding-top: 1rem; border-top: 1px solid #2b3f52; font: 400 12px var(--mono); color: var(--on-navy-muted); }
.stApp .sx-start .go { display: inline-flex; align-items: center; gap: .6rem; font: 600 14px var(--sans); color: #fff; }
.stApp .sx-start .go svg { width: 18px; height: 18px; transition: transform .22s var(--ease); }
.stApp [class*="st-key-tap_"]:hover .sx-start .go svg { transform: translateX(4px); }
.stApp .sx-start .bar { height: 3px; background: #2b3f52; margin-top: 1rem; }
.stApp .sx-start .bar i { display: block; height: 100%; background: var(--on-navy-accent); }

/* Objectives */
.stApp .sx-objectives { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0 2.4rem; counter-reset: obj; }
.stApp .sx-objectives > div { display: grid; grid-template-columns: 2.2rem minmax(0, 1fr); gap: .8rem; padding: 1rem 0;
  border-top: 1px solid var(--line); }
.stApp .sx-objectives .n { font: 500 12px var(--mono); color: var(--blue-2); padding-top: .2rem; }
.stApp .sx-objectives .x { font-size: 15.5px; line-height: 1.6; color: var(--ink); }
.stApp .sx-objectives.single { grid-template-columns: 1fr; }

/* Facts */
.stApp .sx-facts { display: grid; gap: 0; border-top: 1px solid var(--ink); }
.stApp .sx-facts > div { display: flex; justify-content: space-between; gap: 1rem; padding: .8rem 0; border-bottom: 1px solid var(--line); }
.stApp .sx-facts dt { font: 500 11px var(--mono); letter-spacing: .12em; text-transform: uppercase; color: var(--muted); }
.stApp .sx-facts dd { margin: 0; font-size: 14.5px; color: var(--ink); text-align: right; }

/* Path and space cards */
.stApp .sx-feature { display: grid; grid-template-columns: 11rem minmax(0, 1fr) auto; gap: 0 2.2rem; align-items: center;
  background: var(--white); border: 1px solid var(--line); border-left: 3px solid var(--blue-2); padding: 1.9rem 2rem 1.9rem 0;
  transition: border-color .2s, box-shadow .22s var(--ease); border-radius: 0 4px 4px 0; }
.stApp [class*="st-key-tap_"]:hover .sx-feature { border-color: var(--blue-2); box-shadow: 0 16px 36px -26px rgba(15,27,38,.5); }
.stApp .sx-feature .numeral { font: italic 500 6rem/1 var(--serif); color: var(--blue-2); text-align: center; }
.stApp .sx-feature .t { font: 600 1.85rem/1.15 var(--serif); color: var(--ink); margin: .5rem 0 .5rem; letter-spacing: -.018em; }
.stApp .sx-feature .s { font-size: 15px; line-height: 1.65; color: var(--muted); max-width: 560px; }
.stApp .sx-feature .go { display: grid; place-items: center; width: 52px; height: 52px; border: 1px solid var(--ink); border-radius: 50%;
  color: var(--ink); transition: background .2s, color .2s, transform .2s var(--ease); margin-right: .2rem; }
.stApp .sx-feature .go svg { width: 20px; height: 20px; }
.stApp [class*="st-key-tap_"]:hover .sx-feature .go { background: var(--ink); color: var(--paper); transform: translateX(3px); }

.stApp .sx-index { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); border-top: 1px solid var(--ink); }
.stApp .sx-index > div { padding: 1.2rem 1.4rem 1.3rem 0; border-bottom: 1px solid var(--line); }
.stApp .sx-index > div:not(:nth-child(3n+1)) { padding-left: 1.4rem; border-left: 1px solid var(--line); }
.stApp .sx-index .n { font: 500 12px var(--mono); color: var(--faint); }
.stApp .sx-index .t { font: 600 1.12rem/1.3 var(--serif); color: var(--text); margin: .45rem 0 .55rem; }
.stApp .sx-index .x { font-size: 13.5px; line-height: 1.55; color: var(--muted); margin-bottom: .7rem; }

.stApp .sx-space { height: 100%; display: flex; flex-direction: column; gap: .3rem; padding: 1.5rem 1.4rem 1.3rem;
  background: var(--white); border: 1px solid var(--line); border-radius: 4px; transition: border-color .2s, transform .22s var(--ease); min-height: 13.5rem; }
.stApp [class*="st-key-tap_"]:hover .sx-space { border-color: var(--ink); transform: translateY(-2px); }
.stApp .sx-space.navy { background-color: var(--ink); background-image: var(--iso); border-color: var(--ink); }
.stApp .sx-space .top { display: flex; justify-content: space-between; align-items: center; }
.stApp .sx-space .numeral { font: italic 500 1.9rem/1 var(--serif); color: var(--blue-2); }
.stApp .sx-space.navy .numeral { color: var(--on-navy-accent); }
.stApp .sx-space .ic svg { width: 22px; height: 22px; color: var(--muted); }
.stApp .sx-space .t { font: 600 1.35rem/1.2 var(--serif); color: var(--ink); margin-top: 1.1rem; }
.stApp .sx-space.navy .t { color: #f6f3ec; }
.stApp .sx-space .s { font-size: 14px; line-height: 1.55; color: var(--muted); flex: 1; }
.stApp .sx-space.navy .s { color: var(--on-navy-muted); }
.stApp .sx-space .foot { display: flex; justify-content: space-between; align-items: center; margin-top: 1rem; }
.stApp .sx-space .foot svg { width: 18px; height: 18px; color: var(--faint); transition: transform .2s var(--ease); }
.stApp [class*="st-key-tap_"]:hover .sx-space .foot svg { transform: translateX(3px); color: var(--ink); }
.stApp .sx-space.navy .foot svg { color: var(--on-navy-muted); }

/* Process (learning loop) */
.stApp .sx-process { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 0; counter-reset: step; }
.stApp .sx-process > div { padding: 0 1.2rem 0 0; position: relative; }
.stApp .sx-process > div::before { content: ""; display: block; height: 1px; background: var(--line-strong); margin: 1.45rem 0 1.1rem 3.2rem; }
.stApp .sx-process > div:last-child::before { background: transparent; }
.stApp .sx-process .hx { position: absolute; top: 0; left: 0; }
.stApp .sx-process .hx svg { width: 2.9rem; height: 2.9rem; }
.stApp .sx-process .t { font: 600 1.15rem var(--serif); color: var(--ink); margin-bottom: .35rem; }
.stApp .sx-process .x { font-size: 13.5px; line-height: 1.55; color: var(--muted); }

/* Hero */
.stApp .sx-hero-art svg { width: 100%; height: auto; display: block; }
.stApp .sx-watermark { position: absolute; right: -3.5rem; bottom: -4.5rem; opacity: .06; color: #fff; pointer-events: none; }
.stApp .sx-watermark svg { width: 22rem; height: auto; }
.stApp .sx-figures-navy { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); border-top: 1px solid #2b3f52; margin-top: 1.8rem; }
.stApp .sx-figures-navy > div { padding: 1.1rem 1.2rem 0 0; }
.stApp .sx-figures-navy > div + div { padding-left: 1.2rem; border-left: 1px solid #2b3f52; }
.stApp .sx-figures-navy .v { font: 600 2.1rem/1 var(--serif); color: #f6f3ec; font-variant-numeric: tabular-nums; }
.stApp .sx-figures-navy .v small { font: 400 .9rem var(--sans); color: var(--on-navy-muted); }
.stApp .sx-figures-navy .l { font: 500 10.5px var(--mono); letter-spacing: .12em; text-transform: uppercase; color: var(--on-navy-muted); margin-top: .55rem; }

/* Stats on paper */
.stApp .sx-stats { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); border-top: 1px solid var(--ink); border-bottom: 1px solid var(--line); }
.stApp .sx-stats > div { padding: 1.3rem 1.3rem 1.2rem 0; }
.stApp .sx-stats > div + div { padding-left: 1.4rem; border-left: 1px solid var(--line); }
.stApp .sx-stats .l { font: 500 11px var(--mono); letter-spacing: .12em; text-transform: uppercase; color: var(--muted); }
.stApp .sx-stats .v { font: 600 2.4rem/1.05 var(--serif); color: var(--ink); margin-top: .5rem; font-variant-numeric: tabular-nums; }
.stApp .sx-stats .v small { font: 400 1rem var(--sans); color: var(--muted); }
.stApp .sx-stats .d { font-size: 13px; color: var(--muted); margin-top: .3rem; }

/* Figures (risk lab) */
.stApp .sx-figures { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); border: 1px solid var(--line);
  background: var(--white); border-radius: 3px; overflow: hidden; }
.stApp .sx-figures > div { padding: 1.1rem 1.2rem; border-right: 1px solid var(--line); border-bottom: 1px solid var(--line); margin: 0 -1px -1px 0; }
.stApp .sx-figures .l { font: 500 10.5px var(--mono); letter-spacing: .1em; text-transform: uppercase; color: var(--muted); }
.stApp .sx-figures .v { font: 500 1.45rem var(--mono); color: var(--ink); margin-top: .4rem; letter-spacing: -.02em; font-variant-numeric: tabular-nums; white-space: nowrap; }
.stApp .sx-figures .d { font-size: 12.5px; color: var(--muted); margin-top: .2rem; }
.stApp .sx-figures.four { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.stApp .sx-figures.three { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.stApp .sx-figures > div.emph { background-color: var(--ink); background-image: var(--iso); }
.stApp .sx-figures > div.emph .l, .stApp .sx-figures > div.emph .d { color: var(--on-navy-muted); }
.stApp .sx-figures > div.emph .v { color: #fff; }

/* Diagrams */
.stApp .sx-diagram { margin: 1rem 0 1.4rem; background: var(--paper); border: 1px solid var(--line); border-radius: 3px; padding: 1.4rem 1.5rem 1rem; }
.stApp .sx-diagram svg { width: 100%; height: auto; display: block; max-height: 360px; }
.stApp .sx-diagram figcaption { display: grid; grid-template-columns: auto minmax(0, 1fr); gap: .9rem; font-size: 13.5px; color: var(--muted);
  line-height: 1.55; margin-top: 1rem; border-top: 1px solid var(--line); padding-top: .8rem; }
.stApp .sx-diagram figcaption b { font: 500 11px var(--mono); letter-spacing: .12em; text-transform: uppercase; color: var(--blue-2); padding-top: .15rem; white-space: nowrap; }

/* Quiz */
.stApp .sx-qhead { display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 1.2rem; align-items: start; margin-top: 1.6rem;
  padding-top: 1.4rem; border-top: 1px solid var(--line); }
.stApp .sx-qhead .q { font: italic 500 2.3rem/1 var(--serif); color: var(--blue-2); min-width: 2.6rem; }
.stApp .sx-qhead .k { font: 500 11px var(--mono); letter-spacing: .14em; text-transform: uppercase; color: var(--muted); }
.stApp .sx-qhead .p { font: 600 1.22rem/1.45 var(--serif); color: var(--ink); margin-top: .35rem; }
.stApp .sx-steps { display: flex; gap: 4px; margin: 1rem 0 .2rem; }
.stApp .sx-steps i { flex: 1; height: 4px; background: var(--line); }
.stApp .sx-steps i.correct { background: var(--green); }
.stApp .sx-steps i.incorrect { background: var(--red); }
.stApp .sx-steps i.answered { background: var(--blue-2); }
.stApp .sx-steps i.unanswered { background: var(--line-strong); }
.stApp .sx-feedback { border-radius: 3px; padding: 1rem 1.2rem; font-size: 14.5px; line-height: 1.6; border-left: 3px solid; }
.stApp .sx-feedback.correct { background: var(--green-soft); border-color: var(--green); }
.stApp .sx-feedback.incorrect { background: var(--red-soft); border-color: var(--red); }
.stApp .sx-feedback.unanswered { background: var(--paper-2); border-color: var(--line-strong); }
.stApp .sx-feedback .status { font: 500 11px var(--mono); letter-spacing: .14em; text-transform: uppercase; }
.stApp .sx-feedback.correct .status { color: var(--green); }
.stApp .sx-feedback.incorrect .status { color: var(--red); }
.stApp .sx-feedback.unanswered .status { color: var(--muted); }
.stApp .sx-feedback ul { margin: .55rem 0 0; padding: 0; list-style: none; }
.stApp .sx-feedback li { margin: .5rem 0; color: var(--text); padding-left: 1.5rem; position: relative; }
.stApp .sx-feedback li .mark { position: absolute; left: 0; top: .15rem; }
.stApp .sx-feedback li .mark svg { width: 15px; height: 15px; }
.stApp .sx-feedback li.ok .mark { color: var(--green); }
.stApp .sx-feedback li.ko .mark { color: var(--red); }
.stApp .sx-feedback li b { color: var(--ink); font-weight: 600; }
.stApp .sx-feedback li .why { display: block; color: var(--muted); font-size: 14px; }
.stApp .sx-feedback .general { margin: .7rem 0 0; color: var(--text); }
.stApp .sx-result { display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 1.6rem; align-items: center;
  background-color: var(--ink); background-image: var(--iso); border-radius: 4px; padding: 1.6rem 1.8rem; margin-top: 1.6rem; }
.stApp .sx-result .big { font: 600 3.4rem/1 var(--serif); color: #f6f3ec; font-variant-numeric: tabular-nums; }
.stApp .sx-result .big small { font: 400 1.2rem var(--sans); color: var(--on-navy-muted); }
.stApp .sx-result .k { font: 500 11px var(--mono); letter-spacing: .16em; text-transform: uppercase; color: var(--on-navy-accent); }
.stApp .sx-result .k.pass { color: #9fd3b4; }
.stApp .sx-result .k.fail { color: #e7b2a8; }
.stApp .sx-result p { color: var(--on-navy-muted); font-size: 14.5px; margin: .35rem 0 0; line-height: 1.6; }
.stApp .sx-result .meter { position: relative; height: 4px; background: #2b3f52; margin-top: .9rem; }
.stApp .sx-result .meter i { position: absolute; left: 0; top: 0; bottom: 0; background: var(--on-navy-accent); }
.stApp .sx-result .meter b { position: absolute; top: -5px; width: 2px; height: 14px; background: #f6f3ec; }

/* Library */
.stApp .sx-book { display: grid; grid-template-columns: 7.2rem minmax(0, 1fr) auto; gap: 0 1.8rem; align-items: center;
  padding: 1.4rem 0; border-top: 1px solid var(--line); transition: background .2s; }
.stApp [class*="st-key-tap_"]:last-child .sx-book { border-bottom: 1px solid var(--line); }
.stApp .sx-cover { aspect-ratio: 3 / 4; background-color: var(--ink); background-image: var(--iso); color: #f6f3ec; padding: .75rem .7rem; display: flex; flex-direction: column;
  justify-content: space-between; box-shadow: 4px 4px 0 var(--line-strong); transition: transform .22s var(--ease), box-shadow .22s var(--ease); }
.stApp .sx-cover.alt { background-color: var(--blue-2); background-image: var(--iso); }
.stApp .sx-cover .ck { font: 500 8.5px var(--mono); letter-spacing: .14em; text-transform: uppercase; color: var(--on-navy-accent); }
.stApp .sx-cover .ct { font: 600 .9rem/1.15 var(--serif); }
.stApp [class*="st-key-tap_"]:hover .sx-cover { transform: translate(-2px, -2px); box-shadow: 6px 6px 0 var(--blue-2); }
.stApp .sx-book .t { font: 600 1.4rem/1.2 var(--serif); color: var(--ink); margin: .45rem 0 .35rem; }
.stApp .sx-book .s { font-size: 14.5px; line-height: 1.6; color: var(--muted); max-width: 560px; }
.stApp .sx-book .arrow { color: var(--line-strong); transition: transform .2s var(--ease), color .2s; }
.stApp .sx-book .arrow svg { width: 22px; height: 22px; }
.stApp [class*="st-key-tap_"]:hover .sx-book .arrow { transform: translateX(4px); color: var(--blue-2); }
.stApp .sx-doc { max-width: 760px; }

/* Notices */
.stApp .sx-notice { display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 1rem; align-items: start;
  border: 1px dashed var(--line-strong); border-radius: 3px; padding: 1.1rem 1.3rem; background: transparent; }
.stApp .sx-notice svg { width: 20px; height: 20px; color: var(--gold); margin-top: .1rem; }
.stApp .sx-notice b { display: block; color: var(--ink); font-size: 14.5px; margin-bottom: .2rem; }
.stApp .sx-notice p { margin: 0; font-size: 14px; line-height: 1.6; color: var(--muted); }
.stApp .sx-note { font-size: 13.5px; color: var(--muted); line-height: 1.6; border-left: 2px solid var(--line-strong); padding-left: .9rem; margin: 0; }
.stApp .sx-plan { list-style: none; padding: 0; margin: 0; border-top: 1px solid var(--ink); }
.stApp .sx-plan li { display: grid; grid-template-columns: 2.6rem minmax(0, 1fr) auto; gap: 1rem; align-items: baseline; padding: 1rem 0; border-bottom: 1px solid var(--line); }
.stApp .sx-plan .n { font: 500 12px var(--mono); color: var(--faint); }
.stApp .sx-plan .x { font-size: 15.5px; color: var(--text); line-height: 1.55; }
.stApp .sx-progress { height: 3px; background: var(--line); }
.stApp .sx-progress > i { display: block; height: 100%; background: var(--blue-2); }
.stApp .sx-progress-row { display: flex; align-items: center; gap: .9rem; font: 400 12px var(--mono); color: var(--muted); }
.stApp .sx-progress-row .sx-progress { flex: 1; }
.stApp .sx-hr { border: 0; border-top: 1px solid var(--line); margin: 1.8rem 0; }

/* Brand in the sidebar */
.stApp .sx-brand { display: flex; align-items: center; gap: .8rem; padding: .1rem .4rem 1.4rem; }
.stApp .sx-brand svg { flex-shrink: 0; filter: drop-shadow(0 6px 14px rgba(0,0,0,.35)); }
.stApp .sx-brand-name { font: 700 16px var(--sans); letter-spacing: .24em; color: #f6f3ec; }
.stApp .sx-brand-sub { font: 400 10px var(--mono); letter-spacing: .2em; color: var(--on-navy-muted); margin-top: 3px; }
.stApp .sx-side-label { font: 500 10px var(--mono); letter-spacing: .2em; color: #7f93a6; padding: 1.1rem .75rem .35rem; }
.stApp .sx-side-user { border-top: 1px solid #ffffff14; margin-top: 1.4rem; padding: 1rem .75rem 0; font-size: 12.5px; color: var(--on-navy-muted); line-height: 1.5; }
.stApp .sx-side-user b { display: block; color: var(--on-navy); font-weight: 600; font-size: 13px; word-break: break-all; }
.stApp .sx-side-foot { font-size: 11.5px; color: #7f93a6; line-height: 1.55; padding: .9rem .75rem 0; }

.stApp .sx-footer { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; gap: 1rem 2rem; align-items: center;
  border-top: 1px solid var(--ink); margin-top: 4.5rem; padding-top: 1.2rem; font: 400 11px var(--mono); color: var(--muted); letter-spacing: .05em; }
.stApp .sx-footer .m { display: flex; align-items: center; gap: .7rem; color: var(--ink); letter-spacing: .2em; font-weight: 500; }
.stApp .sx-footer .c { text-align: center; }

/* Lesson page */
.stApp .sx-lesson-head { display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 0 1.6rem; align-items: start; margin-top: .4rem; }
.stApp .sx-lesson-head .no { font: italic 500 5.4rem/.82 var(--serif); color: var(--blue-2); letter-spacing: -.04em; padding-top: .35rem; }
.stApp .sx-lesson-head .sx-title { margin: .55rem 0 0; }
.stApp .sx-outline-item { display: grid; grid-template-columns: 2.1rem minmax(0, 1fr); gap: .7rem; align-items: center;
  padding: .55rem .5rem; border-radius: 3px; transition: background .18s; }
.stApp .sx-outline-item .sx-hex { width: 30px; height: 30px; }
.stApp .sx-outline-item .sx-hex .t { font-size: 15px; }
.stApp .sx-outline-item .x { font-size: 13.5px; line-height: 1.4; color: var(--text); }
.stApp .sx-outline-item.current { background: var(--white); box-shadow: inset 3px 0 var(--ink); }
.stApp .sx-outline-item.current .x { color: var(--ink); font-weight: 600; }
.stApp [class*="st-key-tap_"]:hover .sx-outline-item:not(.current) { background: var(--paper-2); }
.stApp .sx-outline-head { font: 500 10.5px var(--mono); letter-spacing: .16em; text-transform: uppercase; color: var(--muted);
  padding: 1rem .5rem .5rem; border-bottom: 1px solid var(--line); margin-bottom: .3rem; }
.stApp .sx-outline-head b { display: block; font: 600 1.05rem/1.3 var(--serif); letter-spacing: 0; text-transform: none; color: var(--ink); margin-top: .35rem; }
.stApp .sx-next { display: flex; flex-direction: column; gap: .35rem; padding: 1.3rem 1.4rem; border: 1px solid var(--line);
  border-radius: 4px; background: var(--white); height: 100%; transition: border-color .2s, transform .2s var(--ease); }
.stApp .sx-next.right { text-align: right; align-items: flex-end; }
.stApp .sx-next .k { font: 500 10.5px var(--mono); letter-spacing: .14em; text-transform: uppercase; color: var(--muted);
  display: inline-flex; align-items: center; gap: .5rem; }
.stApp .sx-next .k svg { width: 15px; height: 15px; }
.stApp .sx-next .t { font: 600 1.2rem/1.3 var(--serif); color: var(--ink); }
.stApp [class*="st-key-tap_"]:hover .sx-next { border-color: var(--ink); transform: translateY(-1px); }
.stApp .sx-h3 { font: 600 1.45rem/1.25 var(--serif); color: var(--ink); margin: .45rem 0 .35rem; padding: 0 !important; letter-spacing: -.012em; }
.stApp .sx-h3.on-navy { color: #f6f3ec; }
.stApp .sx-cover.big { width: 100%; max-width: 15rem; padding: 1.3rem 1.2rem; box-shadow: 8px 8px 0 var(--line-strong); }
.stApp .sx-cover.big .ck { font-size: 10px; }
.stApp .sx-cover.big .ct { font-size: 1.5rem; line-height: 1.15; }

/* ═══ Responsive ═══════════════════════════════════════════════════════════ */
@media (max-width: 1000px) {
  [data-testid="stMainBlockContainer"] { padding: 3.4rem 1.15rem 4rem; }
  .stApp [class*="st-key-doc_"] { padding: 1.5rem 1.15rem 1.2rem; }
  .stApp .sx-section { grid-template-columns: 1fr; margin-top: 2.8rem; }
  .stApp .sx-chapter { grid-template-columns: 3.4rem minmax(0, 1fr); gap: 0 1rem; }
  .stApp .sx-chapter .numeral { font-size: 3rem; text-align: left; }
  .stApp .sx-chapter h3 { font-size: 1.6rem; }
  .stApp .sx-lesson { margin-left: 0; grid-template-columns: 2.7rem minmax(0, 1fr) 1.2rem; padding-right: .3rem; }
  .stApp .sx-lesson .side { grid-column: 2; grid-row: 2; margin-top: .55rem; }
  .stApp .sx-lesson .arrow { grid-column: 3; grid-row: 1; }
  .stApp .sx-lesson .title { font-size: 1.15rem; }
  .stApp .sx-hex { width: 40px; height: 40px; }
  .stApp .sx-feature { grid-template-columns: 1fr; padding: 1.4rem 1.3rem; gap: .2rem; }
  .stApp .sx-feature .numeral { font-size: 3.4rem; text-align: left; }
  .stApp .sx-feature .go { display: none; }
  .stApp .sx-index, .stApp .sx-stats, .stApp .sx-figures-navy, .stApp .sx-objectives { grid-template-columns: 1fr; }
  .stApp .sx-index > div:not(:nth-child(3n+1)) { padding-left: 0; border-left: 0; }
  .stApp .sx-stats > div + div, .stApp .sx-figures-navy > div + div { padding-left: 0; border-left: 0; border-top: 1px solid var(--line); }
  .stApp .sx-figures-navy > div + div { border-top-color: #2b3f52; }
  .stApp .sx-process { grid-template-columns: 1fr; gap: 1.2rem; }
  .stApp .sx-figures.four, .stApp .sx-figures.three { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .stApp .sx-process > div { padding-left: 3.8rem; min-height: 3rem; }
  .stApp .sx-process > div::before { display: none; }
  .stApp .sx-book { grid-template-columns: 4.8rem minmax(0, 1fr); gap: 0 1.1rem; }
  .stApp .sx-book .arrow { display: none; }
  .stApp .sx-footer { grid-template-columns: 1fr; }
  .stApp .sx-footer .c { text-align: left; }
  .stApp [class*="st-key-navy_"] { padding: 1.7rem 1.4rem 1.5rem; }
  .stApp [class*="st-key-sheet_"] { padding: 1.5rem 1.15rem 1.2rem; }
  .stApp [class*="st-key-panel_"] { padding: 1.3rem 1.1rem 1.1rem; }
  .stApp [class*="st-key-outline"] { position: static; }
  .stApp [data-testid="stColumn"]:has(> div > [class*="st-key-outline_"]),
  .stApp [data-testid="stColumn"]:has([class*="st-key-outline_"]) { display: none; }
  .stApp [class*="st-key-mobileonly_"] { display: flex; }
  .stApp .sx-result { grid-template-columns: 1fr; gap: .6rem; }
  .stApp .sx-lesson-head .no { font-size: 3.4rem; }
  .stApp .sx-lesson-head { gap: 0 1rem; }
}
@media (prefers-reduced-motion: reduce) { .stApp * { transition: none !important; } }
"""


def stylesheet() -> str:
    tokens = "".join(f"--{k}:{v};" for k, v in TOKENS.items())
    return (CSS.replace("__FONTS__", FONTS).replace("__TOKENS__", tokens)
            .replace("__ISO__", ISO_GRID))


def inject() -> None:
    st.markdown(f"<style>{stylesheet()}</style>", unsafe_allow_html=True)
