"""
The figures of path 5: expectancy, sample uncertainty, drawdown and risk of ruin.

Everything is exact or a stated closed-form approximation; nothing is a random
simulation, so a lesson, a test and the lab always show the same number.

Conventions
-----------
* Results are in R: a loss costs 1R (the planned risk), a win pays `reward_r`.
* Position sizing is fixed-fractional: each trade risks `risk_pct` of the
  *current* equity, so equity after w wins and l losses is
  (1 + r·R)^w · (1 − r)^l, whatever the order.
* "Ruin" is reaching a loss threshold measured **from the starting equity**
  (for instance −30 %) at any point within N trades. Drawdowns measured from a
  peak are stricter and would give higher probabilities; the lessons say so.
* Trades are independent with a constant win rate. Real results cluster.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


def _check_rate(p: float) -> None:
    if not 0 <= p <= 1:
        raise ValueError("win rate must be between 0 and 1")


def expectancy_r(win_rate: float, reward_r: float, loss_r: float = 1.0) -> float:
    """Average result per trade, in R."""
    _check_rate(win_rate)
    return win_rate * reward_r - (1 - win_rate) * loss_r


def breakeven_win_rate(reward_r: float, loss_r: float = 1.0) -> float:
    """Win rate at which expectancy is zero."""
    if reward_r <= 0 or loss_r <= 0:
        raise ValueError("reward and loss must be positive")
    return loss_r / (reward_r + loss_r)


def profit_factor(win_rate: float, reward_r: float, loss_r: float = 1.0) -> float:
    """Gross gains over gross losses. Infinite with no losing trades."""
    _check_rate(win_rate)
    losses = (1 - win_rate) * loss_r
    return math.inf if losses == 0 else win_rate * reward_r / losses


@dataclass(frozen=True)
class Interval:
    low: float
    high: float

    @property
    def width(self) -> float:
        return self.high - self.low


def win_rate_interval(wins: int, trades: int, z: float = 1.96) -> Interval:
    """
    Wilson score interval for an observed win rate (95 % with z = 1.96).

    Wilson rather than the textbook ± z·√(p(1−p)/n): it stays inside [0, 1]
    and behaves on small samples, which is exactly where traders draw
    conclusions too early.
    """
    if trades < 1 or not 0 <= wins <= trades:
        raise ValueError("need 0 <= wins <= trades and trades >= 1")
    p = wins / trades
    denom = 1 + z * z / trades
    centre = (p + z * z / (2 * trades)) / denom
    half = z * math.sqrt(p * (1 - p) / trades + z * z / (4 * trades * trades)) / denom
    return Interval(max(0.0, centre - half), min(1.0, centre + half))


@dataclass(frozen=True)
class Drawdown:
    pct: float          # largest fall from a peak, in percent (positive number)
    peak: int           # index of the peak
    trough: int         # index of the trough


def max_drawdown(equity: list[float]) -> Drawdown:
    if not equity:
        raise ValueError("empty equity series")
    peak_i, best = 0, (0.0, 0, 0)
    for i, value in enumerate(equity):
        if value > equity[peak_i]:
            peak_i = i
        fall = 1 - value / equity[peak_i] if equity[peak_i] else 0.0
        if fall > best[0]:
            best = (fall, peak_i, i)
    return Drawdown(best[0] * 100, best[1], best[2])


def equity_path(start: float, results_r: list[float], risk_pct: float) -> list[float]:
    """Equity after each trade, fixed-fractional, results given in R."""
    rate = risk_pct / 100
    path = [start]
    for result in results_r:
        path.append(path[-1] * (1 + rate * result))
    return path


def ruin_probability(win_rate: float, reward_r: float, risk_pct: float, trades: int,
                     threshold_pct: float) -> float:
    """
    Probability of losing `threshold_pct` of the starting equity at least once
    within `trades` trades. Exact: dynamic programming over the number of wins
    among the paths that have not yet crossed the threshold.
    """
    _check_rate(win_rate)
    if trades < 1 or not 0 < risk_pct < 100 or not 0 < threshold_pct < 100 or reward_r <= 0:
        raise ValueError("invalid inputs")
    rate = risk_pct / 100
    up, down = math.log1p(rate * reward_r), math.log1p(-rate)
    floor = math.log1p(-threshold_pct / 100)
    alive = {0: 1.0}            # wins so far -> probability, among paths not ruined
    ruined = 0.0
    for t in range(1, trades + 1):
        nxt: dict[int, float] = {}
        for wins, prob in alive.items():
            nxt[wins + 1] = nxt.get(wins + 1, 0.0) + prob * win_rate
            losses = t - wins
            if wins * up + losses * down <= floor + 1e-12:
                ruined += prob * (1 - win_rate)
            else:
                nxt[wins] = nxt.get(wins, 0.0) + prob * (1 - win_rate)
        alive = nxt
    return min(1.0, ruined)


def final_equity_quantiles(win_rate: float, reward_r: float, risk_pct: float, trades: int,
                           start: float = 100.0, quantiles=(0.05, 0.5, 0.95)) -> dict[float, float]:
    """
    Equity after `trades` trades at the given quantiles of the binomial number
    of wins. Final equity does not depend on the order of results, so this is
    exact under the independence assumption.
    """
    _check_rate(win_rate)
    rate = risk_pct / 100
    cumulative, out = 0.0, {}
    pending = sorted(quantiles)
    for wins in range(trades + 1):
        cumulative += math.comb(trades, wins) * win_rate ** wins * (1 - win_rate) ** (trades - wins)
        while pending and cumulative >= pending[0] - 1e-12:
            out[pending.pop(0)] = start * (1 + rate * reward_r) ** wins * (1 - rate) ** (trades - wins)
    for q in pending:
        out[q] = start * (1 + rate * reward_r) ** trades
    return out


def losses_to_limit(limit_pct: float, risk_pct: float) -> int:
    """
    Consecutive full losses before a loss limit (from the day's or the
    account's starting balance) is reached or passed, risking a fixed
    percentage of that starting balance per trade.
    """
    if risk_pct <= 0 or limit_pct <= 0:
        raise ValueError("percentages must be positive")
    return math.ceil(limit_pct / risk_pct - 1e-9)
