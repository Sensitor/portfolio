"""
The accompaniment: the accompanied member's space, the coaches' queue of
requests, and the administrator's cohorts and workshops.

Pages: `accompagnement` (member), `coach_support` (coach), `admin_cohorts`
(administrator). Every read and write goes through a `Store` method that
checks membership or role in its own SQL; the checks here only decide what to
draw. The logic of the forms is `platform.cohorts` and `platform.support`.
"""

from __future__ import annotations

import datetime as _dt

import streamlit as st

from ...core import permissions as P
from ...database.connection import now as _now
from ...trading import coaching as C
from .. import cohorts as K
from .. import support as S
from . import runtime as rt
from .components import crumbs, date_fr, esc, footer, html, note, notice, page_header, section

SELECTED_COHORT = "acc_selected_cohort"


def _month_start() -> str:
    return C.month_start()


def _place(place: str) -> str:
    if not place:
        return "Lieu communiqué avant l'atelier"
    if place.startswith("https://"):
        return f'<a href="{esc(place)}" target="_blank" rel="noopener">Rejoindre l\'atelier</a>'
    return esc(place)


def _workshop_card(w: dict, *, with_place: bool) -> str:
    cancelled = w.get("status") == "cancelled"
    state = " · <b>annulé</b>" if cancelled else ""
    return (f'<div class="sx-c-blank"><div class="rub">{esc(K.when_label(w["starts_at"]))} · '
            f'{int(w["duration_minutes"])} min{state}</div><h3>{esc(w["title"])}</h3>'
            + (f'<p>{esc(w["summary"])}</p>' if w.get("summary") else "")
            + (f'<p>{_place(w.get("place") or "")}</p>' if with_place and not cancelled else "")
            + "</div>")


# ── The member ───────────────────────────────────────────────────────────────

def member_page(catalog, email, route) -> None:
    crumbs("Sensitor", "Accompagnement")
    page_header("Accompagnement", "Avancer <em>accompagné</em>.",
                "Les ateliers de votre cohorte et vos questions à l'équipe, sur votre méthode, votre plan et votre "
                "organisation.")
    store = rt.get_store()
    who = rt.member(email)
    if store is None or not email:
        notice("Réservé aux membres accompagnés", "Connectez-vous pour retrouver votre cohorte.", "lock")
        footer()
        return
    cohorts = store.my_cohorts(email)
    if not P.can(who, "cohort.read"):
        if cohorts:
            notice("Accès Premium requis", "Vous êtes inscrit dans une cohorte, mais votre accès Premium n'est pas "
                   "actif : les ateliers s'afficheront dès qu'il le sera.", "lock")
        else:
            notice("Réservé aux membres accompagnés", "L'accompagnement réunit des membres Premium en cohorte, "
                   "autour d'ateliers réguliers. L'inscription se fait par l'équipe Sensitor ; il n'existe "
                   "aujourd'hui aucun abonnement payant.", "lock")
        footer()
        return

    html('<dl class="sx-facts" style="max-width:640px;margin-top:1.2rem">' + "".join(
        f'<div><dt>Cohorte</dt><dd>{esc(c["title"])}, depuis le {esc(date_fr(c["starts_on"]))}</dd></div>'
        for c in cohorts) + "</dl>")

    workshops = store.my_workshops(email)
    ahead, behind = K.upcoming(workshops, _now())
    section(1, "Les prochains ateliers", "Dans l'ordre. Le lien de connexion n'est visible que par votre cohorte.")
    if not ahead:
        note("Aucun atelier programmé pour l'instant.")
    for w in ahead:
        html(_workshop_card(w, with_place=True))
        if w.get("status") != "cancelled":
            st.download_button("Ajouter à mon agenda (.ics)", data=K.ics(w, w["cohort"]).encode("utf-8"),
                               file_name=f"atelier-{w['id']}.ics", mime="text/calendar", key=f"ics_{w['id']}")
    if behind:
        with st.expander(f"Ateliers passés ({len(behind)})"):
            for w in behind:
                html(_workshop_card(w, with_place=False))

    section(2, "Poser une question à l'équipe", S.FRAME)
    used, quota = store.count_support_requests(email, _month_start()), P.limit(who, "support.monthly_quota")
    note(f"{used} demande{'s' if used > 1 else ''} ce mois-ci sur {quota}.")
    if used < quota:
        with st.form("support_form", clear_on_submit=True):
            topic = st.selectbox("Thème", list(S.TOPICS), format_func=S.TOPICS.get, key="support_topic")
            question = st.text_area("Votre question", max_chars=S.MAX_QUESTION, height=160, key="support_question",
                                    placeholder="Le contexte, ce que vous avez essayé, ce qui coince.")
            if st.form_submit_button("Envoyer à l'équipe", type="primary"):
                try:
                    request = S.clean_request(topic, question)
                except S.SupportError as exc:
                    st.error(str(exc))
                else:
                    if store.create_support_request(email, request) is None:
                        st.error("La demande a été refusée : l'accompagnement n'est pas actif sur ce compte.")
                    else:
                        st.success("Demande envoyée. La réponse s'affichera ici.")

    section(3, "Vos demandes", "Les plus récentes d'abord.")
    mine = store.support_requests(email)
    if not mine:
        note("Aucune demande pour l'instant.")
    for r in mine:
        answered = r["status"] == "answered"
        html(f'<div class="sx-c-blank"><div class="rub">{esc(S.TOPICS.get(r["topic"], r["topic"]))} · '
             f'{esc(date_fr(r["created_at"]))} · {"répondu le " + esc(date_fr(r["answered_at"])) if answered else "en attente"}'
             f'</div><p>{esc(r["question"])}</p>'
             + (f'<p><b>Réponse de l\'équipe</b><br>{esc(r["answer"])}</p>' if answered else "") + "</div>")
        if answered and not r.get("seen_at"):
            store.mark_support_seen(email, r["id"])
    footer()


# ── The coach ────────────────────────────────────────────────────────────────

def coach_page(catalog, email, route) -> None:
    crumbs("Sensitor", "Coaching", "Demandes d'accompagnement")
    page_header("Coaching · réservé à l'équipe", "Les questions des <em>membres accompagnés</em>.",
                "Une question sur la méthode, le plan ou l'organisation, sous un pseudonyme.")
    store = rt.get_store()
    if store is None or not rt.can(email, "support.answer"):
        notice("Accès réservé", "Cette page est réservée aux coachs de Sensitor.", "lock")
        footer()
        return
    note(S.COACH_FRAME)
    pending = store.support_queue(email, "pending")
    section(1, "En attente", f"{len(pending)} demande{'s' if len(pending) > 1 else ''}, la plus ancienne d'abord.")
    if not pending:
        note("Aucune demande en attente.")
    for r in pending:
        html(f'<div class="sx-c-blank"><div class="rub">{esc(C.pseudonym(r["user_email"]))} · '
             f'{esc(S.TOPICS.get(r["topic"], r["topic"]))} · {esc(date_fr(r["created_at"]))}</div>'
             f'<p>{esc(r["question"])}</p></div>')
        with st.form(f"support_answer_{r['id']}"):
            answer = st.text_area("Votre réponse", max_chars=S.MAX_ANSWER, height=160, key=f"support_ans_{r['id']}")
            if st.form_submit_button("Répondre", type="primary"):
                try:
                    text = S.clean_answer(answer)
                except S.SupportError as exc:
                    st.error(str(exc))
                else:
                    if store.answer_support(email, r["id"], text):
                        st.rerun()
                    st.error("Cette demande a déjà reçu une réponse.")
    answered = store.support_queue(email, "answered", limit=30)
    if answered:
        with st.expander(f"Dernières réponses ({len(answered)})"):
            for r in answered:
                html(f'<div class="sx-c-blank"><div class="rub">{esc(C.pseudonym(r["user_email"]))} · '
                     f'{esc(date_fr(r["answered_at"]))}</div><p>{esc(r["question"])}</p>'
                     f'<p><b>Réponse</b><br>{esc(r["answer"])}</p></div>')
    footer()


# ── The administrator ────────────────────────────────────────────────────────

def admin_page(catalog, email, route) -> None:
    crumbs("Sensitor", "Gestion", "Cohortes et ateliers")
    page_header("Gestion · réservé aux administrateurs", "Les cohortes et <em>leurs ateliers</em>.",
                "Créer une cohorte, y inscrire des membres Premium, programmer ses ateliers.")
    store = rt.get_store()
    if store is None or not rt.can(email, "cohort.manage"):
        notice("Accès réservé", "Cette page est réservée aux administrateurs de Sensitor.", "lock")
        footer()
        return

    section(1, "Nouvelle cohorte", "Un groupe de membres accompagnés, avec une date de début.")
    with st.form("cohort_new", clear_on_submit=True):
        title = st.text_input("Titre", key="cohort_title", placeholder="Cohorte de janvier 2027")
        summary = st.text_area("Résumé (facultatif)", key="cohort_summary", height=90)
        c1, c2 = st.columns(2)
        starts = c1.date_input("Début", value=_dt.date.today(), key="cohort_start", format="DD/MM/YYYY")
        ends = c2.date_input("Fin (facultative)", value=None, key="cohort_end", format="DD/MM/YYYY")
        if st.form_submit_button("Créer la cohorte", type="primary"):
            try:
                created = store.create_cohort(email, K.clean_cohort(title, summary, starts, ends))
            except K.CohortError as exc:
                st.error(str(exc))
            else:
                st.session_state[SELECTED_COHORT] = created
                st.success("Cohorte créée.")

    cohorts = store.admin_cohorts(email) or []
    if not cohorts:
        note("Aucune cohorte pour l'instant.")
        footer()
        return
    ids = [c["id"] for c in cohorts]
    labels = {c["id"]: f'{c["title"]} · {"ouverte" if c["status"] == "open" else "close"} · {c["members"]} membre(s)'
              for c in cohorts}
    current = st.session_state.get(SELECTED_COHORT)
    chosen = st.selectbox("Cohorte", ids, format_func=labels.get, key="cohort_pick",
                          index=ids.index(current) if current in ids else 0)
    st.session_state[SELECTED_COHORT] = chosen
    cohort = next(c for c in cohorts if c["id"] == chosen)

    section(2, cohort["title"], "Les membres et leur accès.")
    if st.button("Clore la cohorte" if cohort["status"] == "open" else "Rouvrir la cohorte", key="cohort_status"):
        data = {k: cohort[k] for k in ("title", "summary", "starts_on", "ends_on")}
        store.update_cohort(email, chosen, data, status="closed" if cohort["status"] == "open" else "open")
        st.rerun()
    roster = store.cohort_roster(email, chosen) or []
    for m in roster:
        cols = st.columns([3, 1])
        with cols[0]:
            html(f'<div class="sx-c-row" style="grid-template-columns:1fr"><div><div class="sym">{esc(m["email"])}</div>'
                 f'<div class="when">inscrit le {esc(date_fr(m["created_at"]))} · '
                 f'{"Premium actif" if m["premium"] else "<b>sans accès Premium</b> : ne voit pas les ateliers"}'
                 '</div></div></div>')
        with cols[1]:
            if st.button("Retirer", key=f"cohort_rm_{m['email']}"):
                store.remove_from_cohort(email, chosen, m["email"])
                st.rerun()
    with st.form("cohort_add", clear_on_submit=True):
        address = st.text_input("Inscrire un membre (adresse de son compte)", key="cohort_add_email")
        if st.form_submit_button("Inscrire"):
            if store.add_to_cohort(email, chosen, address):
                st.success("Membre inscrit.")
                st.rerun()
            st.error("Aucun compte pour cette adresse, ou déjà inscrit.")

    section(3, "Les ateliers", "Heure de Paris. Le lieu, souvent un lien de visio, n'est montré qu'à la cohorte.")
    for w in store.admin_workshops(email, chosen) or []:
        cols = st.columns([3, 1])
        with cols[0]:
            html(_workshop_card(w, with_place=True))
        with cols[1]:
            cancelled = w["status"] == "cancelled"
            if st.button("Reprogrammer" if cancelled else "Annuler", key=f"ws_status_{w['id']}"):
                store.set_workshop_status(email, w["id"], "scheduled" if cancelled else "cancelled")
                st.rerun()
    with st.form("workshop_new", clear_on_submit=True):
        title = st.text_input("Titre de l'atelier", key="ws_title")
        summary = st.text_area("Programme (facultatif)", key="ws_summary", height=90)
        c1, c2, c3 = st.columns(3)
        day = c1.date_input("Date", value=_dt.date.today() + _dt.timedelta(days=7), key="ws_day", format="DD/MM/YYYY")
        time = c2.time_input("Heure (Paris)", value=_dt.time(19, 0), key="ws_time", step=900)
        duration = c3.selectbox("Durée", K.DURATIONS, index=K.DURATIONS.index(60), key="ws_duration",
                                format_func=lambda m: f"{m} min")
        place = st.text_input("Lieu ou lien de visio", key="ws_place", placeholder="https://…")
        if st.form_submit_button("Programmer l'atelier", type="primary"):
            try:
                saved = store.save_workshop(email, chosen, K.clean_workshop(title, summary, day, time, duration, place))
            except K.CohortError as exc:
                st.error(str(exc))
            else:
                if saved:
                    st.success("Atelier programmé.")
                    st.rerun()
                st.error("L'atelier a été refusé.")
    footer()


RENDERERS = {"accompagnement": member_page, "coach_support": coach_page, "admin_cohorts": admin_page}
