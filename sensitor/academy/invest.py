"""
The calculations taught in the Investissement track: buying progressively,
value averaging, rebalancing, the weight of a volatile asset in a portfolio,
and the French formula for gains on digital assets.

Pure functions over the lesson examples. None of them says what a market
will do; they say what a method does with the prices it is given. The tax
rate is a parameter, never a constant: it changes, and the lessons say to
check the year's rate on impots.gouv.fr.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


# =============================================================================
# BUYING PROGRESSIVELY
# =============================================================================

@dataclass(frozen=True)
class Accumulation:
    invested: float
    units: float

    @property
    def average_cost(self) -> float:
        return self.invested / self.units


def fixed_amount(amount: float, prices: Sequence[float]) -> Accumulation:
    """Investing the same amount at each price: more units when the price is low."""
    if amount <= 0 or not prices or any(p <= 0 for p in prices):
        raise ValueError("a positive amount and positive prices are needed")
    return Accumulation(amount * len(prices), sum(amount / p for p in prices))


def lump_sum(total: float, price: float) -> Accumulation:
    return Accumulation(total, total / price)


def value_averaging(target_step: float, prices: Sequence[float]) -> list[float]:
    """
    The contributions of value averaging: at each date the holding must be
    worth `target_step` times the number of dates so far. One buys what is
    missing, and sells, as a negative contribution, what exceeds the target.
    """
    units, out = 0.0, []
    for i, price in enumerate(prices, start=1):
        gap = target_step * i - units * price
        out.append(gap)
        units += gap / price
    return out


# =============================================================================
# PORTFOLIO
# =============================================================================

def weight_after_move(weight: float, move: float, other_move: float = 0.0) -> float:
    """The weight of an asset after its price moves by `move` and the rest by `other_move`."""
    a, b = weight * (1 + move), (1 - weight) * (1 + other_move)
    return a / (a + b)


def rebalance_amount(total: float, weight: float, target: float) -> float:
    """What to sell (positive) or buy (negative) of an asset to bring it back to its target weight."""
    return total * (weight - target)


def portfolio_move(weights: Sequence[float], moves: Sequence[float]) -> float:
    """The change of a whole portfolio when each part moves by its own percentage."""
    if abs(sum(weights) - 1) > 1e-9:
        raise ValueError("the weights must add up to 1")
    return sum(w * m for w, m in zip(weights, moves))


# =============================================================================
# FRENCH TAX ON DIGITAL ASSETS
# =============================================================================

def gain_on_disposal(sale_price: float, total_acquisition_cost: float, portfolio_value: float) -> float:
    """
    The gain of a sale under article 150 VH bis of the Code général des impôts:
    the sale price minus the share of the whole portfolio's acquisition cost
    that the sale represents, measured on the value of the whole portfolio
    just before the sale.
    """
    if portfolio_value <= 0 or sale_price < 0 or sale_price > portfolio_value:
        raise ValueError("the sale cannot exceed the portfolio's value")
    return sale_price - total_acquisition_cost * sale_price / portfolio_value


def remaining_acquisition_cost(total_acquisition_cost: float, sale_price: float, portfolio_value: float) -> float:
    """The acquisition cost that stays attached to the portfolio after the sale."""
    return total_acquisition_cost - total_acquisition_cost * sale_price / portfolio_value


# =============================================================================
# CHART ROWS (lesson examples)
# =============================================================================

def volatility_rows(rest_vol: float = 0.10, crypto_vol: float = 0.60, correlation: float = 0.2) -> list[dict]:
    from .savings import portfolio_volatility
    return [{"part": w, "volatilite": round(portfolio_volatility(w / 100, crypto_vol, rest_vol, correlation) * 100, 2)}
            for w in range(0, 51, 5)]


# A constructed price path for the progressive buying and rebalancing lessons:
# a fall of 60 % over a year, then a recovery to three times the low.
EXAMPLE_PATH = (100, 92, 85, 78, 70, 64, 58, 52, 48, 45, 42, 40, 41, 44, 48, 53, 58, 64, 71, 79, 87, 96, 108, 120)


def dca_rows(amount: float = 100.0, prices=EXAMPLE_PATH) -> list[dict]:
    rows, units = [], 0.0
    for i, p in enumerate(prices, start=1):
        units += amount / p
        rows.append({"mois": i, "prix": p, "prix_de_revient": round(amount * i / units, 2),
                     "en_une_fois": prices[0]})
    return rows


def drift_rows(target: float = 0.10, prices=EXAMPLE_PATH, rest_growth: float = 0.004) -> list[dict]:
    """The crypto weight month by month, left alone or rebalanced each quarter to its target."""
    crypto, rest = target * 100_000, (1 - target) * 100_000
    c2, r2 = crypto, rest
    rows = []
    for i, (p0, p1) in enumerate(zip(prices, prices[1:]), start=1):
        crypto *= p1 / p0; rest *= 1 + rest_growth
        c2 *= p1 / p0; r2 *= 1 + rest_growth
        if i % 3 == 0:
            total = c2 + r2; c2, r2 = total * target, total * (1 - target)
        rows.append({"mois": i, "sans_reequilibrage": round(crypto / (crypto + rest) * 100, 2),
                     "reequilibre": round(c2 / (c2 + r2) * 100, 2)})
    return rows


def stress_rows() -> list[dict]:
    """The crisis scenario of the lesson: each pocket's contribution to the fall, in euros."""
    total = 200_000
    return [{"poche": name, "contribution": round(total * w * m)} for name, w, m in
            (("Crypto", 0.05, -0.8), ("Actions", 0.55, -0.3), ("Fonds en euros et liquidités", 0.40, 0.0))]


def recovery_rows() -> list[dict]:
    """The gain needed to make up for a fall, from 10 % to 90 %."""
    return [{"baisse": d, "hausse_necessaire": round((1 / (1 - d / 100) - 1) * 100, 1)} for d in range(10, 91, 10)]
