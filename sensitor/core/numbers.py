"""
Numbers in French typography, for the analyzer's pages read in French.

The analyzer formats its figures the English way, in a few hundred places:
« €1,709.00 », « 35.5% », « +0.18R ». Rather than give each of them a language
argument, the text a page renders in French passes once through `french_html`
(called by `ui.themes.html`), and every chart through `french_figure` (applied by
the chart factories): « 1 709,00 € », « 35,5 % », « +0,18 R ».

What is rewritten, in text only:
* an amount with a currency sign in front, the sign moved after the number;
* a percentage, with a narrow no-break space before « % »;
* a number grouped with commas or written with a decimal point, and an R
  multiple, which takes a space before « R » as on the journal's own pages.

What is never touched: tags and their attributes (an SVG path, a width, a style
value), the content of `<style>`, `<script>` and `<svg>`, plain integers (a year
stays « 2026 »), and dotted dates or versions (« 2025.03.10 »).

No Streamlit.
"""

from __future__ import annotations

import re

NNBSP = " "        # narrow no-break space: thousands, and before « % »
NBSP = " "         # no-break space: before a currency sign
CURRENCIES = "€$£¥"

_NUMBER = r"\d[\d,]*(?:\.\d+)?"
_AMOUNT = re.compile(rf"(?<![\w.,])([-+−]?)([{CURRENCIES}])\s?([-+−]?)({_NUMBER})([KMB]?)(?![\d.])")
_PERCENT = re.compile(rf"(?<![\w.,])([-+−]?)({_NUMBER})\s?%")
_R = re.compile(rf"(?<![\w.,])([-+−]?)({_NUMBER})R\b")
_GROUPED = re.compile(r"(?<![\w.,])(\d{1,3}(?:,\d{3})+(?:\.\d+)?)(?![\d.,]\d)")
_DECIMAL = re.compile(r"(?<![\w.,])(\d+\.\d+)(?![\d.]|,\d)")
_SKIP = ("style", "script", "svg")
_TAG = re.compile(r"(<[^>]*>)")


def french_number(text: str, *, group: bool = True) -> str:
    """« 1,709.00 » → « 1 709,00 ». Grouping from four digits, by narrow spaces."""
    whole, _, decimals = text.replace(",", "").partition(".")
    if group and len(whole) > 3:
        head = len(whole) % 3 or 3
        whole = whole[:head] + "".join(NNBSP + whole[i:i + 3] for i in range(head, len(whole), 3))
    return whole + ("," + decimals if decimals else "")


def french_text(text: str) -> str:
    """The numbers of a plain text in French typography (no tags in it)."""
    if not text or not any(c.isdigit() for c in text):
        return text

    def amount(m):
        sign = m.group(1) or m.group(3)
        suffix = NBSP + {"K": "k", "M": "M", "B": "Md"}[m.group(5)] if m.group(5) else ""
        return f"{sign}{french_number(m.group(4))}{suffix}{NBSP}{m.group(2)}"

    text = _AMOUNT.sub(amount, text)
    text = _PERCENT.sub(lambda m: f"{m.group(1)}{french_number(m.group(2))}{NNBSP}%", text)
    text = _R.sub(lambda m: f"{m.group(1)}{french_number(m.group(2))}{NBSP}R", text)
    text = _GROUPED.sub(lambda m: french_number(m.group(1)), text)
    return _DECIMAL.sub(lambda m: french_number(m.group(1), group=False), text)


def french_html(markup: str) -> str:
    """`french_text` on the text between tags, outside style, script and SVG."""
    if not markup or not any(c.isdigit() for c in markup):
        return markup
    out, skipping = [], None
    for piece in _TAG.split(markup):
        if piece.startswith("<"):
            name = re.match(r"</?\s*([a-zA-Z0-9]+)", piece)
            tag = name.group(1).lower() if name else ""
            if skipping is None and tag in _SKIP and not piece.startswith("</") and not piece.endswith("/>"):
                skipping = tag
            elif skipping == tag and piece.startswith("</"):
                skipping = None
            out.append(piece)
        else:
            out.append(piece if skipping else french_text(piece))
    return "".join(out)


def _template(template: str) -> str:
    """A Plotly hover or text template: the currency after the value, a space before « % » and « R »."""
    if not template:
        return template
    template = re.sub(rf"([{CURRENCIES}])\s?(%\{{[^}}]+\}})", rf"\2{NBSP}\1", template)
    template = re.sub(r"(%\{[^}]+\})%", rf"\1{NNBSP}%", template)
    template = re.sub(r"(%\{[^}]+\})R\b", rf"\1{NBSP}R", template)
    return french_text(template.replace("%{", "\x00{")).replace("\x00{", "%{")


def french_figure(fig):
    """A Plotly figure in French typography: separators, axis currency after the value, templates and labels."""
    fig.update_layout(separators="," + NNBSP)
    layout = fig.layout
    for name in [k for k in layout.to_plotly_json() if k.startswith(("xaxis", "yaxis"))]:
        axis = layout[name]
        prefix = axis.tickprefix
        if prefix and prefix.strip() and prefix.strip()[-1] in CURRENCIES:
            axis.tickprefix = None
            axis.ticksuffix = NBSP + prefix.strip()
        elif prefix and prefix.strip().isalpha():
            axis.tickprefix = None
            axis.ticksuffix = NBSP + prefix.strip()
        if axis.ticksuffix == "%":
            axis.ticksuffix = NNBSP + "%"
    for trace in fig.data:
        for field in ("hovertemplate", "texttemplate"):
            value = getattr(trace, field, None)
            if isinstance(value, str):
                setattr(trace, field, _template(value))
        text = getattr(trace, "text", None)
        if isinstance(text, str):
            trace.text = french_text(text)
        elif text is not None and len(text) and all(isinstance(t, str) for t in text):
            trace.text = [french_text(t) for t in text]
    for note in layout.annotations or ():
        if isinstance(note.text, str):
            note.text = french_html(note.text)
    return fig
