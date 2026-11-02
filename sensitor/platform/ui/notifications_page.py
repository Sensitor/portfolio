"""
The member's notifications (`?page=notifications`): what happened for them
(a reply in a discussion they joined, an answer to a review or a request, a
moderation decision, a workshop of their cohort), the trading room's sessions
published since they last looked, and the public site's new articles.

Read here, and marked read when the page is shown. No e-mail is sent: the
platform has no scheduler, and a digest by e-mail would need one.
"""

from __future__ import annotations

import os
from functools import lru_cache

import streamlit as st

from ...core import permissions as P
from .. import market as M
from . import runtime as rt
from .components import crumbs, date_fr, esc, footer, html, note, notice, page_header, section, tap

KINDS = {"reply": "Communauté", "review": "Revue de trade", "support": "Accompagnement", "moderation": "Modération",
         "workshop": "Atelier"}


def readable(who) -> tuple[str, ...]:
    return tuple(a for a in M.ACCESS if P.can_read(who, a))


@lru_cache(maxsize=1)
def _articles() -> tuple:
    """The public site's published articles, read once per process: they are files, the same for everyone."""
    from ...site import articles
    try:
        return tuple(articles.published())
    except ValueError:
        return ()


def new_articles(since: str) -> list:
    if not os.getenv("SENSITOR_SITE_URL", "").strip():
        return []
    return [a for a in _articles() if a.date.isoformat() > since[:10]]


def unread(email: str | None) -> int:
    """The sidebar's count, from one query."""
    store = rt.get_store()
    if not email or store is None:
        return 0
    state = store.notification_state(email, readable(rt.member(email)))
    return state["mine"] + state["sessions"] + len(new_articles(state["since"]))


def render(catalog, email, route) -> None:
    crumbs("Sensitor", "Notifications")
    page_header("Compte", "Vos <em>notifications</em>.", "Ce qui s'est passé pour vous depuis votre dernière visite.")
    store = rt.get_store()
    if store is None or not email:
        notice("Réservé aux membres", "Connectez-vous pour voir vos notifications.", "lock")
        footer()
        return
    who = rt.member(email)
    state = store.notification_state(email, readable(who))
    since = state["since"]

    sessions = [s for s in store.market_sessions(limit=20)
                if (s.get("published_at") or "") > since and P.can_read(who, s["access"])]
    articles = new_articles(since)
    mine = store.notifications(email)

    section(1, "Nouveautés", "Les séances et les articles publiés depuis votre dernière visite.")
    if not sessions and not articles:
        note("Rien de nouveau dans la salle des marchés ni sur le site.")
    for s in sessions:
        tap(f"notif_session_{s['id']}",
            f'<div class="sx-c-row"><div><div class="sym">{esc(s["title"])}</div><div class="when">Salle des '
            f'marchés · {esc(M.date_label(s["session_date"]))}</div></div><div class="q"></div><div></div>'
            f'<div class="r"></div><span class="go">›</span></div>',
            f"Ouvrir la séance {s['title']}", "market_session", session=str(s["id"]))
    base = os.getenv("SENSITOR_SITE_URL", "").strip().rstrip("/")
    for a in articles:
        html(f'<div class="sx-c-row"><div><div class="sym"><a href="{esc(base)}/articles/{esc(a.slug)}/" '
             f'target="_blank" rel="noopener">{esc(a.title)}</a></div><div class="when">Article · '
             f'{esc(date_fr(a.date.isoformat()))}</div></div></div>')

    section(2, "Pour vous", "Les plus récentes d'abord.")
    if not mine:
        note("Aucune notification pour l'instant.")
    for n in mine:
        fresh = " · nouveau" if not n["read_at"] else ""
        tap(f"notif_{n['id']}",
            f'<div class="sx-c-row"><div><div class="sym">{esc(n["title"])}</div><div class="when">'
            f'{esc(KINDS.get(n["kind"], n["kind"]))} · {esc(date_fr(n["created_at"]))}{fresh}</div></div>'
            f'<div class="q"></div><div></div><div class="r"></div><span class="go">›</span></div>',
            n["title"], n["page"] or "home", **{k: str(v) for k, v in n["fields"].items()})
    store.mark_notifications_read(email)
    footer()
