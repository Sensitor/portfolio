"""
The Library space: the list of resources and one page per resource.

Only resources whose file exists are in the catalogue (the loader refuses the
others), so every « Télécharger » here serves a real file.
"""

from __future__ import annotations

import streamlit as st

from ...platform.ui import runtime as rt
from ...platform.ui.components import (crumbs, esc, footer, hexmark, html, icon, md, note,
                                       page_header, pill, section, tap)
from .. import access
from ..content import Catalog, Resource


def _cover(resource: Resource, index: int, *, big: bool = False) -> str:
    alt = " alt" if index % 2 else ""
    return (f'<div class="sx-cover{alt}{" big" if big else ""}"><span class="ck">'
            f'{esc(resource.kind_label)}</span><span class="ct">{esc(resource.title)}</span>'
            f'<span class="ck">Sensitor</span></div>')


def _access_pill(resource: Resource) -> str:
    return pill("Libre", "free") if resource.access == "public" else pill("Membres", "member", "lock")


def book_row(resource: Resource, *, key: str, index: int = 0, compact: bool = False) -> None:
    summary = "" if compact else f'<div class="s">{esc(resource.description)}</div>'
    tap(key,
        f'<div class="sx-book">{_cover(resource, index)}<div><div class="sx-kicker muted">'
        f'{esc(resource.kind_label)} · {esc(resource.category)}</div><div class="t">'
        f'{esc(resource.title)}</div>{summary}<div style="margin-top:.6rem;display:flex;gap:.4rem">'
        f'{_access_pill(resource)}{pill("PDF", "") if resource.pdf else ""}</div></div><span class="arrow">{icon("arrow")}</span></div>',
        f"Ouvrir la ressource {resource.title}", "resource", resource=resource.id)


def library(catalog: Catalog, email: str | None, route: dict) -> None:
    crumbs("Sensitor", "Bibliothèque")
    page_header("Espace II · Bibliothèque", "Des ressources à garder <em>sous la main</em>.",
                "Fiches de révision et checklists, rédigées pour accompagner les parcours. Chaque "
                "document listé existe réellement et se télécharge.", display=True)
    resources = list(catalog.resources.values())
    if not resources:
        note("La bibliothèque est vide pour l'instant.")
        footer()
        return

    section(1, "Le fonds", f"{len(resources)} ressource{'s' if len(resources) > 1 else ''} publiée"
            f"{'s' if len(resources) > 1 else ''}. Les ebooks sont en préparation.")
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        query = st.text_input("Rechercher", placeholder="Un mot du titre ou de la description",
                              key="lib_query")
    with c2:
        categories = sorted({r.category for r in resources})
        category = st.selectbox("Thème", ["Tous les thèmes", *categories], key="lib_cat")
    with c3:
        kinds = sorted({r.kind_label for r in resources})
        kind = st.selectbox("Type", ["Tous les types", *kinds], key="lib_kind")

    needle = query.strip().lower()
    shown = 0
    for index, resource in enumerate(resources):
        if category != "Tous les thèmes" and resource.category != category:
            continue
        if kind != "Tous les types" and resource.kind_label != kind:
            continue
        if needle and needle not in f"{resource.title} {resource.description}".lower():
            continue
        book_row(resource, key=f"lib_{resource.id}", index=index)
        shown += 1
    if not shown:
        note("Aucune ressource ne correspond à cette recherche.")
    footer()


def resource_page(catalog: Catalog, email: str | None, route: dict) -> None:
    resource = catalog.resource(route.get("resource") or "")
    if resource is None:
        crumbs("Sensitor", "Bibliothèque", "Introuvable")
        page_header("Erreur 404", "Ressource <em>introuvable</em>",
                    "Cette ressource n'existe pas ou n'est plus publiée.")
        rt.link("Retour à la bibliothèque", "library", key="res_nf", kind="primary")
        footer()
        return
    index = list(catalog.resources).index(resource.id)
    crumbs("Sensitor", "Bibliothèque", resource.title)
    rt.link("← La bibliothèque", "library", key="res_back", kind="tertiary")
    left, right = st.columns([0.8, 1.7], gap="large")
    with left:
        html(_cover(resource, index, big=True))
        allowed = access.can_download(resource, email)
        html('<dl class="sx-facts" style="margin-top:2rem">'
             f'<div><dt>Type</dt><dd>{esc(resource.kind_label)}</dd></div>'
             f'<div><dt>Thème</dt><dd>{esc(resource.category)}</dd></div>'
             f'<div><dt>Accès</dt><dd>{"Libre" if resource.access == "public" else "Membres"}</dd></div>'
             f'<div><dt>Format</dt><dd>{"PDF et texte" if resource.pdf else "Texte (Markdown)"}</dd></div>'
             f'<div><dt>Auteur</dt><dd>{esc(resource.author)}</dd></div></dl>')
        if allowed:
            if resource.pdf:
                st.download_button("Télécharger le PDF", data=resource.read_pdf(),
                                   file_name=resource.pdf_name, mime="application/pdf",
                                   key=f"dl_pdf_{resource.id}", type="primary", width="stretch")
            st.download_button("Version texte (.md)" if resource.pdf else "Télécharger",
                               data=resource.read_text().encode("utf-8"),
                               file_name=resource.filename, mime="text/markdown",
                               key=f"dl_{resource.id}", type="secondary" if resource.pdf else "primary",
                               width="stretch")
        else:
            rt.link("Se connecter pour télécharger", "account", key=f"dl_lock_{resource.id}",
                    kind="primary", width="stretch")
    with right:
        page_header(f"{esc(resource.kind_label)} · {esc(resource.category)}", esc(resource.title),
                    resource.description)
        lessons = [catalog.find_lesson(l) for l in resource.lessons]
        lessons = [l for l in lessons if l]
        if lessons:
            html('<div class="sx-kicker muted" style="margin:2rem 0 .3rem">Leçons qui utilisent '
                 'cette ressource</div>')
            for lesson in lessons:
                tap(f"res_lesson_{resource.id}_{lesson.id}",
                    f'<div class="sx-lesson flush">{hexmark(f"{lesson.number:02d}")}<div>'
                    f'<div class="title">{esc(lesson.title)}</div><div class="summary">'
                    f'{esc(lesson.summary)}</div></div><div class="side"></div>'
                    f'<span class="arrow">{icon("arrow")}</span></div>',
                    f"Leçon : {lesson.title}", "lesson", course=lesson.course_id, lesson=lesson.id)

    section(1, "Le document", "Lisible ici, identique au fichier téléchargé.")
    if allowed:
        with st.container(key=f"doc_{resource.id}"):
            md(resource.read_text())
    else:
        with st.container(key="navy_res_locked"):
            html('<div class="sx-kicker on-navy">Réservé aux membres</div><h2 class="sx-h3 on-navy">'
                 'Créez un compte gratuit pour lire et télécharger ce document.</h2>')
            rt.link("Se connecter ou créer un compte", "account", key="res_unlock", kind="primary")
    footer()
