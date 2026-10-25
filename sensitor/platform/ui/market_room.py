"""
The trading room (« Salle des marchés »): the sessions a coach prepares before
the open, and their review after the close.

Three pages: the room (the latest session, the earlier ones, the scenarios'
record), one session's sheet, and the coach's editor. Presentation only: every
rule of what a session may contain is in `platform.market`, every check of who
may write in the store, and who may read in `academy.access`.
"""

from __future__ import annotations

import datetime as _dt

import streamlit as st

from ...academy import access as A
from .. import brand, spaces
from .. import market as M
from . import runtime as rt
from . import trade_visuals as V
from .components import crumbs, esc, footer, html, icon, note, notice, page_header, pill, section, tap
from .trade_reviews import _lesson_choices
from .trading_journal import flash, lesson_ref, show_flash

LETTERS = "ABCD"
OUTCOME_MARK = {"joue": "in", "invalide": "out", "non-declenche": "na"}
DISCLAIMER = ("Analyse pédagogique publiée avant la séance : des scénarios conditionnels, chacun avec ce qui "
              "l'invalide. Ni signal, ni conseil personnalisé, ni recommandation d'achat ou de vente.")


def _space():
    return spaces.space("market")


def _header(title_html: str, lead: str, *, kicker: str = "") -> None:
    space = _space()
    page_header(kicker or f"Espace {space.numeral} · {esc(space.label)}", title_html, lead)


def _print(review: dict | None, count: int) -> str:
    """One square per scenario: played in ink, invalidated in brick and taller, not triggered outlined."""
    outcomes = [o.get("outcome") for o in (review or {}).get("outcomes", [])]
    cls = {"joue": "ok", "invalide": "fail", "non-declenche": "na"}
    marks = "".join(f'<i class="{cls.get(outcomes[i], "na") if i < len(outcomes) else "na"}"></i>'
                    for i in range(count))
    return f'<span class="sx-c-print">{marks}</span>'


def _lesson_title(catalog, target: str) -> str:
    page, fields = spaces.parse_target(target)
    course = catalog.course(fields.get("course", "")) if page == "lesson" else None
    lesson = next((l for l in course.lessons if l.id == fields.get("lesson")), None) if course else None
    return f"{course.title} · {lesson.title}" if lesson else target


def _lessons(catalog, targets: list[str], *, key: str, why: str) -> None:
    for i, target in enumerate(targets):
        if spaces.parse_target(target)[0] == "lesson":
            lesson_ref(f"{key}_{i}", target, _lesson_title(catalog, target), why)


# =============================================================================
# The room
# =============================================================================

def room(catalog, email, route) -> None:
    space = _space()
    crumbs("Sensitor", space.label)
    _header("Préparer la séance, <em>puis la relire</em>.",
            "Avant l'ouverture, le contexte, le calendrier et quelques scénarios, chacun avec ce qui "
            "l'invalide. Après la clôture, ce que chaque scénario a fait et ce que la séance enseigne.")
    show_flash()
    store = rt.get_store()
    coach = bool(email and store is not None and store.is_coach(email))
    sessions = store.market_sessions() if store is not None else []
    if coach:
        _coach_bar(store, email)

    if not sessions:
        html('<div class="sx-c-blank"><div class="rub">Aucune séance publiée pour l\'instant</div>'
             '<h3>Une séance se prépare en trois temps.</h3>'
             '<p>Les séances seront publiées ici par l\'équipe Sensitor, avec leur bilan. Rien n\'est inventé '
             'en attendant : ni séance d\'exemple, ni scénario fictif présenté comme une analyse.</p>'
             '<ol><li><b>Avant la séance</b>Le contexte de la semaine, le calendrier du jour, deux à quatre '
             'scénarios conditionnels et leur invalidation.</li>'
             '<li><b>Pendant</b>Le live, quand il y en a un, sur YouTube ou Vimeo, pour voir la lecture se '
             'faire.</li><li><b>Après</b>Ce que chaque scénario a fait, joué, invalidé ou non déclenché, et '
             'ce que la séance enseigne, avec les leçons qui l\'expliquent.</li></ol></div>')
        _further(space, start=1)
        footer()
        return

    latest, earlier = sessions[0], sessions[1:]
    section(1, "La dernière séance", "Publiée avant l'ouverture ; son bilan suit la clôture.")
    _session_card(latest, email, rt.tier(email), key="latest")
    if earlier:
        section(2, "Les séances précédentes", "Une ligne par séance, et l'issue de chaque scénario.")
        for s in earlier:
            _session_row(s, key="earlier")
    reviewed = [s["review"] for s in sessions if s.get("review")]
    if reviewed:
        t = M.tally(reviewed)
        section(3 if earlier else 2, "Le relevé des scénarios",
                "Une marque par scénario relu : joué, invalidé, non déclenché.")
        marks = [(OUTCOME_MARK[o["outcome"]], f"{s['title']} · {M.OUTCOMES[o['outcome']]}")
                 for s in reversed(sessions) if s.get("review") for o in s["review"]["outcomes"]]
        html(f'<p class="sx-c-summary"><b>{t.total} scénario{"s" if t.total > 1 else ""}</b> relu'
             f'{"s" if t.total > 1 else ""} : {t.played} joué{"s" if t.played > 1 else ""}, {t.invalidated} '
             f'invalidé{"s" if t.invalidated > 1 else ""}, {t.untriggered} non déclenché'
             f'{"s" if t.untriggered > 1 else ""}. <span>Un scénario invalidé n\'est pas une erreur : c\'est '
             'son invalidation qui a fait son travail.</span></p>')
        html(V.record(marks, max_width=520))
    _further(space, start=4 if earlier else 3)
    footer()


def _coach_bar(store, email: str) -> None:
    drafts = store.market_drafts(email)
    with st.container(key="panel_market_coach"):
        html('<div class="sx-kicker">Équipe · préparation</div>')
        rt.link("Préparer une séance", "market_edit", key="market_new", kind="primary")
        if drafts:
            html('<div class="sx-kicker" style="margin-top:1rem">Brouillons</div>')
            for d in drafts:
                tap(f"market_draft_{d['id']}",
                    f'<div class="sx-c-ref">{brand.hook_svg(15, color=V.K["note"])}<div><div class="t">'
                    f'{esc(d["title"])}</div><div class="s">Brouillon · {len(d["content"]["scenarios"])} '
                    f'scénario(s)</div></div><span class="go">{icon("arrow")}</span></div>',
                    f"Reprendre le brouillon {d['title']}", "market_edit", session=str(d["id"]))


def _session_card(s: dict, email, tier, *, key: str) -> None:
    locked = A.lock_reason(s["access"], email, tier)
    scenarios = s["content"]["scenarios"]
    lines = "".join(f'<li><b>Scénario {LETTERS[i]} · {esc(x["instrument"])}</b>{esc(x["title"])}</li>'
                    for i, x in enumerate(scenarios))
    state = "Bilan publié" if s.get("review") else "Bilan après la clôture"
    tap(f"market_{key}_{s['id']}",
        f'<div class="sx-c-blank"><div class="rub">{esc(M.date_label(s["session_date"]))} · '
        f'{esc(M.ACCESS_LABELS[s["access"]])} · {state}</div><h3>{esc(s["title"])}</h3>'
        f'<p>{esc(_excerpt(s["content"]["context"]))}</p>'
        + ('' if locked else f'<ol>{lines}</ol>')
        + '</div>',
        f"Ouvrir la séance {s['title']}", "market_session", session=str(s["id"]))


def _session_row(s: dict, *, key: str) -> None:
    n = len(s["content"]["scenarios"])
    tap(f"market_{key}_{s['id']}",
        f'<div class="sx-c-row"><div><div class="sym">{esc(s["title"])}</div>'
        f'<div class="when">{esc(s["session_date"])}</div></div>'
        f'<div class="q">{esc(_excerpt(s["content"]["context"], 110))}'
        f'<span class="wait">{"Bilan publié" if s.get("review") else "En attente du bilan"}</span></div>'
        f'<div>{_print(s.get("review"), n)}</div><div class="r">{n} scén.</div>'
        f'<span class="go">{icon("arrow")}</span></div>',
        f"Ouvrir la séance {s['title']}", "market_session", session=str(s["id"]))


def _excerpt(text: str, limit: int = 220) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + "…"


def _further(space, *, start: int) -> None:
    if not space.related:
        return
    section(start, "Pour préparer ses propres séances", "Les leçons qui expliquent ce que la salle utilise.")
    for index, (label, target) in enumerate(space.related):
        lesson_ref(f"market_rel_{index}", target, label, "Academy")


# =============================================================================
# One session
# =============================================================================

def session_page(catalog, email, route) -> None:
    space = _space()
    store = rt.get_store()
    coach = bool(email and store is not None and store.is_coach(email))
    try:
        s = store.market_session(int(route.get("session", "")), coach=email if coach else None) if store else None
    except ValueError:
        s = None
    crumbs("Sensitor", space.label, "Séance")
    if s is None:
        _header("Séance introuvable.", "Elle n'existe pas, ou n'est pas encore publiée.")
        rt.link("Revenir à la Salle des marchés", "market", key="market_back")
        footer()
        return
    reason = A.lock_reason(s["access"], email, rt.tier(email))
    content, review = s["content"], s.get("review")
    n = len(content["scenarios"])
    lead = (f"{n} scénario{'s' if n > 1 else ''}, chacun avec son invalidation. "
            + ("Le bilan est publié." if review else "Le bilan suivra la clôture."))
    _header(esc(s["title"]), lead,
            kicker=f"{esc(M.date_label(s['session_date']))} · {esc(M.ACCESS_LABELS[s['access']])}"
                   + (" · brouillon" if s["status"] == "draft" else ""))
    show_flash()
    if coach:
        rt.link("Modifier la séance", "market_edit", key="market_edit_link", session=str(s["id"]))
    if reason:
        notice("Séance réservée aux membres" if reason == A.SIGN_IN else "Séance Premium",
               "Créez un compte gratuit ou connectez-vous pour lire la séance et son bilan."
               if reason == A.SIGN_IN else "Cette séance fait partie de l'offre Premium.", "lock")
        if reason == A.SIGN_IN:
            rt.link("Se connecter ou créer un compte", "account", key="market_signin", kind="primary")
        footer()
        return

    html(f'<div class="sx-j-banner">{brand.hook_svg(16)}<div><b>Pédagogique</b> {esc(DISCLAIMER)}</div></div>')
    section(1, "Le contexte", "Ce qui compte cette semaine, et pourquoi.")
    for paragraph in (p.strip() for p in content["context"].split("\n") if p.strip()):
        html(f'<p class="sx-body">{esc(paragraph)}</p>')
    if content["calendar"]:
        section(2, "Le calendrier du jour", "Heure de Paris. Le poids dit ce que la publication peut faire bouger.")
        rows = "".join(f'<tr><td><code>{esc(c["time"])}</code></td><td>{esc(c["event"])}</td>'
                       f'<td class="w-{esc(c["weight"])}">{esc(c["weight"])}</td></tr>' for c in content["calendar"])
        html(f'<table class="sx-market-cal"><thead><tr><th>Heure</th><th>Publication</th><th>Poids</th></tr></thead>'
             f'<tbody>{rows}</tbody></table>')
    section(3, "Les scénarios", "Chacun écrit comme une condition, avec ce qui le rend faux.")
    outcomes = (review or {}).get("outcomes", [])
    for i, x in enumerate(content["scenarios"]):
        outcome = outcomes[i] if i < len(outcomes) else None
        _scenario(catalog, x, i, outcome, key=f"sc{s['id']}")
    if content.get("live_url"):
        section(4, "Le live", "La lecture en direct, pendant la séance.")
        st.video(content["live_url"])
    _lessons(catalog, content.get("lessons", []), key=f"market_l{s['id']}", why="Academy · utilisé dans cette séance")
    if review:
        section(5, "Le bilan", "Après la clôture : ce que les scénarios ont fait, et ce que la séance enseigne.")
        html(f'<div class="sx-c-margin sx-market-takeaway"><div class="rub">Ce que la séance enseigne</div>'
             f'<p>{_paragraphs(review["takeaway"])}</p></div>')
        if review.get("replay_url"):
            st.video(review["replay_url"])
        _lessons(catalog, review.get("lessons", []), key=f"market_r{s['id']}", why="Academy · pour aller plus loin")
    else:
        note("Le bilan sera publié après la clôture : pour chaque scénario, s'il a été joué, invalidé ou "
             "non déclenché.")
    footer()


def _scenario(catalog, x: dict, i: int, outcome: dict | None, *, key: str) -> None:
    status = ""
    if outcome:
        label = M.OUTCOMES[outcome["outcome"]]
        status = f'<span class="sx-market-outcome o-{outcome["outcome"]}">{esc(label)}</span>'
    comment = (f'<p class="sx-market-comment">{esc(outcome["comment"])}</p>'
               if outcome and outcome.get("comment") else "")
    observe = (f'<div class="sx-market-line"><b>On observe</b><span>{esc(x["observe"])}</span></div>'
               if x.get("observe") else "")
    html(f'<div class="sx-market-scenario"><div class="head"><div class="rub">Scénario {LETTERS[i]} · '
         f'{esc(x["instrument"])}</div>{status}</div><h3>{esc(x["title"])}</h3>'
         f'<div class="sx-market-line"><b>Condition</b><span>{esc(x["condition"])}</span></div>{observe}'
         f'<div class="sx-market-line inval"><b>Invalidation</b><span>{esc(x["invalidation"])}</span></div>'
         f'{comment}</div>')
    _lessons(catalog, x.get("lessons", []), key=f"{key}_{i}", why="Academy · pour ce scénario")


def _paragraphs(text: str) -> str:
    return "<br>".join(esc(line) for line in (text or "").splitlines())


# =============================================================================
# The editor (coaches)
# =============================================================================

def edit_page(catalog, email, route) -> None:
    space = _space()
    crumbs("Sensitor", space.label, "Préparer une séance")
    store = rt.get_store()
    if not email or store is None or not store.is_coach(email):
        _header("Préparer une séance.", "")
        notice("Accès réservé", "La préparation des séances est réservée à l'équipe Sensitor.", "lock")
        footer()
        return
    existing = None
    if route.get("session"):
        try:
            existing = store.market_session(int(route["session"]), coach=email)
        except ValueError:
            existing = None
    _header("Préparer une séance." if existing is None else "Modifier la séance.",
            "Un contexte, le calendrier, deux à quatre scénarios conditionnels avec leur invalidation. "
            "La publication est refusée tant qu'une formulation ressemble à un signal ou à une promesse.")
    show_flash()
    rt.link("Revenir à la Salle des marchés", "market", key="market_back_edit")
    notice("Ce que la salle publie", DISCLAIMER + " Écrivez « si … alors on observe … », jamais « achetez » "
           "ou « vendez », et aucun objectif de gain.", "info")
    _session_form(catalog, store, email, existing)
    if existing and existing["status"] == "published":
        _review_form(catalog, store, email, existing)
    footer()


def _session_form(catalog, store, email: str, existing: dict | None) -> None:
    content = (existing or {}).get("content") or {}
    scenarios = content.get("scenarios", [])
    choices = _lesson_choices(catalog)
    k = f"me{existing['id']}" if existing else "menew"
    with st.container(key=f"panel_{k}"):
        with st.form(f"form_{k}", border=False):
            c1, c2 = st.columns([1, 1])
            with c1:
                day = st.date_input("Date de la séance", key=f"{k}_date", format="DD/MM/YYYY",
                                    value=_dt.date.fromisoformat(existing["session_date"]) if existing else _dt.date.today())
            with c2:
                access = st.selectbox("Accès", list(M.ACCESS), format_func=M.ACCESS_LABELS.get, key=f"{k}_access",
                                      index=list(M.ACCESS).index(existing["access"]) if existing else 1)
            title = st.text_input("Titre (facultatif)", value=(existing or {}).get("title", ""),
                                  max_chars=M.MAX_TITLE, key=f"{k}_title",
                                  placeholder="Séance du jour, par défaut")
            context = st.text_area("Le contexte de la semaine", value=content.get("context", ""),
                                   max_chars=M.MAX_CONTEXT, height=150, key=f"{k}_context")
            calendar = st.text_area("Le calendrier, une publication par ligne : « 14:30 | Emploi américain | forte »",
                                    value=M.calendar_text(content.get("calendar", [])), height=110,
                                    key=f"{k}_calendar")
            raw_scenarios = []
            for i in range(M.MAX_SCENARIOS):
                x = scenarios[i] if i < len(scenarios) else {}
                with st.expander(f"Scénario {LETTERS[i]}" + (f" · {x['instrument']}" if x else ""), expanded=i == 0 or bool(x)):
                    a, b = st.columns([1, 3])
                    with a:
                        instrument = st.text_input("Instrument", value=x.get("instrument", ""),
                                                   max_chars=M.MAX_INSTRUMENT, key=f"{k}_s{i}_instrument")
                    with b:
                        stitle = st.text_input("Titre du scénario", value=x.get("title", ""),
                                               max_chars=M.MAX_TITLE, key=f"{k}_s{i}_title")
                    condition = st.text_area("Si (la condition)", value=x.get("condition", ""),
                                             max_chars=M.MAX_FIELD, height=80, key=f"{k}_s{i}_condition")
                    observe = st.text_area("On observe (ce que la séance apprend à regarder)", value=x.get("observe", ""),
                                           max_chars=M.MAX_FIELD, height=80, key=f"{k}_s{i}_observe")
                    invalidation = st.text_area("Invalidation (obligatoire)", value=x.get("invalidation", ""),
                                                max_chars=M.MAX_FIELD, height=70, key=f"{k}_s{i}_invalidation")
                    lessons = st.multiselect("Leçons liées", list(choices), default=x.get("lessons", []),
                                             format_func=lambda key: choices.get(key, key), key=f"{k}_s{i}_lessons",
                                             placeholder="Choisir")
                raw_scenarios.append({"instrument": instrument, "title": stitle, "condition": condition,
                                      "observe": observe, "invalidation": invalidation, "lessons": lessons})
            live = st.text_input("Lien du live (YouTube ou Vimeo, facultatif)", value=content.get("live_url", ""),
                                 key=f"{k}_live")
            lessons = st.multiselect("Leçons de la séance", list(choices), default=content.get("lessons", []),
                                     format_func=lambda key: choices.get(key, key), key=f"{k}_lessons",
                                     placeholder="Choisir")
            draft = existing is None or existing["status"] == "draft"
            b1, b2, _ = st.columns([1, 1, 2])
            with b1:
                save = st.form_submit_button("Enregistrer le brouillon" if draft else "Enregistrer les modifications")
            with b2:
                publish = st.form_submit_button("Publier", type="primary") if draft else False
        if save or publish:
            try:
                session = M.clean_session({"session_date": day.isoformat(), "title": title, "access": access,
                                           "context": context, "calendar": calendar, "scenarios": raw_scenarios,
                                           "live_url": live, "lessons": lessons})
            except ValueError as exc:
                st.error(_sentence(exc))
                return
            warnings = M.publishable(session)
            session_id = store.save_market_session(email, session, existing["id"] if existing else None)
            if session_id is None:
                st.error("La séance n'a pas pu être enregistrée.")
                return
            if publish:
                problems = store.publish_market_session(email, session_id)
                if problems:
                    flash("Brouillon enregistré, publication refusée : " + " ; ".join(problems) + ".")
                else:
                    flash("Séance publiée.")
                    rt.go("market_session", session=str(session_id))
                    st.rerun()
            elif warnings and draft:
                flash("Brouillon enregistré. Avant publication : " + " ; ".join(warnings) + ".")
            else:
                flash("Enregistré.")
            rt.go("market_edit", session=str(session_id))
            st.rerun()
    if existing:
        c1, c2, _ = st.columns([1, 1, 2])
        with c1:
            if existing["status"] == "published" and st.button("Retirer la publication", key=f"{k}_unpublish"):
                store.unpublish_market_session(email, existing["id"])
                flash("La séance est redevenue un brouillon.")
                st.rerun()
        with c2:
            if existing["status"] == "draft" and st.button("Supprimer le brouillon", key=f"{k}_delete"):
                store.delete_market_session(email, existing["id"])
                flash("Brouillon supprimé.")
                rt.go("market")
                st.rerun()


def _review_form(catalog, store, email: str, s: dict) -> None:
    section(1, "Le bilan après la clôture", "L'issue de chaque scénario, ce que la séance enseigne, le replay.")
    review = s.get("review") or {}
    given = review.get("outcomes", [])
    choices = _lesson_choices(catalog)
    k = f"mr{s['id']}"
    with st.container(key=f"panel_{k}"):
        with st.form(f"form_{k}", border=False):
            outcomes = []
            keys = list(M.OUTCOMES)
            for i, x in enumerate(s["content"]["scenarios"]):
                html(f'<div class="sx-kicker" style="margin-top:.6rem">Scénario {LETTERS[i]} · {esc(x["instrument"])} · '
                     f'{esc(x["title"])}</div>')
                current = given[i] if i < len(given) else {}
                outcome = st.radio("Issue", keys, format_func=M.OUTCOMES.get, horizontal=True, key=f"{k}_o{i}",
                                   index=keys.index(current["outcome"]) if current.get("outcome") in keys else None)
                comment = st.text_input("Ce qu'il a fait", value=current.get("comment", ""), max_chars=M.MAX_FIELD,
                                        key=f"{k}_c{i}")
                outcomes.append({"outcome": outcome, "comment": comment})
            takeaway = st.text_area("Ce que la séance enseigne", value=review.get("takeaway", ""),
                                    max_chars=M.MAX_TAKEAWAY, height=120, key=f"{k}_takeaway")
            replay = st.text_input("Lien du replay (YouTube ou Vimeo, facultatif)", value=review.get("replay_url", ""),
                                   key=f"{k}_replay")
            lessons = st.multiselect("Leçons pour aller plus loin", list(choices), default=review.get("lessons", []),
                                     format_func=lambda key: choices.get(key, key), key=f"{k}_lessons",
                                     placeholder="Choisir")
            send = st.form_submit_button("Publier le bilan", type="primary")
        if send:
            try:
                cleaned = M.clean_review({"outcomes": outcomes, "takeaway": takeaway, "replay_url": replay,
                                          "lessons": lessons}, s["content"]["scenarios"])
            except ValueError as exc:
                st.error(_sentence(exc))
                return
            if store.review_market_session(email, s["id"], cleaned):
                flash("Bilan publié.")
                rt.go("market_session", session=str(s["id"]))
                st.rerun()
            st.error("Le bilan n'a pas pu être enregistré.")


def _sentence(exc: Exception) -> str:
    text = str(exc)
    return text[:1].upper() + text[1:] + ("" if text.endswith(".") else ".")
