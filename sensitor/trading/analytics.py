"""
Trading metrics.

The headline numbers a trading journal lives on: P&L, win rate, profit factor,
expectancy, R multiples, drawdown, streaks and holding time.

Three rules govern everything here, and they are what separate a journal that
tells the truth from one that flatters:

**Sample size travels with every statistic.** A 100% win rate over three trades
and over three hundred are different facts. Every result carries `n`, and the UI
is expected to show it.

**Undefined is not zero.** Profit factor with no losing trades has no value —
it is division by zero, not infinity-dressed-as-a-number. R multiple without a
stop has no denominator. Both return `None`, which keeps them out of averages
instead of dragging them somewhere flattering.

**Net, not gross.** Every money figure includes commission and swap, because
that is the money the trader actually has.

No Streamlit, no database, no broker SDK.
"""

from __future__ import annotations

import statistics
from collections import Counter
from datetime import timedelta

from .models import Trade

# A breakdown bucket below this many trades is reported but flagged: the
# statistics are real, they are just not yet evidence of anything.
MIN_MEANINGFUL_SAMPLE = 10


def closed(trades) -> list[Trade]:
    """Only closed trades — an open position has no result to measure."""
    return [t for t in trades if t.is_closed]


def _mean(values):
    values = [v for v in values if v is not None]
    return statistics.fmean(values) if values else None


# =============================================================================
# HEADLINE METRICS
# =============================================================================

def compute_metrics(trades) -> dict:
    """
    Every headline figure for a set of trades.

    Returns a dict with `n` first: a caller that forgets to check the sample size
    should at least trip over it.
    """
    trades = closed(trades)
    n = len(trades)
    if n == 0:
        return {"n": 0}

    pnls = [t.pnl for t in trades if t.pnl is not None]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    scratches = [p for p in pnls if p == 0]

    gross_profit = sum(wins)
    gross_loss = sum(losses)                     # negative
    net_pnl = sum(pnls)

    # Profit factor is gross profit over gross loss. With no losses there is no
    # denominator; reporting "infinite" would put a meaningless number in a
    # column of meaningful ones.
    profit_factor = (gross_profit / abs(gross_loss)) if gross_loss < 0 else None

    decided = len(wins) + len(losses)            # scratches decide nothing
    win_rate = len(wins) / decided if decided else None

    avg_win = _mean(wins)
    avg_loss = _mean(losses)

    # Expectancy: what one trade is worth on average, in account currency.
    # Computed from the win rate and the two averages rather than as a plain mean
    # so the components stay visible and a caller can see which side moved it.
    if win_rate is not None and avg_win is not None and avg_loss is not None:
        expectancy = win_rate * avg_win + (1 - win_rate) * avg_loss
    else:
        expectancy = _mean(pnls)

    r_values = [t.r_multiple for t in trades if t.r_multiple is not None]
    durations = [t.duration_minutes for t in trades if t.duration_minutes is not None]

    equity = equity_curve(trades)
    drawdown = max_drawdown(equity)
    r_equity = r_curve(trades)
    r_drawdown = max_drawdown(r_equity)

    streaks = compute_streaks(trades)

    return {
        "n": n,
        "n_decided": decided,
        "n_scratch": len(scratches),

        "net_pnl": net_pnl,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "total_commission": sum(t.commission for t in trades),
        "total_swap": sum(t.swap for t in trades),
        "total_costs": sum(t.costs for t in trades),

        "win_rate": win_rate,
        "n_wins": len(wins),
        "n_losses": len(losses),
        "profit_factor": profit_factor,
        "expectancy": expectancy,

        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "best_trade": max(pnls) if pnls else None,
        "worst_trade": min(pnls) if pnls else None,
        "payoff_ratio": (avg_win / abs(avg_loss)) if avg_win and avg_loss else None,

        # R statistics cover only the trades that had a stop. `r_coverage` says
        # how much of the book that is, so a 0.2R average over a fifth of the
        # trades is never mistaken for the whole picture.
        "avg_r": _mean(r_values),
        "total_r": sum(r_values) if r_values else None,
        "expectancy_r": _mean(r_values),
        "best_r": max(r_values) if r_values else None,
        "worst_r": min(r_values) if r_values else None,
        "n_with_r": len(r_values),
        "r_coverage": len(r_values) / n,

        "max_drawdown": drawdown["depth"],
        "max_drawdown_pct": drawdown["depth_pct"],
        "max_drawdown_r": r_drawdown["depth"],
        "current_drawdown": drawdown["current"],

        "avg_holding_minutes": _mean(durations),
        "median_holding_minutes": statistics.median(durations) if durations else None,
        "longest_holding_minutes": max(durations) if durations else None,

        "max_win_streak": streaks["max_wins"],
        "max_loss_streak": streaks["max_losses"],
        "current_streak": streaks["current"],

        "first_trade": min(t.opened_at for t in trades),
        "last_trade": max(t.closed_at for t in trades),
        "symbols": len({t.symbol for t in trades}),
    }


# =============================================================================
# CURVES
# =============================================================================

def equity_curve(trades, starting_balance: float = 0.0) -> list[dict]:
    """
    Cumulative net P&L, one point per closed trade, in close order.

    Ordered by close time rather than open time: the equity a trader sees moves
    when a position is closed, not when it is entered.
    """
    ordered = sorted(closed(trades), key=lambda t: t.closed_at)
    running = starting_balance
    points = []
    for trade in ordered:
        running += trade.pnl or 0.0
        points.append({
            "at": trade.closed_at,
            "equity": running,
            "pnl": trade.pnl,
            "trade_id": trade.id,
            "symbol": trade.symbol,
        })
    return points


def r_curve(trades) -> list[dict]:
    """Cumulative R, over the trades that had a stop."""
    ordered = [t for t in sorted(closed(trades), key=lambda t: t.closed_at)
               if t.r_multiple is not None]
    running = 0.0
    points = []
    for trade in ordered:
        running += trade.r_multiple
        points.append({
            "at": trade.closed_at,
            "equity": running,
            "r": trade.r_multiple,
            "trade_id": trade.id,
        })
    return points


def max_drawdown(curve) -> dict:
    """
    Deepest peak-to-trough decline of a cumulative curve.

    `depth_pct` is relative to the peak and is `None` when the peak is at or
    below zero — a percentage drawdown from a negative balance is not a
    meaningful number, and printing one would be worse than printing nothing.
    """
    if not curve:
        return {"depth": None, "depth_pct": None, "current": None,
                "peak_at": None, "trough_at": None}

    peak = curve[0]["equity"]
    peak_at = curve[0]["at"]
    best_peak_at = trough_at = None
    depth = 0.0
    depth_pct = None

    for point in curve:
        value = point["equity"]
        if value > peak:
            peak, peak_at = value, point["at"]
        decline = value - peak
        if decline < depth:
            depth = decline
            best_peak_at, trough_at = peak_at, point["at"]
            depth_pct = (decline / peak) if peak > 0 else None

    final = curve[-1]["equity"]
    running_peak = max(p["equity"] for p in curve)
    current = min(final - running_peak, 0.0)

    return {
        "depth": depth,
        "depth_pct": depth_pct,
        "current": current,
        "peak_at": best_peak_at,
        "trough_at": trough_at,
    }


def daily_pnl(trades) -> list[dict]:
    """Net P&L per calendar day, ordered, including only days that traded."""
    buckets: dict = {}
    for trade in closed(trades):
        day = trade.closed_at.date()
        entry = buckets.setdefault(day, {"date": day, "pnl": 0.0, "n": 0, "r": 0.0,
                                         "n_with_r": 0})
        entry["pnl"] += trade.pnl or 0.0
        entry["n"] += 1
        if trade.r_multiple is not None:
            entry["r"] += trade.r_multiple
            entry["n_with_r"] += 1
    return sorted(buckets.values(), key=lambda b: b["date"])


# =============================================================================
# STREAKS
# =============================================================================

def compute_streaks(trades) -> dict:
    """
    Longest runs of wins and losses, and the run in progress.

    Scratches break a streak rather than extending either side: a flat trade is
    not a win, and counting it as one would inflate the number traders most
    like to quote.
    """
    ordered = sorted(closed(trades), key=lambda t: t.closed_at)
    max_wins = max_losses = 0
    run = 0
    run_is_win = None

    for trade in ordered:
        outcome = trade.is_win
        pnl = trade.pnl
        if pnl == 0 or outcome is None:
            run, run_is_win = 0, None
            continue
        if outcome == run_is_win:
            run += 1
        else:
            run, run_is_win = 1, outcome
        if outcome:
            max_wins = max(max_wins, run)
        else:
            max_losses = max(max_losses, run)

    current = 0 if run_is_win is None else (run if run_is_win else -run)
    return {"max_wins": max_wins, "max_losses": max_losses, "current": current}


def losing_streak_positions(trades, length: int = 2) -> list[int]:
    """
    Indices of trades taken immediately after `length` consecutive losses.

    The psychology module uses this to compare behaviour after a run of losses
    with behaviour the rest of the time. Returned as positions into the
    close-ordered list so the caller decides what to measure.
    """
    ordered = sorted(closed(trades), key=lambda t: t.closed_at)
    out, run = [], 0
    for i, trade in enumerate(ordered):
        if run >= length:
            out.append(i)
        if trade.is_win is False:
            run += 1
        elif trade.pnl == 0:
            pass                      # a scratch neither extends nor breaks it
        else:
            run = 0
    return out


# =============================================================================
# DISTRIBUTIONS
# =============================================================================

def pnl_distribution(trades, bins: int = 20) -> dict:
    """Histogram of per-trade net P&L, with the win/loss split."""
    pnls = [t.pnl for t in closed(trades) if t.pnl is not None]
    if not pnls:
        return {}
    low, high = min(pnls), max(pnls)
    if low == high:
        return {"edges": [low, high], "counts": [len(pnls)], "n": len(pnls)}

    width = (high - low) / bins
    counts = [0] * bins
    for value in pnls:
        index = min(int((value - low) / width), bins - 1)
        counts[index] += 1
    edges = [low + i * width for i in range(bins + 1)]
    return {
        "edges": edges, "counts": counts, "n": len(pnls),
        "n_wins": sum(1 for p in pnls if p > 0),
        "n_losses": sum(1 for p in pnls if p < 0),
    }


def r_distribution(trades) -> dict:
    """
    R multiples grouped into the buckets traders actually think in.

    Deliberately not a uniform histogram: "worse than -1R" is a meaningful
    category — it means the stop did not hold — and it deserves its own bar
    rather than being averaged into a range.
    """
    values = [t.r_multiple for t in closed(trades) if t.r_multiple is not None]
    if not values:
        return {}

    buckets = [
        ("< -1R", lambda r: r < -1),
        ("-1R to 0", lambda r: -1 <= r < 0),
        ("0 to 1R", lambda r: 0 <= r < 1),
        ("1R to 2R", lambda r: 1 <= r < 2),
        ("2R to 3R", lambda r: 2 <= r < 3),
        ("> 3R", lambda r: r >= 3),
    ]
    counts = Counter()
    for value in values:
        for label, test in buckets:
            if test(value):
                counts[label] += 1
                break

    return {
        "labels": [label for label, _ in buckets],
        "counts": [counts[label] for label, _ in buckets],
        "n": len(values),
        "beyond_stop": counts["< -1R"],
    }


def holding_time_summary(trades) -> dict:
    """Holding time in a shape the UI can render without doing arithmetic."""
    minutes = [t.duration_minutes for t in closed(trades)
               if t.duration_minutes is not None]
    if not minutes:
        return {}
    return {
        "n": len(minutes),
        "average": statistics.fmean(minutes),
        "median": statistics.median(minutes),
        "shortest": min(minutes),
        "longest": max(minutes),
        "average_delta": timedelta(minutes=statistics.fmean(minutes)),
    }


def format_duration(minutes: float | None, lang: str = "en") -> str:
    """Minutes as the largest sensible unit."""
    if minutes is None:
        return "—"
    if minutes < 60:
        return f"{minutes:.0f} min"
    if minutes < 60 * 24:
        return f"{minutes / 60:.1f} h"
    days = minutes / (60 * 24)
    return f"{days:.1f} j" if lang == "fr" else f"{days:.1f} d"


# =============================================================================
# DOWNSAMPLING
# =============================================================================

def downsample(points, max_points: int = 300, value_key: str = "equity") -> list[dict]:
    """
    Thin a curve to at most `max_points`, keeping the shape that matters.

    A phone cannot draw five thousand points and should not download them. But
    *how* a curve is thinned decides whether the picture stays true, and the
    obvious method is wrong here: taking every nth point skips whatever falls
    between the samples, and on an equity curve the thing most likely to fall
    between them is the single deepest trough. The drawdown a trader is looking
    at would render shallower on the phone than on the desktop, which is the
    same figure disagreeing with itself across two screens.

    So each bucket contributes its first, lowest, highest and last point, in
    time order. The extremes survive by construction, so the depth of every
    drawdown and the height of every peak are preserved exactly; only the
    uneventful stretches between them are thinned.

    Returns the points themselves, not copies — callers serialise them.
    """
    points = list(points or [])
    if max_points < 4 or len(points) <= max_points:
        return points

    # Four points per bucket in the worst case, so aim for a quarter as many
    # buckets as the budget allows.
    buckets = max(1, max_points // 4)
    size = len(points) / buckets

    kept: list[dict] = []
    seen: set[int] = set()
    for i in range(buckets):
        start = int(i * size)
        end = int((i + 1) * size) if i < buckets - 1 else len(points)
        chunk = points[start:end]
        if not chunk:
            continue
        lowest = min(chunk, key=lambda p: p[value_key])
        highest = max(chunk, key=lambda p: p[value_key])
        for point in (chunk[0], lowest, highest, chunk[-1]):
            if id(point) not in seen:
                seen.add(id(point))
                kept.append(point)

    # The buckets were walked in order but each contributed up to four points
    # out of order, so sort once at the end rather than per bucket.
    order = {id(p): i for i, p in enumerate(points)}
    kept.sort(key=lambda p: order[id(p)])
    return kept
