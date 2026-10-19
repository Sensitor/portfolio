"""
The measurements taught in path 10: how closely a trader follows a written
plan, and what the departures from it cost.

Pure functions over a journal of trades in R, each marked as following the
plan or not. The lessons, the exercises, the case chart and the tests use
these definitions. The case journal is a constructed example and is labelled
as such wherever it appears.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class JournalTrade:
    result_r: float
    followed: bool              # every rule of the written plan was respected
    tag: str = ""               # the rule broken, when one was


def compliance_rate(trades: Sequence[JournalTrade]) -> float:
    """The share of trades that respected every rule."""
    if not trades:
        raise ValueError("an empty journal has no compliance rate")
    return sum(t.followed for t in trades) / len(trades)


def results(trades: Sequence[JournalTrade], *, followed: bool) -> list[float]:
    return [t.result_r for t in trades if t.followed is followed]


def mean(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("no value to average")
    return sum(values) / len(values)


def cost_of_departures(trades: Sequence[JournalTrade]) -> float:
    """What the trades that broke a rule added up to, in R. Negative: they cost money."""
    return sum(results(trades, followed=False))


def cumulative(values: Sequence[float]) -> list[float]:
    out, total = [], 0.0
    for v in values:
        total += v
        out.append(round(total, 10))
    return out


def risk_after_drawdown(risk_pct: float, drawdown: float, *, threshold: float = 0.10,
                        factor: float = 0.5) -> float:
    """
    A plan's de-risking rule: past `threshold` of drawdown, the risk per trade
    is multiplied by `factor` until the account recovers.
    """
    if not 0 <= drawdown < 1 or risk_pct <= 0:
        raise ValueError("drawdown between 0 and 1, positive risk")
    return risk_pct * factor if drawdown >= threshold else risk_pct


# The month of the case lesson: 24 trades in R, constructed for the lesson.
CASE_MONTH: tuple[JournalTrade, ...] = (
    JournalTrade(2.0, True), JournalTrade(-1.0, True), JournalTrade(-1.0, True),
    JournalTrade(-1.0, False, "revanche"), JournalTrade(1.8, True), JournalTrade(-1.0, True),
    JournalTrade(2.2, True), JournalTrade(-1.0, True), JournalTrade(-1.8, False, "stop déplacé"),
    JournalTrade(-1.0, True), JournalTrade(2.0, True), JournalTrade(-1.0, False, "hors zone"),
    JournalTrade(-1.0, True), JournalTrade(1.5, True), JournalTrade(0.6, False, "sortie anticipée"),
    JournalTrade(-1.0, True), JournalTrade(2.0, True), JournalTrade(-1.0, True),
    JournalTrade(-2.2, False, "taille doublée"), JournalTrade(-1.0, True), JournalTrade(2.5, True),
    JournalTrade(-1.0, True), JournalTrade(-1.0, False, "revanche"), JournalTrade(1.8, True),
)


def case_rows() -> list[dict]:
    """The case month, trade by trade: the curve as traded, and the curve of the plan alone."""
    traded = cumulative([t.result_r for t in CASE_MONTH])
    plan_only = cumulative([t.result_r if t.followed else 0.0 for t in CASE_MONTH])
    return [{"trade": i + 1, "realise": traded[i], "plan": plan_only[i], "ecart": not t.followed}
            for i, t in enumerate(CASE_MONTH)]
