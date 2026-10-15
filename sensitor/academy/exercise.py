"""
Numeric practical exercises.

A step asks for one number. The answer is checked against the expected value
within an absolute tolerance stated in the exercise file, then the worked
solution is shown either way — the point of the exercise is the reasoning, and
a correct number reached by luck deserves the explanation as much as a wrong one.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

from .content import ExerciseStep

CORRECT = "correct"
INCORRECT = "incorrect"
UNANSWERED = "unanswered"
INVALID = "invalid"

_SPACES = re.compile(r"[\s  ]")


def parse_number(text: str | None) -> float | None:
    """
    Read a number the way a French speaker types it.

    "1 234,5", "1234.5" and "0,33" all parse. Returns None for an empty field and
    raises ValueError for anything that is not a number, so the page can tell
    "you left this blank" from "this is not a number".
    """
    if text is None:
        return None
    cleaned = _SPACES.sub("", str(text)).replace("€", "").replace("$", "")
    if not cleaned:
        return None
    if cleaned.count(",") == 1 and "." not in cleaned:
        cleaned = cleaned.replace(",", ".")
    value = float(cleaned)
    if not math.isfinite(value):
        raise ValueError("nombre non fini")
    return value


@dataclass(frozen=True)
class StepResult:
    step_id: str
    status: str
    value: float | None
    expected: float


def check_step(step: ExerciseStep, text: str | None) -> StepResult:
    try:
        value = parse_number(text)
    except ValueError:
        return StepResult(step.id, INVALID, None, step.answer)
    if value is None:
        return StepResult(step.id, UNANSWERED, None, step.answer)
    ok = abs(value - step.answer) <= step.tolerance + 1e-12
    return StepResult(step.id, CORRECT if ok else INCORRECT, value, step.answer)
