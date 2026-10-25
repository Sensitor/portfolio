"""
The arithmetic of inflation taught in the course « L'inflation »: a rate from a
price index, cumulative and annualised inflation, purchasing power, the time it
takes prices to double, and how much each component contributes to the total.

Pure functions over plain numbers; rates are fractions (0.02 for 2 %). The
lessons quote figures these functions compute, and the tests recompute them.
These are identities and definitions, not forecasts: what causes inflation is
the subject of the lessons, not of this module.
"""

from __future__ import annotations

import math
from typing import Iterable, Mapping


def rate_from_index(start: float, end: float) -> float:
    """Price change between two index values."""
    if start <= 0 or end <= 0:
        raise ValueError("a price index is positive")
    return end / start - 1


def cumulative(rates: Iterable[float]) -> float:
    """Inflation over several periods: rates compound, they do not add."""
    total = 1.0
    for r in rates:
        if r <= -1:
            raise ValueError("a rate cannot be -100 % or below")
        total *= 1 + r
    return total - 1


def annualised(total: float, years: float) -> float:
    """The constant yearly rate that gives `total` over `years`."""
    if years <= 0 or total <= -1:
        raise ValueError("years must be positive and the total above -100 %")
    return (1 + total) ** (1 / years) - 1


def real_value(amount: float, total_inflation: float) -> float:
    """What `amount` buys, in today's money, after `total_inflation`."""
    if total_inflation <= -1:
        raise ValueError("inflation cannot be -100 % or below")
    return amount / (1 + total_inflation)


def years_to_halve(rate: float) -> float:
    """Years for a constant inflation `rate` to halve purchasing power (prices double)."""
    if rate <= 0:
        raise ValueError("purchasing power only halves with a positive rate")
    return math.log(2) / math.log(1 + rate)


def contributions(weights: Mapping[str, float], rates: Mapping[str, float]) -> dict[str, float]:
    """
    Contribution of each component to total inflation: its weight in the basket
    times its own rate. Weights are shares of spending and must sum to 1.
    """
    if set(weights) != set(rates):
        raise ValueError("every component needs a weight and a rate")
    if abs(sum(weights.values()) - 1) > 1e-9 or any(w < 0 for w in weights.values()):
        raise ValueError("weights are non-negative shares that sum to 1")
    return {k: weights[k] * rates[k] for k in weights}


def quantity_growth(money: float, velocity: float, output: float) -> float:
    """
    Price growth implied by the identity M × V = P × Y, in growth rates:
    (1 + m)(1 + v) = (1 + p)(1 + y). An identity, true by construction; it says
    nothing about which variable moves which.
    """
    return (1 + money) * (1 + velocity) / (1 + output) - 1
