"""
The Academy space: home, course, lesson, quiz, Trading Lab and progress pages.

Each page reads the shared catalogue and, for a signed-in member, that member's
own rows — always through a store method scoped by the verified email. Counts,
scores and dates come from the database; a member with no activity sees an
empty state, never a placeholder figure.
"""

from __future__ import annotations

import json

import streamlit as st

from ...platform import spaces
from ...platform.ui import runtime as rt
from ...platform.ui.components import (crumbs, date_fr, duration, esc, footer, hexmark, html,
                                       icon, note, notice, numeral, page_header, pill,
                                       progress_bar, section, tap)
from .. import access, progress as P
from .. import quiz as Q
from ..content import Catalog, Course, Lesson
from . import lesson_view, quiz_view, risk_view
from .library import book_row

FORMATS = (
    ("Leçons écrites et schémas originaux", "live"),
    ("Quiz corrigés, explication par réponse", "live"),
    ("Exercices chiffrés avec corrigé", "live"),
    ("Calculateur de risque", "live"),
    ("Vidéos intégrées aux leçons", "soon"),
    ("Ebooks", "soon"),
)


# =============================================================================
# Member state
# =============================================================================

class Member:
    """What one signed-in member has done. Empty for a visitor."""

    def __init__(self, email: str | None):
        store = rt.get_store()
        self.email = email
        self.tier = rt.tier(email)
        rows = store.completed_lessons(email) if email and store else []
        self.attempts = store.quiz_attempts(email, limit=10_000) if email and store else []
        self.completed = P.completed_by_course(rows)
        self.completed_at = {(r["course_id"], r["lesson_id"]): r["completed_at"] for r in rows}
        self.passed = P.passed_quiz_ids(self.attempts)

    def progress(self, course: Course) -> P.CourseProgress:
        return P.course_progress(course, self.completed.get(course.id, set()),
                                 passed_quizzes=self.passed)


def lesson_state(lesson: Lesson, member: Member, progress: P.CourseProgress) -> str:
    if lesson.id in progress.completed:
        return "done"
    if not access.can_read_lesson(lesson, member.email, member.tier):
        return "locked"
    if progress.next_lesson and progress.next_lesson.id == lesson.id and member.email:
        return "current"
    return "todo"


def _outline_state(item: Lesson, reading: Lesson, member: Member,
                   progress: P.CourseProgress) -> str:
    """In a lesson's outline, only the lesson being read is marked current."""
    state = lesson_state(item, member, progress)
    if item.id == reading.id:
        return "done" if state == "done" else "current"
    return "todo" if state == "current" else state


def lesson_row(lesson: Lesson, state: str, *, flush: bool = False, when: str = "") -> str:
    if state == "done":
        badge = pill(f"Terminée{' · ' + when if when else ''}", "done", "check")
    elif lesson.is_public:
        badge = pill("Libre", "free")
    elif lesson.access == "premium":
        badge = pill("Premium", "member", "lock")
    else:
        badge = pill("Membres", "member", "lock")
    return (f'<div class="sx-lesson{" flush" if flush else ""}{" locked" if state == "locked" else ""}">'
            f'{hexmark(f"{lesson.number:02d}", state)}<div><div class="title">{esc(lesson.title)}</div>'
            f'<div class="summary">{esc(lesson.summary)}</div></div><div class="side">'
            f'{esc(duration(lesson.duration_minutes))}{badge}</div>'
            f'<span class="arrow">{icon("arrow")}</span></div>')


def start_card(course: Course, member: Member, *, key: str) -> None:
    """The navy starting point: where to begin or resume, as one link."""
    progress = member.progress(course)
    target = progress.next_lesson or course.lessons[0]
    if not member.email:
        verb, kicker = "Commencer", "Commencer · accès libre"
    elif progress.lessons_finished:
        verb, kicker = "Relire", "Parcours terminé"
    elif progress.started:
        verb, kicker = "Reprendre", f"Reprendre · leçon {target.number} sur {progress.total}"
    else:
        verb, kicker = "Commencer", f"Commencer · leçon 1 sur {progress.total}"
    foot = (f"{progress.done} / {progress.total} leçons terminées" if member.email
            else f"{esc(duration(target.duration_minutes))} · sans compte")
    tap(key,
        f'<div class="sx-start"><div class="sx-kicker on-navy">{kicker}</div>'
        f'<div class="t">{esc(target.title)}</div><div class="s">{esc(target.summary)}</div>'
        f'<div class="bar"><i style="width:{progress.fraction * 100:.0f}%"></i></div>'
        f'<div class="foot"><span>{foot}</span><span class="go">{verb} {icon("arrow")}</span></div></div>',
        f"{verb} : {target.title}", "lesson", course=course.id, lesson=target.id)


def course_feature(catalog: Catalog, course: Course, *, key: str) -> None:
    path = catalog.path(course.path_id)
    tap(key,
        f'<div class="sx-feature"><div class="numeral">{numeral(path.number if path else 1)}</div>'
        f'<div><div class="sx-kicker">{esc(path.label) if path else "Parcours"} · {esc(path.title if path else "")}'
        f'</div><div class="t">{esc(course.title)}</div><div class="s">{esc(course.summary)}</div>'
        f'<div class="sx-meta"><span><b>{len(course.modules)}</b> chapitres</span><span>'
        f'<b>{len(course.lessons)}</b> leçons</span><span>{esc(duration(course.duration_minutes))}'
        f'</span><span>{esc(course.level_label.lower())}</span></div></div>'
        f'<span class="go">{icon("arrow")}</span></div>',
        f"Ouvrir le parcours {course.title}", "course", course=course.id)


# =============================================================================
# Academy home
# =============================================================================

def academy_home(catalog: Catalog, email: str | None, route: dict) -> None:
    member = Member(email)
    crumbs("Sensitor", "Academy")
    courses = catalog.available_courses()
    left, right = st.columns([1.35, 1], gap="large", vertical_alignment="bottom")
    with left:
        page_header(f"Espace {spaces.space('academy').numeral} · Academy", "Apprendre le <em>trading</em>, comprendre la monnaie.",
                    "Le trading d'abord, de la première bougie au processus discipliné ; puis la monnaie, "
                    "Bitcoin et la crypto, pour comprendre ce qui porte les marchés. Chaque parcours ouvre "
                    "lorsque son contenu est rédigé, sourcé, relu et testé.",
                    display=True)
    with right:
        step = P.next_step(catalog, member.completed, member.passed)
        target = step.course or (courses[0] if courses else None)
        if target:
            start_card(target, member, key="academy_start")

    section(1, "Les parcours ouverts",
            "Un parcours est une suite de chapitres et de leçons, conclue par un quiz de validation.")
    for course in courses:
        course_feature(catalog, course, key=f"academy_course_{course.id}")
        if email:
            progress = member.progress(course)
            html(f'<div style="margin-top:.8rem">{progress_bar(progress.fraction, f"{progress.done} / {progress.total} leçons terminées")}</div>')

    total = len(catalog.paths)
    section(2, "Le programme complet",
            f"{total} parcours en {len(catalog.tracks) or 1} filières. Ceux qui sont en préparation "
            "sont annoncés ici et ne sont pas lisibles.")
    groups = [(t.title, t.summary, catalog.paths_in(t.id)) for t in catalog.tracks] or [("", "", list(catalog.paths))]
    for title, summary, paths in groups:
        if not paths:
            continue
        if title:
            opened = sum(1 for p in paths if p.is_available)
            html(f'<div class="sx-track"><div class="sx-kicker">{esc(title)} · {opened} sur {len(paths)} '
                 f'ouvert{"s" if opened > 1 else ""}</div><p>{esc(summary)}</p></div>')
        cells = []
        for path in paths:
            status = pill("Ouvert", "live") if path.is_available else pill("En préparation", "soon")
            cells.append(f'<div><span class="n">{path.number:02d} · {numeral(path.number)}</span>'
                         f'<div class="t">{esc(path.title)}</div><div class="x">{esc(path.summary)}</div>'
                         f'{status}</div>')
        html(f'<div class="sx-index">{"".join(cells)}</div>')

    section(3, "Les formats", "Ce qui est disponible aujourd'hui, et ce qui ne l'est pas encore.")
    rows = "".join(f'<li><span class="n">{i:02d}</span><span class="x">{esc(label)}</span>'
                   f'{pill("Disponible", "live") if kind == "live" else pill("En préparation", "soon")}</li>'
                   for i, (label, kind) in enumerate(FORMATS, start=1))
    html(f'<ul class="sx-plan">{rows}</ul>')
    footer()


# =============================================================================
# Course
# =============================================================================

def course_page(catalog: Catalog, email: str | None, route: dict) -> None:
    course = catalog.course(route.get("course") or "")
    if course is None:
        _not_found("Ce parcours n'existe pas ou n'est pas encore publié.")
        return
    member = Member(email)
    progress = member.progress(course)
    path = catalog.path(course.path_id)

    crumbs("Sensitor", "Academy", course.title)
    left, right = st.columns([1.4, 1], gap="large", vertical_alignment="bottom")
    with left:
        kicker = f"{esc(path.label)} · {esc(path.title)}" if path else "Parcours"
        meta = [f"{icon('clock')}<b>{esc(duration(course.duration_minutes))}</b>",
                f"<b>{len(course.modules)}</b> chapitres", f"<b>{len(course.lessons)}</b> leçons",
                f"niveau {esc(course.level_label.lower())}"]
        if course.final_quiz_id:
            meta.append("quiz de validation")
        page_header(kicker, esc(course.title), course.summary, meta)
    with right:
        start_card(course, member, key="course_start")

    section(1, "Ce que vous saurez faire",
            "Les objectifs du parcours. Le quiz de validation vérifie chacun d'eux.")
    items = "".join(f'<div><span class="n">{i:02d}</span><span class="x">{esc(o)}</span></div>'
                    for i, o in enumerate(course.objectives, start=1))
    html(f'<div class="sx-objectives">{items}</div>')

    free = sum(1 for l in course.lessons if l.is_public)
    section(2, "Le plan du parcours",
            f"{len(course.modules)} chapitres, {len(course.lessons)} leçons. "
            + (f"{free} leçon se lit sans compte" if free == 1 else f"{free} leçons se lisent sans compte")
            + " ; les suivantes demandent un compte gratuit.")
    for module in course.modules:
        html(f'<div class="sx-chapter"><div class="numeral">{numeral(module.number)}.</div><div>'
             f'<div class="k">Chapitre {numeral(module.number)} · {len(module.lessons)} '
             f'leçon{"s" if len(module.lessons) > 1 else ""} · {esc(duration(module.duration_minutes))}'
             f'</div><h3>{esc(module.title)}</h3><p>{esc(module.summary)}</p></div></div>')
        for lesson in module.lessons:
            state = lesson_state(lesson, member, progress)
            when = date_fr(member.completed_at.get((course.id, lesson.id), ""))
            tap(f"course_{lesson.id}", lesson_row(lesson, state, when=when),
                f"Leçon {lesson.number} : {lesson.title}", "lesson",
                course=course.id, lesson=lesson.id)

    if course.final_quiz_id:
        quiz = catalog.quiz(course.final_quiz_id)
        tries = [a for a in member.attempts if a["quiz_id"] == quiz.id]
        if quiz.id in member.passed:
            best = max(a["correct"] for a in tries)
            badge, state = pill(f"Réussi · {best} / {len(quiz.questions)}", "done", "check"), "done"
        elif tries:
            badge, state = pill(f"{len(tries)} tentative{'s' if len(tries) > 1 else ''}", "member"), "final"
        else:
            required = Q.required_correct(len(quiz.questions), quiz.pass_threshold)
            badge, state = pill(f"Réussite à {required} / {len(quiz.questions)}", ""), "final"
        html('<div class="sx-chapter"><div class="numeral">Q.</div><div><div class="k">Évaluation '
             'finale</div><h3>Quiz de validation</h3><p>Des questions sur l\'ensemble du parcours, '
             'corrigées à la fin, avec un renvoi vers la leçon de chaque erreur.</p></div></div>')
        tap("course_final",
            f'<div class="sx-lesson final">{hexmark("Q", state)}<div><div class="title">'
            f'{esc(quiz.title)}</div><div class="summary">{len(quiz.questions)} questions · '
            f'repassable autant de fois que nécessaire</div></div><div class="side">{badge}</div>'
            f'<span class="arrow">{icon("arrow")}</span></div>',
            "Ouvrir le quiz de validation", "quiz", quiz=quiz.id, course=course.id)

    section(3, "À propos du parcours")
    c1, c2 = st.columns([1, 1.2], gap="large")
    with c1:
        prerequisites = ", ".join(course.prerequisites) or "Aucun"
        html('<dl class="sx-facts">'
             f'<div><dt>Niveau</dt><dd>{esc(course.level_label)}</dd></div>'
             f'<div><dt>Prérequis</dt><dd>{esc(prerequisites)}</dd></div>'
             f'<div><dt>Durée de lecture</dt><dd>{esc(duration(course.duration_minutes))}</dd></div>'
             f'<div><dt>Accès</dt><dd>{free} en accès libre · {len(course.lessons) - free} réservées aux membres</dd></div>'
             '<div><dt>Format</dt><dd>Leçons écrites, schémas, quiz, exercice</dd></div></dl>')
    with c2:
        ids = []
        for lesson in course.lessons:
            ids += [r for r in lesson.resources if r not in ids]
        resources = [catalog.resource(r) for r in ids if catalog.resource(r)]
        if resources:
            html('<div class="sx-kicker muted" style="margin-bottom:.3rem">Ressources du parcours</div>')
            for index, resource in enumerate(resources):
                book_row(resource, key=f"course_res_{resource.id}", index=index, compact=True)
    footer()


# =============================================================================
# Lesson
# =============================================================================

def lesson_page(catalog: Catalog, email: str | None, route: dict) -> None:
    course = catalog.course(route.get("course") or "")
    lesson = course.lesson(route.get("lesson") or "") if course else None
    if lesson is None:
        _not_found("Cette leçon n'existe pas ou n'est pas encore publiée.")
        return
    member = Member(email)
    progress = member.progress(course)
    module = course.module_of(lesson)

    crumbs("Sensitor", "Academy", course.title, f"Leçon {lesson.number:02d}")
    outline, body = st.columns([0.85, 2.75], gap="large")
    with outline:
        with st.container(key=f"outline_{lesson.id}"):
            rt.link("← Le parcours", "course", key="lesson_back", kind="tertiary", course=course.id)
            html(f'<div class="sx-outline-head">Plan du parcours<b>{esc(course.title)}</b></div>')
            for item in course.lessons:
                state = _outline_state(item, lesson, member, progress)
                tap(f"outline_{item.id}",
                    f'<div class="sx-outline-item{" current" if item.id == lesson.id else ""}">'
                    f'{hexmark(str(item.number), state)}<span class="x">{esc(item.title)}</span></div>',
                    f"Leçon {item.number} : {item.title}", "lesson", course=course.id, lesson=item.id)

    with body:
        with st.container(key=f"mobileonly_outline_{lesson.id}"):
            with st.expander(f"Plan du parcours · leçon {lesson.number} sur {len(course.lessons)}"):
                for item in course.lessons:
                    state = _outline_state(item, lesson, member, progress)
                    tap(f"m_outline_{item.id}",
                        f'<div class="sx-outline-item{" current" if item.id == lesson.id else ""}">'
                        f'{hexmark(str(item.number), state)}<span class="x">{esc(item.title)}</span></div>',
                        f"Leçon {item.number} : {item.title}", "lesson", course=course.id,
                        lesson=item.id)
        done = lesson.id in progress.completed
        state = (pill("Terminée", "done", "check") if done else
                 pill("Accès libre", "free") if lesson.is_public else
                 pill("Premium", "member", "lock") if lesson.access == "premium" else
                 pill("Membres", "member", "lock"))
        chapter = f"Chapitre {numeral(module.number)} · {esc(module.title)}" if module else ""
        html(f'<div class="sx-lesson-head"><div class="no">{lesson.number:02d}</div><div>'
             f'<div class="sx-kicker">{chapter}</div><h1 class="sx-title">{esc(lesson.title)}</h1>'
             f'</div></div><p class="sx-lead" style="margin-top:1rem">{esc(lesson.summary)}</p>'
             f'<div class="sx-meta"><span>{icon("clock")}{esc(duration(lesson.duration_minutes))} de '
             f'lecture</span><span>{state}</span>'
             + (f'<span>quiz · {len(catalog.quiz(lesson.quiz_id).questions)} questions</span>'
                if lesson.quiz_id else "")
             + (f'<span>mis à jour le {esc(date_fr(lesson.updated))}</span>' if lesson.updated else "")
             + '</div>')

        lesson_view.render_objectives(lesson)
        reason = access.lock_reason(lesson.access, email, rt.tier(email))
        if reason == access.UPGRADE:
            with st.container(key="navy_locked"):
                html('<div class="sx-kicker on-navy">Leçon Premium</div>'
                     '<h2 class="sx-h3 on-navy">Cette leçon fait partie de l\'Academy Premium.</h2>'
                     '<p>Votre compte donne accès à toutes les leçons gratuites, aux quiz et à votre '
                     'progression. L\'offre Premium est en préparation : aucun paiement n\'est demandé '
                     'aujourd\'hui.</p>')
            footer()
            return
        if reason == access.SIGN_IN:
            with st.container(key="navy_locked"):
                html('<div class="sx-kicker on-navy">Leçon réservée aux membres</div>'
                     '<h2 class="sx-h3 on-navy">Créez un compte gratuit pour lire la suite.</h2>'
                     '<p>Le compte ouvre toutes les leçons publiées, les quiz et l\'enregistrement de '
                     'votre progression. Aucun moyen de paiement n\'est demandé.</p>')
                rt.link("Se connecter ou créer un compte", "account", key="lesson_unlock", kind="primary")
            footer()
            return

        with st.container(key=f"sheet_{lesson.id}"):
            lesson_view.render_blocks(lesson, catalog, email=email)
            lesson_view.render_sources(lesson)
        lesson_view.render_quiz(lesson, catalog, email=email)
        _lesson_resources(catalog, lesson)
        _completion(course, lesson, member)
        _neighbours(catalog, course, lesson)
    footer()


def _lesson_resources(catalog: Catalog, lesson: Lesson) -> None:
    resources = [catalog.resource(r) for r in lesson.resources if catalog.resource(r)]
    if not resources:
        return
    html('<div class="sx-kicker muted" style="margin:2.2rem 0 .3rem">Ressources liées à cette leçon</div>')
    for index, resource in enumerate(resources):
        book_row(resource, key=f"lesson_res_{lesson.id}_{resource.id}", index=index, compact=True)


def _completion(course: Course, lesson: Lesson, member: Member) -> None:
    with st.container(key=f"navy_done_{lesson.id}"):
        if not member.email:
            html('<div class="sx-kicker on-navy">Fin de la leçon</div><h2 class="sx-h3 on-navy">'
                 'Gardez la trace de votre avancement.</h2><p>Avec un compte gratuit, chaque leçon '
                 'terminée et chaque quiz sont enregistrés dans votre progression.</p>')
            rt.link("Créer un compte gratuit", "account", key="done_signup", kind="primary")
            return
        store = rt.get_store()
        stamp = member.completed_at.get((course.id, lesson.id))
        if stamp:
            html(f'<div class="sx-kicker on-navy">Leçon terminée</div><h2 class="sx-h3 on-navy">'
                 f'Terminée le {esc(date_fr(stamp))}.</h2><p>Elle compte dans votre progression. '
                 f'Vous pouvez la relire autant que nécessaire.</p>')
            if st.button("Marquer comme non terminée", key=f"undo_{lesson.id}", type="tertiary"):
                store.unmark_lesson(member.email, course.id, lesson.id)
                st.rerun()
        else:
            html('<div class="sx-kicker on-navy">Fin de la leçon</div><h2 class="sx-h3 on-navy">'
                 'Avez-vous terminé cette leçon ?</h2><p>La marquer comme terminée l\'ajoute à votre '
                 'progression et vous propose la leçon suivante.</p>')
            if st.button("Marquer la leçon comme terminée", key=f"done_{lesson.id}", type="primary"):
                store.mark_lesson_complete(member.email, course.id, lesson.id, version=lesson.version)
                st.toast("Leçon enregistrée dans votre progression.")
                st.rerun()


def _neighbours(catalog: Catalog, course: Course, lesson: Lesson) -> None:
    previous, following = course.neighbours(lesson.id)
    c1, c2 = st.columns(2)
    with c1:
        if previous:
            tap("nav_prev", f'<div class="sx-next"><span class="k">{icon("back")}Leçon '
                f'{previous.number:02d}</span><span class="t">{esc(previous.title)}</span></div>',
                f"Leçon précédente : {previous.title}", "lesson", course=course.id, lesson=previous.id)
    with c2:
        if following:
            tap("nav_next", f'<div class="sx-next right"><span class="k">Leçon {following.number:02d}'
                f'{icon("arrow")}</span><span class="t">{esc(following.title)}</span></div>',
                f"Leçon suivante : {following.title}", "lesson", course=course.id, lesson=following.id)
        elif course.final_quiz_id:
            tap("nav_quiz", f'<div class="sx-next right"><span class="k">Évaluation{icon("arrow")}'
                f'</span><span class="t">Quiz de validation</span></div>',
                "Quiz de validation", "quiz", quiz=course.final_quiz_id, course=course.id)


# =============================================================================
# Quiz page
# =============================================================================

def quiz_page(catalog: Catalog, email: str | None, route: dict) -> None:
    quiz = catalog.quiz(route.get("quiz") or "")
    if quiz is None:
        _not_found("Ce quiz n'existe pas ou n'est pas encore publié.")
        return
    course = catalog.course(route.get("course") or quiz.course_id or "")
    crumbs("Sensitor", "Academy", *( [course.title] if course else []), "Quiz de validation")
    if course:
        rt.link("← Le parcours", "course", key="quiz_back", kind="tertiary", course=course.id)
    page_header("Évaluation finale", esc(quiz.title), quiz.intro)
    quiz_view.render(quiz, scope="page", catalog=catalog, email=email)
    footer()


# =============================================================================
# Trading Lab
# =============================================================================

def lab(catalog: Catalog, email: str | None, route: dict) -> None:
    crumbs("Sensitor", "Trading Lab")
    page_header(f"Espace {spaces.space('lab').numeral} · Trading Lab", "S'exercer <em>sans capital réel</em>.",
                "Les outils et exercices du programme, réunis au même endroit. Chaque calcul est "
                "celui des leçons, avec ses hypothèses écrites.", display=True)

    section(1, "Calculateur de risque",
            "Montant risqué, distance au stop, ratio gain / risque, taille de position et effet "
            "d'une série de pertes.")
    risk_view.render(scope="lab")

    section(2, "Espérance et risque de ruine",
            "Ce que rapporte une approche en moyenne, et la probabilité de traverser une baisse "
            "donnée avant que son avantage ait le temps de jouer.")
    risk_view.render_ruin(scope="lab")

    section(3, "Exercices pratiques",
            "Des cas chiffrés, résolus étape par étape, avec un corrigé pour chaque étape.")
    shown = 0
    for course in catalog.available_courses():
        for lesson in course.lessons:
            for block in lesson.blocks:
                if block.kind != "exercise" or not catalog.exercise(block.target):
                    continue
                exercise = catalog.exercise(block.target)
                shown += 1
                badge = pill("Libre", "free") if lesson.is_public else pill("Membres", "member", "lock")
                tap(f"lab_ex_{exercise.id}",
                    f'<div class="sx-lesson flush">{hexmark(f"{shown:02d}")}<div><div class="title">'
                    f'{esc(exercise.title)}</div><div class="summary">{len(exercise.steps)} étapes · '
                    f'dans la leçon « {esc(lesson.title)} »</div></div><div class="side">{badge}</div>'
                    f'<span class="arrow">{icon("arrow")}</span></div>',
                    f"Exercice : {exercise.title}", "lesson", course=course.id, lesson=lesson.id)
    if not shown:
        note("Aucun exercice publié pour l'instant.")

    section(4, "En préparation", "Annoncé pour le Trading Lab, pas encore disponible.")
    rows = "".join(f'<li><span class="n">{i:02d}</span><span class="x">{esc(p)}</span>'
                   f'{pill("Prévu", "soon")}</li>'
                   for i, p in enumerate(spaces.space("lab").planned, start=1))
    html(f'<ul class="sx-plan">{rows}</ul>')
    footer()


# =============================================================================
# Progress
# =============================================================================

def progress_page(catalog: Catalog, email: str | None, route: dict) -> None:
    crumbs("Sensitor", "Progression")
    page_header(f"Espace {spaces.space('progress').numeral} · Progression", "Mesurer ce que l'on <em>apprend</em>.",
                "Vos leçons terminées, vos quiz et les notions à revoir, calculés à partir de ce "
                "que vous avez réellement fait.")
    if not email:
        with st.container(key="navy_progress_locked"):
            html('<div class="sx-kicker on-navy">Réservé aux membres</div><h2 class="sx-h3 on-navy">'
                 'Connectez-vous pour suivre votre progression.</h2><p>La progression est '
                 'personnelle : elle n\'est visible que par vous.</p>')
            rt.link("Se connecter ou créer un compte", "account", key="prompt_signin", kind="primary")
        footer()
        return
    member = Member(email)
    courses = catalog.available_courses()
    total = sum(len(c.lessons) for c in courses)
    done = sum(member.progress(c).done for c in courses)
    finals = [c.final_quiz_id for c in courses if c.final_quiz_id]
    html('<div class="sx-stats" style="margin-top:2rem">'
         f'<div><div class="l">Leçons terminées</div><div class="v">{done}<small> / {total}</small></div>'
         f'<div class="d">dans les parcours ouverts</div></div>'
         f'<div><div class="l">Quiz de validation</div><div class="v">'
         f'{sum(1 for q in finals if q in member.passed)}<small> / {len(finals)}</small></div>'
         f'<div class="d">réussi</div></div>'
         f'<div><div class="l">Tentatives de quiz</div><div class="v">{len(member.attempts)}</div>'
         f'<div class="d">contrôles et évaluations</div></div></div>')

    section(1, "Par parcours")
    for course in courses:
        progress = member.progress(course)
        html(f'<div class="sx-kicker muted" style="margin:.4rem 0 .6rem">{esc(course.title)} · '
             f'{progress.done} / {progress.total}</div>{progress_bar(progress.fraction)}')
        for lesson in course.lessons:
            state = lesson_state(lesson, member, progress)
            when = date_fr(member.completed_at.get((course.id, lesson.id), ""))
            tap(f"prog_{lesson.id}", lesson_row(lesson, state, flush=True, when=when),
                f"Leçon {lesson.number} : {lesson.title}", "lesson", course=course.id, lesson=lesson.id)

    section(2, "Historique des quiz", "Vos tentatives, de la plus récente à la plus ancienne.")
    if not member.attempts:
        note("Aucun quiz passé pour l'instant. Un contrôle de compréhension conclut chaque leçon.")
    else:
        rows = "".join(
            f"<tr><td>{esc(date_fr(a['created_at']))}</td>"
            f"<td>{esc(catalog.quiz(a['quiz_id']).title if catalog.quiz(a['quiz_id']) else a['quiz_id'])}</td>"
            f"<td>{a['correct']} / {a['total']}</td><td>{'Réussi' if a['passed'] else 'Non validé'}</td></tr>"
            for a in member.attempts[:30])
        html('<table><thead><tr><th>Date</th><th>Quiz</th><th>Score</th><th>Résultat</th></tr>'
             f'</thead><tbody>{rows}</tbody></table>')
        _mistakes(catalog, member.attempts)

    section(4, "Vos données", "Votre progression vous appartient : exportez-la à tout moment.")
    store = rt.get_store()
    if store is not None:
        payload = json.dumps({"lesson_progress": store.completed_lessons(email),
                              "quiz_attempts": store.quiz_attempts(email, limit=100_000)},
                             ensure_ascii=False, indent=2)
        st.download_button("Exporter ma progression (JSON)", data=payload.encode("utf-8"),
                           file_name="sensitor-progression.json", mime="application/json",
                           key="export_progress")
    footer()


def _mistakes(catalog: Catalog, attempts) -> None:
    latest: dict[str, dict] = {}
    for attempt in attempts:
        latest.setdefault(attempt["quiz_id"], attempt)
    missed = []
    for quiz_id, attempt in latest.items():
        quiz = catalog.quiz(quiz_id)
        if quiz is None or attempt["quiz_version"] != quiz.version:
            continue
        for question in quiz.questions:
            if set(attempt["responses"].get(question.id, [])) != set(question.correct_ids):
                missed.append((quiz, question))
    section(3, "À revoir", "Les questions manquées lors de votre dernière tentative de chaque quiz.")
    if not missed:
        note("Rien à revoir : votre dernière tentative de chaque quiz est sans erreur.")
        return
    for index, (quiz, question) in enumerate(missed):
        lesson = catalog.find_lesson(question.lesson_id) if question.lesson_id else None
        fragment = (f'<div class="sx-lesson flush">{hexmark("?", "todo")}<div><div class="title" '
                    f'style="font-size:1.08rem">{esc(question.prompt)}</div><div class="summary">'
                    f'{esc(quiz.title)}{" · relire : " + esc(lesson.title) if lesson else ""}</div></div>'
                    f'<div class="side"></div><span class="arrow">{icon("arrow")}</span></div>')
        if lesson:
            tap(f"miss_{index}", fragment, f"Relire : {lesson.title}", "lesson",
                course=lesson.course_id, lesson=lesson.id)
        else:
            html(fragment)


def _not_found(text: str) -> None:
    crumbs("Sensitor", "Introuvable")
    page_header("Erreur 404", "Page <em>introuvable</em>", text)
    rt.link("Retour à l'accueil", "home", key="nf_home", kind="primary")
    footer()
