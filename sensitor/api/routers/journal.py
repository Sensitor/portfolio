"""
The reflection journal over HTTP.

Every route requires a bearer token and takes the member from it and nowhere
else; no route accepts an address. Entries are checked by `platform.journal`
before they are stored, and counted by it for the summary. A note that belongs
to someone else answers 404, exactly like one that does not exist, so an id
reveals nothing.
"""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from ...platform import journal as J
from ..deps import Store, current_user, get_store

UNPROCESSABLE = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", None) or 422

router = APIRouter(prefix="/journal", tags=["journal"])


class EntryRequest(BaseModel):
    kind: str
    body: str
    mood: int | None = None
    prompt: str = ""
    checks: list[str] | None = None


@router.get("/kinds")
def kinds() -> list[dict]:
    """The entry types, their guided questions and routines. Public: the same for everyone."""
    return [asdict(k) for k in J.KINDS]


@router.get("")
def list_entries(email: str = Depends(current_user), store: Store = Depends(get_store),
                 kind: str | None = Query(None), limit: int = Query(100, ge=1, le=1000)) -> list[dict]:
    return store.journal_entries(email, kind, limit=limit)


@router.post("", status_code=status.HTTP_201_CREATED)
def add_entry(body: EntryRequest, email: str = Depends(current_user),
              store: Store = Depends(get_store)) -> dict:
    try:
        kind, text, mood, prompt = J.clean_entry(body.kind, body.body, mood=body.mood,
                                                 prompt=body.prompt)
        checks = J.clean_checks(kind, body.checks)
    except ValueError as exc:
        raise HTTPException(status_code=UNPROCESSABLE, detail=str(exc)) from exc
    return {"id": store.add_journal_entry(email, kind=kind, body=text, mood=mood, prompt=prompt,
                                          checks=checks)}


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(entry_id: int, email: str = Depends(current_user),
                 store: Store = Depends(get_store)) -> None:
    if not store.delete_journal_entry(email, entry_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no such entry")


@router.get("/summary")
def summary(email: str = Depends(current_user), store: Store = Depends(get_store)) -> dict:
    """Counts and the average of the member's own scale, each with its sample size."""
    return asdict(J.summarize(store.journal_entries(email, limit=100_000)))
