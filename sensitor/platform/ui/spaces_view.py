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
from .components import (SPACE_ICONS, crumbs, esc, footer, hexmark, html, icon, notice,
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


def tools(catalog, email, route) -> None:
    space = spaces.space("tools")
    _header(space)
    url = rt.tools_url()
    html(f'<div style="margin-top:1.2rem">{pill(space.status_label, "sep", "external")}</div>')
    section(1, "Une application à part, pour l'instant",
            "L'analyse de portefeuille et le journal de trading existent et fonctionnent, dans une "
            "application distincte. Ils rejoindront cet espace membre dans une étape ultérieure.")
    html('<ul class="sx-plan">'
         '<li><span class="n">01</span><span class="x">Analyse de portefeuille : performance, '
         'risque, allocation, scénarios historiques.</span><span></span></li>'
         '<li><span class="n">02</span><span class="x">Journal de trading : import MetaTrader 5 '
         'ou saisie, statistiques par setup et par session.</span><span></span></li>'
         '<li><span class="n">03</span><span class="x">Les mêmes comptes : l\'adresse et le mot '
         'de passe utilisés ici fonctionnent aussi là-bas.</span><span></span></li></ul>')
    if url:
        st.link_button("Ouvrir l'application d'analyse", url)
    else:
        notice("Lien non configuré",
               "L'adresse de l'application d'analyse n'est pas renseignée pour ce déploiement "
               "(variable SENSITOR_TOOLS_URL).", "info")
    footer()


def space_cards(*, key: str, exclude: tuple[str, ...] = ()) -> None:
    """The map of spaces, three per row, each one a link."""
    shown = [s for s in spaces.SPACES if s.id not in exclude]
    for start in range(0, len(shown), 3):
        cols = st.columns(3)
        for col, space in zip(cols, shown[start:start + 3]):
            kind = {"live": "live", "preparing": "soon", "separate": "sep"}[space.status]
            navy = " navy" if space.id == "academy" else ""
            with col:
                tap(f"{key}_{space.id}",
                    f'<div class="sx-space{navy}"><div class="top"><span class="numeral">'
                    f'{space.numeral}</span><span class="ic">{icon(SPACE_ICONS[space.id])}</span>'
                    f'</div><div class="t">{esc(space.label)}</div><div class="s">'
                    f'{esc(space.summary)}</div><div class="foot">'
                    f'{pill(space.status_label, "on-navy" if navy else kind)}{icon("arrow")}</div></div>',
                    f"{space.label} — {space.status_label}", space.entry)
