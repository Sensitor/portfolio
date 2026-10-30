"""
Pages for spaces that are not built here yet.

One template, deliberately plain about its status: what the space will contain,
what already exists that is related, and an explicit statement that nothing in
the space is active. No sample posts, no fake members, no placeholder numbers.
"""

from __future__ import annotations

import streamlit as st

from .. import spaces
from . import runtime as rt
from .components import (crumbs, esc, footer, hexmark, html, icon, notice,
                         page_header, pill, section, tap)


def _header(space: spaces.Space) -> None:
    crumbs("Sensitor", space.label)
    page_header(f"Espace {space.numeral} · {esc(space.status_label)}",
                esc(space.label), space.summary)


def preparing(catalog, email, route) -> None:
    space = spaces.space_of(route["page"])
    _header(space)
    html(f'<div style="margin-top:1.2rem">{pill(space.status_label, "soon", "clock")}</div>')
    notice("Cet espace n'est pas encore ouvert",
           "Aucune de ses fonctionnalités n'est active : cette page décrit ce qui est prévu. "
           "Il sera ouvert lorsque son contenu sera rédigé, relu et réellement utilisable.",
           "clock")

    section(1, "Ce qui est prévu", "Le programme annoncé pour cet espace, sans date promise.")
    items = "".join(f'<li><span class="n">{i:02d}</span><span class="x">{esc(p)}</span>'
                    f'{pill("Prévu", "soon")}</li>' for i, p in enumerate(space.planned, start=1))
    html(f'<ul class="sx-plan">{items}</ul>')

    if space.related:
        section(2, "Disponible aujourd'hui", "Ce qui existe déjà et prépare à cet espace.")
        for index, (label, target) in enumerate(space.related):
            page, fields = spaces.parse_target(target)
            tap(f"related_{space.id}_{index}",
                f'<div class="sx-lesson flush">{hexmark(f"{index + 1:02d}")}<div><div class="title">'
                f'{esc(label)}</div></div><div class="side"></div><span class="arrow">'
                f'{icon("arrow")}</span></div>', label, page, **fields)
    footer()


def space_cards(*, key: str, exclude: tuple[str, ...] = ()) -> None:
    """
    The map of spaces: one register, a line per space, each line a link. The
    status is said in words, in its role colour; no space is singled out.
    """
    shown = [s for s in spaces.SPACES if s.id not in exclude]
    for space in shown:
        kind = {"live": "live", "preparing": "soon", "separate": "sep"}[space.status]
        tap(f"{key}_{space.id}",
            f'<div class="sx-c-space"><span class="n">{space.numeral}</span>'
            f'<span class="t">{esc(space.label)}</span><span class="s">{esc(space.summary)}</span>'
            f'<span class="st {kind}">{esc(space.status_label)}</span>'
            f'<span class="go">{icon("arrow")}</span></div>',
            f"{space.label}, {space.status_label.lower()}", space.entry)
