"""
The measurements taught in path 7: what a series of backtested trades says,
and how much of it is noise.

Pure functions over lists of results in R. The lessons, the exercises and the
tests use the same definitions as `expectancy.py`, which this module extends:
expectancy there is computed from assumptions, here from recorded trades.

None of these figures says a strategy will work. They say how large the
uncertainty around a measured result is, which is the question a backtest
can actually answer.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

from .expectancy import Interval


@dataclass(frozen=True)
class Summary:
    trades: int
    wins: int
    win_rate: float
    average_win: float              # in R, over winning trades
    average_loss: float             # in R, a positive number, over losing trades
    gross_expectancy: float         # mean result in R, before costs
    net_expectancy: float           # mean result in R, after costs
    profit_factor: float | None     # gross wins over gross losses; None without a loss
    sd: float                       # sample standard deviation of the results


def summarize(results_r: Sequence[float], cost_r: float = 0.0) -> Summary:
    """
    The figures of a recorded series. `cost_r` is the average cost of one trade
    (spread, commission, slippage) in R, subtracted from every result.
    A result of exactly zero counts as neither a win nor a loss.
    """
    n = len(results_r)
    if n < 2:
        raise ValueError("a series needs at least two trades")
    if cost_r < 0:
        raise ValueError("costs cannot be negative")
    wins = [r for r in results_r if r > 0]
    losses = [-r for r in results_r if r < 0]
    mean = sum(results_r) / n
    sd = math.sqrt(sum((r - mean) ** 2 for r in results_r) / (n - 1))
    return Summary(
        trades=n, wins=len(wins), win_rate=len(wins) / n,
        average_win=sum(wins) / len(wins) if wins else 0.0,
        average_loss=sum(losses) / len(losses) if losses else 0.0,
        gross_expectancy=mean, net_expectancy=mean - cost_r,
        profit_factor=sum(wins) / sum(losses) if losses else None, sd=sd)


def standard_error(sd: float, trades: int) -> float:
    if trades < 2 or sd < 0:
        raise ValueError("need at least two trades and a non-negative deviation")
    return sd / math.sqrt(trades)


def mean_interval(mean: float, sd: float, trades: int, z: float = 1.96) -> Interval:
    """
    The usual normal approximation of a 95 % interval around a mean result:
    mean ± z · sd / √n. Reasonable from a few dozen trades; on fewer, it is
    optimistic, which is one more reason not to conclude on fewer.
    """
    half = z * standard_error(sd, trades)
    return Interval(mean - half, mean + half)


def trades_needed(sd: float, half_width: float, z: float = 1.96) -> int:
    """How many trades bring the half-width of that interval down to `half_width`."""
    if sd <= 0 or half_width <= 0:
        raise ValueError("deviation and half-width must be positive")
    return math.ceil((z * sd / half_width) ** 2 - 1e-9)


def false_discovery_chance(variants: int, alpha: float = 0.05) -> float:
    """
    Chance that at least one of `variants` independent tests of strategies with
    no edge at all looks significant at level `alpha`: 1 − (1 − alpha)^k.
    """
    if variants < 1 or not 0 < alpha < 1:
        raise ValueError("need at least one variant and 0 < alpha < 1")
    return 1 - (1 - alpha) ** variants


def degradation(in_sample: float, out_of_sample: float) -> float:
    """Share of the in-sample expectancy lost out of sample, as a fraction."""
    if in_sample <= 0:
        raise ValueError("the in-sample expectancy must be positive")
    return 1 - out_of_sample / in_sample
