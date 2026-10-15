"""
Small presentation helpers shared by the Academy pages.

`html()` exists because Streamlit runs Markdown over `st.markdown` input even
with `unsafe_allow_html`: an indented line inside an HTML string becomes a code
block. Every fragment is therefore flattened onto one line before rendering.
"""

from __future__ import annotations

import html as _html
from datetime import datetime

import streamlit as st

from ..content import Lesson

MONTHS = ("janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
          "septembre", "octobre", "novembre", "décembre")
DAYS = ("lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche")


def esc(value) -> str:
    return _html.escape(str(value), quote=True)


def md(text: str) -> None:
    """
    Render Markdown with literal dollar signs.

    Streamlit treats `$…$` as inline LaTeX, so "10 000 $ … 100 $" would become a
    formula. Prices in dollars are everywhere in these lessons; formulas use the
    dedicated `::: formula` block instead.
    """
    st.markdown(text.replace("$", "\\$"))


def html(fragment: str) -> None:
    flat = " ".join(line.strip() for line in fragment.splitlines() if line.strip())
    st.markdown(flat.replace("$", "&#36;"), unsafe_allow_html=True)


# ── Formatting ───────────────────────────────────────────────────────────────

def number(value: float, decimals: int = 2) -> str:
    """French formatting: narrow no-break space for thousands, comma for decimals."""
    text = f"{value:,.{decimals}f}"
    return text.replace(",", " ").replace(".", ",")


def money(value: float, currency: str = "$", decimals: int = 2) -> str:
    symbol = {"USD": "$", "EUR": "€", "GBP": "£", "CHF": "CHF"}.get(currency, currency)
    return f"{number(value, decimals)} {symbol}"


def percent(value: float, decimals: int = 1) -> str:
    return f"{number(value, decimals)} %"


def parse_stamp(stamp: str | None) -> datetime | None:
    if not stamp:
        return None
    try:
        return datetime.fromisoformat(stamp)
    except ValueError:
        return None


def date_fr(stamp, *, with_day: bool = False) -> str:
    moment = parse_stamp(stamp) if isinstance(stamp, str) else stamp
    if moment is None:
        return ""
    text = f"{moment.day} {MONTHS[moment.month - 1]} {moment.year}"
    return f"{DAYS[moment.weekday()]} {text}" if with_day else text


def duration(minutes: int | None) -> str:
    if not minutes:
        return ""
    if minutes < 60:
        return f"{minutes} min"
    hours, rest = divmod(minutes, 60)
    return f"{hours} h {rest:02d}" if rest else f"{hours} h"


# ── Fragments ────────────────────────────────────────────────────────────────

def tag(text: str, kind: str = "") -> str:
    return f'<span class="ac-tag {kind}">{esc(text)}</span>'


def access_tag(lesson: Lesson) -> str:
    return tag("Accès libre", "open") if lesson.is_public else tag("Membres", "member")


def progress_bar(fraction: float, label: str = "") -> str:
    width = max(0.0, min(1.0, fraction)) * 100
    bar = f'<div class="ac-progress" role="progressbar" aria-valuemin="0" aria-valuemax="100" ' \
          f'aria-valuenow="{width:.0f}"><i style="width:{width:.1f}%"></i></div>'
    if not label:
        return bar
    return f'<div class="ac-progress-row">{bar}<span>{esc(label)}</span></div>'


def page_header(eyebrow: str, title: str, lead: str = "", meta: list[str] | None = None) -> None:
    meta_html = ""
    if meta:
        meta_html = '<div class="ac-meta">' + "".join(f"<span>{m}</span>" for m in meta) + "</div>"
    lead_html = f'<p class="ac-lead">{esc(lead)}</p>' if lead else ""
    html(f'<div class="ac-eyebrow">{eyebrow}</div><h1 class="ac-h1">{esc(title)}</h1>'
         f'{lead_html}{meta_html}')


def section(title: str, subtitle: str = "") -> None:
    sub = f'<p class="ac-sub">{esc(subtitle)}</p>' if subtitle else ""
    html(f'<div class="ac-section"><div><h2 class="ac-h2">{esc(title)}</h2>{sub}</div></div>')


def note(text: str) -> None:
    html(f'<p class="ac-note">{esc(text)}</p>')


def footer() -> None:
    html('<div class="ac-footer"><span>© SENSITOR · ACADEMY</span>'
         '<span>CONTENU ÉDUCATIF — NE CONSTITUE PAS UN CONSEIL EN INVESTISSEMENT</span>'
         '<span>APPRENDRE AVEC MÉTHODE</span></div>')


def diagram(svg: str, caption: str) -> None:
    html(f'<figure class="ac-diagram">{svg}<figcaption>{esc(caption)}</figcaption></figure>')
