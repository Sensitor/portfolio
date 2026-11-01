"""
Internal management over HTTP, for administrators.

The same `Store` methods as the platform's « Membres » page, which check the
administrator role in their own SQL: a caller without it gets 403 from every
route, whatever the route's own check says. A member's address travels in the
request body, never in the path, so it does not end up in an access log.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from ..deps import Store, current_user, get_store

UNPROCESSABLE = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", None) or 422

router = APIRouter(prefix="/admin", tags=["admin"])

_FORBIDDEN = HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="administrators only")


class GrantRequest(BaseModel):
    email: str
    reason: str
    ends_at: str | None = None        # ISO 8601, UTC; none for no end


def _admin(email: str, store: Store) -> str:
    if not store.is_admin(email):
        raise _FORBIDDEN
    return email


@router.get("/members")
def members(q: str = Query(default="", max_length=200), email: str = Depends(current_user),
            store: Store = Depends(get_store)) -> list[dict]:
    rows = store.admin_members(_admin(email, store), query=q)
    if rows is None:
        raise _FORBIDDEN
    return rows


@router.post("/access", status_code=status.HTTP_201_CREATED)
def grant(body: GrantRequest, email: str = Depends(current_user), store: Store = Depends(get_store)) -> dict:
    _admin(email, store)
    try:
        entitlement = store.grant_access(email, body.email, reason=body.reason, ends_at=body.ends_at)
    except ValueError as exc:
        raise HTTPException(status_code=UNPROCESSABLE, detail=str(exc)) from exc
    if entitlement is None:
        raise HTTPException(status_code=UNPROCESSABLE, detail="unknown member or empty reason")
    return {"id": entitlement}


@router.delete("/access/{entitlement_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke(entitlement_id: int, email: str = Depends(current_user), store: Store = Depends(get_store)) -> None:
    _admin(email, store)
    if not store.revoke_access(email, entitlement_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no such active entitlement")
