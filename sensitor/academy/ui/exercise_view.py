"""
The numeric exercise component: one input per step, checked together, then the
worked solution for every step — right or wrong, since the reasoning is the
point. A member who prefers to read the solution first can reveal it directly.
"""

from __future__ import annotations

import streamlit as st

from .. import exercise as X
from ..content import Exercise
from ...platform.ui.components import esc, html, md

LABELS = {X.CORRECT: "Juste", X.INCORRECT: "À revoir", X.UNANSWERED: "Sans réponse",
          X.INVALID: "Nombre illisible"}
CLASSES = {X.CORRECT: "correct", X.INCORRECT: "incorrect", X.UNANSWERED: "neutral",
           X.INVALID: "neutral"}


def render(exercise: Exercise, *, scope: str) -> None:
    key = f"ex::{scope}::{exercise.id}"
    state = st.session_state.setdefault(key, {"run": 0, "checked": False, "revealed": False})
    run = state["run"]

    with st.container(key=f"panel_ex_{scope}_{exercise.id}"):
        html(f'<div class="sx-kicker">Exercice pratique · {len(exercise.steps)} étapes</div>'
             f'<h2 class="sx-h3">{esc(exercise.title)}</h2>')
        md(exercise.context)

        for index, step in enumerate(exercise.steps, start=1):
            unit = f" ({step.unit})" if step.unit else ""
            st.text_input(f"{index}. {step.prompt}{unit}", key=f"{key}::{run}::{step.id}",
                          placeholder="Votre réponse", disabled=state["checked"])
            if state["checked"] or state["revealed"]:
                _solution(step, st.session_state.get(f"{key}::{run}::{step.id}"),
                          checked=state["checked"], key=f"{scope}_{exercise.id}_{run}_{step.id}")

        cols = st.columns(2)
        if not state["checked"]:
            with cols[0]:
                if st.button("Vérifier mes réponses", key=f"{key}::check::{run}", type="primary"):
                    state["checked"] = True
                    st.rerun()
            if not state["revealed"]:
                with cols[1]:
                    if st.button("Afficher le corrigé", key=f"{key}::reveal::{run}"):
                        state["revealed"] = True
                        st.rerun()
        else:
            results = [X.check_step(s, st.session_state.get(f"{key}::{run}::{s.id}"))
                       for s in exercise.steps]
            right = sum(r.status == X.CORRECT for r in results)
            html(f'<div class="sx-result"><div class="big">{right}<small> / {len(results)}</small>'
                 f'</div><div><div class="k {"pass" if right == len(results) else "fail"}">'
                 f'Étapes justes</div><p>Chaque corrigé est affiché sous son étape.</p></div></div>')
            if exercise.conclusion:
                md(exercise.conclusion)
            if st.button("Recommencer l'exercice", key=f"{key}::restart::{run}"):
                state.update(run=run + 1, checked=False, revealed=False)
                st.rerun()


def _solution(step, text: str | None, *, checked: bool, key: str) -> None:
    if checked:
        result = X.check_step(step, text)
        label, cls = LABELS[result.status], CLASSES[result.status]
        if result.value is not None and result.status == X.INCORRECT:
            label += f" · vous avez répondu {esc(text)}"
    else:
        label, cls = "Corrigé", "neutral"
    with st.container(key=f"solution_{cls}_{key}"):
        html(f'<div class="sx-callout-title">{label}</div>')
        md(step.solution)
