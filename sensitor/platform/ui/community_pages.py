"""
The community's pages: the discussions (`community`), one discussion
(`community_thread`), and the administrator's moderation queue
(`admin_moderation`).

Signed-in members read and write; a visitor sees the charter and is asked to
sign in. Every message can be reported. The rules are `platform.community`;
every read and write is a `Store` method, moderation checked in its SQL.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import streamlit as st

from ...core import mailer
from ...core import permissions as P
from .. import community as C
from . import runtime as rt
from .components import crumbs, date_fr, esc, footer, html, note, notice, page_header, section, tap

THEME_ALL = "tout"


def _day_ago() -> str:
    return (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(timespec="seconds")


def _charter() -> None:
    rows = "".join(f'<div><span class="n">{i:02d}</span><span class="x"><b>{esc(t)}</b><br>'
                   f'<span style="color:var(--muted);font-size:14px">{esc(x)}</span></span></div>'
                   for i, (t, x) in enumerate(C.CHARTER, start=1))
    html(f'<div class="sx-objectives single">{rows}</div>')


def _may_post(store, email: str) -> str | None:
    """None when the member may write now; otherwise why not, in French."""
    who = rt.member(email)
    if not P.can(who, "community.post"):
        return "Connectez-vous pour écrire."
    if mailer.configured() and not (store.get_user(email) or {}).get("email_verified_at"):
        return "Vérifiez votre adresse (lien reçu par e-mail, ou depuis la page Compte) pour écrire."
    if store.count_community_posts(email, _day_ago()) >= P.limit(who, "community.daily_posts"):
        return "Vous avez atteint le nombre de messages du jour. Revenez demain."
    return None


def index(catalog, email, route) -> None:
    crumbs("Sensitor", "Communauté")
    page_header("Espace IX · Communauté", "Apprendre <em>ensemble</em>.",
                "Questions, analyses partagées et retours d'expérience, entre membres. Une analyse dit ce qui "
                "l'invaliderait ; personne ne dit quoi acheter.")
    store = rt.get_store()
    if store is None or not rt.can(email, "community.read"):
        section(1, "La charte", "Cinq règles, pour une communauté qui apprend.")
        _charter()
        notice("Réservé aux membres", "Créez un compte gratuit ou connectez-vous pour lire et écrire.", "lock")
        rt.link("Se connecter ou créer un compte", "account", key="community_sign_in", kind="primary")
        footer()
        return

    themes = [THEME_ALL, *C.THEMES]
    current = route.get("theme") if route.get("theme") in C.THEMES else THEME_ALL
    chosen = st.selectbox("Thème", themes, index=themes.index(current), key="community_theme",
                          format_func=lambda t: "Tous les thèmes" if t == THEME_ALL else C.THEMES[t])
    theme = None if chosen in (None, THEME_ALL) else chosen
    threads = store.community_threads(email, theme=theme)
    section(1, "Les discussions", "Les plus actives d'abord.")
    if not threads:
        note("Aucune discussion pour l'instant dans ce thème. Lancez la première.")
    for t in threads:
        lock = " · fermée" if t["locked"] else ""
        tap(f"community_thread_{t['id']}",
            f'<div class="sx-c-row"><div><div class="sym">{esc(t["title"])}</div>'
            f'<div class="when">{esc(C.THEMES.get(t["theme"], t["theme"]))} · {esc(t["author"])}{lock}</div></div>'
            f'<div class="q">{t["posts"]} message{"s" if t["posts"] > 1 else ""}'
            f'<span class="wait">{esc(date_fr(t["last_post_at"]))}</span></div><div></div><div class="r"></div>'
            f'<span class="go">›</span></div>',
            f"Ouvrir la discussion {t['title']}", "community_thread", thread=str(t["id"]))

    section(2, "Lancer une discussion", "Un titre clair, puis votre question ou votre analyse.")
    blocked = _may_post(store, email)
    if blocked:
        note(blocked)
    else:
        courses = {"": "Aucun cours en particulier", **{c.id: c.title for c in catalog.available_courses()}}
        with st.form("community_new", clear_on_submit=True):
            new_theme = st.selectbox("Thème", list(C.THEMES), format_func=C.THEMES.get, key="community_new_theme",
                                     index=list(C.THEMES).index(theme) if theme else 0)
            course = st.selectbox("Cours lié (facultatif)", list(courses), format_func=courses.get,
                                  key="community_new_course")
            title = st.text_input("Titre", max_chars=C.MAX_TITLE, key="community_new_title")
            body = st.text_area("Message", max_chars=C.MAX_BODY, height=180, key="community_new_body")
            if st.form_submit_button("Publier", type="primary"):
                try:
                    thread = C.clean_thread(new_theme, title, body)
                except C.CommunityError as exc:
                    st.error(str(exc))
                else:
                    created = store.create_thread(email, thread, course_id=course or None)
                    if created:
                        rt.go("community_thread", thread=str(created))
                        st.rerun()
                    st.error("La discussion n'a pas pu être créée.")
    section(3, "La charte", "Elle vaut pour chaque message ; un message qui l'enfreint peut être signalé.")
    _charter()
    footer()


def thread_page(catalog, email, route) -> None:
    store = rt.get_store()
    crumbs("Sensitor", "Communauté", "Discussion")
    if store is None or not rt.can(email, "community.read"):
        page_header("Communauté", "Discussion réservée <em>aux membres</em>.", "")
        rt.link("Se connecter", "account", key="thread_sign_in", kind="primary")
        footer()
        return
    try:
        thread = store.community_thread(email, int(route.get("thread", "")))
    except ValueError:
        thread = None
    if thread is None:
        page_header("Communauté", "Discussion <em>introuvable</em>.", "")
        rt.link("Revenir à la communauté", "community", key="thread_back", kind="primary")
        footer()
        return
    course = catalog.course(thread["course_id"]) if thread["course_id"] else None
    meta = [C.THEMES.get(thread["theme"], thread["theme"]), f"lancée par {thread['author']}",
            date_fr(thread["created_at"])] + ([f"cours : {course.title}"] if course else [])
    page_header("Communauté · " + " · ".join(meta[:1]), esc(thread["title"]), " · ".join(meta[1:]))
    rt.link("← Toutes les discussions", "community", key="thread_all", kind="tertiary")
    admin = rt.can(email, "community.moderate")

    for post in thread["posts"]:
        if post["deleted"]:
            html('<div class="sx-c-blank"><p><i>Message supprimé par son auteur.</i></p></div>')
            continue
        if post["hidden"]:
            reason = f" Motif : {esc(post['hidden_reason'])}." if post.get("hidden_reason") else ""
            html(f'<div class="sx-c-blank"><p><i>Message masqué par la modération.{reason}</i></p>'
                 + (f'<p style="color:var(--muted)">{esc(post["body"])}</p>' if post["mine"] and post["body"] else "")
                 + "</div>")
            continue
        edited = " · modifié" if post["edited_at"] else ""
        html(f'<div class="sx-c-blank"><div class="rub">{esc(post["author"])} · {esc(date_fr(post["created_at"]))}'
             f'{edited}</div><p style="white-space:pre-wrap">{esc(post["body"])}</p></div>')
        cols = st.columns([1, 1, 4])
        if post["mine"]:
            with cols[0]:
                if st.button("Supprimer", key=f"post_del_{post['id']}", type="tertiary"):
                    store.delete_post(email, post["id"])
                    st.rerun()
            with cols[1].popover("Modifier"):
                with st.form(f"post_edit_{post['id']}"):
                    text = st.text_area("Message", value=post["body"], max_chars=C.MAX_BODY, key=f"pe_{post['id']}")
                    if st.form_submit_button("Enregistrer"):
                        try:
                            store.edit_post(email, post["id"], C.clean_post(text))
                        except C.CommunityError as exc:
                            st.error(str(exc))
                        else:
                            st.rerun()
        else:
            with cols[0].popover("Signaler"):
                with st.form(f"post_report_{post['id']}"):
                    reason = st.selectbox("Motif", list(C.REPORT_REASONS), format_func=C.REPORT_REASONS.get,
                                          key=f"pr_reason_{post['id']}")
                    details = st.text_area("Précisions (facultatif)", max_chars=C.MAX_DETAILS,
                                           key=f"pr_details_{post['id']}")
                    if st.form_submit_button("Envoyer le signalement"):
                        done = store.report_post(email, post["id"], C.clean_report(reason, details))
                        if done:
                            st.success("Signalement reçu. Un administrateur l'examine ; le message est masqué s'il "
                                       "enfreint la charte ou la loi.")
                        else:
                            st.info("Vous avez déjà signalé ce message.")

    if admin:
        if st.button("Rouvrir la discussion" if thread["locked"] else "Fermer la discussion", key="thread_lock"):
            store.lock_thread(email, thread["id"], not thread["locked"])
            st.rerun()
    if thread["locked"]:
        note("Cette discussion est fermée : on ne peut plus y répondre.")
    else:
        blocked = _may_post(store, email)
        if blocked:
            note(blocked)
        else:
            with st.form("thread_reply", clear_on_submit=True):
                body = st.text_area("Votre réponse", max_chars=C.MAX_BODY, height=140, key="thread_reply_body")
                if st.form_submit_button("Répondre", type="primary"):
                    try:
                        text = C.clean_post(body)
                    except C.CommunityError as exc:
                        st.error(str(exc))
                    else:
                        if store.reply(email, thread["id"], text) is None:
                            st.error("La réponse n'a pas pu être publiée.")
                        else:
                            st.rerun()
    footer()


def moderation_page(catalog, email, route) -> None:
    crumbs("Sensitor", "Gestion", "Modération")
    page_header("Gestion · réservé aux administrateurs", "Les <em>signalements</em>.",
                "Chaque signalement est examiné. Masquer un message laisse à son auteur le motif de la décision.")
    store = rt.get_store()
    if store is None or not rt.can(email, "community.moderate"):
        notice("Accès réservé", "Cette page est réservée aux administrateurs de Sensitor.", "lock")
        footer()
        return
    queue = store.moderation_queue(email) or []
    section(1, "À examiner", f"{len(queue)} signalement{'s' if len(queue) > 1 else ''}, le plus ancien d'abord.")
    if not queue:
        note("Aucun signalement en attente.")
    for r in queue:
        html(f'<div class="sx-c-blank"><div class="rub">{esc(C.REPORT_REASONS.get(r["reason"], r["reason"]))} · '
             f'{esc(date_fr(r["created_at"]))} · {esc(r["title"])} · {esc(r["author"])}</div>'
             f'<p style="white-space:pre-wrap">{esc(r["body"])}</p>'
             + (f'<p><b>Précisions</b> : {esc(r["details"])}</p>' if r["details"] else "") + "</div>")
        with st.form(f"moderate_{r['id']}"):
            note_text = st.text_input("Motif complémentaire, lu par l'auteur si le message est masqué (facultatif)",
                                      key=f"mod_note_{r['id']}")
            c1, c2, _ = st.columns([1, 1, 2])
            hide = c1.form_submit_button("Masquer le message", type="primary")
            dismiss = c2.form_submit_button("Classer sans suite")
            if hide or dismiss:
                store.moderate(email, r["id"], hide=hide, note=note_text)
                st.rerun()
        rt.link("Voir la discussion", "community_thread", key=f"mod_thread_{r['id']}", kind="tertiary",
                thread=str(r["thread_id"]))
    footer()


RENDERERS = {"community": index, "community_thread": thread_page, "admin_moderation": moderation_page}
