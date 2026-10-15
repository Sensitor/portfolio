"""
The quiz component.

Two modes, chosen by the quiz file:

* **immediate** — each question has its own « Vérifier » button and shows its
  explanation at once. When every question has been checked, the attempt is
  scored and, for a signed-in member, stored.
* **deferred** — the member answers everything, submits once, then reviews the
  full correction. Unanswered questions trigger a confirmation before
  submitting, and are reported as unanswered rather than wrong.

Scoring is `academy.quiz.grade`; this module only collects answers and renders
the result. Widget keys include a run counter so « Recommencer » starts from a
clean slate without touching other quizzes on the page.
"""

from __future__ import annotations

import streamlit as st

from .. import access
from .. import quiz as Q
from ..content import Catalog, Question, Quiz
from . import runtime as rt
from .components import date_fr, esc, html


def _state(scope: str, quiz: Quiz) -> dict:
    key = f"quiz::{scope}::{quiz.id}"
    if key not in st.session_state:
        st.session_state[key] = {"run": 0, "checked": {}, "result": None,
                                 "recorded": False, "confirm": False}
    return st.session_state[key]


def _widget_key(scope: str, quiz: Quiz, run: int, question: Question, option: str = "") -> str:
    return f"quizw::{scope}::{quiz.id}::{run}::{question.id}::{option}"


def _selection(scope: str, quiz: Quiz, run: int, question: Question) -> list[str]:
    if question.kind == "single":
        value = st.session_state.get(_widget_key(scope, quiz, run, question))
        return [value] if value else []
    return [o.id for o in question.options
            if st.session_state.get(_widget_key(scope, quiz, run, question, o.id))]


def render(quiz: Quiz, *, scope: str, catalog: Catalog, email: str | None) -> None:
    state = _state(scope, quiz)
    run = state["run"]
    total = len(quiz.questions)
    required = Q.required_correct(total, quiz.pass_threshold)
    immediate = quiz.feedback == "immediate"

    with st.container(key=f"panel_quiz_{scope}_{quiz.id}"):
        kicker = "Contrôle de compréhension" if immediate else "Évaluation"
        meta = f"{total} question{'s' if total > 1 else ''} · réussite à {required} / {total}"
        intro = f'<p class="ac-sub">{esc(quiz.intro)}</p>' if quiz.intro else ""
        html(f'<div class="ac-eyebrow">{kicker} · {meta}</div>'
             f'<h3 class="ac-h3" style="margin-top:.5rem">{esc(quiz.title)}</h3>{intro}')

        if not access.can_take_quiz(catalog, quiz, email):
            html('<p class="ac-sub">Ce quiz est réservé aux membres. Créez un compte '
                 'gratuit pour le passer et garder la trace de vos résultats.</p>')
            rt.link("Se connecter ou créer un compte", "account", key=f"qlock_{scope}_{quiz.id}",
                    kind="primary")
            return

        _history(quiz, email)

        if state["result"] is not None and not immediate:
            _review(quiz, state["result"], catalog, scope)
            _restart_button(state, scope, quiz)
            return

        for index, question in enumerate(quiz.questions, start=1):
            _question(quiz, question, index, total, scope=scope, run=run,
                      state=state, immediate=immediate, catalog=catalog)

        if immediate:
            _immediate_summary(quiz, state, email, scope)
        else:
            _deferred_submit(quiz, state, email, scope, run)


def _history(quiz: Quiz, email: str | None) -> None:
    if not email:
        html('<p class="ac-sub">Vous n\'êtes pas connecté : vos réponses seront corrigées '
             'mais pas enregistrées.</p>')
        return
    store = rt.get_store()
    attempts = store.quiz_attempts(email, quiz.id, limit=50) if store else []
    if not attempts:
        return
    last = attempts[0]
    best = max(attempts, key=lambda a: a["correct"])
    verdict = "réussi" if last["passed"] else "non validé"
    html(f'<p class="ac-sub">Dernière tentative le {esc(date_fr(last["created_at"]))} : '
         f'<b>{last["correct"]} / {last["total"]}</b> ({verdict}). '
         f'Meilleur score : {best["correct"]} / {best["total"]} · '
         f'{len(attempts)} tentative{"s" if len(attempts) > 1 else ""}.</p>')


def _question(quiz: Quiz, question: Question, index: int, total: int, *, scope: str,
              run: int, state: dict, immediate: bool, catalog: Catalog) -> None:
    checked = question.id in state["checked"]
    hint = " · plusieurs réponses possibles" if question.kind == "multiple" else ""
    html(f'<div style="margin-top:1rem" class="ac-eyebrow">Question {index} / {total}{hint}</div>'
         f'<p class="ac-question">{esc(question.prompt)}</p>')

    labels = {o.id: o.text for o in question.options}
    if question.kind == "single":
        st.radio(question.prompt, options=[o.id for o in question.options],
                 format_func=labels.get, index=None, label_visibility="collapsed",
                 key=_widget_key(scope, quiz, run, question), disabled=checked)
    else:
        for option in question.options:
            st.checkbox(option.text, key=_widget_key(scope, quiz, run, question, option.id),
                        disabled=checked)

    if not immediate:
        return
    if checked:
        outcome = Q.grade_question(question, state["checked"][question.id])
        _feedback(question, outcome, catalog, scope, show_lesson=False)
        return
    selected = _selection(scope, quiz, run, question)
    if st.button("Vérifier", key=f"check_{scope}_{quiz.id}_{run}_{question.id}",
                 disabled=not selected):
        state["checked"][question.id] = selected
        st.rerun()


def _feedback(question: Question, outcome: Q.QuestionResult, catalog: Catalog,
              scope: str, *, show_lesson: bool) -> None:
    titles = {Q.CORRECT: "Bonne réponse", Q.INCORRECT: "Réponse incorrecte",
              Q.UNANSWERED: "Sans réponse"}
    items = []
    selected = set(outcome.selected)
    for option in question.options:
        if option.correct:
            mark, cls = "✓", "ok"
        elif option.id in selected:
            mark, cls = "×", "ko"
        else:
            continue
        chosen = " — votre choix" if option.id in selected else ""
        items.append(f'<li class="{cls}"><span class="mark">{mark}</span>'
                     f'<b>{esc(option.text)}</b>{chosen}'
                     f'<span class="why">{esc(option.explanation)}</span></li>')
    general = f'<p style="margin:.6rem 0 0">{esc(question.explanation)}</p>' \
        if question.explanation else ""
    html(f'<div class="ac-feedback {outcome.status}"><div class="status">'
         f'{titles[outcome.status]}</div><ul>{"".join(items)}</ul>{general}</div>')

    if show_lesson and question.lesson_id and outcome.status != Q.CORRECT:
        lesson = catalog.find_lesson(question.lesson_id)
        if lesson:
            rt.link(f"Relire : {lesson.title}", "lesson",
                    key=f"reread_{scope}_{question.id}", kind="tertiary",
                    course=lesson.course_id, lesson=lesson.id)


def _record(quiz: Quiz, result: Q.QuizResult, email: str | None) -> None:
    store = rt.get_store()
    if email and store is not None:
        store.record_quiz_attempt(email, quiz.id, version=result.quiz_version,
                                  correct=result.correct_count, total=result.total,
                                  passed=result.passed, responses=result.responses())


def _immediate_summary(quiz: Quiz, state: dict, email: str | None, scope: str) -> None:
    if len(state["checked"]) < len(quiz.questions):
        return
    result = Q.grade(quiz, state["checked"])
    if not state["recorded"]:
        _record(quiz, result, email)
        state["recorded"] = True
    verdict = ("Notion acquise." if result.passed
               else "Relisez les passages concernés avant de poursuivre.")
    html(f'<div class="ac-rule"></div><div class="ac-score"><span class="big">'
         f'{result.correct_count} / {result.total}</span><span class="ac-sub">{verdict}'
         f'{" Résultat enregistré dans votre progression." if email else ""}</span></div>')
    _restart_button(state, scope, quiz)


def _deferred_submit(quiz: Quiz, state: dict, email: str | None, scope: str, run: int) -> None:
    responses = {q.id: _selection(scope, quiz, run, q) for q in quiz.questions}
    missing = [i for i, q in enumerate(quiz.questions, start=1) if not responses[q.id]]
    html('<div class="ac-rule"></div>')

    def submit():
        result = Q.grade(quiz, responses)
        _record(quiz, result, email)
        state["result"] = result
        state["confirm"] = False

    if state["confirm"] and missing:
        numbers = ", ".join(str(n) for n in missing)
        st.warning(f"{len(missing)} question{'s' if len(missing) > 1 else ''} sans réponse "
                   f"(n° {numbers}). Elles seront comptées comme non réussies.")
        cols = st.columns([1, 1, 2])
        with cols[0]:
            if st.button("Soumettre quand même", key=f"force_{scope}_{quiz.id}_{run}",
                         type="primary"):
                submit()
                st.rerun()
        with cols[1]:
            if st.button("Revenir aux questions", key=f"back_{scope}_{quiz.id}_{run}"):
                state["confirm"] = False
                st.rerun()
        return

    if st.button("Soumettre mes réponses", key=f"submit_{scope}_{quiz.id}_{run}", type="primary"):
        if missing:
            state["confirm"] = True
        else:
            submit()
        st.rerun()


def _review(quiz: Quiz, result: Q.QuizResult, catalog: Catalog, scope: str) -> None:
    verdict = "Quiz validé" if result.passed else "Pas encore validé"
    detail = (f"Seuil de réussite : {result.required} / {result.total}."
              + (f" {result.unanswered_count} question(s) sans réponse."
                 if result.unanswered_count else ""))
    html(f'<div class="ac-rule"></div><div class="ac-eyebrow">{verdict}</div>'
         f'<div class="ac-score"><span class="big">{result.correct_count} / {result.total}</span>'
         f'<span class="ac-sub">{esc(detail)}</span></div>')
    if result.mistakes:
        html('<p class="ac-sub" style="margin-top:.8rem">La correction de chaque question '
             'suit. Pour chaque erreur, un lien renvoie à la leçon qui traite la notion.</p>')
    for index, (question, outcome) in enumerate(zip(quiz.questions, result.results), start=1):
        html(f'<div style="margin-top:1.1rem" class="ac-eyebrow">Question {index}</div>'
             f'<p class="ac-question">{esc(question.prompt)}</p>')
        _feedback(question, outcome, catalog, scope, show_lesson=True)


def _restart_button(state: dict, scope: str, quiz: Quiz) -> None:
    if st.button("Recommencer", key=f"restart_{scope}_{quiz.id}_{state['run']}"):
        state.update(run=state["run"] + 1, checked={}, result=None, recorded=False,
                     confirm=False)
        st.rerun()
