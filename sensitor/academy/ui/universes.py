"""
The two universes of the Academy, side by side: Trading, and Monnaie et crypto.

They are presented as one programme in two halves that complete each other:
the first teaches how to act on a market, the second why money and markets
move and how to keep what one has built. Counts come from the catalogue; a
universe with no open course says so instead of linking anywhere.
"""

from __future__ import annotations

import streamlit as st

from ...platform.ui.components import UNIVERSE_ICONS, esc, html, icon, numeral, tap
from ..content import MONNAIE, TRADING, UNIVERSES, Catalog, Course

PITCH = {
    TRADING: ("Lire un marché, décider avec méthode.",
              "La méthode du trader, de la première bougie au processus discipliné : structure, "
              "liquidité, zones, gestion du risque, psychologie et backtesting.",
              ("Price action", "Risque", "Psychologie", "Backtesting")),
    MONNAIE: ("Comprendre la monnaie, diversifier avec la crypto.",
              "Ce qui fait la valeur de l'argent, puis Bitcoin et la crypto : création monétaire, "
              "inflation, rendement réel et diversification, pour préserver un patrimoine dans le temps.",
              ("Monnaie", "Inflation", "Patrimoine", "Bitcoin")),
}

JOIN = ("<b>Deux savoirs qui se complètent.</b> Le trading apprend à agir sur les marchés ; la monnaie "
        "explique pourquoi ils bougent, et comment diversifier ce que l'on construit.")


def path_mark(catalog: Catalog, path) -> str:
    """A path's number on its card: I, II in Trading; M1, M2 in Monnaie et crypto, whose
    title face has no serif to tell a roman I from a plain bar."""
    track = catalog.track(path.track) if path else None
    if track and track.universe == MONNAIE:
        return f"{track.code}{path.number}"
    return numeral(path.number if path else 1)


def chapter_mark(number: int, universe: str) -> str:
    return f"{number:02d}" if universe == MONNAIE else f"{numeral(number)}."


def courses_in(catalog: Catalog, universe: str) -> list[Course]:
    return [c for c in catalog.available_courses() if catalog.universe_of(c) == universe]


def cards(catalog: Catalog, *, key: str) -> None:
    columns = st.columns(len(UNIVERSES), gap="medium")
    for column, (universe, label) in zip(columns, UNIVERSES.items()):
        title, text, topics = PITCH[universe]
        courses = courses_in(catalog, universe)
        lessons = sum(len(c.lessons) for c in courses)
        chips = "".join(f"<span>{esc(t)}</span>" for t in topics)
        if courses:
            count = (f"<span><b>{len(courses)}</b> cours ouvert{'s' if len(courses) > 1 else ''} · "
                     f"<b>{lessons}</b> leçons</span>")
            go = f'<span class="go">Commencer {icon("arrow")}</span>'
        else:
            count, go = "<span>En préparation</span>", ""
        body = (f'<div class="sx-ucard uni-{universe}"><div class="top">'
                f'{icon(UNIVERSE_ICONS[universe])}<span class="sx-uni uni-{universe}">'
                f'{esc(label)}</span></div><div class="t">{esc(title)}</div><div class="s">{esc(text)}</div>'
                f'<div class="topics">{chips}</div><div class="foot">{count}{go}</div></div>')
        with column:
            if courses:
                tap(f"{key}_{universe}", body, f"Commencer l'univers {label} : {courses[0].title}",
                    "course", course=courses[0].id)
            else:
                html(body)
    html(f'<p class="sx-ujoin">{JOIN}</p>')


def head(universe: str, detail: str, *, first: bool = False) -> None:
    """The heading that opens the part of a list belonging to one universe."""
    html(f'<div class="sx-uhead uni-{universe}{" first" if first else ""}">{icon(UNIVERSE_ICONS[universe])}'
         f'<b>{esc(UNIVERSES[universe])}</b><span>{esc(detail)}</span></div>')
