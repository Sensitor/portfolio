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

Two universes share the system. Trading keeps the blue accent and Playfair
titles; Monnaie et crypto takes a copper accent and Space Grotesk titles. A
page of that universe swaps the accent tokens of its main column, so every
numeral, rule, marker and bar follows without a rule of its own.

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
    # The Monnaie et crypto universe: copper where Trading has blue.
    "copper": "#7e3c13", "copper-2": "#9c4a1a", "copper-soft": "#f4e2d4", "copper-line": "#dcb79a",
    "on-navy-copper": "#e6b98e",
}

FONTS = ("https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500"
         "&family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700"
         "&family=Playfair+Display:ital,wght@0,500;0,600;0,700;1,500;1,600"
         "&family=Space+Grotesk:wght@400;500;600;700"
         "&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400;1,6..72,500"
         "&family=Schibsted+Grotesk:wght@400;500;600;700&display=swap")

ISO_GRID = ("repeating-linear-gradient(30deg, rgba(169,198,226,.055) 0 1px, transparent 1px 34px),"
            "repeating-linear-gradient(150deg, rgba(169,198,226,.055) 0 1px, transparent 1px 34px),"
            "repeating-linear-gradient(90deg, rgba(169,198,226,.035) 0 1px, transparent 1px 58.9px)")

CSS = """
@import url('__FONTS__');
:root { __TOKENS__
  --serif: 'Playfair Display', Georgia, 'Times New Roman', serif;
  --sans: 'DM Sans', -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif;
  --mono: 'DM Mono', 'SFMono-Regular', Consolas, monospace;
  --grotesk: 'Space Grotesk', 'DM Sans', -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif;
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
/* The control that reopens a collapsed sidebar: a visible tile, not a faint glyph. */
[data-testid="stExpandSidebarButton"] { background: var(--white) !important; border: 1px solid var(--line-strong) !important;
  border-radius: 4px !important; box-shadow: 0 1px 3px rgba(15, 27, 38, .12) !important; opacity: 1 !important; }
[data-testid="stExpandSidebarButton"]:hover { border-color: var(--blue-2) !important; }
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
.stApp div:has(> input[type="email"]), .stApp div:has(> input[type="number"]),
.stApp div:has(> textarea), .stApp [data-testid="stTextAreaRootElement"] {
  background-color: var(--white) !important;
}
.stApp [data-testid="stTextAreaRootElement"] { border: 1px solid var(--line-strong) !important; border-radius: 3px !important; }
/* Streamlit 1.64 draws the selectbox as a react-aria ComboBox, not a baseweb select. */
.stApp [data-testid="stSelectbox"] .react-aria-ComboBox div:has(> input) { border-color: var(--line-strong) !important; border-radius: 3px !important; }
.stApp [data-testid="stSelectbox"] .react-aria-ComboBox button { color: var(--muted) !important; }
.stApp [data-testid="stTextInputRootElement"]:focus-within,
.stApp [data-testid="stTextAreaRootElement"]:focus-within,
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
.stApp [data-testid="stRadioOption"]:not([data-selected="true"]) > div > div:first-child > div { background: transparent !important; }
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
.stApp [class*="st-key-panel_"] [data-testid="stForm"] { border: 0; background: transparent; padding: 0; }
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
.stApp [class*="st-key-callout_opinion"] { background: var(--white); border: 1px solid var(--gold); border-left: 3px solid var(--gold); }
.stApp [class*="st-key-callout_debate"] { background: var(--paper); border-left-color: var(--muted); border-left-style: double; border-left-width: 4px; }
.stApp [class*="st-key-callout_recap"] { background-color: var(--ink); background-image: var(--iso); border-left: 0; border-radius: 4px; padding: 1.5rem 1.8rem .7rem; }
.stApp [class*="st-key-callout_recap"] p, .stApp [class*="st-key-callout_recap"] li,
.stApp [class*="st-key-callout_recap"] strong { color: var(--on-navy) !important; }
.stApp [class*="st-key-callout_"] p, .stApp [class*="st-key-callout_"] li { font-size: 15.5px; }
.stApp .sx-callout-title { font: 500 11px var(--mono); letter-spacing: .16em; text-transform: uppercase; color: var(--blue); }
.stApp [class*="st-key-callout_example"] .sx-callout-title { color: var(--gold); }
.stApp [class*="st-key-callout_warning"] .sx-callout-title, .stApp [class*="st-key-callout_mistake"] .sx-callout-title { color: var(--red); }
.stApp [class*="st-key-callout_definition"] .sx-callout-title { color: var(--ink); }
.stApp [class*="st-key-callout_opinion"] .sx-callout-title { color: var(--gold); }
.stApp [class*="st-key-callout_opinion"] .sx-callout-title::before { content: "◆ "; }
.stApp [class*="st-key-callout_debate"] .sx-callout-title { color: var(--muted); }
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

/* Interactive charts */
.stApp [class*="st-key-chart_"] { background: var(--white); border: 1px solid var(--line); border-radius: 4px; padding: 1.3rem 1.4rem .9rem; margin: 1.2rem 0 1.4rem; }
.stApp .sx-chart-title { font: 600 1.05rem/1.35 var(--serif); color: var(--ink); margin-bottom: .2rem; }
.stApp .sx-chart-foot { border-top: 1px solid var(--line); padding-top: .7rem; }
.stApp .sx-chart-foot > b { font: 500 11px var(--mono); letter-spacing: .12em; text-transform: uppercase; color: var(--blue); margin-right: .6rem; }
.stApp .sx-chart-foot > span { font-size: 14px !important; color: var(--text); }
.stApp .sx-chart-credit, .stApp [class*="st-key-chart_"] p.sx-chart-credit { margin: .45rem 0 0 !important; font-size: 12.5px !important; line-height: 1.55 !important; color: var(--muted) !important; }
.stApp .sx-chart-credit a { color: var(--blue); }
.stApp .sx-chart-key { color: var(--faint); }
.stApp .sx-track { margin: 2.2rem 0 .9rem; }
.stApp .sx-track:first-of-type { margin-top: .4rem; }
.stApp .sx-track p { margin: .35rem 0 0; max-width: 46rem; font-size: 14.5px; line-height: 1.6; color: var(--muted); }
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
/* Reflection journal */
.stApp .sx-entry-head { display: flex; flex-wrap: wrap; align-items: center; gap: .4rem .8rem; font: 500 11px var(--mono); letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
.stApp .sx-entry-q { margin: .9rem 0 .2rem; font: italic 500 1.05rem/1.45 var(--serif); color: var(--ink); }
.stApp .sx-entry-body { margin-top: .6rem; font-size: 15px; line-height: 1.7; color: var(--ink); overflow-wrap: anywhere; }
.stApp [class*="st-key-panel_entry_"] { margin-bottom: .2rem; padding: 1.3rem 1.6rem .6rem; }
.stApp .sx-routine-label { margin: .4rem 0 .2rem; font: 500 11px var(--mono); letter-spacing: .1em; text-transform: uppercase; color: var(--muted); }
.stApp .sx-entry-routine { margin-top: .9rem; padding-top: .7rem; border-top: 1px solid var(--line); }
.stApp .sx-entry-routine b { font: 500 11px var(--mono); letter-spacing: .1em; text-transform: uppercase; color: var(--muted); }
.stApp .sx-entry-routine ul { list-style: none; margin: .5rem 0 0; padding: 0; display: grid; gap: .3rem; }
.stApp .sx-entry-routine li { display: flex; gap: .5rem; align-items: flex-start; font-size: 13.5px; line-height: 1.5; }
.stApp .sx-entry-routine li svg { width: 15px; height: 15px; flex: none; margin-top: .15rem; }
.stApp .sx-entry-routine li.on { color: var(--ink); }
.stApp .sx-entry-routine li.on svg { color: var(--green, #3f6553); }
.stApp .sx-entry-routine li.off { color: var(--faint); }
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
.stApp .sx-brand-sub { font: 400 9px var(--mono); letter-spacing: .09em; white-space: nowrap; color: var(--on-navy-muted); margin-top: 3px; }
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

/* ═══ Universes ════════════════════════════════════════════════════════════ */
/* A copper card, or a whole page marked by crumbs(universe="monnaie"). */
.stApp .uni-monnaie,
.stApp:has(.sx-scope.uni-monnaie) [data-testid="stMain"] {
  --blue: var(--copper); --blue-2: var(--copper-2); --blue-soft: var(--copper-soft);
  --on-navy-accent: var(--on-navy-copper); --serif: var(--grotesk);
}
/* Space Grotesk has no italic: accent words and numerals stay upright, in copper. */
.stApp:has(.sx-scope.uni-monnaie) [data-testid="stMain"] :is(.sx-display em, .sx-title em, .numeral, .no, .q),
.stApp .uni-monnaie :is(.numeral, .t em), .stApp .uni-monnaie.numeral { font-style: normal; }
.stApp:has(.sx-scope.uni-monnaie) [data-testid="stMain"] :is(.sx-display, .sx-title, .sx-section h2, .sx-chapter h3) { letter-spacing: -.035em; }
.stApp:has(.sx-scope.uni-monnaie) .sx-pill.member { border-color: var(--copper-line); }
.stApp .sx-uni { display: inline-flex; align-items: center; gap: .45rem; font: 500 10.5px var(--mono); letter-spacing: .14em;
  text-transform: uppercase; padding: 4px 9px 4px 7px; border-radius: 2px; border: 1px solid; white-space: nowrap; vertical-align: 1px; }
.stApp .sx-uni svg { width: 14px; height: 14px; }
.stApp .sx-uni.uni-trading { color: var(--blue); background: var(--blue-soft); border-color: #b4c6d7; }
.stApp .sx-uni.uni-monnaie { color: var(--copper); background: var(--copper-soft); border-color: var(--copper-line); }
.stApp .sx-kicker .sx-uni { display: flex; width: fit-content; margin: 0 0 .75rem; }
.stApp .sx-outline-head .sx-uni { display: flex; width: fit-content; margin-bottom: .8rem; }
/* The landing headline names both universes, each word in its own accent. */
.stApp .sx-display.sx-eco { font-size: clamp(2.2rem, 3.4vw, 3.3rem); line-height: 1.1; }
.stApp .sx-display em.cu { color: var(--copper-2); font-family: var(--grotesk); font-style: normal; font-weight: 600; letter-spacing: -.045em; }
.stApp .sx-display.on-navy em.cu { color: var(--on-navy-copper); }
/* The head of a universe in the Academy lists */
.stApp .sx-uhead { display: flex; flex-wrap: wrap; align-items: center; gap: .4rem .8rem; margin: 2.6rem 0 1rem;
  padding-bottom: .75rem; border-bottom: 2px solid var(--blue-2); }
.stApp .sx-uhead.first { margin-top: .6rem; }
.stApp .sx-uhead svg { width: 24px; height: 24px; color: var(--blue-2); }
.stApp .sx-uhead b { font: 600 1.55rem/1.2 var(--serif); color: var(--ink); letter-spacing: -.015em; }
.stApp .sx-uhead span { margin-left: auto; font: 400 12px var(--mono); letter-spacing: .05em; color: var(--muted); }
.stApp .sx-index[class*="uni-"] { border-top: 2px solid var(--blue-2); }
/* The two universe cards */
.stApp .sx-ucard { height: 100%; display: flex; flex-direction: column; gap: .45rem; background: var(--white);
  border: 1px solid var(--line); border-top: 4px solid var(--blue-2); border-radius: 0 0 4px 4px; padding: 1.6rem 1.7rem 1.35rem;
  transition: border-color .2s, transform .22s var(--ease), box-shadow .22s var(--ease); }
.stApp [class*="st-key-tap_"]:hover .sx-ucard { border-color: var(--blue-2); transform: translateY(-2px);
  box-shadow: 0 16px 36px -26px rgba(15,27,38,.5); }
.stApp .sx-ucard .top { display: flex; align-items: center; justify-content: space-between; }
.stApp .sx-ucard .top > svg { width: 34px; height: 34px; color: var(--blue-2); }
/* Side by side, the two cards keep the same rhythm whatever the length of their text. */
.stApp .sx-ucard .t { font: 600 1.7rem/1.16 var(--serif); color: var(--ink); letter-spacing: -.02em; margin-top: .7rem; min-height: 2.32em; }
.stApp .sx-ucard .s { font-size: 15px; line-height: 1.65; color: var(--muted); flex: 1; min-height: 4.95em; }
.stApp .sx-ucard .topics { display: flex; flex-wrap: wrap; gap: .35rem; margin-top: .4rem; }
.stApp .sx-ucard .topics span { font: 500 10.5px var(--mono); letter-spacing: .06em; color: var(--blue); background: var(--blue-soft);
  padding: 3px 7px; border-radius: 2px; }
.stApp .sx-ucard .foot { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: .5rem 1rem;
  border-top: 1px solid var(--line); padding-top: .9rem; margin-top: .9rem; font: 400 12px var(--mono); color: var(--muted); }
.stApp .sx-ucard .foot b { color: var(--ink); font-weight: 500; }
.stApp .sx-ucard .go { display: inline-flex; align-items: center; gap: .5rem; font: 600 14px var(--sans); color: var(--blue-2); }
.stApp .sx-ucard .go svg { width: 17px; height: 17px; transition: transform .2s var(--ease); }
.stApp [class*="st-key-tap_"]:hover .sx-ucard .go svg { transform: translateX(4px); }
.stApp code.sx-hash { display: block; font: 400 13px/1.6 var(--mono); color: var(--ink); background: var(--paper);
  border: 1px solid var(--line); border-radius: 3px; padding: .6rem .8rem; overflow-wrap: anywhere; word-break: break-all; }
.stApp code.sx-hash b { color: var(--blue-2); font-weight: 600; }
.stApp .sx-ujoin { margin: 1.2rem auto 0; max-width: 46rem; text-align: center; font-size: 15px; line-height: 1.65; color: var(--muted); }
.stApp .sx-ujoin b { color: var(--ink); font-weight: 600; }

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
  .stApp .sx-ucard .t, .stApp .sx-ucard .s { min-height: 0; }
}
@media (prefers-reduced-motion: reduce) { .stApp * { transition: none !important; } }
"""

JOURNAL_CSS = """
/* ═══ Journal de trading ═══════════════════════════════════════════════════ */
.stApp .st-key-jnav { border-bottom: 1px solid var(--line); padding-bottom: .1rem; margin-top: .4rem; }
.stApp [class*="st-key-jnav"] [data-testid="stHorizontalBlock"] { gap: .35rem; flex-wrap: wrap; }
.stApp [class*="st-key-jnav"] [data-testid="stColumn"] { width: auto !important; flex: 0 0 auto !important; min-width: 0 !important; }
.stApp [class*="st-key-jnav"] .stButton > button { background: transparent !important; border: 0 !important; border-radius: 0 !important;
  box-shadow: none !important; padding: .55rem .9rem .65rem; min-height: 0; border-bottom: 2px solid transparent !important; }
.stApp [class*="st-key-jnav"] .stButton > button p { font: 500 12px var(--mono) !important; letter-spacing: .1em; text-transform: uppercase; color: var(--muted) !important; }
.stApp [class*="st-key-jnav"] .stButton > button:hover p { color: var(--ink) !important; }
.stApp [class*="st-key-jnav"] .stButton > button[data-testid="stBaseButton-primary"] { border-bottom-color: var(--blue-2) !important; }
.stApp [class*="st-key-jnav"] .stButton > button[data-testid="stBaseButton-primary"] p { color: var(--ink) !important; }

.stApp .sx-j-banner { display: flex; gap: .8rem; align-items: center; background: var(--gold-soft); border: 1px solid #d6c39c;
  border-radius: 3px; padding: .75rem 1rem; color: var(--ink); font-size: 14px; }
.stApp .sx-j-banner svg { width: 18px; height: 18px; color: var(--gold); flex: 0 0 auto; }
.stApp .sx-j-banner b { font: 500 11px var(--mono); letter-spacing: .12em; text-transform: uppercase; color: var(--gold); margin-right: .3rem; }

.stApp .sx-j-hero { display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 2.2rem; align-items: center; }
.stApp .sx-j-hero .lead .k { font: 500 11px var(--mono); letter-spacing: .16em; text-transform: uppercase; color: var(--on-navy-accent); }
.stApp .sx-j-hero .lead h3 { font: 600 1.9rem/1.2 var(--serif); color: #f6f3ec; margin: .45rem 0 .5rem; letter-spacing: -.015em; }
.stApp .sx-j-hero .lead h3 em { color: var(--on-navy-accent); }
.stApp .sx-j-hero .lead p { margin: 0; font-size: 14.5px; line-height: 1.65; }
.stApp .sx-j-kpis { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); border-top: 1px solid #2b3f52; margin-top: 1.8rem; }
.stApp .sx-j-kpis > div { padding: 1.05rem 1.1rem .2rem 0; }
.stApp .sx-j-kpis > div:not(:nth-child(3n+1)) { padding-left: 1.1rem; border-left: 1px solid #2b3f52; }
.stApp .sx-j-kpis > div:nth-child(n+4) { border-top: 1px solid #2b3f52; }
.stApp .sx-j-kpis .v { font: 600 1.95rem/1.05 var(--serif); color: #f6f3ec; font-variant-numeric: tabular-nums; white-space: nowrap; }
.stApp .sx-j-kpis .v.up { color: #9fd3b4; } .stApp .sx-j-kpis .v.down { color: #e7b2a8; }
.stApp .sx-j-kpis .v small { font: 400 .85rem var(--sans); color: var(--on-navy-muted); }
.stApp .sx-j-kpis .l { font: 500 10.5px var(--mono); letter-spacing: .12em; text-transform: uppercase; color: var(--on-navy-muted); margin-top: .5rem; }
.stApp .sx-j-kpis .d { font-size: 12.5px; color: var(--on-navy-muted); margin-top: .2rem; opacity: .85; }

.stApp .sx-j-rules { list-style: none; margin: 0; padding: 0; border-top: 1px solid var(--ink); }
.stApp .sx-j-rules li { display: grid; grid-template-columns: minmax(0, 15rem) minmax(0, 1fr) 5.4rem 6.4rem; gap: 1.1rem;
  align-items: center; padding: .8rem 0; border-bottom: 1px solid var(--line); margin: 0 !important; }
.stApp .sx-j-rules .name { font-size: 14.5px; color: var(--ink); font-weight: 500; }
.stApp .sx-j-rules li.clean .name { color: var(--muted); font-weight: 400; }
.stApp .sx-j-rules .bar { height: 8px; background: var(--paper-2); border-radius: 4px; overflow: hidden; }
.stApp .sx-j-rules .bar i { display: block; height: 100%; background: var(--red); border-radius: 4px; }
.stApp .sx-j-rules .n { font: 400 12.5px var(--mono); color: var(--muted); text-align: right; }
.stApp .sx-j-rules .cost { font: 500 13px var(--mono); text-align: right; font-variant-numeric: tabular-nums; }
.stApp .cost.down, .stApp .sx-j-r.down { color: var(--red); } .stApp .cost.up, .stApp .sx-j-r.up { color: var(--green); }
.stApp .cost.ok { color: var(--green); font-weight: 400; font-size: 12px; letter-spacing: .04em; }
.stApp .cost.flat, .stApp .sx-j-r.flat { color: var(--muted); }

.stApp .sx-j-priority { border: 1px solid var(--line); border-top: 3px solid var(--gold); background: var(--white); border-radius: 3px; padding: 1.3rem 1.4rem 1.1rem; }
.stApp .sx-j-priority .k { font: 500 10.5px var(--mono); letter-spacing: .14em; text-transform: uppercase; color: var(--gold); }
.stApp .sx-j-priority h4 { font: 600 1.35rem/1.25 var(--serif); color: var(--ink); margin: .45rem 0 .4rem; }
.stApp .sx-j-priority p { font-size: 14px; line-height: 1.6; color: var(--muted); margin: 0; }
.stApp .sx-j-priority p b { color: var(--ink); }

.stApp .sx-j-legend { display: flex; align-items: center; gap: .3rem; flex-wrap: wrap; font: 400 11px var(--mono); color: var(--muted); margin-top: .5rem; }
.stApp .sx-j-legend i { width: 12px; height: 12px; border-radius: 2px; display: inline-block; }
.stApp .sx-j-legend span { margin: 0 .3rem; }
.stApp .sx-j-legend em { font-style: normal; color: var(--faint); margin-left: .8rem; }
.stApp .sx-calendar, .stApp .sx-ladder { display: block; }
.stApp .sx-calendar { max-width: 560px; }
.stApp table.sx-j-table th:first-child, .stApp table.sx-j-table td:first-child { width: 44%; }
.stApp table.sx-j-table td:not(:first-child), .stApp table.sx-j-table th:not(:first-child) { white-space: nowrap; text-align: right; }
.stApp table.sx-j-table td small { display: block; font: 500 10px var(--mono); letter-spacing: .1em; text-transform: uppercase; color: var(--gold); margin-top: .15rem; }
.stApp table.sx-j-table .sx-j-r { font: 500 13.5px var(--mono); }

.stApp .sx-j-trade { display: grid; grid-template-columns: 3.2rem minmax(0, 1fr) auto 6rem 1.4rem; gap: 0 1.2rem; align-items: center;
  padding: .85rem .3rem; border-top: 1px solid var(--line); transition: background .2s, padding .2s; }
.stApp [class*="st-key-tap_"]:last-child .sx-j-trade { border-bottom: 1px solid var(--line); }
.stApp [class*="st-key-tap_"]:hover .sx-j-trade { background: var(--white); padding-left: .8rem; }
.stApp .sx-j-trade .sym { font: 600 1.12rem/1.2 var(--serif); color: var(--ink); }
.stApp .sx-j-trade .sym span { font: 500 10.5px var(--mono); letter-spacing: .12em; color: var(--blue); margin-left: .5rem; vertical-align: 2px; }
.stApp .sx-j-trade .meta { font: 400 12px var(--mono); color: var(--faint); margin-top: .25rem; }
.stApp .sx-j-trade .tags { display: flex; gap: .35rem; flex-wrap: wrap; justify-content: flex-end; }
.stApp .sx-j-trade .sx-j-r { font: 600 1.05rem var(--mono); text-align: right; font-variant-numeric: tabular-nums; }
.stApp .sx-j-trade .arrow { color: var(--line-strong); }
.stApp .sx-j-trade .arrow svg { width: 18px; height: 18px; }
.stApp .sx-j-trade .sx-ring { width: 46px; height: 46px; }

.stApp .sx-j-big { display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 1.5rem; align-items: center; }
.stApp .sx-j-big .r { font: 600 3.3rem/1 var(--serif); font-variant-numeric: tabular-nums; color: #f6f3ec; }
.stApp .sx-j-big .r.up { color: #9fd3b4; } .stApp .sx-j-big .r.down { color: #e7b2a8; }
.stApp .sx-j-big .k { font: 500 11px var(--mono); letter-spacing: .16em; text-transform: uppercase; color: var(--on-navy-accent); }
.stApp .sx-j-big p { margin: .35rem 0 0; font-size: 14px; line-height: 1.55; }
.stApp .sx-j-facts { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0 1.6rem; margin-top: 1.2rem; }
.stApp .sx-j-facts > div { display: flex; justify-content: space-between; gap: .8rem; padding: .7rem 0; border-bottom: 1px solid var(--line); }
.stApp .sx-j-facts dt { font: 500 10.5px var(--mono); letter-spacing: .12em; text-transform: uppercase; color: var(--muted); }
.stApp .sx-j-facts dd { margin: 0; font-size: 14px; color: var(--ink); text-align: right; font-variant-numeric: tabular-nums; }

.stApp .sx-j-checks { list-style: none; margin: 0; padding: 0; }
.stApp .sx-j-checks li { display: grid; grid-template-columns: 1.6rem minmax(0, 14rem) minmax(0, 1fr); gap: .3rem 1rem; align-items: baseline;
  padding: .7rem 0; border-bottom: 1px solid var(--line); margin: 0 !important; }
.stApp .sx-j-checks .mark { display: grid; place-items: center; width: 22px; height: 22px; border-radius: 50%; position: relative; top: 5px; }
.stApp .sx-j-checks .mark svg { width: 13px; height: 13px; }
.stApp .sx-j-checks li.ok .mark { background: var(--green-soft); color: var(--green); }
.stApp .sx-j-checks li.ko .mark { background: var(--red-soft); color: var(--red); }
.stApp .sx-j-checks li.na .mark { background: var(--paper-2); color: var(--faint); }
.stApp .sx-j-checks b { font-weight: 600; color: var(--ink); font-size: 14.5px; }
.stApp .sx-j-checks li.na b { color: var(--muted); font-weight: 500; }
.stApp .sx-j-checks .why { color: var(--muted); font-size: 14px; line-height: 1.5; }

.stApp .sx-j-marks { list-style: none; margin: 0; padding: 0; }
.stApp .sx-j-marks li { display: grid; grid-template-columns: minmax(0, 12rem) auto minmax(0, 1fr); gap: 1rem; align-items: center; padding: .55rem 0; margin: 0 !important; }
.stApp .sx-j-marks .name { font-size: 14.5px; color: var(--ink); }
.stApp .sx-j-marks .steps { display: flex; gap: 4px; }
.stApp .sx-j-marks .steps i { width: 26px; height: 8px; border-radius: 2px; background: var(--paper-2); }
.stApp .sx-j-marks .steps i.on { background: var(--blue-2); }
.stApp .sx-j-marks .v { font: 400 12px var(--mono); color: var(--muted); }

.stApp .sx-j-quote { border-left: 3px solid var(--blue-2); background: var(--blue-soft); padding: .9rem 1.2rem; border-radius: 0 3px 3px 0;
  color: var(--ink); font-size: 15px; line-height: 1.65; }
.stApp .sx-j-quote .k { display: block; font: 500 10.5px var(--mono); letter-spacing: .12em; text-transform: uppercase; color: var(--blue); margin-bottom: .3rem; }
.stApp .sx-j-text h5 { font: 500 11px var(--mono); letter-spacing: .14em; text-transform: uppercase; color: var(--muted); margin: 1.2rem 0 .35rem; }
.stApp .sx-j-text p { margin: 0; font-size: 15px; line-height: 1.7; color: var(--text); }
.stApp .sx-j-fbhead { display: flex; gap: .8rem; align-items: center; padding-bottom: 1rem; margin-bottom: .6rem; border-bottom: 1px solid var(--line); }
.stApp .sx-j-fbhead svg { width: 34px; height: 34px; padding: 7px; border-radius: 50%; background: var(--ink); color: var(--on-navy-accent); }
.stApp .sx-j-fbhead b { display: block; font: 600 1.15rem var(--serif); color: var(--ink); }
.stApp .sx-j-fbhead span { font: 400 12px var(--mono); color: var(--muted); }
.stApp .sx-j-fbcols { display: grid; gap: 1rem; margin-top: 1rem; }
.stApp .sx-j-fbcols.n2 { grid-template-columns: 1fr 1fr; }
.stApp .sx-j-fbcols > div { border-radius: 3px; padding: .9rem 1.1rem 1rem; }
.stApp .sx-j-fbcols .good { background: var(--green-soft); border-left: 3px solid var(--green); }
.stApp .sx-j-fbcols .work { background: var(--gold-soft); border-left: 3px solid var(--gold); }
.stApp .sx-j-fbcols h5 { font: 500 11px var(--mono); letter-spacing: .14em; text-transform: uppercase; margin: 0 0 .35rem; }
.stApp .sx-j-fbcols .good h5 { color: var(--green); } .stApp .sx-j-fbcols .work h5 { color: var(--gold); }
.stApp .sx-j-fbcols p { margin: 0; font-size: 15px; line-height: 1.65; color: var(--ink); }
.stApp .sx-j-plan { list-style: none; counter-reset: plan; margin: 0; padding: 0; }
.stApp .sx-j-plan li { counter-increment: plan; display: grid; grid-template-columns: 2.2rem minmax(0, 1fr); padding: .55rem 0;
  border-bottom: 1px solid #2b3f52; color: #f6f3ec; font-size: 15px; margin: 0 !important; }
.stApp .sx-j-plan li::before { content: counter(plan, decimal-leading-zero); font: 500 11px var(--mono); color: var(--on-navy-accent); padding-top: .25rem; }
.stApp .sx-j-empty { text-align: center; padding: 2.4rem 1rem 1.2rem; }
.stApp .sx-j-empty h3 { font: 600 1.7rem var(--serif); color: var(--ink); margin: .2rem 0 .5rem; }
.stApp .sx-j-empty p { color: var(--muted); max-width: 560px; margin: 0 auto; font-size: 15px; }

@media (max-width: 1000px) {
  .stApp .sx-j-hero { grid-template-columns: 1fr; gap: 1.2rem; }
  .stApp .sx-j-kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .stApp .sx-j-kpis > div { padding-left: 0 !important; border-left: 0 !important; border-top: 1px solid #2b3f52; }
  .stApp .sx-j-rules li { grid-template-columns: minmax(0, 1fr) auto; }
  .stApp .sx-j-rules .bar { grid-column: 1 / -1; grid-row: 2; }
  .stApp .sx-j-rules .n { display: none; }
  .stApp .sx-j-trade { grid-template-columns: 2.8rem minmax(0, 1fr) 4.8rem; }
  .stApp .sx-j-trade .tags, .stApp .sx-j-trade .arrow { display: none; }
  .stApp .sx-j-checks li { grid-template-columns: 1.6rem minmax(0, 1fr); }
  .stApp .sx-j-checks .why { grid-column: 2; }
  .stApp .sx-j-facts { grid-template-columns: 1fr; }
  .stApp .sx-j-fbcols.n2 { grid-template-columns: 1fr; }
  .stApp .sx-j-marks li { grid-template-columns: minmax(0, 1fr) auto; }
  .stApp .sx-j-marks .v { grid-column: 1 / -1; }
}
"""


# =============================================================================
# DIRECTION « CARNET DE BORD » (prototype, see docs/DIRECTION_ARTISTIQUE.md)
# =============================================================================
#
# A page opts in with `components.carnet()`, which writes the `sx-da` marker;
# everything below applies only under it, so the rest of the platform is
# untouched until the direction is validated. Roles, not shades: each token
# says what it is for, and nothing else uses it.
#
#   paper / sheet / margin     the page, the working surface, the annotation zone
#   ink / ink-2 / graphite     text, secondary text, labels and axes (5.1:1 at worst)
#   rule / rule-strong         hairlines
#   plan                       the member's plan, selection, links
#   up / down                  gain, loss and departure from the plan
#   note                       the voice of annotation: Sensitor and the coach
#   na                         not checkable; shapes only, never text
#
# Type: Newsreader for titles and, in italic, for annotations; Schibsted
# Grotesk for the interface and every figure; DM Mono for times and identifiers
# only. Schibsted has tabular figures (DM Sans has none), used in table columns
# only: its tabular comma is as wide as a digit.

CARNET_TOKENS = {
    "paper": "#F3F0E8", "sheet": "#FFFDF8", "margin": "#EEE9DD",
    "ink": "#0F1B26", "ink-2": "#33414D", "graphite": "#59636B",
    "rule": "#D8D2C3", "rule-strong": "#B7B0A0",
    "plan": "#1F4A72", "plan-soft": "#E1E9F1",
    "up": "#22604A", "up-soft": "#DDEBE2", "down": "#9A3A2C", "down-soft": "#F3E0DA",
    "note": "#855615", "note-soft": "#F2E7D2", "na": "#A2A8AC",
}
CARNET_FONTS = {
    "title": "'Newsreader', Georgia, serif",
    "text": "'Schibsted Grotesk', -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif",
    "code": "'DM Mono', 'SFMono-Regular', Consolas, monospace",
}

CARNET_CSS = """
.stApp:has(.sx-da) { __CTOKENS__ }
__DA__ { font-family: var(--c-text); color: var(--c-ink); font-variant-numeric: normal; }
/* Tabular figures in table columns only: Schibsted's tabular set widens the comma,
   which opens a gap in French decimals anywhere alignment does not need it. */
__DA__ [data-testid="stMarkdownContainer"] td:not(:first-child) { font-variant-numeric: tabular-nums; }
__DA__ [data-testid="stMarkdownContainer"] :is(td, th) { border-left: 0 !important; border-right: 0 !important; }
__DA__ .sx-facts dd { font-variant-numeric: normal; }
__DA__ .sx-calendar text { font-family: var(--c-text); font-size: 8.5px; fill: var(--c-graphite); }
__DA__ .sx-j-legend { font: 500 12px var(--c-text); color: var(--c-graphite); }
__DA__ .sx-j-legend em { font: italic 400 13.5px var(--c-title); color: var(--c-graphite); }
__DA__ [data-testid="stMarkdownContainer"] :is(p, li, td, th, dd, dt),
__DA__ [data-testid="stWidgetLabel"] p, __DA__ button p, __DA__ input, __DA__ textarea,
__DA__ [data-baseweb="select"] * { font-family: var(--c-text); }

/* Titles: one direct sentence per page; the accent word keeps its italic, in the plan's blue. */
__DA__ .sx-title { font: 600 clamp(2.1rem, 3.6vw, 2.9rem)/1.05 var(--c-title); letter-spacing: -.02em; }
__DA__ .sx-title em { font-weight: 500; color: var(--c-plan); }
__DA__ .sx-lead { font: 400 17px/1.6 var(--c-text); color: var(--c-ink-2); }
/* The rubric is the only spaced capital of the system. */
__DA__ .sx-kicker { font: 600 11.5px var(--c-text); letter-spacing: .08em; color: var(--c-graphite); }
__DA__ .sx-crumbs { font: 500 12.5px var(--c-text); color: var(--c-graphite); }
__DA__ .sx-crumbs b { font-weight: 600; }

/* Sections: a question and its answer, stacked; a hairline, no lead-in bar. */
__DA__ .sx-section { display: block; border-top: 1px solid var(--c-rule-strong); padding-top: 1.1rem; margin: 3rem 0 1.1rem; }
__DA__ .sx-section::before { display: none; }
__DA__ .sx-section .num { font: 600 12px var(--c-text); letter-spacing: 0; color: var(--c-note); display: inline; margin: 0 .6rem 0 0; }
__DA__ .sx-section > div { display: flex; align-items: baseline; }
__DA__ .sx-section h2 { font: 600 1.6rem/1.2 var(--c-title); letter-spacing: -.012em; }
__DA__ .sx-section p { font: 400 15px/1.6 var(--c-text); color: var(--c-graphite); margin-top: .35rem; max-width: 720px; }
__DA__ .sx-note { font: italic 400 15px/1.55 var(--c-title); color: var(--c-ink-2); border-left: 2px solid var(--c-note); }
__DA__ .sx-footer { font-family: var(--c-text); letter-spacing: .04em; }

/* Tabs: sentence case, the plan's blue underline. */
__DA__ [class*="st-key-jnav"] .stButton > button p { font: 500 14px var(--c-text) !important; letter-spacing: 0; text-transform: none; color: var(--c-graphite) !important; }
__DA__ [class*="st-key-jnav"] .stButton > button[data-testid="stBaseButton-primary"] { border-bottom-color: var(--c-plan) !important; }
__DA__ [class*="st-key-jnav"] .stButton > button[data-testid="stBaseButton-primary"] p { color: var(--c-ink) !important; font-weight: 600 !important; }
/* Period: a quiet choice of words, not three tiles. */
__DA__ [data-testid="stRadio"] [role="radiogroup"] label { border: 0 !important; background: transparent !important; box-shadow: none !important; padding: .2rem .9rem .2rem 0 !important; }
__DA__ [data-testid="stRadio"] [role="radiogroup"] label p { font: 500 14px var(--c-text); color: var(--c-graphite); }
__DA__ [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) p { color: var(--c-ink); font-weight: 600; text-decoration: underline 2px var(--c-plan); text-underline-offset: 6px; }

/* Tables: a ledger. Rules only, figures right-aligned and tabular. */
__DA__ [data-testid="stMarkdownContainer"] table { background: transparent; border: 0; border-top: 2px solid var(--c-ink); }
__DA__ [data-testid="stMarkdownContainer"] th { font: 600 12px var(--c-text); letter-spacing: .02em; text-transform: none; color: var(--c-graphite);
  background: transparent; border-bottom: 1px solid var(--c-rule-strong); padding: 9px 12px 9px 0; }
__DA__ [data-testid="stMarkdownContainer"] td { padding: 10px 12px 10px 0; border-bottom: 1px solid var(--c-rule); font-size: 14.5px; }
__DA__ table.sx-j-table td small { font: italic 400 13px var(--c-title); letter-spacing: 0; text-transform: none; color: var(--c-note); }
__DA__ .sx-j-r { font-family: var(--c-text) !important; font-weight: 600; }
__DA__ .sx-j-r.up, __DA__ .up { color: var(--c-up); } __DA__ .sx-j-r.down, __DA__ .down { color: var(--c-down); }
__DA__ .sx-pill { font: 600 11px var(--c-text); letter-spacing: .02em; text-transform: none; border-radius: 2px; }
__DA__ .sx-pill.soon { color: var(--c-note); background: var(--c-note-soft); border-color: transparent; }
__DA__ .sx-pill.live { color: var(--c-up); background: var(--c-up-soft); border-color: transparent; }
__DA__ .sx-pill.done { color: #fff; background: var(--c-plan); border-color: var(--c-plan); }
__DA__ .sx-facts dt, __DA__ .sx-j-facts dt { font: 500 13px var(--c-text); letter-spacing: 0; text-transform: none; color: var(--c-graphite); }

/* The label for synthetic data: a slip of paper, with the hook. */
__DA__ .sx-j-banner { background: var(--c-margin); border: 0; border-left: 3px solid var(--c-note); border-radius: 0; font: 400 14px var(--c-text); }
__DA__ .sx-j-banner b { font: 600 13px var(--c-text); letter-spacing: 0; text-transform: none; color: var(--c-note); }

/* ── The record (le relevé): one mark per trade ─────────────────────────── */
__DA__ .sx-c-record { display: grid; grid-template-columns: minmax(0, 1fr) 19rem; border-top: 2px solid var(--c-ink); background: var(--c-sheet); }
__DA__ .sx-c-record .body { padding: 1.5rem 1.8rem 1.4rem 0; }
__DA__ .sx-c-record .rub { font: 600 11.5px var(--c-text); letter-spacing: .08em; text-transform: uppercase; color: var(--c-graphite); }
__DA__ .sx-c-record h3 { font: 600 1.75rem/1.2 var(--c-title); letter-spacing: -.012em; color: var(--c-ink); margin: .35rem 0 1rem; }
__DA__ .sx-c-record h3 em { font-style: italic; font-weight: 500; color: var(--c-plan); }
__DA__ .sx-c-count { display: flex; gap: 1.6rem; align-items: flex-end; }
__DA__ .sx-c-count .big { font: 600 3rem/1 var(--c-text); letter-spacing: -.03em; color: var(--c-ink); white-space: nowrap; }
__DA__ .sx-c-count .big small { font-size: 1.3rem; color: var(--c-graphite); font-weight: 500; letter-spacing: 0; }
__DA__ .sx-c-count .lab { font: 500 13px var(--c-text); color: var(--c-graphite); margin-top: .3rem; }
__DA__ .sx-c-count svg { flex: 1; min-width: 0; height: 52px; }
__DA__ .sx-c-key { display: flex; gap: 1.1rem; flex-wrap: wrap; font: 500 12.5px var(--c-text); color: var(--c-graphite); margin-top: .5rem; }
__DA__ .sx-c-key i { display: inline-block; width: 4px; height: 12px; margin-right: .4rem; vertical-align: -1px; }

/* ── The margin: where Sensitor says what a figure means ───────────────── */
__DA__ .sx-c-margin { background: var(--c-margin); border-left: 1px solid var(--c-rule-strong); padding: 1.3rem 1.3rem 1rem; }
__DA__ .sx-c-margin .rub { color: var(--c-note); }
__DA__ .sx-c-notes { list-style: none; margin: .7rem 0 0; padding: 0; }
__DA__ .sx-c-notes li { display: grid; grid-template-columns: 1.4rem minmax(0, 1fr); margin: 0 0 .9rem !important; padding: 0;
  font: italic 400 15px/1.5 var(--c-title) !important; color: var(--c-ink-2) !important; }
__DA__ .sx-c-notes li b { font: 600 13px/1.6 var(--c-text); font-style: normal; color: var(--c-note); }

/* ── Figures with their sentence ───────────────────────────────────────── */
__DA__ .sx-c-figures { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); border-top: 1px solid var(--c-rule-strong); }
__DA__ .sx-c-figures > div { padding: 1rem 1.2rem .9rem 0; border-bottom: 1px solid var(--c-rule); }
__DA__ .sx-c-figures > div:not(:nth-child(3n+1)) { padding-left: 1.2rem; border-left: 1px solid var(--c-rule); }
__DA__ .sx-c-figures .l { font: 500 13px var(--c-text); color: var(--c-graphite); }
__DA__ .sx-c-figures .v { font: 600 1.9rem/1.15 var(--c-text); letter-spacing: -.025em; color: var(--c-ink); margin-top: .2rem; white-space: nowrap; }
__DA__ .sx-c-figures .v.up { color: var(--c-up); } __DA__ .sx-c-figures .v.down { color: var(--c-down); }
__DA__ .sx-c-figures .s { font: italic 400 14.5px/1.45 var(--c-title); color: var(--c-ink-2); margin-top: .3rem; }

/* ── The ledger of rules ───────────────────────────────────────────────── */
__DA__ .sx-c-ledger { list-style: none; margin: 0; padding: 0; border-top: 2px solid var(--c-ink); }
__DA__ .sx-c-ledger li { display: grid; grid-template-columns: minmax(0, 1fr) 9.5rem 5.2rem 6.4rem; gap: 1rem; align-items: center;
  padding: .72rem 0; border-bottom: 1px solid var(--c-rule); margin: 0 !important; font-size: 15px; }
__DA__ .sx-c-ledger li.clean { color: var(--c-graphite); }
__DA__ .sx-c-ledger .marks { display: flex; gap: 3px; flex-wrap: wrap; }
__DA__ .sx-c-ledger .marks i { width: 3px; height: 14px; background: var(--c-down); display: block; }
__DA__ .sx-c-ledger .marks em { font: italic 400 13.5px var(--c-title); color: var(--c-graphite); }
__DA__ .sx-c-ledger .n { font: 500 13px var(--c-text); color: var(--c-graphite); text-align: right; }
__DA__ .sx-c-ledger .cost { font: 600 14.5px var(--c-text); text-align: right; }
__DA__ .sx-c-ledger .cost.ok { font: italic 400 14px var(--c-title); color: var(--c-up); }
__DA__ .sx-c-ledger .cost.down { color: var(--c-down); } __DA__ .sx-c-ledger .cost.up { color: var(--c-up); }

/* A note in the margin that asks for action: the hook, the ochre, a lesson. */
__DA__ .sx-c-todo { background: var(--c-margin); border-left: 3px solid var(--c-note); padding: 1.1rem 1.2rem 1rem; }
__DA__ .sx-c-todo .rub { font: 600 11.5px var(--c-text); letter-spacing: .08em; text-transform: uppercase; color: var(--c-note); display: flex; gap: .45rem; align-items: center; }
__DA__ .sx-c-todo h4 { font: 600 1.25rem/1.25 var(--c-title); color: var(--c-ink); margin: .45rem 0 .35rem; }
__DA__ .sx-c-todo p { font: italic 400 15px/1.5 var(--c-title); color: var(--c-ink-2); margin: 0; }

/* ── Rows: a trade, a request ──────────────────────────────────────────── */
__DA__ .sx-c-row { display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(0, 1.6fr) auto 5.6rem 1.2rem; gap: 0 1.3rem; align-items: center;
  padding: .8rem .2rem; border-top: 1px solid var(--c-rule); transition: background .15s; }
__DA__ [class*="st-key-tap_"]:last-child .sx-c-row { border-bottom: 1px solid var(--c-rule); }
__DA__ [class*="st-key-tap_"]:hover .sx-c-row { background: var(--c-sheet); }
__DA__ [class*="st-key-tap_"]:hover .sx-c-row .go { color: var(--c-plan); transform: translateX(3px); }
__DA__ .sx-c-row .sym { font: 600 15.5px var(--c-text); color: var(--c-ink); }
__DA__ .sx-c-row .sym span { font: 500 12.5px var(--c-text); color: var(--c-plan); margin-left: .45rem; }
__DA__ .sx-c-row .when { font: 400 12px var(--c-code); color: var(--c-graphite); margin-top: .15rem; }
__DA__ .sx-c-row .q { font: italic 400 15px/1.4 var(--c-title); color: var(--c-ink-2); }
__DA__ .sx-c-row .wait { font: 500 12.5px var(--c-text); color: var(--c-note); margin-top: .15rem; font-style: normal; display: block; }
__DA__ .sx-c-row .r { font: 600 15px var(--c-text); text-align: right; white-space: nowrap; }
__DA__ .sx-c-row .go { color: var(--c-rule-strong); transition: transform .15s, color .15s; }
__DA__ .sx-c-row .go svg { width: 16px; height: 16px; }

/* The print of a trade: the plan's rules, always in the same order. */
.stApp .sx-c-print { display: inline-flex; gap: 3px; vertical-align: middle; }
.stApp .sx-c-print i { width: 10px; height: 10px; display: block; }
.stApp .sx-c-print i.ok { background: var(--c-ink); }
.stApp .sx-c-print i.fail { background: var(--c-down); height: 14px; margin-top: -2px; }
.stApp .sx-c-print i.na { border: 1px solid var(--c-na); }
.stApp .sx-c-print.big i { width: 16px; height: 16px; } .stApp .sx-c-print.big i.fail { height: 22px; margin-top: -3px; }

/* A lesson to read, from the journal: a reference, not a chapter. */
__DA__ .sx-c-ref { display: grid; grid-template-columns: 1.4rem minmax(0, 1fr) auto; gap: .8rem; align-items: center; padding: .75rem 0; border-top: 1px solid var(--c-rule); }
__DA__ [class*="st-key-tap_"]:last-child .sx-c-ref { border-bottom: 1px solid var(--c-rule); }
__DA__ .sx-c-ref .t { font: 600 1.08rem var(--c-title); color: var(--c-ink); }
__DA__ .sx-c-ref .s { font: 500 12.5px var(--c-text); color: var(--c-graphite); }
__DA__ .sx-c-ref .go { color: var(--c-rule-strong); } __DA__ .sx-c-ref .go svg { width: 16px; height: 16px; }
__DA__ [class*="st-key-tap_"]:hover .sx-c-ref .t { color: var(--c-plan); }

/* ── The checks of one trade, as a list with its print ─────────────────── */
__DA__ .sx-j-checks li { grid-template-columns: 1.4rem minmax(0, 15rem) minmax(0, 1fr); }
__DA__ .sx-j-checks .mark { width: 14px; height: 14px; border-radius: 0; top: 3px; }
__DA__ .sx-j-checks .mark svg { display: none; }
__DA__ .sx-j-checks li.ok .mark { background: var(--c-ink); } __DA__ .sx-j-checks li.ko .mark { background: var(--c-down); height: 18px; top: 1px; }
__DA__ .sx-j-checks li.na .mark { background: transparent; border: 1px solid var(--c-na); }
__DA__ .sx-j-checks b { font: 600 15px var(--c-text); } __DA__ .sx-j-checks li.ko b { color: var(--c-down); }
__DA__ .sx-j-checks .why { font: italic 400 15px/1.45 var(--c-title); color: var(--c-ink-2); }

/* ── The corrected copy: the coach's review ────────────────────────────── */
__DA__ .sx-c-copy { display: grid; grid-template-columns: minmax(0, 1fr) 21rem; border-top: 2px solid var(--c-ink); background: var(--c-sheet); }
__DA__ .sx-c-copy .body { padding: 1.3rem 1.6rem 1.2rem 0; }
__DA__ p.sx-c-quote { font: italic 400 1.35rem/1.45 var(--c-title); color: var(--c-ink); margin: .3rem 0 0; }
__DA__ .sx-c-quote::before { content: "« "; color: var(--c-note); } __DA__ .sx-c-quote::after { content: " »"; color: var(--c-note); }
__DA__ .sx-c-who { font: 500 13px var(--c-text); color: var(--c-graphite); margin-top: .5rem; }
__DA__ .sx-c-marks { list-style: none; margin: 0; padding: 0; }
__DA__ .sx-c-marks li { display: grid; grid-template-columns: minmax(0, 11rem) auto minmax(0, 1fr); gap: 1rem; align-items: center; padding: .55rem 0;
  border-bottom: 1px solid var(--c-rule); margin: 0 !important; }
__DA__ .sx-c-marks .name { font: 500 14.5px var(--c-text); }
__DA__ .sx-c-marks .v { font: italic 400 14.5px var(--c-title); color: var(--c-ink-2); }
__DA__ .sx-c-points { counter-reset: none; list-style: none; margin: 0; padding: 0; }
__DA__ .sx-c-points li { display: grid; grid-template-columns: 2rem minmax(0, 1fr); gap: .2rem; padding: .9rem 0; border-bottom: 1px solid var(--c-rule); margin: 0 !important; }
__DA__ .sx-c-points li > b { font: 600 15px var(--c-text); color: var(--c-note); }
__DA__ .sx-c-points h5 { font: 600 13px var(--c-text); letter-spacing: .02em; color: var(--c-graphite); margin: 0 0 .2rem; }
__DA__ .sx-c-points li.good h5 { color: var(--c-up); } __DA__ .sx-c-points li.work h5 { color: var(--c-down); }
__DA__ .sx-c-points p { font: italic 400 16.5px/1.55 var(--c-title) !important; color: var(--c-ink) !important; margin: 0; }
__DA__ .sx-c-visa { display: inline-flex; gap: .8rem; align-items: center; border: 1.5px solid var(--c-ink); padding: .7rem 1rem .65rem .8rem; margin-top: 1.2rem; }
__DA__ .sx-c-visa b { display: block; font: 600 14px var(--c-text); color: var(--c-ink); }
__DA__ .sx-c-visa span { font: italic 400 13.5px var(--c-title); color: var(--c-ink-2); }
__DA__ .sx-c-status { font: 600 13px var(--c-text); color: var(--c-note); display: inline-flex; gap: .4rem; align-items: center; }
__DA__ .sx-c-status.done { color: var(--c-up); }

__DA__ .sx-c-row .meta2 { font: 500 13.5px var(--c-text); color: var(--c-graphite); }
__DA__ .sx-c-row .meta2 em { font: italic 400 14.5px var(--c-title); color: var(--c-down); }

/* The verdict: the one strong block of a page. No grid on it: the grid lives on the binding. */
__DA__ [class*="st-key-navy_"] { background-image: none; border-radius: 0; }
__DA__ .sx-c-verdict .k { font: 600 11.5px var(--c-text); letter-spacing: .08em; text-transform: uppercase; color: var(--on-navy-accent); }
__DA__ .sx-c-verdict .r { font: 600 3rem/1.05 var(--c-text); letter-spacing: -.03em; color: #f6f3ec; margin-top: .3rem; }
__DA__ .sx-c-verdict .r.up { color: #9fd3b4; } __DA__ .sx-c-verdict .r.down { color: #e7b2a8; }
__DA__ .sx-c-verdict p { font: italic 400 16px var(--c-title); color: var(--on-navy-muted) !important; margin: .3rem 0 0; }
__DA__ .sx-c-verdict .pr { display: flex; gap: .8rem; align-items: center; margin-top: 1rem; padding-top: .9rem; border-top: 1px solid #2b3f52; }
__DA__ .sx-c-verdict .pr span:last-child { font: 500 13px var(--c-text); color: var(--on-navy-muted); }
__DA__ .sx-c-verdict .sx-c-print i.ok { background: #f6f3ec; } __DA__ .sx-c-verdict .sx-c-print i.fail { background: #e7b2a8; }
__DA__ .sx-c-verdict .sx-c-print i.na { border-color: #6e7d8a; }
__DA__ svg text { font-variant-numeric: proportional-nums; }

__DA__ .sx-c-summary { font: 400 17px/1.55 var(--c-text); color: var(--c-ink-2); margin: 1.2rem 0 0; border-top: 2px solid var(--c-ink); padding-top: .9rem; }
__DA__ .sx-c-summary b { color: var(--c-ink); font-weight: 600; }
__DA__ .sx-c-summary span { color: var(--c-graphite); font-size: 15px; }
__DA__ .sx-c-done { list-style: none; margin: 0; padding: 0; border-top: 1px solid var(--c-rule-strong); }
__DA__ .sx-c-done li { display: grid; grid-template-columns: 10rem 7rem minmax(0, 1fr); padding: .55rem 0; border-bottom: 1px solid var(--c-rule);
  margin: 0 !important; font: 500 14px var(--c-text); color: var(--c-ink-2); }
__DA__ .sx-c-done li span:last-child { font: italic 400 14.5px var(--c-title); color: var(--c-graphite); }
__DA__ p.sx-c-none { font: italic 400 15px/1.5 var(--c-title); color: var(--c-ink-2); margin-top: .6rem; }
__DA__ .sx-c-copy .sx-c-notes li { font-size: 14px !important; margin-bottom: .55rem !important; }
__DA__ .sx-c-broken { margin-top: 1.1rem; padding-top: .8rem; border-top: 1px solid var(--c-rule); }
__DA__ .sx-c-broken .rub { display: flex; gap: .7rem; align-items: center; }
__DA__ .sx-c-broken ul { list-style: none; margin: .5rem 0 0; padding: 0; }
__DA__ .sx-c-broken li { font: 400 14.5px/1.45 var(--c-text) !important; color: var(--c-ink-2); margin: 0 0 .35rem !important; padding-left: 1rem; position: relative; }
__DA__ .sx-c-broken li::before { content: ""; position: absolute; left: 0; top: .3rem; width: 4px; height: 12px; background: var(--c-down); }
__DA__ .sx-c-broken li b { color: var(--c-down); font-weight: 600; }
__DA__ .sx-j-facts dd { font-family: var(--c-text); font-variant-numeric: normal; }
__DA__ .sx-c-copy .rub, __DA__ .sx-c-margin .rub { font: 600 11.5px var(--c-text); letter-spacing: .08em; text-transform: uppercase; color: var(--c-graphite); }
__DA__ .sx-c-margin .rub { color: var(--c-note); }

/* Panels and the one strong block keep their roles: a sheet, and a verdict. */
__DA__ [class*="st-key-panel_"] { background: var(--c-sheet); border: 0; border-top: 2px solid var(--c-ink); border-radius: 0; }
__DA__ [class*="st-key-chart_"] { background: var(--c-sheet); border: 0; border-top: 2px solid var(--c-ink); border-radius: 0; }
__DA__ .sx-chart-foot b { font: 600 12.5px var(--c-text); letter-spacing: 0; text-transform: none; color: var(--c-note); }
__DA__ .sx-chart-foot span { font: italic 400 15px/1.5 var(--c-title); color: var(--c-ink-2); }

@media (max-width: 1000px) {
  __DA__ .sx-c-record, __DA__ .sx-c-copy { grid-template-columns: 1fr; }
  __DA__ .sx-c-record .body, __DA__ .sx-c-copy .body { padding-right: 0; }
  __DA__ .sx-c-margin { border-left: 0; border-top: 1px solid var(--c-rule-strong); }
  __DA__ .sx-c-count { flex-direction: column; align-items: stretch; gap: .6rem; }
  __DA__ .sx-c-figures { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  __DA__ .sx-c-figures > div { padding-left: 0 !important; border-left: 0 !important; padding-right: .8rem; }
  __DA__ .sx-c-ledger li { grid-template-columns: minmax(0, 1fr) auto; }
  __DA__ .sx-c-ledger .marks { grid-column: 1 / -1; grid-row: 2; }
  __DA__ .sx-c-ledger .n { display: none; }
  __DA__ .sx-c-row { grid-template-columns: minmax(0, 1fr) auto; gap: .35rem 1rem; }
  __DA__ .sx-c-row .q { grid-column: 1 / -1; grid-row: 2; }
  __DA__ .sx-c-row .go { display: none; }
  __DA__ .sx-j-checks li { grid-template-columns: 1.4rem minmax(0, 1fr); }
  __DA__ .sx-c-marks li { grid-template-columns: minmax(0, 1fr) auto; }
  __DA__ .sx-c-marks .v { grid-column: 1 / -1; }
}
"""


def stylesheet() -> str:
    tokens = "".join(f"--{k}:{v};" for k, v in TOKENS.items())
    carnet = ("".join(f"--c-{k}:{v};" for k, v in CARNET_TOKENS.items())
              + "".join(f"--c-{k}:{v};" for k, v in CARNET_FONTS.items()))
    da = CARNET_CSS.replace("__CTOKENS__", carnet).replace("__DA__", '.stApp:has(.sx-da) [data-testid="stMain"]')
    return ((CSS + JOURNAL_CSS + da).replace("__FONTS__", FONTS).replace("__TOKENS__", tokens)
            .replace("__ISO__", ISO_GRID))


def inject() -> None:
    st.markdown(f"<style>{stylesheet()}</style>", unsafe_allow_html=True)
