"""
The Academy pages.

Each page reads the catalogue (shared content) and, when someone is signed in,
that person's rows from the store — always through a method scoped by their
verified email. No figure on these pages is invented: counts, scores and dates
come from the database, and a member with no activity sees an empty state, not
a placeholder number.
"""

from __future__ import annotations

import json
from datetime import datetime

import streamlit as st

from ...core.security import MIN_PASSWORD_LENGTH
from .. import access, progress as P
from ..content import Catalog, Course, Lesson
from . import lesson_view, quiz_view, risk_view
from . import runtime as rt
from .components import (access_tag, date_fr, duration, esc, footer, html, note,
                         md, page_header, progress_bar, section, tag)

HERO_ART = """
<svg viewBox="0 0 420 240" role="img" aria-label="Une tendance haussière décrite par ses sommets et ses creux de swing">
<g stroke="#ffffff12"><line x1="0" y1="40" x2="420" y2="40"/><line x1="0" y1="100" x2="420" y2="100"/>
<line x1="0" y1="160" x2="420" y2="160"/><line x1="0" y1="220" x2="420" y2="220"/></g>
<polyline points="10,210 80,140 120,175 200,95 240,135 320,60 360,92 410,30" fill="none" stroke="#9db8d2" stroke-width="2" stroke-linejoin="round"/>
<g stroke="#9db8d2" stroke-opacity=".35" stroke-dasharray="3 5"><line x1="80" y1="140" x2="200" y2="140"/>
<line x1="200" y1="95" x2="320" y2="95"/><line x1="120" y1="175" x2="240" y2="175"/><line x1="240" y1="135" x2="360" y2="135"/></g>
<g fill="#101a24" stroke="#9db8d2" stroke-width="1.5"><circle cx="80" cy="140" r="4"/><circle cx="200" cy="95" r="4"/><circle cx="320" cy="60" r="4"/></g>
<g fill="#9db8d2"><circle cx="120" cy="175" r="4"/><circle cx="240" cy="135" r="4"/><circle cx="360" cy="92" r="4"/></g>
<g font-family="DM Mono, monospace" font-size="11" fill="#8e9cab"><text x="70" y="126">S1</text><text x="190" y="81">S2</text>
<text x="310" y="46">S3</text><text x="112" y="196">C1</text><text x="232" y="156">C2</text><text x="352" y="113">C3</text></g>
</svg>
"""


# =============================================================================
# Shared lookups
# =============================================================================

def _member_state(catalog: Catalog, email: str | None):
    """(completed by course, attempts, passed quiz ids) — empty for visitors."""
    store = rt.get_store()
    if not email or store is None:
        return {}, [], set()
    completed = P.completed_by_course(store.completed_lessons(email))
    attempts = store.quiz_attempts(email, limit=10_000)
    return completed, attempts, P.passed_quiz_ids(attempts)


def _course_progress(course: Course, completed, passed):
    return P.course_progress(course, completed.get(course.id, set()), passed_quizzes=passed)


def _lesson_rows(course: Course, done: set[str], *, scope: str) -> None:
    """The lesson list of a course: one row button per lesson."""
    for module in course.modules:
        html(f'<div class="ac-eyebrow" style="margin-top:1.3rem">{esc(module.title)}</div>')
        for lesson in module.lessons:
            state = "terminée" if lesson.id in done else (
                "accès libre" if lesson.is_public else "membres")
            mark = "✓ " if lesson.id in done else ""
            label = (f"{lesson.number:02d} — {mark}{lesson.title}  ·  "
                     f"{duration(lesson.duration_minutes)} · {state}")
            with st.container(key=f"row_{scope}_{lesson.id}"):
                rt.link(label, "lesson", key=f"open_{scope}_{lesson.id}", width="stretch",
                        course=course.id, lesson=lesson.id)


# =============================================================================
# Home
# =============================================================================

def home(catalog: Catalog, email: str | None) -> None:
    if email:
        _dashboard(catalog, email)
    else:
        _landing(catalog)
    footer()


def _landing(catalog: Catalog) -> None:
    course = catalog.course("premiers-pas") or next(iter(catalog.available_courses()), None)

    with st.container(key="dark_hero"):
        left, right = st.columns([1.15, 0.85], vertical_alignment="center")
        with left:
            html('<div class="ac-hero-kicker">Sensitor Academy · Formation au trading</div>'
                 '<h1 class="ac-hero-title">Comprendre le marché.<br><em>Maîtriser ses '
                 'décisions.</em></h1><p class="ac-hero-text">Des parcours structurés, des '
                 'leçons illustrées, des quiz corrigés et des exercices chiffrés pour apprendre '
                 'à lire un marché, à mesurer son risque et à évaluer ses propres décisions.</p>')
            b1, b2, _ = st.columns([1.25, 1.1, 0.6])
            with b1:
                if course:
                    rt.link("Commencer le premier parcours", "course", key="hero_start",
                            kind="primary", course=course.id)
            with b2:
                rt.link("Créer un compte gratuit", "account", key="hero_account")
        with right:
            html(f'<div class="ac-hero-art">{HERO_ART}</div>')

    section("Une méthode d'apprentissage", "Comprendre, pratiquer, vérifier.")
    html('<div class="ac-cols">'
         '<div class="ac-col"><div class="num">01</div><h4>Des leçons qui expliquent</h4>'
         '<p>Définitions précises, schémas originaux, exemples chiffrés et erreurs fréquentes. '
         'Chaque leçon distingue ce qui est un mécanisme de marché de ce qui relève d\'une '
         'interprétation.</p></div>'
         '<div class="ac-col"><div class="num">02</div><h4>Des quiz qui corrigent</h4>'
         '<p>Chaque réponse est expliquée, qu\'elle soit juste ou fausse, et chaque erreur '
         'renvoie à la leçon qui traite la notion.</p></div>'
         '<div class="ac-col"><div class="num">03</div><h4>Le risque au centre</h4>'
         '<p>Un calculateur testé, des cas pratiques corrigés pas à pas et des simulations de '
         'séries de pertes, avec leurs hypothèses écrites noir sur blanc.</p></div></div>')

    if course:
        section("Le premier parcours", course.summary)
        html(f'<div class="ac-meta" style="margin-top:.4rem"><span><b>{len(course.lessons)}</b> '
             f'leçons</span><span><b>{esc(duration(course.duration_minutes))}</b> au total</span>'
             f'<span>niveau <b>{esc(course.level_label.lower())}</b></span>'
             f'<span><b>1</b> quiz de validation</span></div>')
        _lesson_rows(course, set(), scope="landing")

    section("Le programme", "Dix parcours, ouverts au fur et à mesure de leur rédaction.")
    _curriculum(catalog, compact=True)

    if catalog.resources:
        section("La bibliothèque", "Des fiches et checklists à garder sous la main.")
        _resource_list(catalog, None, compact=True)

    html('<p class="ac-note" style="margin-top:2rem">Sensitor Academy est un service de '
         'formation. Aucun contenu ne constitue un conseil en investissement ni une promesse '
         'de résultat. Le trading comporte un risque de perte en capital.</p>')


def _dashboard(catalog: Catalog, email: str) -> None:
    completed, attempts, passed = _member_state(catalog, email)
    today = date_fr(datetime.now(), with_day=True)
    page_header(f"{esc(today)} · Votre espace", "Reprendre votre apprentissage",
                "La régularité compte davantage que la vitesse.")

    step = P.next_step(catalog, completed, passed)
    with st.container(key="dark_next"):
        if step.kind == "lesson":
            progress = _course_progress(step.course, completed, passed)
            verb = "Continuer" if progress.started else "Commencer"
            html(f'<div class="ac-hero-kicker">{esc(step.course.title)} · leçon '
                 f'{step.lesson.number} sur {progress.total}</div>'
                 f'<h2 class="ac-hero-title" style="font-size:2rem">{esc(step.lesson.title)}</h2>'
                 f'<p class="ac-hero-text">{esc(step.lesson.summary)}</p>')
            rt.link(f"{verb} la leçon", "lesson", key="dash_continue", kind="primary",
                    course=step.course.id, lesson=step.lesson.id)
        elif step.kind == "final_quiz":
            html(f'<div class="ac-hero-kicker">{esc(step.course.title)}</div>'
                 '<h2 class="ac-hero-title" style="font-size:2rem">Toutes les leçons sont '
                 'terminées.</h2><p class="ac-hero-text">Il reste le quiz de validation pour '
                 'vérifier l\'ensemble du parcours.</p>')
            rt.link("Passer le quiz de validation", "quiz", key="dash_quiz", kind="primary",
                    quiz=step.course.final_quiz_id, course=step.course.id)
        else:
            html('<div class="ac-hero-kicker">Parcours terminé</div><h2 class="ac-hero-title" '
                 'style="font-size:2rem">Vous avez terminé les parcours disponibles.</h2>'
                 '<p class="ac-hero-text">Le laboratoire de risque et la bibliothèque restent à '
                 'votre disposition. Les prochains parcours sont en préparation.</p>')
            rt.link("Ouvrir le laboratoire de risque", "lab", key="dash_lab", kind="primary")

    section("Votre progression", "Calculée à partir de vos leçons terminées et de vos quiz.")
    courses = catalog.available_courses()
    lessons_total = sum(len(c.lessons) for c in courses)
    lessons_done = sum(_course_progress(c, completed, passed).done for c in courses)
    final_ids = [c.final_quiz_id for c in courses if c.final_quiz_id]
    finals_passed = sum(1 for q in final_ids if q in passed)
    last = attempts[0] if attempts else None
    last_quiz = catalog.quiz(last["quiz_id"]) if last else None
    last_value = f'{last["correct"]}<small> / {last["total"]}</small>' if last else "—"
    last_detail = (f'{esc(last_quiz.title if last_quiz else last["quiz_id"])} · '
                   f'{esc(date_fr(last["created_at"]))}' if last else "Aucun quiz passé pour l'instant")
    html('<div class="ac-stats">'
         f'<div class="ac-stat"><div class="label">Leçons terminées</div><div class="value">'
         f'{lessons_done}<small> / {lessons_total}</small></div><div class="detail">'
         f'dans les parcours ouverts</div></div>'
         f'<div class="ac-stat"><div class="label">Quiz de validation</div><div class="value">'
         f'{finals_passed}<small> / {len(final_ids)}</small></div><div class="detail">'
         f'réussi{"s" if finals_passed > 1 else ""}</div></div>'
         f'<div class="ac-stat"><div class="label">Dernier quiz</div><div class="value">'
         f'{last_value}</div><div class="detail">{last_detail}</div></div></div>')

    for course in courses:
        progress = _course_progress(course, completed, passed)
        html(f'<div style="margin-top:1.4rem"><div class="ac-eyebrow">Parcours '
             f'{catalog.path(course.path_id).number if catalog.path(course.path_id) else ""}'
             f'</div><h3 class="ac-h3" style="margin-top:.4rem">{esc(course.title)}</h3>'
             f'{progress_bar(progress.fraction, f"{progress.done} / {progress.total} leçons")}</div>')
        rt.link("Voir le parcours", "course", key=f"dash_course_{course.id}", course=course.id)

    section("Outils et ressources")
    c1, c2, c3 = st.columns(3)
    with c1:
        html('<h3 class="ac-h3">Laboratoire de risque</h3><p class="ac-sub">Budget de risque, '
             'taille de position et séries de pertes.</p>')
        rt.link("Ouvrir", "lab", key="dash_tool_lab")
    with c2:
        html('<h3 class="ac-h3">Bibliothèque</h3><p class="ac-sub">Fiches de révision et '
             'checklists à télécharger.</p>')
        rt.link("Ouvrir", "library", key="dash_tool_lib")
    with c3:
        html('<h3 class="ac-h3">Progression détaillée</h3><p class="ac-sub">Historique des '
             'quiz et erreurs à revoir.</p>')
        rt.link("Ouvrir", "progress", key="dash_tool_prog")


# =============================================================================
# Paths
# =============================================================================

def paths(catalog: Catalog, email: str | None) -> None:
    page_header("Sensitor Academy · Le programme", "Construisez votre méthode.",
                "Une progression structurée, des bases jusqu'au processus de trading "
                "discipliné. Les parcours ouvrent au fur et à mesure que leur contenu est "
                "rédigé et relu.")
    completed, _, passed = _member_state(catalog, email)
    for path in catalog.paths:
        if not path.is_available:
            continue
        section(f"Parcours {path.number} — {path.title}", path.summary)
        for course in path.courses:
            progress = _course_progress(course, completed, passed)
            label = f"{progress.done} / {progress.total} leçons" if email else \
                f"{len(course.lessons)} leçons · {duration(course.duration_minutes)}"
            html(f'<h3 class="ac-h3" style="margin-top:1rem">{esc(course.title)}</h3>'
                 f'<p class="ac-sub">{esc(course.summary)}</p>'
                 f'<div style="margin:.8rem 0">{progress_bar(progress.fraction, label)}</div>')
            rt.link("Ouvrir le parcours", "course", key=f"paths_open_{course.id}",
                    kind="primary", course=course.id)
    section("En préparation", "Annoncés dans le programme, sans contenu publié pour l'instant.")
    _curriculum(catalog, compact=False, only_planned=True)
    footer()


def _curriculum(catalog: Catalog, *, compact: bool, only_planned: bool = False) -> None:
    items = []
    for path in catalog.paths:
        if only_planned and path.is_available:
            continue
        status = tag("Ouvert", "open") if path.is_available else tag("En préparation", "soon")
        summary = "" if compact else f"<small>{esc(path.summary)}</small>"
        cls = "" if path.is_available else "muted"
        items.append(f'<li class="{cls}"><span class="n">{path.number:02d}</span>'
                     f'<span class="t">{esc(path.title)}{summary}</span>{status}</li>')
    html(f'<ul class="ac-list">{"".join(items)}</ul>')


# =============================================================================
# Course
# =============================================================================

def course_page(catalog: Catalog, email: str | None, course_id: str | None) -> None:
    course = catalog.course(course_id or "")
    if course is None:
        _not_found("Ce parcours n'existe pas ou n'est pas encore publié.")
        return
    completed, attempts, passed = _member_state(catalog, email)
    progress = _course_progress(course, completed, passed)
    path = catalog.path(course.path_id)

    rt.link("← Tous les parcours", "paths", key="course_back", kind="tertiary")
    meta = [f"niveau <b>{esc(course.level_label.lower())}</b>",
            f"<b>{len(course.lessons)}</b> leçons",
            f"<b>{esc(duration(course.duration_minutes))}</b> de lecture"]
    eyebrow = f"Parcours {path.number} · {esc(path.title)}" if path else "Parcours"
    page_header(eyebrow, course.title, course.summary, meta)

    if email:
        html(f'<div style="margin-top:1.2rem;max-width:520px">'
             f'{progress_bar(progress.fraction, f"{progress.done} / {progress.total} leçons terminées")}</div>')
    if progress.next_lesson:
        verb = "Continuer" if progress.started else "Commencer"
        rt.link(f"{verb} : {progress.next_lesson.title}", "lesson", key="course_next",
                kind="primary", course=course.id, lesson=progress.next_lesson.id)

    left, right = st.columns([1.6, 1], gap="large")
    with left:
        section("Plan du parcours")
        _lesson_rows(course, progress.completed, scope="course")
        if course.final_quiz_id:
            quiz = catalog.quiz(course.final_quiz_id)
            state = "à passer"
            if email:
                tries = [a for a in attempts if a["quiz_id"] == quiz.id]
                if quiz.id in passed:
                    best = max(a["correct"] for a in tries)
                    state = f"réussi · meilleur score {best} / {len(quiz.questions)}"
                elif tries:
                    state = f"{len(tries)} tentative{'s' if len(tries) > 1 else ''}, pas encore validé"
            html('<div class="ac-eyebrow" style="margin-top:1.3rem">Évaluation</div>')
            with st.container(key="row_course_finalquiz"):
                rt.link(f"Quiz de validation · {len(quiz.questions)} questions · {state}",
                        "quiz", key="course_final", width="stretch", quiz=quiz.id,
                        course=course.id)
    with right:
        section("Objectifs")
        html("<ul class='ac-sub' style='padding-left:1.1rem;font-size:14.5px;line-height:1.75'>"
             + "".join(f"<li>{esc(o)}</li>" for o in course.objectives) + "</ul>")
        if not email:
            html('<div class="ac-locked" style="margin-top:1rem"><h3 class="ac-h3">Deux leçons '
                 'en accès libre</h3><p class="ac-sub">Les deux premières leçons se lisent sans '
                 'compte. Créez un compte gratuit pour accéder à la suite et enregistrer votre '
                 'progression.</p></div>')
            rt.link("Créer un compte", "account", key="course_signup")
    footer()


# =============================================================================
# Lesson
# =============================================================================

def lesson_page(catalog: Catalog, email: str | None, course_id: str | None,
                lesson_id: str | None) -> None:
    course = catalog.course(course_id or "")
    lesson = course.lesson(lesson_id or "") if course else None
    if lesson is None:
        _not_found("Cette leçon n'existe pas ou n'est pas encore publiée.")
        return
    completed, _, _ = _member_state(catalog, email)
    done = completed.get(course.id, set())
    module = next((m for m in course.modules if m.id == lesson.module_id), None)

    outline, body = st.columns([0.9, 2.6], gap="large")
    with outline:
        rt.link(f"← {course.title}", "course", key="lesson_back", kind="tertiary",
                course=course.id)
        for item in course.lessons:
            mark = "✓ " if item.id in done else ""
            prefix = "rowcurrent" if item.id == lesson.id else "row"
            with st.container(key=f"{prefix}_outline_{item.id}"):
                rt.link(f"{item.number:02d}  {mark}{item.title}", "lesson",
                        key=f"outline_{item.id}", width="stretch", course=course.id,
                        lesson=item.id)

    with body:
        meta = [access_tag(lesson)]
        if lesson.id in done:
            meta.append(tag("Terminée", "done"))
        eyebrow = (f"Leçon {lesson.number:02d} · {esc(module.title if module else '')} · "
                   f"{esc(duration(lesson.duration_minutes))}")
        page_header(eyebrow, lesson.title, lesson.summary, meta)

        if not access.can_read_lesson(lesson, email):
            lesson_view.render_objectives(lesson)
            html('<div class="ac-locked"><h3 class="ac-h3">Leçon réservée aux membres</h3>'
                 '<p class="ac-sub">Créez un compte gratuit ou connectez-vous pour lire cette '
                 'leçon, passer son quiz et enregistrer votre progression.</p></div>')
            rt.link("Se connecter ou créer un compte", "account", key="lesson_unlock",
                    kind="primary")
            footer()
            return

        lesson_view.render_objectives(lesson)
        lesson_view.render_blocks(lesson, catalog, email=email)
        lesson_view.render_quiz(lesson, catalog, email=email)
        _lesson_resources(catalog, lesson, email)
        lesson_view.render_sources(lesson)
        _completion(course, lesson, email, done)
        _neighbours(course, lesson)
    footer()


def _lesson_resources(catalog: Catalog, lesson: Lesson, email: str | None) -> None:
    resources = [catalog.resource(rid) for rid in lesson.resources]
    resources = [r for r in resources if r]
    if not resources:
        return
    html('<div class="ac-rule"></div><div class="ac-eyebrow">Ressources liées</div>')
    for resource in resources:
        c1, c2 = st.columns([3, 1], vertical_alignment="center")
        with c1:
            html(f'<p style="margin:0"><b>{esc(resource.title)}</b> '
                 f'<span class="ac-sub">· {esc(resource.kind_label)}</span></p>')
        with c2:
            _download(resource, email, key=f"lesson_dl_{lesson.id}_{resource.id}")


def _completion(course: Course, lesson: Lesson, email: str | None, done: set[str]) -> None:
    html('<div class="ac-rule"></div>')
    if not email:
        note("Connectez-vous pour enregistrer votre progression.")
        return
    store = rt.get_store()
    if store is None:
        note("La base de données est indisponible : la progression ne peut pas être enregistrée.")
        return
    if lesson.id in done:
        html('<p class="ac-sub">Leçon marquée comme terminée.</p>')
        if st.button("Marquer comme non terminée", key=f"undo_{lesson.id}", type="tertiary"):
            store.unmark_lesson(email, course.id, lesson.id)
            st.rerun()
    elif st.button("Marquer la leçon comme terminée", key=f"done_{lesson.id}", type="primary"):
        store.mark_lesson_complete(email, course.id, lesson.id, version=lesson.version)
        st.toast("Leçon enregistrée dans votre progression.")
        st.rerun()


def _neighbours(course: Course, lesson: Lesson) -> None:
    previous, following = course.neighbours(lesson.id)
    c1, c2 = st.columns(2)
    with c1:
        if previous:
            rt.link(f"← {previous.title}", "lesson", key="nav_prev", width="stretch",
                    course=course.id, lesson=previous.id)
    with c2:
        if following:
            rt.link(f"{following.title} →", "lesson", key="nav_next", width="stretch",
                    course=course.id, lesson=following.id)
        elif course.final_quiz_id:
            rt.link("Quiz de validation →", "quiz", key="nav_quiz", width="stretch",
                    quiz=course.final_quiz_id, course=course.id)


# =============================================================================
# Quiz page
# =============================================================================

def quiz_page(catalog: Catalog, email: str | None, quiz_id: str | None,
              course_id: str | None) -> None:
    quiz = catalog.quiz(quiz_id or "")
    if quiz is None:
        _not_found("Ce quiz n'existe pas ou n'est pas encore publié.")
        return
    course = catalog.course(course_id or quiz.course_id or "")
    if course:
        rt.link(f"← {course.title}", "course", key="quiz_back", kind="tertiary",
                course=course.id)
    page_header("Évaluation", quiz.title)
    quiz_view.render(quiz, scope="page", catalog=catalog, email=email)
    footer()


# =============================================================================
# Library
# =============================================================================

def library(catalog: Catalog, email: str | None) -> None:
    page_header("Sensitor Academy · Bibliothèque", "Ressources à garder sous la main.",
                "Fiches de révision et checklists rédigées pour accompagner les parcours. "
                "Chaque document listé ici existe réellement et se télécharge.")
    if not catalog.resources:
        note("La bibliothèque est vide pour l'instant.")
        footer()
        return
    c1, c2 = st.columns([2, 1])
    with c1:
        query = st.text_input("Rechercher", placeholder="Un mot du titre ou de la description",
                              key="lib_query")
    with c2:
        categories = sorted({r.category for r in catalog.resources.values()})
        category = st.selectbox("Thème", ["Tous les thèmes", *categories], key="lib_cat")
    _resource_list(catalog, email, query=query, category=category)
    footer()


def _resource_list(catalog: Catalog, email: str | None, *, compact: bool = False,
                   query: str = "", category: str = "Tous les thèmes") -> None:
    needle = query.strip().lower()
    shown = 0
    for index, resource in enumerate(catalog.resources.values(), start=1):
        if category != "Tous les thèmes" and resource.category != category:
            continue
        if needle and needle not in f"{resource.title} {resource.description}".lower():
            continue
        shown += 1
        lessons = [catalog.find_lesson(l) for l in resource.lessons]
        linked = ", ".join(l.title for l in lessons if l)
        access_label = tag("Accès libre", "open") if resource.access == "public" else tag("Membres", "member")
        c1, c2 = st.columns([3, 1], vertical_alignment="center")
        with c1:
            linked_html = "" if compact or not linked else \
                f'<p class="ac-sub" style="font-size:13px">Leçons liées : {esc(linked)}</p>'
            html(f'<div class="ac-resource" style="margin-top:1rem"><div class="ac-resource-cover">'
                 f'{index}</div><div><div class="kind">{esc(resource.kind_label)} · '
                 f'{esc(resource.category)} {access_label}</div><h3 class="ac-h3" '
                 f'style="margin-top:.35rem">{esc(resource.title)}</h3><p class="ac-sub">'
                 f'{esc(resource.description)}</p>{linked_html}</div></div>')
        with c2:
            _download(resource, email, key=f"lib_dl_{'c' if compact else 'f'}_{resource.id}")
        if not compact and access.can_download(resource, email):
            with st.expander(f"Lire « {resource.title} » ici"):
                md(resource.read_text())
    if not shown:
        note("Aucune ressource ne correspond à cette recherche.")


def _download(resource, email: str | None, *, key: str) -> None:
    if access.can_download(resource, email):
        st.download_button("Télécharger", data=resource.read_text().encode("utf-8"),
                           file_name=resource.filename, mime="text/markdown", key=key,
                           width="stretch")
    else:
        rt.link("Réservé aux membres", "account", key=f"{key}_lock", width="stretch")


# =============================================================================
# Lab
# =============================================================================

def lab(catalog: Catalog, email: str | None) -> None:
    page_header("Sensitor Academy · Laboratoire", "Le laboratoire de risque.",
                "Refaites les calculs du parcours avec vos propres hypothèses : montant "
                "risqué, distance au stop, ratio gain / risque, taille de position et effet "
                "d'une série de pertes.")
    risk_view.render(scope="lab")
    lesson = catalog.find_lesson("budget-de-risque")
    if lesson:
        html('<div class="ac-rule"></div>')
        rt.link("Relire la leçon « Le budget de risque »", "lesson", key="lab_lesson",
                kind="tertiary", course=lesson.course_id, lesson=lesson.id)
    footer()


# =============================================================================
# Progress
# =============================================================================

def progress_page(catalog: Catalog, email: str | None) -> None:
    page_header("Sensitor Academy · Progression", "Mesurer ce que l'on apprend.",
                "Vos leçons terminées, vos quiz et les notions à revoir.")
    if not email:
        _sign_in_prompt("Connectez-vous pour suivre votre progression.")
        return
    completed, attempts, passed = _member_state(catalog, email)

    for course in catalog.available_courses():
        progress = _course_progress(course, completed, passed)
        section(course.title, f"{progress.done} / {progress.total} leçons terminées")
        html(f'<div style="max-width:520px;margin:.6rem 0 .4rem">{progress_bar(progress.fraction)}</div>')
        items = []
        for lesson in course.lessons:
            status = tag("Terminée", "done") if lesson.id in progress.completed else tag("À lire")
            items.append(f'<li><span class="n">{lesson.number:02d}</span><span class="t">'
                         f'{esc(lesson.title)}</span>{status}</li>')
        html(f'<ul class="ac-list">{"".join(items)}</ul>')

    section("Historique des quiz", "Vos tentatives, de la plus récente à la plus ancienne.")
    if not attempts:
        note("Vous n'avez encore passé aucun quiz. Les contrôles de compréhension se trouvent "
             "à la fin de chaque leçon.")
    else:
        rows = "".join(
            f"<tr><td>{esc(date_fr(a['created_at']))}</td>"
            f"<td>{esc(catalog.quiz(a['quiz_id']).title if catalog.quiz(a['quiz_id']) else a['quiz_id'])}</td>"
            f"<td>{a['correct']} / {a['total']}</td><td>{'Réussi' if a['passed'] else 'Non validé'}</td></tr>"
            for a in attempts[:30])
        html('<table><thead><tr><th>Date</th><th>Quiz</th><th>Score</th><th>Résultat</th></tr>'
             f'</thead><tbody>{rows}</tbody></table>')
        _mistakes(catalog, attempts)

    section("Vos données")
    store = rt.get_store()
    if store is not None:
        payload = json.dumps({"lesson_progress": store.completed_lessons(email),
                              "quiz_attempts": store.quiz_attempts(email, limit=100_000)},
                             ensure_ascii=False, indent=2)
        st.download_button("Exporter ma progression (JSON)", data=payload.encode("utf-8"),
                           file_name="sensitor-academy-progression.json",
                           mime="application/json", key="export_progress")
    footer()


def _mistakes(catalog: Catalog, attempts) -> None:
    """Questions missed in the latest attempt of each quiz, linked to their lesson."""
    latest: dict[str, dict] = {}
    for attempt in attempts:
        latest.setdefault(attempt["quiz_id"], attempt)
    missed = []
    for quiz_id, attempt in latest.items():
        quiz = catalog.quiz(quiz_id)
        if quiz is None or attempt["quiz_version"] != quiz.version:
            continue
        for question in quiz.questions:
            chosen = set(attempt["responses"].get(question.id, []))
            if chosen != set(question.correct_ids):
                missed.append((quiz, question))
    section("À revoir", "Les questions manquées lors de votre dernière tentative de chaque quiz.")
    if not missed:
        note("Rien à revoir : votre dernière tentative de chaque quiz est sans erreur.")
        return
    for index, (quiz, question) in enumerate(missed):
        lesson = catalog.find_lesson(question.lesson_id) if question.lesson_id else None
        html(f'<p style="margin:.9rem 0 .1rem"><b>{esc(question.prompt)}</b></p>'
             f'<p class="ac-sub" style="margin:0">{esc(quiz.title)}</p>')
        if lesson:
            rt.link(f"Relire : {lesson.title}", "lesson", key=f"miss_{index}", kind="tertiary",
                    course=lesson.course_id, lesson=lesson.id)


# =============================================================================
# Account
# =============================================================================

REASONS = {
    "invalid_email": "Adresse e-mail invalide.",
    "invalid_credentials": "Adresse ou mot de passe incorrect.",
    "already_registered": "Un compte existe déjà avec cette adresse. Connectez-vous.",
    "weak_password": "Mot de passe trop faible.",
    "locked": "Trop de tentatives. Réessayez dans quelques minutes.",
}


def account(catalog: Catalog, email: str | None) -> None:
    if email:
        page_header("Sensitor Academy · Compte", "Votre compte")
        html(f'<p class="ac-lead">Connecté avec <b>{esc(email)}</b>.</p>')
        if not rt.multi_user():
            st.warning("Cette installation fonctionne en mode local (SENSITOR_AUTH n'est pas "
                       "réglé sur « multi ») : l'adresse e-mail sert d'identifiant sans mot de "
                       "passe. Ce mode convient à un usage personnel, pas à un site ouvert.")
        if st.button("Se déconnecter", key="sign_out"):
            rt.sign_out()
            rt.go("home")
            st.rerun()
        note("Le même compte donne accès à l'application d'analyse de portefeuille Sensitor.")
        footer()
        return

    page_header("Sensitor Academy · Compte", "Connexion",
                "Un compte gratuit donne accès à toutes les leçons publiées et enregistre "
                "votre progression et vos résultats de quiz.")
    multi = rt.multi_user()
    if rt.get_store() is None:
        st.error("La base de données est indisponible : la connexion est impossible pour l'instant.")
        return
    left, _ = st.columns([1.3, 1])
    with left:
        tab_in, tab_up = st.tabs(["Se connecter", "Créer un compte"])
        with tab_in:
            with st.form("sign_in_form"):
                address = st.text_input("Adresse e-mail", key="si_email")
                password = st.text_input("Mot de passe", type="password", key="si_pw") if multi else None
                if st.form_submit_button("Se connecter", type="primary"):
                    _finish(rt.sign_in(address, password))
        with tab_up:
            with st.form("sign_up_form"):
                address = st.text_input("Adresse e-mail", key="su_email")
                password = st.text_input(f"Mot de passe ({MIN_PASSWORD_LENGTH} caractères minimum)", type="password",
                                         key="su_pw") if multi else None
                if st.form_submit_button("Créer mon compte", type="primary"):
                    _finish(rt.sign_up(address, password))
        if not multi:
            note("Mode local : aucun mot de passe n'est demandé. Pour un site ouvert au public, "
                 "réglez SENSITOR_AUTH=multi.")
    footer()


def _finish(result) -> None:
    if result:
        rt.go("home")
        st.rerun()
    message = REASONS.get(getattr(result, "reason", None), "La connexion a échoué.")
    detail = getattr(result, "detail", None) or ""
    if getattr(result, "reason", None) == "weak_password":
        if "space" in detail:
            message += " Il ne doit pas commencer ni finir par une espace."
        else:
            message += f" Il doit compter au moins {MIN_PASSWORD_LENGTH} caractères."
    st.error(message)


def _sign_in_prompt(text: str) -> None:
    html(f'<div class="ac-locked"><p class="ac-sub" style="margin:0">{esc(text)}</p></div>')
    rt.link("Se connecter ou créer un compte", "account", key="prompt_signin", kind="primary")
    footer()


def _not_found(text: str) -> None:
    page_header("Introuvable", "Page introuvable", text)
    rt.link("Retour à l'accueil", "home", key="nf_home", kind="primary")
