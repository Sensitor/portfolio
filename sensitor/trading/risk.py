"""
Trading risk.

How much is risked per trade, how consistently, how that changes over time, and
how much of it is on the table at once.

The distinction from `analytics`: that module measures results, this one measures
exposure. A trader with a good month can still have a risk problem, and the
numbers that reveal it — dispersion of position risk, drift in sizing, losses
worse than the stop — are not in any P&L summary.

What this module will not do: estimate risk of ruin, recommend a position size,
or apply Kelly. Those need a stable edge and a stable distribution, and a few
hundred discretionary trades give neither. Everything here describes what was
risked, not what should be.

No Streamlit, no database.
"""

from __future__ import annotations

import math
import statistics

from .analytics import closed

# Below this, dispersion statistics are too noisy to mean anything.
MIN_SAMPLE = 8


def _risks(trades) -> list[float]:
    return [t.risk_amount for t in closed(trades) if t.risk_amount is not None]


# =============================================================================
# RISK PROFILE
# =============================================================================

def risk_profile(trades) -> dict:
    """
    How much this trader risks, and how consistently.

    `coverage` is the share of trades that had a stop at all. Every other figure
    here describes only those trades, so a profile computed over a third of the
    book must be read as such — the coverage number is what makes that visible
    instead of implied.
    """
    all_closed = closed(trades)
    risks = _risks(all_closed)
    if not all_closed:
        return {"n": 0}

    if not risks:
        return {"n": len(all_closed), "n_with_stop": 0,
                "coverage": 0.0, "no_stop_count": len(all_closed)}

    mean = statistics.fmean(risks)
    median = statistics.median(risks)
    spread = statistics.pstdev(risks) if len(risks) > 1 else 0.0

    # Coefficient of variation: spread relative to size, so it compares across
    # accounts and currencies. A disciplined fixed-risk trader sits near zero.
    # Dispersion over a handful of trades is noise, so the consistency figure is
    # withheld rather than shown with a caveat nobody reads.
    consistency = (spread / mean) if mean > 0 and len(risks) >= MIN_SAMPLE else None

    return {
        "n": len(all_closed),
        "n_with_stop": len(risks),
        "coverage": len(risks) / len(all_closed),
        "no_stop_count": len(all_closed) - len(risks),
        "mean_risk": mean,
        "median_risk": median,
        "min_risk": min(risks),
        "max_risk": max(risks),
        "risk_spread": spread,
        "consistency": consistency,
        "largest_vs_median": max(risks) / median if median > 0 else None,
    }


def risk_over_time(trades, window: int = 10) -> list[dict]:
    """
    Rolling median risk, in trade order.

    Median rather than mean: one outsized trade should show up as an outlier in
    the series, not bend the whole line.
    """
    ordered = [t for t in sorted(closed(trades), key=lambda t: t.opened_at)
               if t.risk_amount is not None]
    if len(ordered) < window:
        return []

    points = []
    for i in range(window - 1, len(ordered)):
        chunk = [t.risk_amount for t in ordered[i - window + 1: i + 1]]
        points.append({
            "at": ordered[i].opened_at,
            "median_risk": statistics.median(chunk),
            "trade_id": ordered[i].id,
        })
    return points


def risk_drift(trades, window: int = 10) -> dict:
    """
    Whether risk per trade has been rising or falling.

    Compares the first and last rolling windows. A direction, not a trend line:
    fitting a slope to a dozen points would dress a rough comparison up as
    something more precise than it is.
    """
    series = risk_over_time(trades, window)
    if len(series) < 2:
        return {}

    start = series[0]["median_risk"]
    end = series[-1]["median_risk"]
    if start <= 0:
        return {}

    change = (end - start) / start
    return {
        "start_median": start,
        "end_median": end,
        "change": change,
        "direction": "up" if change > 0.15 else ("down" if change < -0.15 else "stable"),
        "n_points": len(series),
        "from": series[0]["at"],
        "to": series[-1]["at"],
    }


# =============================================================================
# STOP DISCIPLINE
# =============================================================================

def stop_discipline(trades) -> dict:
    """
    Whether losses stayed within the stop.

    A loss worse than -1R means the stop did not do its job: it was moved,
    removed, gapped through, or slipped. The module cannot tell which — it
    reports the count and leaves the diagnosis to the trader, who knows.

    Measured on `r_multiple_gross`, the price-based figure, deliberately. The net
    R includes commission and swap, so a trade stopped out at exactly -1R gross
    lands past -1R net on costs alone; judged that way, a disciplined trader with
    a per-trade commission looks like one whose stops never hold. The averages
    below are also gross, so they compare like with like.
    """
    with_r = [t for t in closed(trades) if t.r_multiple_gross is not None]
    losses = [t for t in with_r if t.r_multiple_gross < 0]
    if not losses:
        return {"n_losses": 0, "n_with_r": len(with_r)}

    beyond = [t for t in losses if t.r_multiple_gross < -1.05]   # 5% for slippage
    worst = min(t.r_multiple_gross for t in losses)

    return {
        "n_with_r": len(with_r),
        "n_losses": len(losses),
        "n_beyond_stop": len(beyond),
        "share_beyond_stop": len(beyond) / len(losses),
        "worst_loss_r": worst,
        "avg_loss_r": statistics.fmean(t.r_multiple_gross for t in losses),
        "measured_on": "gross",
        "beyond_stop_trades": [t.id for t in beyond],
    }


# =============================================================================
# CONCURRENT EXPOSURE
# =============================================================================

def concurrent_exposure(trades) -> dict:
    """
    How many positions were open at once, and how much was risked simultaneously.

    Per-trade risk is the usual measure and it understates the real one: five
    trades each risking 1% taken at the same time on correlated instruments is
    not five separate 1% bets. This finds the busiest moment by sweeping the
    open/close events in time order.
    """
    events = []
    for trade in closed(trades):
        events.append((trade.opened_at, 1, trade.risk_amount or 0.0, trade.symbol))
        events.append((trade.closed_at, -1, -(trade.risk_amount or 0.0), trade.symbol))
    if not events:
        return {}

    events.sort(key=lambda e: (e[0], -e[1]))   # opens before closes at the same instant

    count = risk = 0.0
    peak_count = peak_risk = 0.0
    peak_at = peak_risk_at = None
    open_symbols: dict = {}
    peak_symbols: list = []

    for moment, delta, risk_delta, symbol in events:
        count += delta
        risk += risk_delta
        if delta > 0:
            open_symbols[symbol] = open_symbols.get(symbol, 0) + 1
        else:
            open_symbols[symbol] = open_symbols.get(symbol, 0) - 1
            if open_symbols[symbol] <= 0:
                open_symbols.pop(symbol, None)

        if count > peak_count:
            peak_count, peak_at = count, moment
            peak_symbols = sorted(open_symbols)
        if risk > peak_risk:
            peak_risk, peak_risk_at = risk, moment

    return {
        "max_concurrent": int(peak_count),
        "max_concurrent_at": peak_at,
        "max_concurrent_symbols": peak_symbols,
        "max_simultaneous_risk": peak_risk,
        "max_simultaneous_risk_at": peak_risk_at,
    }


def trades_per_day(trades) -> dict:
    """Activity per trading day — the input to any overtrading question."""
    ordered = closed(trades)
    if not ordered:
        return {}
    by_day: dict = {}
    for trade in ordered:
        by_day.setdefault(trade.opened_at.date(), []).append(trade)

    counts = [len(v) for v in by_day.values()]
    busiest_day = max(by_day, key=lambda d: len(by_day[d]))

    return {
        "n_days": len(by_day),
        "mean_per_day": statistics.fmean(counts),
        "median_per_day": statistics.median(counts),
        "max_per_day": max(counts),
        "busiest_day": busiest_day,
        "counts_by_day": {d: len(v) for d, v in sorted(by_day.items())},
    }


# =============================================================================
# EXPECTED LOSING RUNS
# =============================================================================

def expected_loss_streak(win_rate: float | None, n_trades: int) -> dict:
    """
    The longest losing run to expect from this win rate, by chance alone.

    Useful because the most common reason a trader abandons a working system is
    a losing run that was statistically unremarkable. With a 45% win rate over
    200 trades, a run of nine losses is the *expected* maximum, not evidence that
    anything broke.

    Uses the standard approximation for the longest run of independent failures,
    log(n) / log(1/q). Trades are not perfectly independent — a trader's state
    carries over — so treat this as an order of magnitude, not a threshold.
    """
    if not win_rate or n_trades < 10 or win_rate >= 1:
        return {}
    loss_rate = 1 - win_rate
    if loss_rate <= 0:
        return {}

    expected = math.log(n_trades) / math.log(1 / loss_rate)
    return {
        "win_rate": win_rate,
        "n_trades": n_trades,
        "expected_max_streak": expected,
        "expected_max_streak_rounded": max(1, round(expected)),
        "assumption": "independent trades",
    }


def streak_context(trades) -> dict:
    """
    The observed worst losing run against the one to expect.

    Answers "was that run unusual?" with a number rather than a feeling.
    """
    from .analytics import compute_metrics, compute_streaks

    metrics = compute_metrics(trades)
    if metrics.get("n", 0) < 10:
        return {}

    streaks = compute_streaks(trades)
    expected = expected_loss_streak(metrics.get("win_rate"), metrics["n"])
    if not expected:
        return {}

    observed = streaks["max_losses"]
    return {
        "observed_max_losses": observed,
        "expected_max_losses": expected["expected_max_streak_rounded"],
        "unusual": observed > expected["expected_max_streak"] * 1.5,
        "win_rate": metrics["win_rate"],
        "n": metrics["n"],
    }


def summary(trades) -> dict:
    """Everything in this module, for a caller that wants one call."""
    return {
        "profile": risk_profile(trades),
        "drift": risk_drift(trades),
        "stops": stop_discipline(trades),
        "exposure": concurrent_exposure(trades),
        "activity": trades_per_day(trades),
        "streaks": streak_context(trades),
    }
