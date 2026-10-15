"""
Quiz scoring and explained feedback.

Rules, stated once
------------------
* A question is **correct** only when the selected options are exactly the
  correct set. Multiple-answer questions get no partial credit: picking two of
  three right answers plus a wrong one is not "mostly right" in a risk decision,
  and partial credit would make the score harder to read.
* An **unanswered** question counts as not correct, and is reported as
  unanswered rather than wrong, so the review can say "you skipped this" instead
  of showing an explanation for a choice nobody made.
* The pass mark is a count, not a float comparison: `required` is the smallest
  number of correct answers whose share reaches the threshold. 7 / 10 at 0.7
  passes; floating point does not get a vote.

Responses are validated: an unknown question or option id, or two answers to a
single-choice question, raises `ValueError`. The API maps that to a 422, so a
malformed submission is refused instead of being scored as wrong.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from .content import Question, Quiz

CORRECT = "correct"
INCORRECT = "incorrect"
UNANSWERED = "unanswered"


@dataclass(frozen=True)
class QuestionResult:
    question_id: str
    status: str
    selected: tuple[str, ...]
    correct: tuple[str, ...]

    @property
    def is_correct(self) -> bool:
        return self.status == CORRECT


@dataclass(frozen=True)
class QuizResult:
    quiz_id: str
    quiz_version: int
    results: tuple[QuestionResult, ...]
    correct_count: int
    total: int
    required: int
    pass_threshold: float

    @property
    def score(self) -> float:
        return self.correct_count / self.total if self.total else 0.0

    @property
    def passed(self) -> bool:
        return self.correct_count >= self.required

    @property
    def unanswered_count(self) -> int:
        return sum(r.status == UNANSWERED for r in self.results)

    @property
    def mistakes(self) -> tuple[QuestionResult, ...]:
        return tuple(r for r in self.results if not r.is_correct)

    def responses(self) -> dict[str, list[str]]:
        return {r.question_id: list(r.selected) for r in self.results}


def required_correct(total: int, threshold: float) -> int:
    """Smallest count of correct answers that reaches `threshold`."""
    return min(total, max(0, math.ceil(threshold * total - 1e-9)))


def normalise_responses(quiz: Quiz,
                        raw: Mapping[str, Iterable[str] | str | None]) -> dict[str, tuple[str, ...]]:
    """Validate and canonicalise a submission. Missing questions are unanswered."""
    known = {q.id: q for q in quiz.questions}
    unknown = sorted(set(raw) - set(known))
    if unknown:
        raise ValueError(f"questions inconnues : {', '.join(unknown)}")

    clean: dict[str, tuple[str, ...]] = {}
    for question in quiz.questions:
        value = raw.get(question.id)
        if value is None:
            selected: tuple[str, ...] = ()
        elif isinstance(value, str):
            selected = (value,)
        else:
            selected = tuple(dict.fromkeys(str(v) for v in value))
        for option_id in selected:
            if question.option(option_id) is None:
                raise ValueError(f"{question.id} : proposition inconnue « {option_id} »")
        if question.kind == "single" and len(selected) > 1:
            raise ValueError(f"{question.id} : une seule réponse attendue")
        clean[question.id] = tuple(sorted(selected))
    return clean


def grade_question(question: Question, selected: Iterable[str]) -> QuestionResult:
    chosen = tuple(sorted(set(selected)))
    correct = tuple(sorted(question.correct_ids))
    if not chosen:
        status = UNANSWERED
    elif set(chosen) == set(correct):
        status = CORRECT
    else:
        status = INCORRECT
    return QuestionResult(question.id, status, chosen, correct)


def grade(quiz: Quiz, raw: Mapping[str, Iterable[str] | str | None]) -> QuizResult:
    responses = normalise_responses(quiz, raw)
    results = tuple(grade_question(q, responses[q.id]) for q in quiz.questions)
    correct = sum(r.is_correct for r in results)
    total = len(results)
    return QuizResult(quiz_id=quiz.id, quiz_version=quiz.version, results=results,
                      correct_count=correct, total=total,
                      required=required_correct(total, quiz.pass_threshold),
                      pass_threshold=quiz.pass_threshold)


def public_view(quiz: Quiz) -> dict:
    """The quiz as a client may see it before answering: no answer key."""
    return {
        "id": quiz.id,
        "title": quiz.title,
        "intro": quiz.intro,
        "feedback": quiz.feedback,
        "pass_threshold": quiz.pass_threshold,
        "required": required_correct(len(quiz.questions), quiz.pass_threshold),
        "version": quiz.version,
        "questions": [
            {"id": q.id, "prompt": q.prompt, "kind": q.kind,
             "options": [{"id": o.id, "text": o.text} for o in q.options]}
            for q in quiz.questions
        ],
    }


def feedback_view(quiz: Quiz, result: QuizResult) -> dict:
    """The graded result with every explanation, for display after submission."""
    questions = []
    for question, outcome in zip(quiz.questions, result.results):
        questions.append({
            "id": question.id,
            "prompt": question.prompt,
            "status": outcome.status,
            "selected": list(outcome.selected),
            "correct": list(outcome.correct),
            "explanation": question.explanation,
            "lesson_id": question.lesson_id,
            "options": [{"id": o.id, "text": o.text, "correct": o.correct,
                         "explanation": o.explanation} for o in question.options],
        })
    return {
        "quiz_id": result.quiz_id,
        "quiz_version": result.quiz_version,
        "correct": result.correct_count,
        "total": result.total,
        "required": result.required,
        "score": result.score,
        "passed": result.passed,
        "unanswered": result.unanswered_count,
        "questions": questions,
    }
