"""
Trading analytics over HTTP.

Every figure here comes from `trading.context.TradingContext` — the same object
the five Streamlit pages read. Not the same *kind* of object: the same class,
built the same way, from the same store. The phone and the app cannot disagree
about a trader's expectancy because there is only one implementation of it.

Nothing in this file computes anything. Where a response looks like arithmetic
it is a field lookup; the one exception is slicing a list for pagination.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ...trading.context import PERIODS, build_context
from ...trading.journal import TradeFilter, TradeJournal
from ..deps import Store, current_user, get_store
from ..schemas import (
    BreakdownRow, CurvePoint, DayPnL, Finding, TradesPage, TradingMetrics,
)

# Starlette renamed this constant. The fallback is the literal rather than the
# old attribute: a `getattr(..., getattr(...))` evaluates its default eagerly
# and so touches the deprecated name on every import, which is the opposite of
# the point.
UNPROCESSABLE = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", None) or 422

router = APIRouter(prefix="/trading", tags=["trading"])

DIMENSIONS = ("symbol", "setup", "combination", "session", "weekday", "hour",
              "month", "timeframe", "direction", "regime", "risk_band")


def _context(store: Store, email: str, period: str, account: str | None,
             symbol: str | None = None, lang: str = "en"):
    """
    The caller's trading context.

    `email` arrives from the bearer token and nowhere else, and is handed
    straight to the store, which scopes every query by it. There is no request
    field that can name a different user, which is what makes an endpoint like
    this safe to expose at all.
    """
    if period not in PERIODS:
        raise HTTPException(
            status_code=UNPROCESSABLE,
            detail=f"period must be one of {', '.join(PERIODS)}",
        )
    criteria = TradeFilter(symbols=[symbol] if symbol else None)
    return build_context(
        TradeJournal(store.list_trades(email)),
        lang=lang, period=period, account_id=account, criteria=criteria,
    )


# A single dependency block, so every route below takes the same query surface
# and none of them can quietly add a `user` parameter.
def _common(email: str = Depends(current_user),
            store: Store = Depends(get_store),
            period: str = Query("ALL", description=f"One of {', '.join(PERIODS)}."),
            account: str | None = Query(None),
            symbol: str | None = Query(None),
            lang: str = Query("en", pattern="^(en|fr)$")):
    return _context(store, email, period, account, symbol, lang)


@router.get("/metrics", response_model=TradingMetrics)
def metrics(ctx=Depends(_common)) -> TradingMetrics:
    """
    Headline figures for the window.

    `n` leads the response for the same reason it leads the engine's dict: a
    client that renders a win rate without checking how many trades produced it
    is a client that will show 100% over two trades.
    """
    return TradingMetrics(**ctx.metrics)


@router.get("/equity", response_model=list[CurvePoint])
def equity(ctx=Depends(_common)) -> list[CurvePoint]:
    return [CurvePoint(at=p["at"], equity=p["equity"]) for p in ctx.equity_curve]


@router.get("/r-curve", response_model=list[CurvePoint])
def r_curve(ctx=Depends(_common)) -> list[CurvePoint]:
    """Cumulative R, over the trades that had a stop. Empty when none did."""
    return [CurvePoint(at=p["at"], equity=p["equity"]) for p in ctx.r_curve]


@router.get("/daily", response_model=list[DayPnL])
def daily(ctx=Depends(_common)) -> list[DayPnL]:
    return [DayPnL(date=str(d["date"]), pnl=d["pnl"], n=d["n"])
            for d in ctx.daily_pnl]


@router.get("/breakdown/{dimension}", response_model=list[BreakdownRow])
def breakdown(dimension: str, ctx=Depends(_common)) -> list[BreakdownRow]:
    """
    Performance grouped by any recorded dimension.

    Every row carries `n` and `reliable`. A client is expected to mark the
    unreliable ones rather than rank them alongside the rest — a two-trade
    bucket always tops a table sorted by win rate.
    """
    if dimension not in DIMENSIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"dimension must be one of {', '.join(DIMENSIONS)}",
        )
    return [
        BreakdownRow(
            key=str(row["key"]), label=row["label"], n=row["n"],
            reliable=row["reliable"], net_pnl=row["net_pnl"],
            win_rate=row["win_rate"], expectancy=row["expectancy"],
            profit_factor=row["profit_factor"], avg_r=row["avg_r"],
            total_r=row["total_r"],
        )
        for row in ctx.breakdown(dimension)
    ]


@router.get("/risk")
def risk(ctx=Depends(_common)) -> dict:
    """
    Sizing, drift, stop discipline, exposure and losing runs.

    Returned as the engine's own nested dict rather than flattened into a
    schema: its shape is the documentation, and reshaping it here would be the
    first step toward the API and the app describing risk differently.

    `stops.measured_on` is `"gross"`, deliberately — stop discipline is judged
    on price movement before costs, because a trade stopped at exactly -1R lands
    past -1R net on commission alone.
    """
    return ctx.risk


@router.get("/psychology")
def psychology(ctx=Depends(_common)) -> dict:
    """
    Behavioural comparisons between groups of the caller's own trades.

    None of it establishes cause, and every comparison carries both sample
    sizes. See `/trading/findings` for the sentences the engine phrases.
    """
    return ctx.psychology


@router.get("/findings", response_model=list[Finding])
def findings(ctx=Depends(_common)) -> list[Finding]:
    """
    The comparisons worth surfacing, as sentences the engine wrote.

    Passed through verbatim in both languages. Each one names itself a
    correlation and carries its sample size; a client must render them as they
    are rather than paraphrase, because the phrasing is the safeguard.
    """
    return [Finding(**f) for f in ctx.findings]


@router.get("/trades", response_model=TradesPage)
def trades(ctx=Depends(_common),
           limit: int = Query(100, ge=1, le=1000),
           offset: int = Query(0, ge=0),
           closed_only: bool = Query(True)) -> TradesPage:
    """
    The journal itself, newest close first.

    Derived values travel with each trade — R, risk, duration, session — so a
    client never recomputes them.
    """
    journal = ctx.closed if closed_only else ctx.scoped
    ordered = journal.sorted_by("closed_at")
    rows = ordered.to_dicts()
    return TradesPage(trades=rows[offset:offset + limit], total=len(rows),
                      limit=limit, offset=offset)


@router.get("/accounts")
def accounts(email: str = Depends(current_user),
             store: Store = Depends(get_store)) -> list[dict]:
    """The caller's trading accounts, with when each was last synced."""
    from dataclasses import asdict
    return [asdict(a) for a in store.list_accounts(email)]


@router.get("/periods", response_model=list[str])
def periods(ctx=Depends(_common)) -> list[str]:
    """Only the windows this journal's history can actually cover."""
    return ctx.available_periods
