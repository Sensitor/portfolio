"""
Endpoints shaped for a phone.

The other routers serve one thing each, which is the right shape for a browser
on a fast connection and the wrong one for a handset. Three differences drive
everything here:

**Round trips are expensive.** On a mobile network each request costs a hundred
milliseconds or more before a byte arrives, and every one of them wakes the
radio. A home screen assembled from six requests is slow *and* a battery cost.
`/mobile/overview` returns the whole screen in one.

**Bytes are expensive.** A five-thousand-trade equity curve is a megabyte a
phone cannot draw and should not pay for. Curves are thinned by the engine's
`downsample`, which keeps every peak and trough rather than sampling at a
stride — the alternative renders a shallower drawdown on the phone than on the
desktop, which is one figure disagreeing with itself.

**The app is reopened constantly.** Most of those openings find nothing
changed. Every response here carries an `ETag`; a client that sends it back in
`If-None-Match` gets a 304 with no body, and `/mobile/trades?since=` returns
only what has been touched since it last looked.

Like every other router, this one computes nothing. The thinning is
`trading.analytics.downsample`, the version string is `Store.trades_version`.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from ...trading.analytics import downsample
from ...trading.context import build_context
from ...trading.journal import TradeJournal
from ..deps import Store, current_user, get_store
from ..schemas import MobileOverview, TradeDelta

router = APIRouter(prefix="/mobile", tags=["mobile"])

# Starlette renamed this constant; the fallback is the literal rather than the
# deprecated attribute, which a `getattr` default would touch eagerly.
UNPROCESSABLE = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", None) or 422

# How much of a curve a phone gets. Four hundred points is more than a handset
# screen has pixels across, so the limit costs nothing visible.
CURVE_POINTS = 400


def _cursor(since: str | None) -> str | None:
    """
    Validate and repair a sync cursor.

    Two reasons this is not just passed through.

    A `+` in a query string decodes to a space, so a client that interpolates
    an ISO timestamp with a UTC offset — `2026-09-21T12:00:00+00:00` — sends
    something the server reads as `…12:00:00 00:00`. The stored timestamps keep
    their `+`, and `'+' > ' '`, so a **string** comparison then matches every
    row: the endpoint silently returns the entire journal, which is the exact
    download it exists to avoid. The space is put back before anything is
    compared.

    And an unparseable cursor is rejected rather than ignored. Ignoring it
    returns everything, which looks like success and is the worst available
    answer — a phone would re-download its whole history and never learn why.
    """
    if not since:
        return None
    candidate = since.strip()
    if " " in candidate and "+" not in candidate:
        # Only the offset separator can legitimately be a space here, and only
        # because the transport ate a plus.
        candidate = candidate.replace(" ", "+", 1)
    try:
        datetime.fromisoformat(candidate)
    except ValueError:
        raise HTTPException(
            status_code=UNPROCESSABLE,
            detail=("`since` must be an ISO timestamp — pass back the "
                    "`server_time` from the previous response, URL-encoded."),
        ) from None
    return candidate


def _etag(store: Store, email: str) -> str:
    return f'W/"{store.trades_version(email)}"'


def _unchanged_response(etag: str) -> Response:
    """
    A bare 304.

    Returned as a `Response` rather than by setting a status code and handing
    back an empty dict: a route with a `response_model` validates whatever it
    returns, and an empty dict is not a valid overview — so that route answered
    500 on precisely the request it exists to make cheap. Returning a `Response`
    object tells FastAPI to skip validation, which is the only correct way to
    send a body-less status from a typed endpoint.
    """
    return Response(status_code=status.HTTP_304_NOT_MODIFIED,
                    headers={"ETag": etag})


def _not_modified(request: Request, etag: str) -> bool:
    """
    Whether the client already has this exact version.

    `If-None-Match` may carry several tags and may quote them differently, so
    the header is split rather than compared whole — a client that sends back
    exactly what it was given must always match, and one that sends a list must
    not be forced into a full download because of it.
    """
    header = request.headers.get("if-none-match")
    if not header:
        return False
    presented = {tag.strip() for tag in header.split(",")}
    return etag in presented or "*" in presented


@router.get("/overview", response_model=MobileOverview,
            response_model_exclude_none=False)
def overview(request: Request, response: Response,
             email: str = Depends(current_user),
             store: Store = Depends(get_store),
             period: str = Query("ALL"),
             account: str | None = Query(None),
             lang: str = Query("en", pattern="^(en|fr)$"),
             curve_points: int = Query(CURVE_POINTS, ge=20, le=2000),
             include_r: bool = Query(
                 False,
                 description="Include the cumulative-R curve. Off by default: "
                             "it is a second full curve a home screen does not "
                             "draw, and bytes are the scarce thing here.")):
    """
    Everything a home screen shows, in one request.

    Headline metrics, a thinned equity curve, the strongest and weakest
    instruments, the psychology findings, open positions and the sync state —
    assembled from one `TradingContext`, so every figure describes the same set
    of trades. Six separate requests could each land on a different moment;
    this cannot.
    """
    etag = _etag(store, email)
    response.headers["ETag"] = etag
    if _not_modified(request, etag):
        return _unchanged_response(etag)

    ctx = build_context(TradeJournal(store.list_trades(email)),
                        lang=lang, period=period, account_id=account)
    metrics = ctx.metrics
    symbols = ctx.breakdown("symbol")

    return {
        "etag": etag,
        "period": ctx.period,
        "available_periods": ctx.available_periods,
        "currency": ctx.currency,
        "metrics": metrics,
        "equity": downsample(ctx.equity_curve, curve_points),
        "r_curve": downsample(ctx.r_curve, curve_points) if include_r else [],
        "daily": ctx.daily_pnl[-90:],
        "by_symbol": symbols[:8],
        "findings": ctx.findings,
        "open_positions": len(ctx.open_trades),
        "accounts": [
            {"id": a.id, "name": a.name, "broker": a.broker,
             "currency": a.currency, "last_synced_at": a.last_synced_at,
             "last_sync_trades": a.last_sync_trades}
            for a in store.list_accounts(email)
        ],
        # Restated here so a client rendering from this payload alone still has
        # the caveats that travel with the numbers elsewhere.
        "notes": {
            "r_coverage": metrics.get("r_coverage"),
            "undefined_is_null": True,
            "findings_are_correlations": True,
        },
    }


@router.get("/trades", response_model=TradeDelta)
def trades(request: Request, response: Response,
           email: str = Depends(current_user),
           store: Store = Depends(get_store),
           since: str | None = Query(
               None, description="ISO timestamp. Returns only trades whose "
                                 "`updated_at` is later, for incremental sync."),
           limit: int = Query(200, ge=1, le=1000),
           account: str | None = Query(None)):
    """
    The journal, incrementally.

    With no `since`, a first page. With one, only what has changed — filtered on
    `updated_at` rather than `closed_at`, because a trade annotated today is a
    change the client needs even though it closed in March.

    `server_time` comes back so the client stores the server's clock as its next
    cursor rather than its own. A phone whose clock runs fast would otherwise
    ask for changes since a moment that has not happened yet and silently miss
    everything written in between.
    """
    etag = _etag(store, email)
    response.headers["ETag"] = etag
    if _not_modified(request, etag):
        return _unchanged_response(etag)

    from ...database.connection import now as server_now

    cursor = _cursor(since)
    rows = store.list_trades(email, account_id=account, limit=limit,
                             updated_since=cursor)
    return {
        "etag": etag,
        "server_time": server_now(),
        "since": cursor,
        "trades": [t.to_dict() for t in rows],
        "count": len(rows),
        "complete": len(rows) < limit,
    }


@router.get("/version")
def version(email: str = Depends(current_user),
            store: Store = Depends(get_store)) -> dict:
    """
    The current data version, as one tiny response.

    What a client polls on resume when it wants to know whether to fetch at all.
    Cheaper than a conditional request on a large endpoint, because it is a
    count and a maximum rather than an assembled payload the server throws away.
    """
    return {"etag": _etag(store, email)}
