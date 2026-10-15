"""
The lesson reader: renders a lesson's blocks in order.

Markdown goes through `st.markdown`; callouts are keyed containers so the
stylesheet can colour them by kind while their body stays real Markdown;
figures are the original SVGs, inlined; formulas use KaTeX; exercises, the risk
tool and the quiz are their own components.
"""

from __future__ import annotations

import streamlit as st

from ..content import Catalog, Lesson
from ..markup import CALLOUT_KINDS
from . import exercise_view, quiz_view, risk_view
from .components import diagram, esc, html, md


def render_blocks(lesson: Lesson, catalog: Catalog, *, email: str | None) -> None:
    for index, block in enumerate(lesson.blocks):
        if block.kind == "markdown":
            md(block.text)
        elif block.kind == "callout":
            kind = block.callout_kind if block.callout_kind in CALLOUT_KINDS else "note"
            with st.container(key=f"callout_{kind}_{lesson.id}_{index}"):
                html(f'<div class="ac-callout-title">{esc(block.title)}</div>')
                md(block.text)
        elif block.kind == "figure":
            diagram(catalog.figures.get(block.target, ""), block.text)
        elif block.kind == "formula":
            st.latex(block.text)
        elif block.kind == "exercise":
            exercise = catalog.exercise(block.target)
            if exercise:
                exercise_view.render(exercise, scope=lesson.id)
        elif block.kind == "tool" and block.target == "risk-calculator":
            risk_view.render(scope=f"lesson_{lesson.id}", compact=True)


def render_objectives(lesson: Lesson) -> None:
    if not lesson.objectives:
        return
    items = "".join(f"<li>{esc(o)}</li>" for o in lesson.objectives)
    html(f'<div class="ac-objectives"><div class="ac-eyebrow">À la fin de cette leçon, '
         f'vous saurez</div><ul>{items}</ul></div>')


def render_quiz(lesson: Lesson, catalog: Catalog, *, email: str | None) -> None:
    quiz = catalog.quiz(lesson.quiz_id)
    if quiz:
        quiz_view.render(quiz, scope=f"lesson_{lesson.id}", catalog=catalog, email=email)


def render_sources(lesson: Lesson) -> None:
    if not lesson.sources:
        return
    items = "".join(f"<li>{esc(s)}</li>" for s in lesson.sources)
    html(f'<div class="ac-rule"></div><div class="ac-eyebrow">Sources</div>'
         f'<ul class="ac-sub" style="padding-left:1.1rem">{items}</ul>')
