"""
The calculations taught in path 8: reading a release, what the market already
expects, and how much a published figure can move a price.

Pure functions. The lessons, the exercises and the tests use these definitions,
so a number printed in a lesson is the number this module returns.

None of these figures predicts the direction of a market. A surprise says how
far a figure lands from what was expected; an implied move says how large a
move the options market is pricing, not which way it will go.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Sequence
from zoneinfo import ZoneInfo

PARIS = ZoneInfo("Europe/Paris")
NEW_YORK = ZoneInfo("America/New_York")
QUARTER_POINT = 0.25          # the usual step of a central bank decision, in points


# =============================================================================
# RELEASES
# =============================================================================

def surprise(actual: float, consensus: float) -> float:
    """Published minus expected. Positive: the figure came out above the consensus."""
    return actual - consensus


def standardized_surprise(actual: float, consensus: float, past_surprises: Sequence[float]) -> float:
    """
    The surprise in units of the usual surprise: divided by the sample standard
    deviation of past surprises on the same indicator. Comparable across
    indicators measured in different units.
    """
    if len(past_surprises) < 2:
        raise ValueError("at least two past surprises are needed")
    mean = sum(past_surprises) / len(past_surprises)
    sd = math.sqrt(sum((s - mean) ** 2 for s in past_surprises) / (len(past_surprises) - 1))
    if sd == 0:
        raise ValueError("past surprises do not vary")
    return surprise(actual, consensus) / sd


def monthly_changes(levels: Sequence[float | None]) -> list[float | None]:
    """Change from one month to the next; None where either month is missing."""
    return [None if a is None or b is None else b - a for a, b in zip(levels, levels[1:])]


def release_time_paris(day: date, hour: int, minute: int, zone: ZoneInfo = NEW_YORK) -> time:
    """
    The Paris time of a release published at `hour:minute` in `zone` on `day`.
    The United States and Europe change clocks on different weekends, so an
    American release usually at 14:30 in Paris comes out at 13:30 for a few
    weeks each spring and autumn.
    """
    local = datetime(day.year, day.month, day.day, hour, minute, tzinfo=zone)
    return local.astimezone(PARIS).time()


# =============================================================================
# CENTRAL BANKS AND RATES
# =============================================================================

def implied_rate(futures_price: float) -> float:
    """A rate future is quoted 100 minus the expected rate: 95,80 means 4,20 %."""
    return 100.0 - futures_price


def priced_moves(implied: float, current: float, step: float = QUARTER_POINT) -> float:
    """How many steps of `step` points the market expects; negative for cuts."""
    return (implied - current) / step


def move_probability(implied: float, current: float, step: float = QUARTER_POINT) -> float:
    """
    The probability of one move of `step`, read from a single meeting as the
    share of the step already priced, between 0 and 1. A simplification: it
    assumes only two outcomes, no move or one step, and ignores the risk
    premium in the future's price.
    """
    return max(0.0, min(1.0, abs(implied - current) / step))


def curve_spread(long_yield: float, short_yield: float) -> float:
    """Long minus short, in points. Negative: the curve is inverted."""
    return long_yield - short_yield


@dataclass(frozen=True)
class Run:
    start: str
    end: str
    months: int


def inverted_runs(months: Sequence[str], spreads: Sequence[float | None]) -> list[Run]:
    """Consecutive months with a negative spread, as runs from first to last month."""
    runs: list[Run] = []
    current: list[str] = []
    for month, spread in zip(months, spreads):
        if spread is not None and spread < 0:
            current.append(month)
        elif current:
            runs.append(Run(current[0], current[-1], len(current)))
            current = []
    if current:
        runs.append(Run(current[0], current[-1], len(current)))
    return runs


def real_rate(nominal: float, inflation: float) -> float:
    """The simple difference used in market commentary: nominal minus inflation, in points."""
    return nominal - inflation


# =============================================================================
# EVENT VOLATILITY
# =============================================================================

def expected_move(price: float, annual_vol_pct: float, days: float, days_per_year: float = 365) -> float:
    """
    One standard deviation of the price over `days`, from an annualised
    implied volatility in percent. About two times in three the move stays
    inside it; it says nothing of the direction.
    """
    if price <= 0 or annual_vol_pct < 0 or days <= 0:
        raise ValueError("price and horizon must be positive, volatility not negative")
    return price * annual_vol_pct / 100 * math.sqrt(days / days_per_year)


def event_size(amount: float, stop_distance: float, slippage: float, value_per_point: float) -> float:
    """
    The size whose loss at the stop, slippage included, equals `amount`. Around
    a release a stop is often filled beyond its level: sizing on the stop alone
    understates the risk.
    """
    if stop_distance <= 0 or slippage < 0 or value_per_point <= 0:
        raise ValueError("stop and value per point must be positive, slippage not negative")
    return amount / ((stop_distance + slippage) * value_per_point)


def loss_at_stop(size: float, stop_distance: float, slippage: float, value_per_point: float) -> float:
    """What a stop-out costs once the slippage is added."""
    return size * (stop_distance + slippage) * value_per_point
