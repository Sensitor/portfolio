"""
Savings over time, in nominal and in real terms: the arithmetic of the course
« Inflation et patrimoine » and of its simulator.

Pure functions, no Streamlit. Rates are annual fractions (0.05 for 5 %). The
projection runs month by month: the capital grows at the monthly equivalent of
the nominal rate, fees are taken monthly as a share of the capital, the
contribution is added at the end of each month, and the real value is the
nominal value divided by the price level reached.

Every rate here is held constant: an assumption, stated in the simulator, that
markets never satisfy. The point is to show mechanisms (compounding, fees,
inflation), not to predict a balance.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


def real_rate(nominal: float, inflation: float) -> float:
    """The exact real return, Fisher's relation: (1 + nominal) ÷ (1 + inflation) − 1."""
    if inflation <= -1:
        raise ValueError("inflation cannot be -100 % or below")
    return (1 + nominal) / (1 + inflation) - 1


def compound(amount: float, rate: float, years: float) -> float:
    if rate <= -1:
        raise ValueError("a rate cannot be -100 % or below")
    return amount * (1 + rate) ** years


def doubling_time(rate: float) -> float:
    """Exact years to double at a constant `rate`."""
    if rate <= 0:
        raise ValueError("doubling needs a positive rate")
    return math.log(2) / math.log(1 + rate)


def rule_of_72(rate: float) -> float:
    """The mental shortcut: 72 divided by the rate in percent."""
    if rate <= 0:
        raise ValueError("the rule needs a positive rate")
    return 72 / (rate * 100)


def geometric_mean(returns: list[float]) -> float:
    """The constant yearly rate equivalent to a sequence of yearly returns."""
    total = 1.0
    for r in returns:
        if r <= -1:
            raise ValueError("a yearly return cannot be -100 % or below")
        total *= 1 + r
    return total ** (1 / len(returns)) - 1


def portfolio_volatility(w1: float, vol1: float, vol2: float, correlation: float) -> float:
    """Volatility of two assets held in weights w1 and 1 − w1, for a given correlation."""
    if not 0 <= w1 <= 1 or vol1 < 0 or vol2 < 0 or not -1 <= correlation <= 1:
        raise ValueError("weights in [0, 1], volatilities non-negative, correlation in [-1, 1]")
    w2 = 1 - w1
    return math.sqrt((w1 * vol1) ** 2 + (w2 * vol2) ** 2 + 2 * w1 * w2 * correlation * vol1 * vol2)


@dataclass(frozen=True)
class Year:
    year: int
    contributed: float      # initial capital plus every contribution so far
    nominal: float          # what the account shows
    real: float             # what it buys, in money of the start
    fees: float             # fees paid so far


def project(initial: float, years: int, nominal_rate: float, inflation: float, *,
            monthly_contribution: float = 0.0, annual_fee: float = 0.0, tax_on_gains: float = 0.0) -> list[Year]:
    """
    Year-end values of a savings account, from year 0. Constant rates. If
    `tax_on_gains` is set, it is applied once, to the gains, at the last year.
    """
    if initial < 0 or monthly_contribution < 0 or years < 1:
        raise ValueError("amounts must be non-negative and the duration at least one year")
    if not 0 <= annual_fee < 1 or not 0 <= tax_on_gains < 1:
        raise ValueError("fees and tax are shares between 0 and 1")
    if nominal_rate <= -1 or inflation <= -1:
        raise ValueError("rates cannot be -100 % or below")
    growth = (1 + nominal_rate) ** (1 / 12)
    keep = (1 - annual_fee) ** (1 / 12)
    balance, contributed, fees = float(initial), float(initial), 0.0
    rows = [Year(0, contributed, balance, balance, 0.0)]
    for year in range(1, years + 1):
        for _ in range(12):
            balance *= growth
            fee = balance * (1 - keep)
            balance -= fee
            fees += fee
            balance += monthly_contribution
            contributed += monthly_contribution
        nominal = balance
        if year == years and tax_on_gains:
            nominal = balance - max(balance - contributed, 0.0) * tax_on_gains
        rows.append(Year(year, contributed, nominal, nominal / (1 + inflation) ** year, fees))
    return rows
