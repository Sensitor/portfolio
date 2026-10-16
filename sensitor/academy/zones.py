"""
The zone rules taught in path 4: Fair Value Gaps, order blocks, retracements
and the OTE band, and the overlap of two zones.

Pure functions over plain sequences, like `structure.py`: the lessons, the
exercises and the tests use the same definitions, so a figure quoted in a
lesson is a figure this module computes.

Every rule here is a convention of the course, stated in the lessons as such.
None of them says what price will do.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

BULLISH = "bullish"
BEARISH = "bearish"

# The OTE band as most methods quote it: from 62 % to 79 % of the leg, with
# 70.5 % as its middle. A convention, not a property of markets.
OTE_SHALLOW, OTE_MIDDLE, OTE_DEEP = 0.62, 0.705, 0.79


@dataclass(frozen=True)
class Gap:
    """A Fair Value Gap: the price range three bars leave untraded."""
    kind: str
    index: int          # the middle bar, the one whose move leaves the gap
    low: float
    high: float

    @property
    def size(self) -> float:
        return self.high - self.low

    @property
    def midpoint(self) -> float:
        """The « consequent encroachment »: half way through the gap."""
        return (self.low + self.high) / 2


def fair_value_gaps(highs: Sequence[float], lows: Sequence[float]) -> list[Gap]:
    """
    Every three-bar gap, in order.

    Bullish at bar `i` when the low of bar `i + 1` is above the high of bar
    `i - 1`; bearish when the high of bar `i + 1` is below the low of bar
    `i - 1`. Strict inequalities: bars that touch leave no gap.
    """
    if len(highs) != len(lows):
        raise ValueError("highs and lows must have the same length")
    gaps = []
    for i in range(1, len(highs) - 1):
        if lows[i + 1] > highs[i - 1]:
            gaps.append(Gap(BULLISH, i, highs[i - 1], lows[i + 1]))
        elif highs[i + 1] < lows[i - 1]:
            gaps.append(Gap(BEARISH, i, highs[i + 1], lows[i - 1]))
    return gaps


def filled_fraction(gap: Gap, extreme: float) -> float:
    """
    How much of a gap later prices have traded into, from 0 to 1.

    `extreme` is the furthest price reached into the gap: the lowest low since
    a bullish gap formed, the highest high since a bearish one formed.
    """
    if gap.size <= 0:
        raise ValueError("a gap must have a positive size")
    reached = gap.high - extreme if gap.kind == BULLISH else extreme - gap.low
    return min(1.0, max(0.0, reached / gap.size))


def order_block(opens: Sequence[float], closes: Sequence[float], impulse: int, *,
                direction: str) -> int | None:
    """
    The index of the order block of an impulse starting at bar `impulse`.

    Course convention: the last bar of the opposite colour before the impulse,
    a down bar for a move up and an up bar for a move down. None when there is
    no such bar.
    """
    if direction not in (BULLISH, BEARISH):
        raise ValueError("direction must be 'bullish' or 'bearish'")
    if not 0 <= impulse < len(opens) or len(opens) != len(closes):
        raise ValueError("impulse must index the bars, and opens and closes must match")
    for i in range(impulse - 1, -1, -1):
        if (closes[i] < opens[i]) if direction == BULLISH else (closes[i] > opens[i]):
            return i
    return None


def retracement(start: float, end: float, ratio: float) -> float:
    """The price `ratio` of the way back from `end` towards `start`."""
    return end - ratio * (end - start)


def ote_zone(start: float, end: float, shallow: float = OTE_SHALLOW,
             deep: float = OTE_DEEP) -> tuple[float, float]:
    """The OTE band of a leg from `start` to `end`, as (low, high)."""
    if not 0 < shallow < deep < 1:
        raise ValueError("ratios must satisfy 0 < shallow < deep < 1")
    a, b = retracement(start, end, shallow), retracement(start, end, deep)
    return (min(a, b), max(a, b))


def overlap(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float] | None:
    """The common part of two price zones, or None when they do not meet."""
    low, high = max(min(a), min(b)), min(max(a), max(b))
    return (low, high) if low < high else None
