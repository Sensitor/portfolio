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


def _separate(space_id: str, title: str, intro: str, items: tuple[str, ...], page: str,
              button: str) -> None:
    """A space that lives in the analytics application, reachable by link when configured."""
    space = spaces.space(space_id)
    _header(space)
    url = rt.tools_url()
    html(f'<div style="margin-top:1.2rem">{pill(space.status_label, "sep", "external")}</div>')
    section(1, title, intro)
    rows = "".join(f'<li><span class="n">{i:02d}</span><span class="x">{esc(x)}</span><span></span></li>'
                   for i, x in enumerate(items, start=1))
    html(f'<ul class="sx-plan">{rows}</ul>')
    if url:
        st.link_button(button, f"{url.rstrip('/')}/?page={page}")
    else:
        notice("Lien non configuré",
               "L'adresse de l'application d'analyse n'est pas renseignée pour ce déploiement "
               "(variable SENSITOR_TOOLS_URL).", "info")
    footer()


def tools(catalog, email, route) -> None:
    _separate("tools", "Une application à part, pour l'instant",
              "L'analyse de portefeuille existe et fonctionne, dans une application distincte. Elle "
              "rejoindra cet espace membre dans une étape ultérieure.",
              ("Performance, allocation et contributions, avec Bitcoin et les cryptomonnaies parmi les "
               "actifs suivis.",
               "Risque : volatilité, drawdown, VaR, corrélations, concentration et diversification.",
               "Stress tests historiques, dont l'hiver crypto de 2022, et chocs personnalisés.",
               "Simulateur Monte Carlo et frontière efficiente.",
               "Les mêmes comptes : l'adresse et le mot de passe utilisés ici fonctionnent aussi là-bas."),
              "overview", "Ouvrir l'analyse de portefeuille")


def journal(catalog, email, route) -> None:
    _separate("journal", "Le journal du trader, dans l'application d'analyse",
              "Le journal de trading existe et fonctionne, dans la même application que le "
              "portefeuille. Il rejoindra cet espace membre dans une étape ultérieure.",
              ("Saisie des trades ou synchronisation MetaTrader 5, avec setups, émotions et discipline.",
               "Performance en R, espérance, profit factor, drawdown et séries.",
               "Analyse par setup, actif, session, jour et unité de temps.",
               "Risque, discipline et psychologie, puis revue hebdomadaire exportable.",
               "Les mêmes comptes : l'adresse et le mot de passe utilisés ici fonctionnent aussi là-bas."),
              "trading_overview", "Ouvrir le journal de trading")


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
                    f"{space.label}, {space.status_label.lower()}", space.entry)
