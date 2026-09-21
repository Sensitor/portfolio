"""
Saved portfolios and their snapshots.

Thin over `Store`. Every method it calls leads with the caller's email, which
comes from the bearer token — so a portfolio id in a path is a *filter*, not an
identifier the server trusts. Asking for someone else's id returns 404, the
same answer as asking for one that does not exist, because distinguishing them
would confirm that it exists.
"""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..deps import Store, current_user, get_store
from ..schemas import Deleted, PortfolioOut, SavePortfolioRequest, SnapshotOut

# Starlette renamed this constant. The fallback is the literal rather than the
# old attribute: a `getattr(..., getattr(...))` evaluates its default eagerly
# and so touches the deprecated name on every import, which is the opposite of
# the point.
UNPROCESSABLE = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", None) or 422

router = APIRouter(prefix="/portfolios", tags=["portfolios"])

_NOT_FOUND = HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                           detail="no such portfolio")


@router.get("", response_model=list[PortfolioOut])
def list_portfolios(email: str = Depends(current_user),
                    store: Store = Depends(get_store),
                    clients_only: bool = Query(False)) -> list[PortfolioOut]:
    return [PortfolioOut(**asdict(p))
            for p in store.list_portfolios(email, clients_only=clients_only)]


@router.get("/{portfolio_id}", response_model=PortfolioOut)
def get_portfolio(portfolio_id: int, email: str = Depends(current_user),
                  store: Store = Depends(get_store)) -> PortfolioOut:
    portfolio = store.get_portfolio(email, portfolio_id)
    if portfolio is None:
        raise _NOT_FOUND
    return PortfolioOut(**asdict(portfolio))


@router.post("", response_model=PortfolioOut, status_code=status.HTTP_201_CREATED)
def save_portfolio(body: SavePortfolioRequest,
                   email: str = Depends(current_user),
                   store: Store = Depends(get_store)) -> PortfolioOut:
    """
    Create or overwrite a portfolio by name.

    Overwriting rather than erroring on a duplicate name matches the app: a name
    is how someone identifies one book across the iterations they save.
    """
    if not body.name.strip() or not body.holdings:
        raise HTTPException(status_code=UNPROCESSABLE,
                            detail="a name and at least one holding are required")
    portfolio_id = store.save_portfolio(
        email, body.name, body.holdings, mode=body.mode, currency=body.currency,
        notes=body.notes, client_name=body.client_name)
    portfolio = store.get_portfolio(email, portfolio_id)
    if portfolio is None:
        raise _NOT_FOUND
    return PortfolioOut(**asdict(portfolio))


@router.delete("/{portfolio_id}", response_model=Deleted)
def delete_portfolio(portfolio_id: int, email: str = Depends(current_user),
                     store: Store = Depends(get_store)) -> Deleted:
    """
    Delete a portfolio and its snapshots.

    `Store.delete_portfolio` returns False when the row was not this user's,
    which becomes a 404 — the same answer as a portfolio that never existed.
    """
    if not store.delete_portfolio(email, portfolio_id):
        raise _NOT_FOUND
    return Deleted(deleted=True)


@router.get("/{portfolio_id}/snapshots", response_model=list[SnapshotOut])
def list_snapshots(portfolio_id: int, email: str = Depends(current_user),
                   store: Store = Depends(get_store),
                   limit: int = Query(200, ge=1, le=10_000)) -> list[SnapshotOut]:
    """
    The recorded history of one portfolio.

    Snapshots carry no user column; the store reaches them through the
    portfolio, so an id belonging to someone else yields an empty list rather
    than their history.
    """
    if store.get_portfolio(email, portfolio_id) is None:
        raise _NOT_FOUND
    return [SnapshotOut(**asdict(s))
            for s in store.list_snapshots(email, portfolio_id, limit=limit)]


@router.get("/{portfolio_id}/latest", response_model=SnapshotOut)
def latest_snapshot(portfolio_id: int, email: str = Depends(current_user),
                    store: Store = Depends(get_store)) -> SnapshotOut:
    snapshot = store.latest_snapshot(email, portfolio_id)
    if snapshot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="no snapshots recorded for that portfolio")
    return SnapshotOut(**asdict(snapshot))
