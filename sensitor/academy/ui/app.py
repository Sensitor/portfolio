"""
The Academy app: sidebar, routing, and the content-error guard.
"""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from ..content import ContentError
from . import pages, theme
from . import runtime as rt
from .brand import logo_svg
from .components import esc, html

NAV = (
    ("home", "Vue d'ensemble"),
    ("paths", "Parcours"),
    ("library", "Bibliothèque"),
    ("lab", "Laboratoire de risque"),
    ("progress", "Progression"),
)
SECTION_OF = {"course": "paths", "lesson": "paths", "quiz": "paths"}


def _sidebar(current: str, email: str | None) -> None:
    active = SECTION_OF.get(current, current)
    with st.sidebar:
        html(f'<div class="ac-brand">{logo_svg(38, uid="side")}<div>'
             f'<div class="ac-brand-name">SENSITOR</div>'
             f'<div class="ac-brand-sub">ACADEMY</div></div></div>')
        html('<div class="ac-side-label">APPRENDRE</div>')
        for page, label in NAV:
            rt.link(label, page, key=f"nav_{page}",
                    kind="primary" if page == active else "secondary", width="stretch")
        html('<div class="ac-side-label">VOTRE ESPACE</div>')
        rt.link("Compte" if email else "Se connecter", "account", key="nav_account",
                kind="primary" if active == "account" else "secondary", width="stretch")
        who = (f"<b>{esc(email)}</b>Membre" if email
               else "<b>Visiteur</b>Deux leçons en accès libre")
        html(f'<div class="ac-side-user">{who}</div>'
             '<div class="ac-side-foot">Contenu éducatif. Ne constitue pas un conseil en '
             'investissement.</div>')


def _scroll_to_top() -> None:
    if st.session_state.pop("ac_scroll_top", False):
        components.html(
            "<script>const d=window.parent.document;"
            "const m=d.querySelector('[data-testid=\"stMain\"]');"
            "if(m){m.scrollTo(0,0);}window.parent.scrollTo(0,0);</script>",
            height=0)


def main() -> None:
    theme.inject()
    route = rt.route()
    page = route.get("page", "home")

    try:
        catalog = rt.catalog()
    except ContentError as exc:
        st.error("Le contenu de l'Academy contient des erreurs et ne peut pas être affiché.")
        st.code("\n".join(exc.problems))
        return

    email = rt.current_user()
    _sidebar(page, email)

    if page == "paths":
        pages.paths(catalog, email)
    elif page == "course":
        pages.course_page(catalog, email, route.get("course"))
    elif page == "lesson":
        pages.lesson_page(catalog, email, route.get("course"), route.get("lesson"))
    elif page == "quiz":
        pages.quiz_page(catalog, email, route.get("quiz"), route.get("course"))
    elif page == "library":
        pages.library(catalog, email)
    elif page == "lab":
        pages.lab(catalog, email)
    elif page == "progress":
        pages.progress_page(catalog, email)
    elif page == "account":
        pages.account(catalog, email)
    else:
        pages.home(catalog, email)

    _scroll_to_top()
