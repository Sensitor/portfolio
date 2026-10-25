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
from . import (account, home, market_room, portfolio_space, psychology, spaces_view, theme, trade_reviews,
               trading_journal)
from . import runtime as rt
from .components import edition, esc, html

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
    "market": market_room.room,
    "market_session": market_room.session_page,
    "market_edit": market_room.edit_page,
    "community": spaces_view.preparing,
    "portfolio": portfolio_space.RENDERERS["portfolio"],
    "pf_overview": portfolio_space.RENDERERS["pf_overview"],
    "pf_performance": portfolio_space.RENDERERS["pf_performance"],
    "pf_health": portfolio_space.RENDERERS["pf_health"],
    "pf_xray": portfolio_space.RENDERERS["pf_xray"],
    "pf_risk": portfolio_space.RENDERERS["pf_risk"],
    "pf_stress": portfolio_space.RENDERERS["pf_stress"],
    "pf_optimize": portfolio_space.RENDERERS["pf_optimize"],
    "pf_simulator": portfolio_space.RENDERERS["pf_simulator"],
    "pf_copilot": portfolio_space.RENDERERS["pf_copilot"],
    "pf_reports": portfolio_space.RENDERERS["pf_reports"],
    "pf_portfolios": portfolio_space.RENDERERS["pf_portfolios"],
    "journal": trading_journal.dashboard,
    "journal_trades": trading_journal.trades_page,
    "journal_trade": trading_journal.trade_page,
    "journal_add": trading_journal.add_page,
    "journal_plan": trading_journal.plan_page,
    "journal_reviews": trade_reviews.reviews_page,
    "coach": trade_reviews.coach_page,
}


def _free_lessons(catalog) -> int:
    return len(catalog.public_lessons())


def _sidebar(page: str, email: str | None, catalog) -> None:
    current = spaces.space_of(page)
    with st.sidebar:
        html(f'<div class="sx-brand">{brand.mark_svg(42, uid="side")}<div>'
             f'<div class="sx-brand-name">SENSITOR</div>'
             f'<div class="sx-brand-sub">TRADING · MONNAIE · CRYPTO</div></div></div>')
        rt.link("Vue d'ensemble", "home", key="nav_home",
                kind="primary" if page == "home" else "secondary", width="stretch")
        for label, members in spaces.by_group():
            html(f'<div class="sx-side-label">{esc(label.upper())}</div>')
            for space in members:
                prefix = {"preparing": "navprep", "separate": "navsep"}.get(space.status, "nav")
                active = current is not None and current.id == space.id
                rt.link(space.label, space.entry, key=f"{prefix}_{space.id}",
                        kind="primary" if active else "secondary", width="stretch")
        store = rt.get_store() if email else None
        if store is not None and store.is_coach(email):
            pending = len(store.coach_queue(email, "pending"))
            html('<div class="sx-side-label">COACHING</div>')
            rt.link(f"File de revue · {pending}" if pending else "File de revue", "coach", key="nav_coach",
                    kind="primary" if page == "coach" else "secondary", width="stretch")
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
    edition(spaces.edition_of(page))
    RENDERERS.get(page, home.render)(catalog, email, route)
    _scroll_to_top()
    rt.flush_cookie()
