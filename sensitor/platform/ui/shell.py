"""
The platform shell: brand, grouped navigation, routing.

The sidebar is built from `spaces.SPACES`, so a new space appears in it by being
declared there. Every page id resolves to exactly one renderer below; spaces in
preparation share one honest page template (`spaces_view.preparing`).
"""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from ...academy.content import ContentError
from ...academy.ui import pages as academy
from ...academy.ui import library as library_pages
from .. import brand, spaces
from . import account, home, psychology, spaces_view, theme
from . import runtime as rt
from .components import esc, html

RENDERERS = {
    "home": home.render,
    "account": account.render,
    "reset": account.reset_page,
    "verify": account.verify_page,
    "academy": academy.academy_home,
    "course": academy.course_page,
    "lesson": academy.lesson_page,
    "quiz": academy.quiz_page,
    "library": library_pages.library,
    "resource": library_pages.resource_page,
    "lab": academy.lab,
    "progress": academy.progress_page,
    "psychology": psychology.render,
    "market": spaces_view.preparing,
    "community": spaces_view.preparing,
    "tools": spaces_view.tools,
    "journal": spaces_view.journal,
}


def _free_lessons(catalog) -> int:
    return len(catalog.public_lessons())


def _sidebar(page: str, email: str | None, catalog) -> None:
    current = spaces.space_of(page)
    with st.sidebar:
        html(f'<div class="sx-brand">{brand.mark_svg(42, uid="side")}<div>'
             f'<div class="sx-brand-name">SENSITOR</div>'
             f'<div class="sx-brand-sub">TRADING · BITCOIN · CRYPTO</div></div></div>')
        rt.link("Vue d'ensemble", "home", key="nav_home",
                kind="primary" if page == "home" else "secondary", width="stretch")
        for label, members in spaces.by_group():
            html(f'<div class="sx-side-label">{esc(label.upper())}</div>')
            for space in members:
                prefix = {"preparing": "navprep", "separate": "navsep"}.get(space.status, "nav")
                active = current is not None and current.id == space.id
                rt.link(space.label, space.entry, key=f"{prefix}_{space.id}",
                        kind="primary" if active else "secondary", width="stretch")
        html('<div class="sx-side-label">COMPTE</div>')
        rt.link("Mon compte" if email else "Se connecter", "account", key="nav_account",
                kind="primary" if page == "account" else "secondary", width="stretch")
        who = (f"<b>{esc(email)}</b>Membre · un compte pour tous les espaces" if email
               else f"<b>Visiteur</b>{_free_lessons(catalog)} leçons en accès libre, sans compte")
        html(f'<div class="sx-side-user">{who}</div><div class="sx-side-foot">Contenu éducatif. '
             'Ne constitue pas un conseil en investissement.</div>')


def _scroll_to_top() -> None:
    if st.session_state.pop("ac_scroll_top", False):
        components.html(
            "<script>const d=window.parent.document;"
            "const m=d.querySelector('[data-testid=\"stMain\"]');"
            "if(m){m.scrollTo(0,0);}window.parent.scrollTo(0,0);</script>", height=0)


def main() -> None:
    theme.inject()
    route = rt.route()
    page = route["page"]

    try:
        catalog = rt.catalog()
    except ContentError as exc:
        st.error("Le contenu de l'Academy contient des erreurs et ne peut pas être affiché.")
        st.code("\n".join(exc.problems))
        rt.flush_cookie()
        return

    email = rt.current_user()
    _sidebar(page, email, catalog)
    RENDERERS.get(page, home.render)(catalog, email, route)
    _scroll_to_top()
    rt.flush_cookie()
