"""
Sensitor Academy over HTTP.

Content routes answer anonymous callers for public lessons and refuse
member-only ones with 401. Progress and attempt history require a bearer token
and, like every other router, take the user from that token and nowhere else.

The answer key never leaves the server before a submission: `GET` on a quiz
returns the questions without the `correct` flags, and the graded feedback is
only produced by `POST …/attempts`.

No calculation lives here. Scoring is `academy.quiz`, progress is
`academy.progress`, risk figures are `academy.risk`, and access rules are
`academy.access`.
"""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse, Response
from pydantic import BaseModel, Field

from ...academy import access, progress, quiz as Q, risk as R, views
from ...academy.content import Catalog, cached_catalog
from ..deps import Store, current_user, get_store, optional_user

UNPROCESSABLE = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", None) or 422

router = APIRouter(prefix="/academy", tags=["academy"])


def get_catalog() -> Catalog:
    # Same override as the Streamlit runtime: tests point it at a fixture tree.
    return cached_catalog(os.getenv("SENSITOR_ACADEMY_CONTENT") or None)


def _not_found(what: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"no such {what}")


_SIGN_IN = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                         detail="sign in to read member content",
                         headers={"WWW-Authenticate": "Bearer"})
_PREMIUM = HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                         detail="premium content: this account's tier does not include it")


def _tier(store: Store, email: str | None) -> str | None:
    user = store.get_user(email) if email else None
    return (user or {}).get("tier")


def _deny(email: str | None) -> HTTPException:
    """401 to sign in, 403 when signed in and the content is premium."""
    return _PREMIUM if email else _SIGN_IN


class AttemptRequest(BaseModel):
    responses: dict[str, list[str]] = Field(default_factory=dict)


class RiskPlanRequest(BaseModel):
    equity: float
    risk_pct: float
    entry: float
    stop: float
    direction: str
    target: float | None = None
    contract_size: float | None = None
    quote_to_account: float = 1.0
    lot_step: float | None = None
    min_lot: float | None = None
    pip_size: float | None = None


def _course_or_404(catalog: Catalog, course_id: str):
    course = catalog.course(course_id)
    if course is None:
        raise _not_found("course")
    return course


def _lesson_or_404(catalog: Catalog, course_id: str, lesson_id: str):
    lesson = _course_or_404(catalog, course_id).lesson(lesson_id)
    if lesson is None:
        raise _not_found("lesson")
    return lesson


def _passed(store: Store, email: str) -> set[str]:
    return progress.passed_quiz_ids(store.quiz_attempts(email, limit=10_000))


# ── Catalogue ────────────────────────────────────────────────────────────────

@router.get("/catalog")
def catalog(catalog: Catalog = Depends(get_catalog)) -> dict:
    """The curriculum: every path, with the courses of the available ones."""
    return {"paths": [views.path_view(p) for p in catalog.paths]}


@router.get("/courses/{course_id}")
def course(course_id: str, catalog: Catalog = Depends(get_catalog),
           email: str | None = Depends(optional_user),
           store: Store = Depends(get_store)) -> dict:
    found = _course_or_404(catalog, course_id)
    state = None
    if email:
        done = {r["lesson_id"] for r in store.completed_lessons(email, course_id)}
        state = progress.course_progress(found, done, passed_quizzes=_passed(store, email))
    return views.course_view(found, state)


@router.get("/courses/{course_id}/lessons/{lesson_id}")
def lesson(course_id: str, lesson_id: str, catalog: Catalog = Depends(get_catalog),
           email: str | None = Depends(optional_user), store: Store = Depends(get_store)) -> dict:
    found = _lesson_or_404(catalog, course_id, lesson_id)
    if not access.can_read_lesson(found, email, _tier(store, email)):
        raise _deny(email)
    return views.lesson_view(catalog, found)


@router.post("/courses/{course_id}/lessons/{lesson_id}/complete",
             status_code=status.HTTP_204_NO_CONTENT)
def complete_lesson(course_id: str, lesson_id: str,
                    catalog: Catalog = Depends(get_catalog),
                    email: str = Depends(current_user),
                    store: Store = Depends(get_store)) -> None:
    found = _lesson_or_404(catalog, course_id, lesson_id)
    store.mark_lesson_complete(email, course_id, lesson_id, version=found.version)


@router.delete("/courses/{course_id}/lessons/{lesson_id}/complete",
               status_code=status.HTTP_204_NO_CONTENT)
def uncomplete_lesson(course_id: str, lesson_id: str,
                      catalog: Catalog = Depends(get_catalog),
                      email: str = Depends(current_user),
                      store: Store = Depends(get_store)) -> None:
    _lesson_or_404(catalog, course_id, lesson_id)
    store.unmark_lesson(email, course_id, lesson_id)


# ── Quizzes ──────────────────────────────────────────────────────────────────

def _quiz_or_404(catalog: Catalog, quiz_id: str):
    found = catalog.quiz(quiz_id)
    if found is None:
        raise _not_found("quiz")
    return found


@router.get("/quizzes/{quiz_id}")
def get_quiz(quiz_id: str, catalog: Catalog = Depends(get_catalog),
             email: str | None = Depends(optional_user), store: Store = Depends(get_store)) -> dict:
    found = _quiz_or_404(catalog, quiz_id)
    if not access.can_take_quiz(catalog, found, email, _tier(store, email)):
        raise _deny(email)
    return Q.public_view(found)


@router.post("/quizzes/{quiz_id}/attempts")
def submit_attempt(quiz_id: str, body: AttemptRequest,
                   catalog: Catalog = Depends(get_catalog),
                   email: str | None = Depends(optional_user),
                   store: Store = Depends(get_store)) -> dict:
    """
    Grade a submission and return every explanation.

    Signed-in attempts are stored; anonymous attempts on public quizzes are
    graded and forgotten. `stored` says which happened.
    """
    found = _quiz_or_404(catalog, quiz_id)
    if not access.can_take_quiz(catalog, found, email, _tier(store, email)):
        raise _deny(email)
    try:
        result = Q.grade(found, body.responses)
    except ValueError as exc:
        raise HTTPException(status_code=UNPROCESSABLE, detail=str(exc)) from exc
    attempt_id = None
    if email:
        attempt_id = store.record_quiz_attempt(
            email, found.id, version=result.quiz_version, correct=result.correct_count,
            total=result.total, passed=result.passed, responses=result.responses())
    feedback = Q.feedback_view(found, result)
    feedback.update(stored=attempt_id is not None, attempt_id=attempt_id)
    return feedback


@router.get("/quizzes/{quiz_id}/attempts")
def list_attempts(quiz_id: str, catalog: Catalog = Depends(get_catalog),
                  email: str = Depends(current_user),
                  store: Store = Depends(get_store),
                  limit: int = Query(20, ge=1, le=200)) -> list[dict]:
    _quiz_or_404(catalog, quiz_id)
    return store.quiz_attempts(email, quiz_id, limit=limit)


# ── Progress ─────────────────────────────────────────────────────────────────

@router.get("/progress")
def my_progress(catalog: Catalog = Depends(get_catalog),
                email: str = Depends(current_user),
                store: Store = Depends(get_store)) -> dict:
    completed = progress.completed_by_course(store.completed_lessons(email))
    attempts = store.quiz_attempts(email, limit=10_000)
    passed = progress.passed_quiz_ids(attempts)
    step = progress.next_step(catalog, completed, passed)
    return {
        "courses": [views.progress_view(progress.course_progress(
                        c, completed.get(c.id, set()), passed_quizzes=passed))
                    for c in catalog.available_courses()],
        "recent_attempts": attempts[:10],
        "next": {"kind": step.kind,
                 "course_id": step.course.id if step.course else None,
                 "lesson_id": step.lesson.id if step.lesson else None},
    }


# ── Library ──────────────────────────────────────────────────────────────────

@router.get("/resources")
def resources(catalog: Catalog = Depends(get_catalog)) -> list[dict]:
    return [views.resource_view(r) for r in catalog.resources.values()]


@router.get("/resources/{resource_id}/download")
def download(resource_id: str, catalog: Catalog = Depends(get_catalog),
             email: str | None = Depends(optional_user), store: Store = Depends(get_store),
             format: str = Query("md", pattern="^(md|pdf)$")) -> Response:
    """The resource file: Markdown by default, `?format=pdf` when a PDF exists."""
    found = catalog.resource(resource_id)
    if found is None:
        raise _not_found("resource")
    if not access.can_download(found, email, _tier(store, email)):
        raise _deny(email)
    if format == "pdf":
        if not found.pdf:
            raise _not_found("pdf for this resource")
        return Response(found.read_pdf(), media_type="application/pdf",
                        headers={"Content-Disposition": f'attachment; filename="{found.pdf_name}"'})
    return PlainTextResponse(
        found.read_text(), media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{found.filename}"'})


# ── Risk lab ─────────────────────────────────────────────────────────────────

@router.post("/risk/plan")
def risk_plan(body: RiskPlanRequest) -> dict:
    """Risk amount, stop distance, reward-to-risk and, with a spec, position size."""
    spec = None
    if body.contract_size is not None:
        spec = R.InstrumentSpec(contract_size=body.contract_size,
                                quote_to_account=body.quote_to_account,
                                lot_step=body.lot_step, min_lot=body.min_lot,
                                pip_size=body.pip_size)
    try:
        result = R.plan(equity=body.equity, risk_pct=body.risk_pct, entry=body.entry,
                        stop=body.stop, direction=body.direction, target=body.target,
                        spec=spec)
    except R.RiskInputError as exc:
        raise HTTPException(status_code=UNPROCESSABLE, detail=exc.errors) from exc
    return views.risk_plan_view(result)


class ExpectancyRequest(BaseModel):
    win_rate: float = Field(gt=0, lt=1)
    reward_r: float = Field(gt=0, le=20)
    risk_pct: float = Field(gt=0, lt=100)
    trades: int = Field(ge=1, le=1000)
    threshold_pct: float = Field(gt=0, lt=100)


@router.post("/risk/expectancy")
def risk_expectancy(body: ExpectancyRequest) -> dict:
    """Expectancy, break-even, risk of ruin and final-equity range (exact, see path 5)."""
    try:
        return views.expectancy_view(body.win_rate, body.reward_r, body.risk_pct, body.trades,
                                     body.threshold_pct)
    except ValueError as exc:
        raise HTTPException(status_code=UNPROCESSABLE, detail=str(exc)) from exc
