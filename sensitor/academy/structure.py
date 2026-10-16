"""
The structure rules taught in path 2, as code.

The lessons define a swing with an explicit rule; this module applies that rule
so the exercises' answers are computed rather than asserted, and so a future
chart exercise can mark the swings itself.

Rule (default `n = 2`): bar *i* is a swing high when its high is strictly
greater than the highs of the `n` bars before and the `n` bars after; a swing
low, symmetrically, on the lows. A swing is confirmed at the close of bar
`i + n`. Bars without `n` neighbours on each side cannot be swings yet.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

HIGH = "high"
LOW = "low"


@dataclass(frozen=True)
class Swing:
    index: int          # 0-based bar index
    kind: str           # high | low
    price: float
    confirmed_at: int   # 0-based index of the bar whose close confirms it


def swings(highs: Sequence[float], lows: Sequence[float], n: int = 2) -> list[Swing]:
    if len(highs) != len(lows):
        raise ValueError("highs and lows must have the same length")
    if n < 1:
        raise ValueError("n must be at least 1")
    found = []
    for i in range(n, len(highs) - n):
        around = list(range(i - n, i)) + list(range(i + 1, i + n + 1))
        if all(highs[i] > highs[j] for j in around):
            found.append(Swing(i, HIGH, highs[i], i + n))
        if all(lows[i] < lows[j] for j in around):
            found.append(Swing(i, LOW, lows[i], i + n))
    return found


def is_break(close: float, level: float, *, direction: str) -> bool:
    """A break in close, per the course convention: beyond the level, not at it."""
    if direction == "up":
        return close > level
    if direction == "down":
        return close < level
    raise ValueError("direction must be 'up' or 'down'")


def equal_levels(levels: Sequence[float], tolerance: float) -> list[list[int]]:
    """
    Group swing levels that sit within `tolerance` of each other ("equal highs"
    or "equal lows"). Returns the groups of indices with at least two members,
    in order. Grouping is by distance to the group's first level, so a slow
    drift of many small steps is not mistaken for one level.
    """
    if tolerance < 0:
        raise ValueError("tolerance must be non-negative")
    groups: list[list[int]] = []
    for i, level in enumerate(levels):
        for group in groups:
            if abs(level - levels[group[0]]) <= tolerance + 1e-12:
                group.append(i)
                break
        else:
            groups.append([i])
    return [g for g in groups if len(g) >= 2]


def is_sweep(high: float, low: float, close: float, level: float, *, side: str) -> bool:
    """
    A sweep, per the course convention: the bar trades beyond the level and
    closes back on the original side. `side="above"` for a level of highs,
    `side="below"` for a level of lows.
    """
    if side == "above":
        return high > level and close <= level
    if side == "below":
        return low < level and close >= level
    raise ValueError("side must be 'above' or 'below'")
