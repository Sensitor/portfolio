"""
A real portfolio, in quantities: what it is worth today, and which part of it
the analysis covers.

Two steps, shared by the separate analytics app and the platform's
« Portefeuille et risque » space so they can never value the same holdings
differently:

* `value(quantities, prices)`: each line's value in the base currency, the
  total and the weights. `prices` comes from `portfolio.latest_prices`, which
  has already converted every quote into the base currency and filled a price
  typed by hand where no provider has one; a line without any price is listed,
  never valued at zero.
* `split_analysed(values, analysed)`: a line priced by hand has a value today
  and no history, so the analyzer cannot give it a volatility, a correlation or
  a drawdown and leaves it out. Its money must leave the analysed book with it,
  or the analysed portfolio comes out larger than the lines actually in it.

No Streamlit, no network.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Valuation:
    values: dict[str, float]      # ticker -> value in the base currency
    total: float
    weights: dict[str, float]     # ticker -> share of the total
    unpriced: tuple[str, ...]     # lines with a quantity and no price at all


def value(quantities: dict[str, float], prices: dict[str, float]) -> Valuation:
    """Quantity × price for every line that has a price, in the base currency."""
    values = {t: float(prices[t]) * float(q) for t, q in quantities.items() if t in prices and q and q > 0}
    total = sum(values.values())
    weights = {t: v / total for t, v in values.items()} if total > 0 else {}
    unpriced = tuple(t for t, q in quantities.items() if t not in prices and q and q > 0)
    return Valuation(values, total, weights, unpriced)


def split_analysed(values: dict[str, float], analysed: list[str]) -> tuple[float, dict[str, float]]:
    """The value the analysis covers, and the lines it leaves out with their value."""
    covered = sum(values[t] for t in analysed if t in values)
    excluded = {t: v for t, v in values.items() if t not in analysed}
    return covered, excluded
