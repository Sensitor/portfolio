"""
The lesson reader: renders a lesson's blocks in order.

Markdown goes through `md` (dollar signs kept literal); callouts are keyed
containers so the stylesheet colours them by kind while their body stays real
Markdown; figures are the original SVGs, numbered in reading order; formulas
use KaTeX; exercises, the risk tool and the quiz are their own components.
"""

from __future__ import annotations

import streamlit as st

from ...platform.ui.components import diagram, esc, html, md
from ..content import Catalog, Lesson
from ..markup import CALLOUT_KINDS
from . import exercise_view, quiz_view, risk_view


def render_blocks(lesson: Lesson, catalog: Catalog, *, email: str | None) -> None:
    figure = 0
    for index, block in enumerate(lesson.blocks):
        if block.kind == "markdown":
            md(block.text)
        elif block.kind == "callout":
            kind = block.callout_kind if block.callout_kind in CALLOUT_KINDS else "note"
            with st.container(key=f"callout_{kind}_{lesson.id}_{index}"):
                html(f'<div class="sx-callout-title">{esc(block.title)}</div>')
                md(block.text)
        elif block.kind == "figure":
            figure += 1
            diagram(catalog.figures.get(block.target, ""), block.text, figure)
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
    items = "".join(f'<div><span class="n">{i:02d}</span><span class="x">{esc(o)}</span></div>'
                    for i, o in enumerate(lesson.objectives, start=1))
    html(f'<div style="margin:2rem 0 1.4rem"><div class="sx-kicker muted" style="margin-bottom:.2rem">'
         f'À la fin de cette leçon, vous saurez</div><div class="sx-objectives">{items}</div></div>')


def render_quiz(lesson: Lesson, catalog: Catalog, *, email: str | None) -> None:
    quiz = catalog.quiz(lesson.quiz_id)
    if quiz:
        html('<div style="height:1.4rem"></div>')
        quiz_view.render(quiz, scope=f"lesson_{lesson.id}", catalog=catalog, email=email)


def render_sources(lesson: Lesson) -> None:
    if not lesson.sources:
        return
    items = "".join(f"<li>{esc(s)}</li>" for s in lesson.sources)
    html(f'<hr class="sx-hr"><div class="sx-kicker muted">Sources</div>'
         f'<ul class="sx-body" style="padding-left:1.1rem;font-size:14px;margin-top:.5rem">{items}</ul>')
