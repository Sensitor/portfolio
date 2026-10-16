"""
The quiz component.

Two modes, chosen by the quiz file:

* **immediate** — each question has its own « Vérifier » button and shows its
  explanation at once. When every question has been checked, the attempt is
  scored and, for a signed-in member, stored.
* **deferred** — the member answers everything, submits once, then reviews the
  full correction. Unanswered questions trigger a confirmation before
  submitting, and are reported as unanswered rather than wrong.

A segmented bar at the top shows where the member is: answered, right, wrong.
Scoring is `academy.quiz.grade`; this module only collects answers and renders
the result. Widget keys include a run counter so « Recommencer » starts from a
clean slate without touching other quizzes on the page.
"""

from __future__ import annotations

import streamlit as st

from ...platform.ui import runtime as rt
from ...platform.ui.components import date_fr, esc, html, icon
from .. import access
from .. import quiz as Q
from ..content import Catalog, Question, Quiz


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


def _steps(quiz: Quiz, scope: str, run: int, state: dict) -> str:
    cells = []
    result = state["result"]
    for index, question in enumerate(quiz.questions):
        if result is not None:
            cls = result.results[index].status
        elif question.id in state["checked"]:
            cls = Q.grade_question(question, state["checked"][question.id]).status
        elif _selection(scope, quiz, run, question):
            cls = "answered"
        else:
            cls = ""
        cells.append(f'<i class="{cls}"></i>')
    return f'<div class="sx-steps" aria-hidden="true">{"".join(cells)}</div>'


def render(quiz: Quiz, *, scope: str, catalog: Catalog, email: str | None) -> None:
    state = _state(scope, quiz)
    run = state["run"]
    total = len(quiz.questions)
    required = Q.required_correct(total, quiz.pass_threshold)
    immediate = quiz.feedback == "immediate"

    with st.container(key=f"panel_quiz_{scope}_{quiz.id}"):
        kicker = "Contrôle de compréhension" if immediate else "Évaluation · correction à la fin"
        html(f'<div class="sx-kicker">{kicker}</div><h2 class="sx-h3">{esc(quiz.title)}</h2>'
             f'<div class="sx-meta" style="margin-top:.4rem"><span><b>{total}</b> question'
             f'{"s" if total > 1 else ""}</span><span>réussite à <b>{required} / {total}</b></span>'
             f'<span>{"correction après chaque question" if immediate else "une seule soumission"}'
             f'</span></div>')

        if not access.can_take_quiz(catalog, quiz, email):
            html('<p class="sx-body" style="margin-top:1rem">Ce quiz est réservé aux membres. Créez '
                 'un compte gratuit pour le passer et garder la trace de vos résultats.</p>')
            rt.link("Se connecter ou créer un compte", "account", key=f"qlock_{scope}_{quiz.id}",
                    kind="primary")
            return

        _history(quiz, email)
        html(_steps(quiz, scope, run, state))

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
        html('<p class="sx-note" style="margin-top:1rem">Vous n\'êtes pas connecté : vos réponses '
             'sont corrigées mais pas enregistrées.</p>')
        return
    store = rt.get_store()
    attempts = store.quiz_attempts(email, quiz.id, limit=50) if store else []
    if not attempts:
        return
    last = attempts[0]
    best = max(attempts, key=lambda a: a["correct"])
    verdict = "réussi" if last["passed"] else "non validé"
    html(f'<p class="sx-note" style="margin-top:1rem">Dernière tentative le '
         f'{esc(date_fr(last["created_at"]))} : <b>{last["correct"]} / {last["total"]}</b> '
         f'({verdict}) · meilleur score {best["correct"]} / {best["total"]} · '
         f'{len(attempts)} tentative{"s" if len(attempts) > 1 else ""}.</p>')


def _question_head(index: int, total: int, question: Question) -> None:
    hint = " · plusieurs réponses possibles" if question.kind == "multiple" else ""
    html(f'<div class="sx-qhead"><div class="q">Q{index}</div><div><div class="k">Question {index} '
         f'sur {total}{hint}</div><div class="p">{esc(question.prompt)}</div></div></div>')


def _question(quiz: Quiz, question: Question, index: int, total: int, *, scope: str,
              run: int, state: dict, immediate: bool, catalog: Catalog) -> None:
    checked = question.id in state["checked"]
    _question_head(index, total, question)
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
        _feedback(question, Q.grade_question(question, state["checked"][question.id]),
                  catalog, scope, show_lesson=False)
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
            mark, cls = icon("check"), "ok"
        elif option.id in selected:
            mark, cls = icon("cross"), "ko"
        else:
            continue
        chosen = " (votre choix)" if option.id in selected else ""
        items.append(f'<li class="{cls}"><span class="mark">{mark}</span><b>{esc(option.text)}</b>'
                     f'{chosen}<span class="why">{esc(option.explanation)}</span></li>')
    general = f'<p class="general">{esc(question.explanation)}</p>' if question.explanation else ""
    html(f'<div class="sx-feedback {outcome.status}"><div class="status">{titles[outcome.status]}'
         f'</div><ul>{"".join(items)}</ul>{general}</div>')

    if show_lesson and question.lesson_id and outcome.status != Q.CORRECT:
        lesson = catalog.find_lesson(question.lesson_id)
        if lesson:
            rt.link(f"Relire : {lesson.title}", "lesson", key=f"reread_{scope}_{question.id}",
                    kind="tertiary", course=lesson.course_id, lesson=lesson.id)


def _record(quiz: Quiz, result: Q.QuizResult, email: str | None) -> None:
    store = rt.get_store()
    if email and store is not None:
        store.record_quiz_attempt(email, quiz.id, version=result.quiz_version,
                                  correct=result.correct_count, total=result.total,
                                  passed=result.passed, responses=result.responses())


def _banner(result: Q.QuizResult, verdict: str, detail: str) -> None:
    fill = result.correct_count / result.total * 100
    mark = result.required / result.total * 100
    html(f'<div class="sx-result"><div class="big">{result.correct_count}<small> / {result.total}'
         f'</small></div><div><div class="k {"pass" if result.passed else "fail"}">{esc(verdict)}</div>'
         f'<p>{esc(detail)}</p><div class="meter" aria-hidden="true"><i style="width:{fill:.0f}%"></i>'
         f'<b style="left:{mark:.0f}%"></b></div></div></div>')


def _immediate_summary(quiz: Quiz, state: dict, email: str | None, scope: str) -> None:
    if len(state["checked"]) < len(quiz.questions):
        return
    result = Q.grade(quiz, state["checked"])
    if not state["recorded"]:
        _record(quiz, result, email)
        state["recorded"] = True
    verdict = "Notion acquise" if result.passed else "À consolider"
    detail = (("Résultat enregistré dans votre progression. " if email else "")
              + ("Vous pouvez passer à la suite." if result.passed
                 else "Relisez les passages concernés avant de poursuivre."))
    _banner(result, verdict, detail)
    _restart_button(state, scope, quiz)


def _deferred_submit(quiz: Quiz, state: dict, email: str | None, scope: str, run: int) -> None:
    responses = {q.id: _selection(scope, quiz, run, q) for q in quiz.questions}
    missing = [i for i, q in enumerate(quiz.questions, start=1) if not responses[q.id]]
    html('<hr class="sx-hr">')

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
            if st.button("Soumettre quand même", key=f"force_{scope}_{quiz.id}_{run}", type="primary"):
                submit()
                st.rerun()
        with cols[1]:
            if st.button("Revenir aux questions", key=f"back_{scope}_{quiz.id}_{run}"):
                state["confirm"] = False
                st.rerun()
        return

    answered = len(quiz.questions) - len(missing)
    html(f'<p class="sx-note">{answered} / {len(quiz.questions)} questions répondues.</p>')
    if st.button("Soumettre mes réponses", key=f"submit_{scope}_{quiz.id}_{run}", type="primary"):
        if missing:
            state["confirm"] = True
        else:
            submit()
        st.rerun()


def _review(quiz: Quiz, result: Q.QuizResult, catalog: Catalog, scope: str) -> None:
    verdict = "Quiz validé" if result.passed else "Pas encore validé"
    detail = (f"Seuil de réussite : {result.required} / {result.total}."
              + (f" {result.unanswered_count} question(s) sans réponse." if result.unanswered_count else "")
              + (" La correction de chaque question suit ; chaque erreur renvoie à sa leçon."
                 if result.mistakes else ""))
    _banner(result, verdict, detail)
    for index, (question, outcome) in enumerate(zip(quiz.questions, result.results), start=1):
        _question_head(index, len(quiz.questions), question)
        _feedback(question, outcome, catalog, scope, show_lesson=True)


def _restart_button(state: dict, scope: str, quiz: Quiz) -> None:
    if st.button("Recommencer", key=f"restart_{scope}_{quiz.id}_{state['run']}"):
        state.update(run=state["run"] + 1, checked={}, result=None, recorded=False, confirm=False)
        st.rerun()
