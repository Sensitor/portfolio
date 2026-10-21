"""
Presentation primitives shared by every Sensitor space.

`html()` flattens a fragment onto one line before handing it to `st.markdown`:
Streamlit runs Markdown over HTML input, so an indented line would otherwise
become a code block. Dollar signs are encoded because Streamlit reads `$…$` as
LaTeX — prices in dollars are everywhere in the lessons.

`tap()` is the stretched-link pattern: a composition drawn in HTML, with a real
Streamlit button laid over it. The button carries the accessible label and the
keyboard focus; the drawing is `aria-hidden`.
"""

from __future__ import annotations

import html as _html
import re
from datetime import datetime

import streamlit as st

from .. import brand
from . import runtime as rt

MONTHS = ("janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
          "septembre", "octobre", "novembre", "décembre")
DAYS = ("lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche")
NUMERALS = ("I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII")


# ── Rendering ────────────────────────────────────────────────────────────────

def esc(value) -> str:
    return _html.escape(str(value), quote=True)


def html(fragment: str) -> None:
    flat = " ".join(line.strip() for line in fragment.splitlines() if line.strip())
    st.markdown(flat.replace("$", "&#36;"), unsafe_allow_html=True)


_UNIT_SPACE = re.compile(r"(?<=\d) (?=(?:%|€|\$|R\b|pips\b|points?\b|BTC\b|ans\b))")


_THOUSANDS = re.compile(r"(?<=\d) (?=\d{3}(?!\d))")


def keep_units(text: str) -> str:
    """
    A number never splits across lines: not from its unit (« 6 % », « 100 € »,
    « 2,28 R »), and not inside its thousands groups (« 200 000 »).
    """
    return _UNIT_SPACE.sub("\u00a0", _THOUSANDS.sub("\u00a0", text))


def md(text: str) -> None:
    st.markdown(keep_units(text).replace("$", "\\$"))


def tap(key: str, fragment: str, label: str, page: str, **fields) -> None:
    """Draw `fragment` and make the whole of it a link to `page`."""
    with st.container(key=f"tap_{key}"):
        html(f'<div class="sx-tapbody" aria-hidden="true">{fragment}</div>')
        rt.link(label, page, key=f"tapbtn_{key}", width="stretch", **fields)


# ── Formatting ───────────────────────────────────────────────────────────────

def number(value: float, decimals: int = 2) -> str:
    text = f"{value:,.{decimals}f}"
    return text.replace(",", " ").replace(".", ",")


def money(value: float, currency: str = "$", decimals: int = 2) -> str:
    symbol = {"USD": "$", "EUR": "€", "GBP": "£", "CHF": "CHF"}.get(currency, currency)
    return f"{number(value, decimals)} {symbol}"


def percent(value: float, decimals: int = 1) -> str:
    return f"{number(value, decimals)} %"


def date_fr(stamp, *, with_day: bool = False) -> str:
    moment = stamp
    if isinstance(stamp, str):
        try:
            moment = datetime.fromisoformat(stamp)
        except ValueError:
            return ""
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


def numeral(n: int) -> str:
    return NUMERALS[n - 1] if 1 <= n <= len(NUMERALS) else str(n)


# ── Icons (line, 24 px grid) ─────────────────────────────────────────────────

_ICONS = {
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "back": '<path d="M19 12H5M11 6l-6 6 6 6"/>',
    "lock": '<rect x="5" y="11" width="14" height="9" rx="1.5"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
    "check": '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    "cross": '<path d="M6 6l12 12M18 6L6 18"/>',
    "clock": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
    "book": '<path d="M4 5.5A1.5 1.5 0 0 1 5.5 4H11v16H5.5A1.5 1.5 0 0 1 4 18.5z"/><path d="M20 5.5A1.5 1.5 0 0 0 18.5 4H13v16h5.5a1.5 1.5 0 0 0 1.5-1.5z"/>',
    "library": '<path d="M5 4h3v16H5zM10 4h3v16h-3z"/><path d="M15.2 4.6l2.9-.8 3.5 15.4-2.9.8z"/>',
    "mind": '<circle cx="12" cy="12" r="8.5"/><path d="M12 3.5v17M3.5 12h17"/><circle cx="12" cy="12" r="3"/>',
    "lab": '<path d="M9 3h6M10 3v6.5L4.8 18.3A1.8 1.8 0 0 0 6.3 21h11.4a1.8 1.8 0 0 0 1.5-2.7L14 9.5V3"/><path d="M7.5 15h9"/>',
    "market": '<path d="M4 20V4M4 20h16"/><path d="M7.5 15l3.5-4 3 2.5 5-6.5"/>',
    "people": '<circle cx="9" cy="8.5" r="3.2"/><path d="M3.5 19.5c.6-3.2 2.8-5 5.5-5s4.9 1.8 5.5 5"/><path d="M15.5 5.6a3.2 3.2 0 0 1 0 6M17 14.8c1.9.6 3.1 2.2 3.5 4.7"/>',
    "progress": '<path d="M4 20h16"/><path d="M7 16v-4M12 16V8M17 16V5"/>',
    "tools": '<path d="M4 7h10M18 7h2M4 17h4M12 17h8"/><circle cx="16" cy="7" r="2"/><circle cx="10" cy="17" r="2"/>',
    "file": '<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4M9 12h6M9 16h6"/>',
    "download": '<path d="M12 4v11M7 10l5 5 5-5M5 20h14"/>',
    "external": '<path d="M14 4h6v6M20 4l-9 9"/><path d="M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>',
    "dot": '<circle cx="12" cy="12" r="3"/>',
    "info": '<circle cx="12" cy="12" r="8.5"/><path d="M12 11v5M12 8h.01"/>',
    "candle": '<path d="M7 3v4M7 15v6M17 5v3M17 17v2"/><rect x="5" y="7" width="4" height="8" rx=".6"/><rect x="15" y="8" width="4" height="9" rx=".6"/>',
    "coin": '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="5.5"/><path d="M12 9.2v5.6"/>',
}

UNIVERSE_ICONS = {"trading": "candle", "monnaie": "coin"}

SPACE_ICONS = {"academy": "book", "library": "library", "psychology": "mind", "lab": "lab",
               "market": "market", "community": "people", "progress": "progress", "tools": "tools",
               "journal": "file"}


def icon(name: str) -> str:
    return (f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{_ICONS[name]}</svg>')


# ── Marks ────────────────────────────────────────────────────────────────────

_HEX = "24,2.5 42.6,13.25 42.6,34.75 24,45.5 5.4,34.75 5.4,13.25"


def hexmark(label: str, state: str = "todo") -> str:
    """Pointy-top hexagon, as in the monogram. States: todo current done locked final."""
    inner = (f'<path class="c" d="M16.5 24.5l5 5 10-10.5" fill="none" stroke-width="2.4" '
             f'stroke-linecap="round" stroke-linejoin="round"/>' if state == "done" else
             f'<text class="t" x="24" y="28.6" text-anchor="middle">{esc(label)}</text>')
    return (f'<svg class="sx-hex is-{state}" viewBox="0 0 48 48" aria-hidden="true">'
            f'<polygon class="h" points="{_HEX}"/>{inner}</svg>')


def pill(text: str, kind: str = "", icon_name: str | None = None) -> str:
    glyph = icon(icon_name) if icon_name else ""
    return f'<span class="sx-pill {kind}">{glyph}{esc(text)}</span>'


def universe_tag(universe: str, label: str) -> str:
    """The badge naming a universe: Trading in blue, Monnaie et crypto in copper."""
    return (f'<span class="sx-uni uni-{esc(universe)}">{icon(UNIVERSE_ICONS.get(universe, "dot"))}'
            f'{esc(label)}</span>')


def progress_bar(fraction: float, label: str = "") -> str:
    width = max(0.0, min(1.0, fraction)) * 100
    bar = (f'<div class="sx-progress" role="progressbar" aria-valuemin="0" aria-valuemax="100" '
           f'aria-valuenow="{width:.0f}"><i style="width:{width:.1f}%"></i></div>')
    return f'<div class="sx-progress-row">{bar}<span>{esc(label)}</span></div>' if label else bar


# ── Page furniture ───────────────────────────────────────────────────────────

def crumbs(*parts: str, universe: str = "") -> None:
    """`universe` marks the page as part of one; the stylesheet then recolours its main column."""
    items = '<i>/</i>'.join(f"<b>{esc(p)}</b>" if i == len(parts) - 1 else esc(p)
                            for i, p in enumerate(parts))
    scope = f'<span class="sx-scope uni-{esc(universe)}" hidden></span>' if universe else ""
    html(f'<nav class="sx-crumbs" aria-label="Fil d\'Ariane">{items}{scope}</nav>')


def carnet() -> None:
    """
    Opt the page into the « Carnet de bord » direction (prototype). The marker is
    invisible; the stylesheet applies the direction's tokens to the page under it.
    """
    html('<span class="sx-da" hidden></span>')


def page_header(kicker: str, title_html: str, lead: str = "", meta: list[str] | None = None,
                *, display: bool = False) -> None:
    """`title_html` may contain one <em> for the accent word; everything else is escaped."""
    meta_html = ('<div class="sx-meta">' + "".join(f"<span>{m}</span>" for m in meta) + "</div>"
                 if meta else "")
    lead_html = f'<p class="sx-lead">{esc(lead)}</p>' if lead else ""
    cls = "sx-display" if display else "sx-title"
    html(f'<div class="sx-kicker">{kicker}</div><h1 class="{cls}">{title_html}</h1>'
         f'{lead_html}{meta_html}')


def section(number: int, title: str, intro: str = "", *, compact: bool = False) -> None:
    intro_html = f"<p>{esc(intro)}</p>" if intro else "<p></p>"
    html(f'<div class="sx-section{" compact" if compact else ""}"><div><span class="num">§ '
         f'{number:02d}</span><h2>{esc(title)}</h2></div>{intro_html}</div>')


def note(text: str) -> None:
    html(f'<p class="sx-note">{esc(text)}</p>')


def notice(title: str, text: str, icon_name: str = "info") -> None:
    html(f'<div class="sx-notice">{icon(icon_name)}<div><b>{esc(title)}</b>'
         f'<p>{esc(text)}</p></div></div>')


def diagram(svg: str, caption: str, number: int | None = None) -> None:
    label = f"Figure {number}" if number else "Figure"
    html(f'<figure class="sx-diagram">{svg}<figcaption><b>{label}</b>'
         f'<span>{esc(caption)}</span></figcaption></figure>')


def footer() -> None:
    html(f'<footer class="sx-footer"><span class="m">{brand.monogram_svg(16, color="#0f1b26")}'
         f'SENSITOR</span><span class="c">CONTENU ÉDUCATIF · NE CONSTITUE PAS UN CONSEIL EN '
         f'INVESTISSEMENT</span><span>APPRENDRE AVEC MÉTHODE</span></footer>')
