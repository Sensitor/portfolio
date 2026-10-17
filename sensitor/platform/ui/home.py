"""
The platform home: a presentation of Sensitor for visitors, a dashboard for
members. Every number shown is counted from the published content or from the
member's own rows — nothing is illustrative.
"""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from ...academy import progress as P
from .. import brand
from . import runtime as rt
from .components import (crumbs, date_fr, duration, esc, footer, hexmark, html, icon,
                         note, numeral, page_header, progress_bar, section, tap)
from .spaces_view import space_cards

STRUCTURE_ART = """
<svg viewBox="0 0 440 260" role="img" aria-label="Une tendance haussière décrite par ses sommets et ses creux de swing">
<g stroke="#ffffff14"><line x1="0" y1="50" x2="440" y2="50"/><line x1="0" y1="115" x2="440" y2="115"/>
<line x1="0" y1="180" x2="440" y2="180"/><line x1="0" y1="245" x2="440" y2="245"/></g>
<polyline points="12,232 88,152 130,192 214,104 256,148 340,64 382,100 432,30" fill="none" stroke="#a9c6e2" stroke-width="2.2" stroke-linejoin="round"/>
<g stroke="#a9c6e2" stroke-opacity=".4" stroke-dasharray="3 5"><line x1="88" y1="152" x2="214" y2="152"/>
<line x1="214" y1="104" x2="340" y2="104"/><line x1="130" y1="192" x2="256" y2="192"/><line x1="256" y1="148" x2="382" y2="148"/></g>
<g fill="#0f1b26" stroke="#a9c6e2" stroke-width="1.6"><circle cx="88" cy="152" r="4.5"/><circle cx="214" cy="104" r="4.5"/><circle cx="340" cy="64" r="4.5"/></g>
<g fill="#a9c6e2"><circle cx="130" cy="192" r="4.5"/><circle cx="256" cy="148" r="4.5"/><circle cx="382" cy="100" r="4.5"/></g>
<g font-family="DM Mono, monospace" font-size="11.5" fill="#a9b7c4"><text x="76" y="137">S1</text><text x="202" y="89">S2</text>
<text x="328" y="49">S3</text><text x="120" y="215">C1</text><text x="246" y="171">C2</text><text x="372" y="123">C3</text></g>
</svg>
"""

LOOP = (("Comprendre", "Une notion, définie précisément, avec un schéma."),
        ("Observer", "La notion appliquée à un cas, chiffres à l'appui."),
        ("Pratiquer", "Un quiz ou un exercice, sans capital réel."),
        ("Corriger", "Chaque réponse expliquée, juste ou fausse."),
        ("Réviser", "Les erreurs reviennent dans la progression."))


def render(catalog, email, route) -> None:
    if email:
        _dashboard(catalog, email)
    else:
        _landing(catalog)
    footer()


def _counts(catalog) -> tuple[int, int, int]:
    lessons = sum(len(c.lessons) for c in catalog.available_courses())
    questions = sum(len(q.questions) for q in catalog.quizzes.values())
    return lessons, questions, len(catalog.paths)


def _landing(catalog) -> None:
    lessons, questions, paths = _counts(catalog)
    course = next(iter(catalog.available_courses()), None)

    with st.container(key="navy_hero"):
        left, right = st.columns([1.2, 0.8], vertical_alignment="center", gap="large")
        with left:
            html('<div class="sx-kicker on-navy">Sensitor · Trading, Bitcoin et crypto</div>'
                 '<h1 class="sx-display on-navy">Apprendre le trading.<br><em>Maîtriser ses '
                 'décisions.</em></h1><p class="sx-lead on-navy">Des parcours structurés pour apprendre '
                 'à lire un marché, mesurer son risque et évaluer ses décisions, complétés par une filière '
                 'sur la monnaie, Bitcoin et la crypto pour comprendre ce qui porte les marchés et '
                 'préserver un patrimoine. Leçons sourcées, quiz corrigés, simulateurs et outils '
                 'd\'analyse, sur un seul compte.</p>')
            b1, b2, _ = st.columns([1, 1, 0.6])
            with b1:
                if course:
                    rt.link("Commencer le parcours", "course", key="hero_start",
                            kind="primary", course=course.id)
            with b2:
                rt.link("Créer un compte gratuit", "account", key="hero_account")
        with right:
            html(f'<div class="sx-hero-art">{STRUCTURE_ART}</div>')
        html('<div class="sx-figures-navy">'
             f'<div><div class="v">{lessons}</div><div class="l">leçons publiées</div></div>'
             f'<div><div class="v">{questions}</div><div class="l">questions corrigées</div></div>'
             f'<div><div class="v">{paths}<small> parcours</small></div><div class="l">au '
             f'programme, ouverts un à un</div></div></div>'
             f'<div class="sx-watermark">{brand.monogram_svg(320, color="#ffffff")}</div>')

    section(1, "Apprendre, trader, investir : un seul compte",
            "Chaque espace partage la même identité et le même compte. Ceux qui ne sont pas encore "
            "prêts le disent, et ouvrent quand ils le sont réellement.")
    space_cards(key="home_space")

    if course:
        section(2, "Le premier parcours", course.summary)
        _feature(catalog, course, key="home_feature")
        public = [l for l in course.lessons if l.is_public]
        if public:
            html('<div class="sx-kicker muted" style="margin:2rem 0 .3rem">En accès libre, sans '
                 'compte</div>')
            for lesson in public:
                tap(f"home_free_{lesson.id}", _lesson_row(lesson, "todo", flush=True),
                    f"Leçon {lesson.number} : {lesson.title}", "lesson",
                    course=course.id, lesson=lesson.id)

    section(3, "Une boucle d'apprentissage",
            "Chaque leçon suit le même cycle, du concept à la correction de vos propres réponses.")
    steps = "".join(f'<div><span class="hx">{hexmark(f"{i:02d}", "current" if i == 1 else "todo")}'
                    f'</span><div class="t">{esc(t)}</div><div class="x">{esc(x)}</div></div>'
                    for i, (t, x) in enumerate(LOOP, start=1))
    html(f'<div class="sx-process">{steps}</div>')

    html('<p class="sx-note" style="margin-top:3rem">Sensitor est un service de formation. Aucun '
         'contenu ne constitue un conseil en investissement ni une promesse de résultat. Le trading '
         'comporte un risque de perte en capital.</p>')


def _feature(catalog, course, *, key: str) -> None:
    path = catalog.path(course.path_id)
    tap(key,
        f'<div class="sx-feature"><div class="numeral">{numeral(path.number if path else 1)}</div>'
        f'<div><div class="sx-kicker">{esc(path.label) if path else "Parcours"} · '
        f'{esc(path.title if path else "")}</div><div class="t">{esc(course.title)}</div>'
        f'<div class="s">{esc(course.summary)}</div><div class="sx-meta"><span>'
        f'<b>{len(course.lessons)}</b> leçons</span><span><b>{esc(duration(course.duration_minutes))}'
        f'</b></span><span>niveau {esc(course.level_label.lower())}</span><span>quiz de validation'
        f'</span></div></div><span class="go">{icon("arrow")}</span></div>',
        f"Ouvrir le parcours {course.title}", "course", course=course.id)


def _lesson_row(lesson, state: str, *, flush: bool = False) -> str:
    access = ('<span class="sx-pill free">Libre</span>' if lesson.is_public
              else f'<span class="sx-pill member">{icon("lock")}Membres</span>')
    return (f'<div class="sx-lesson{" flush" if flush else ""}">{hexmark(f"{lesson.number:02d}", state)}'
            f'<div><div class="title">{esc(lesson.title)}</div><div class="summary">'
            f'{esc(lesson.summary)}</div></div><div class="side">{esc(duration(lesson.duration_minutes))}'
            f'{access}</div><span class="arrow">{icon("arrow")}</span></div>')


def _dashboard(catalog, email: str) -> None:
    store = rt.get_store()
    rows = store.completed_lessons(email) if store else []
    attempts = store.quiz_attempts(email, limit=10_000) if store else []
    completed = P.completed_by_course(rows)
    passed = P.passed_quiz_ids(attempts)

    crumbs("Sensitor", "Vue d'ensemble")
    page_header(f"{esc(date_fr(datetime.now(), with_day=True))} · Votre espace",
                "Reprendre là où <em>vous en êtes</em>.",
                "Votre prochaine étape, votre progression réelle et les espaces disponibles.")

    step = P.next_step(catalog, completed, passed)
    left, right = st.columns([1.25, 1], gap="large")
    with left:
        if step.kind == "lesson":
            progress = P.course_progress(step.course, completed.get(step.course.id, set()),
                                         passed_quizzes=passed)
            verb = "Reprendre" if progress.started else "Commencer"
            tap("dash_next",
                f'<div class="sx-start"><div class="sx-kicker on-navy">{verb} · '
                f'{esc(step.course.title)}</div><div class="t">{esc(step.lesson.title)}</div>'
                f'<div class="s">{esc(step.lesson.summary)}</div><div class="bar"><i style="width:'
                f'{progress.fraction * 100:.0f}%"></i></div><div class="foot"><span>Leçon '
                f'{step.lesson.number} sur {progress.total} · {esc(duration(step.lesson.duration_minutes))}'
                f'</span><span class="go">{verb} {icon("arrow")}</span></div></div>',
                f"{verb} la leçon {step.lesson.title}", "lesson",
                course=step.course.id, lesson=step.lesson.id)
        elif step.kind == "final_quiz":
            quiz = catalog.quiz(step.course.final_quiz_id)
            tap("dash_quiz",
                f'<div class="sx-start"><div class="sx-kicker on-navy">Évaluation · '
                f'{esc(step.course.title)}</div><div class="t">Toutes les leçons sont terminées.</div>'
                f'<div class="s">Il reste le quiz de validation pour vérifier l\'ensemble du '
                f'parcours.</div><div class="foot"><span>{len(quiz.questions)} questions</span>'
                f'<span class="go">Passer le quiz {icon("arrow")}</span></div></div>',
                "Passer le quiz de validation", "quiz", quiz=quiz.id, course=step.course.id)
        else:
            tap("dash_done",
                '<div class="sx-start"><div class="sx-kicker on-navy">Parcours terminés</div>'
                '<div class="t">Vous avez terminé les parcours ouverts.</div><div class="s">Le '
                'Trading Lab et la bibliothèque restent à votre disposition ; les prochains parcours '
                f'sont en préparation.</div><div class="foot"><span>Trading Lab</span><span class="go">'
                f'Ouvrir {icon("arrow")}</span></div></div>', "Ouvrir le Trading Lab", "lab")
    with right:
        courses = catalog.available_courses()
        total = sum(len(c.lessons) for c in courses)
        done = sum(P.course_progress(c, completed.get(c.id, set())).done for c in courses)
        finals = [c.final_quiz_id for c in courses if c.final_quiz_id]
        last = attempts[0] if attempts else None
        last_quiz = catalog.quiz(last["quiz_id"]) if last else None
        last_text = "Aucun pour l'instant"
        if last:
            title = last_quiz.title if last_quiz else last["quiz_id"]
            last_text = f"{title} : {last['correct']} / {last['total']}"
        html('<div class="sx-facts" style="height:100%">'
             f'<div><dt>Leçons terminées</dt><dd><b>{done}</b> / {total}</dd></div>'
             f'<div><dt>Quiz de validation</dt><dd><b>{sum(1 for q in finals if q in passed)}</b>'
             f' / {len(finals)} réussi</dd></div>'
             f'<div><dt>Quiz passés</dt><dd>{len(attempts)} tentative{"s" if len(attempts) > 1 else ""}</dd></div>'
             f'<div><dt>Dernier quiz</dt><dd>{esc(last_text)}</dd></div>'
             '</div>')
        rt.link("Voir ma progression détaillée", "progress", key="dash_progress", kind="tertiary")

    section(1, "Vos parcours", "Votre avancement dans chaque parcours ouvert.")
    for course in catalog.available_courses():
        progress = P.course_progress(course, completed.get(course.id, set()), passed_quizzes=passed)
        _feature(catalog, course, key=f"dash_feature_{course.id}")
        html(f'<div style="margin:.8rem 0 0 0">{progress_bar(progress.fraction, f"{progress.done} / {progress.total} leçons terminées")}</div>')

    section(2, "Vos espaces", "Tous les espaces Sensitor, avec leur état réel.")
    space_cards(key="dash_space")
    note("Les espaces en préparation n'ont encore aucune fonctionnalité active.")
