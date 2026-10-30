"""
The figures of path 11: the rules of a prop firm challenge, and the odds of passing one.

Rules
-----
Three rulesets are transcribed from the firms' own pages, each with its address
and the date it was read. They are facts about a product, quoted to be checked:
a firm changes its rules, and the lessons say to read the current page before
buying. Amounts are expressed as a share of the initial balance, which is how
FTMO states them and how Topstep's dollar amounts compare across sizes.

Thresholds
----------
* **Static**: the floor stays at the initial balance minus the maximum loss.
* **End-of-day trailing**: the floor is the highest end-of-day balance minus
  the maximum loss; it only rises. With `lock_at_start`, it stops rising once
  it reaches the initial balance (Topstep); without, it keeps following (FTMO
  1-Step).
* **Daily loss** is measured from the balance at the start of the day, as a
  share of the initial balance. At FTMO a breach fails the account; Topstep's
  optional daily limit only stops the session.

Odds
----
`pass_odds` is exact, not a random simulation: it walks every sequence of wins
and losses as a Markov chain, so a lesson, a test and the lab always show the
same number. Its assumptions are stated where it is used:

* each trade risks the same amount, a share of the **initial** balance;
* a loss costs `loss_r` times that amount, a win pays `reward_r` times it;
* trades are independent, with a constant win rate;
* the account is judged on closed trades: an open position's excursion, which
  can breach a limit intraday, is not modelled;
* the trader stops for the day once the target is reached, and the minimum
  number of days is met by minimal positions afterwards;
* the consistency rule is not part of the odds; `consistency_*` measure it.
"""

from __future__ import annotations

import datetime as _dt
import math
from dataclasses import dataclass, field
from fractions import Fraction
from functools import lru_cache

STATIC = "static"
EOD = "eod"


@dataclass(frozen=True)
class Ruleset:
    id: str
    firm: str
    product: str
    account: float                       # the example size the page uses, in dollars
    target_pct: float                    # profit target, % of the initial balance
    max_loss_pct: float                  # maximum loss, % of the initial balance
    trailing: str                        # STATIC or EOD
    lock_at_start: bool                  # an EOD floor stops at the initial balance
    daily_loss_pct: float | None         # % of the initial balance, from the day's opening balance
    daily_loss_fails: bool               # True: a breach fails; False: it ends the session only
    min_days: int
    consistency: str = ""                # "" | "profit" (best day vs total profit) | "target"
    consistency_pct: float | None = None
    breach_on_touch: bool = False        # reaching the floor exactly is already a breach
    sources: tuple[tuple[str, str, str], ...] = field(default_factory=tuple)   # (label, url, updated)
    consulted: _dt.date = _dt.date(2026, 10, 25)

    @property
    def target(self) -> float:
        return self.account * self.target_pct / 100

    @property
    def max_loss(self) -> float:
        return self.account * self.max_loss_pct / 100

    @property
    def daily_loss(self) -> float | None:
        return None if self.daily_loss_pct is None else self.account * self.daily_loss_pct / 100


_FTMO = ("FTMO, Trading Objectives", "https://ftmo.com/en/trading-objectives/", "2026-10-20")

RULESETS: dict[str, Ruleset] = {
    "ftmo-2-step": Ruleset(
        id="ftmo-2-step", firm="FTMO", product="FTMO Challenge 2-Step, première phase",
        account=100_000, target_pct=10, max_loss_pct=10, trailing=STATIC, lock_at_start=False,
        daily_loss_pct=5, daily_loss_fails=True, min_days=4,
        sources=(_FTMO,)),
    "ftmo-1-step": Ruleset(
        id="ftmo-1-step", firm="FTMO", product="FTMO Challenge 1-Step",
        account=100_000, target_pct=10, max_loss_pct=10, trailing=EOD, lock_at_start=False,
        daily_loss_pct=3, daily_loss_fails=True, min_days=0,
        consistency="profit", consistency_pct=50,
        sources=(_FTMO,)),
    "topstep-50k": Ruleset(
        id="topstep-50k", firm="Topstep", product="Trading Combine 50K",
        account=50_000, target_pct=6, max_loss_pct=4, trailing=EOD, lock_at_start=True,
        daily_loss_pct=2, daily_loss_fails=False, min_days=0,
        consistency="target", consistency_pct=55, breach_on_touch=True,
        sources=(("Topstep Help Center, What is the Maximum Loss Limit?",
                  "https://help.topstep.com/en/articles/8284204", "2026-09-18"),
                 ("Topstep Help Center, Consistency at Topstep",
                  "https://help.topstep.com/en/articles/8284208", "2026-09-17"),
                 ("Topstep Help Center, Daily Loss Limit in the Trading Combine and Express Funded Account",
                  "https://help.topstep.com/en/articles/10490293", "2026-06-30"))),
}


def ruleset(ruleset_id: str) -> Ruleset:
    try:
        return RULESETS[ruleset_id]
    except KeyError:
        raise ValueError(f"unknown ruleset: {ruleset_id}") from None


# =============================================================================
# Thresholds, on a path of days
# =============================================================================

def max_floor(rules: Ruleset, peak_eod: float) -> float:
    """The balance below which the account is lost, given the highest end-of-day balance."""
    initial = rules.account
    if rules.trailing == STATIC:
        return initial - rules.max_loss
    floor = max(peak_eod, initial) - rules.max_loss
    return min(floor, initial) if rules.lock_at_start else floor


def daily_floor(rules: Ruleset, day_open: float) -> float | None:
    """The balance below which today's losses breach the daily limit."""
    return None if rules.daily_loss is None else day_open - rules.daily_loss


def _below(value: float, floor: float, on_touch: bool) -> bool:
    return value <= floor + 1e-9 if on_touch else value < floor - 1e-9


@dataclass(frozen=True)
class Day:
    number: int
    open: float
    close: float
    low: float
    max_floor: float
    daily_floor: float | None
    status: str          # "running" | "passed" | "failed" | "stopped" (session ended by a non-failing limit)
    reason: str = ""     # "max_loss" | "daily_loss" | "target"


def walk(rules: Ruleset, days: list[float], lows: list[float] | None = None) -> list[Day]:
    """
    Apply the rules to a sequence of daily results (closed P&L, in dollars).

    `lows` optionally gives each day's lowest intraday P&L relative to the day's
    open, open positions included: Topstep and FTMO both judge a breach on it.
    The walk stops on the day the account passes or fails. Consistency is not
    applied here; `consistency_*` measure it on the same days.
    """
    balance, peak = rules.account, rules.account
    out: list[Day] = []
    for i, pnl in enumerate(days, start=1):
        floor = max_floor(rules, peak)
        dfloor = daily_floor(rules, balance)
        low = balance + min(pnl, lows[i - 1] if lows else pnl, 0.0)
        close = balance + pnl
        status, reason = "running", ""
        if _below(low, floor, rules.breach_on_touch):
            status, reason = "failed", "max_loss"
        elif dfloor is not None and _below(low, dfloor, rules.breach_on_touch or not rules.daily_loss_fails):
            if rules.daily_loss_fails:
                status, reason = "failed", "daily_loss"
            else:
                status, reason = "stopped", "daily_loss"
                close = max(close, dfloor)
        if status not in ("failed",) and close - rules.account >= rules.target - 1e-9 and i >= rules.min_days:
            status, reason = "passed", "target"
        out.append(Day(i, balance, close, low, floor, dfloor, status, reason))
        if status in ("passed", "failed"):
            break
        balance = close
        peak = max(peak, close)
    return out


# =============================================================================
# Consistency
# =============================================================================

def consistency_profit_ok(daily_profits: list[float], pct: float = 50) -> bool:
    """FTMO 1-Step: the best day may not exceed `pct` % of the total (closed) profit."""
    total = sum(daily_profits)
    best = max(daily_profits, default=0.0)
    return total > 0 and best <= total * pct / 100 + 1e-9


def consistency_profit_needed(best_day: float, pct: float = 50) -> float:
    """FTMO 1-Step: the total profit needed for `best_day` to respect the rule."""
    return best_day / (pct / 100)


def consistency_target(target: float, best_day: float, pct: float = 55) -> float:
    """Topstep: the profit target, raised to best day ÷ 55 % when the best day is too large."""
    return max(target, best_day / (pct / 100))


# =============================================================================
# Sizing
# =============================================================================

def losses_to(limit: float, risk: float) -> int:
    """Consecutive full losses of `risk` that reach `limit` (same unit)."""
    if limit <= 0 or risk <= 0:
        raise ValueError("limit and risk must be positive")
    return math.ceil(limit / risk - 1e-9)


def wins_to(target: float, risk: float, reward_r: float) -> int:
    """Consecutive wins of `reward_r` × `risk` that reach `target`."""
    if target <= 0 or risk <= 0 or reward_r <= 0:
        raise ValueError("target, risk and reward must be positive")
    return math.ceil(target / (risk * reward_r) - 1e-9)


def expected_trades_to_target(target_pct: float, risk_pct: float, win_rate: float,
                              reward_r: float, loss_r: float = 1.0) -> float:
    """Average number of trades to earn the target, from the expectancy alone. Infinite without an edge."""
    edge = win_rate * reward_r - (1 - win_rate) * loss_r
    return math.inf if edge <= 0 else target_pct / (risk_pct * edge)


def cost_per_pass(fee: float, pass_probability: float) -> float:
    """What a pass costs on average when each attempt costs `fee`: fee ÷ probability."""
    if fee < 0:
        raise ValueError("fee cannot be negative")
    return math.inf if pass_probability <= 0 else fee / pass_probability


# =============================================================================
# The odds of passing, exactly
# =============================================================================

@dataclass(frozen=True)
class Odds:
    passed: float
    failed_max: float
    failed_daily: float
    running: float               # neither passed nor failed after `max_trades`
    mean_trades_to_pass: float   # conditional on passing; nan if it never passes

    @property
    def failed(self) -> float:
        return self.failed_max + self.failed_daily


def pass_odds(rules: Ruleset, *, win_rate: float, reward_r: float, risk_pct: float,
              trades_per_day: int = 2, max_trades: int = 400, loss_r: float = 1.0) -> Odds:
    """Probability of passing `rules` before failing them, within `max_trades` trades."""
    if not 0 <= win_rate <= 1:
        raise ValueError("win rate must be between 0 and 1")
    if risk_pct <= 0 or reward_r <= 0 or loss_r <= 0 or trades_per_day < 1 or max_trades < 1:
        raise ValueError("risk, reward, loss, trades per day and horizon must be positive")
    return _odds(rules, round(win_rate, 6), round(reward_r, 4), round(risk_pct, 4), trades_per_day,
                 max_trades, round(loss_r, 4))


@lru_cache(maxsize=256)
def _odds(rules: Ruleset, p: float, reward_r: float, risk_pct: float, k: int, n: int,
          loss_r: float) -> Odds:
    # Integer units: a loss costs `lose` units and a win pays `win` units, both
    # exact multiples of a common fraction of the risked amount.
    ratio = Fraction(reward_r).limit_denominator(40) / Fraction(loss_r).limit_denominator(40)
    win, lose = ratio.numerator, ratio.denominator
    unit_pct = risk_pct * loss_r / lose                  # % of the initial balance per unit
    target = rules.target_pct / unit_pct
    max_loss = rules.max_loss_pct / unit_pct
    daily = None if rules.daily_loss_pct is None else rules.daily_loss_pct / unit_pct
    touch = rules.breach_on_touch

    def floor_of(peak: int) -> float:
        if rules.trailing == STATIC:
            return -max_loss
        f = max(peak, 0) - max_loss
        return min(f, 0.0) if rules.lock_at_start else f

    def below(x: float, f: float, on_touch: bool) -> bool:
        return x <= f + 1e-9 if on_touch else x < f - 1e-9

    # state: (pnl, peak at the last day end, pnl at the day's open, stopped today)
    states = {(0, 0, 0, False): 1.0}
    passed = failed_max = failed_daily = weighted = 0.0
    for t in range(n):
        new: dict = {}
        for (pnl, peak, open_, stopped), prob in states.items():
            if stopped:
                outcomes = ((pnl, prob),)
            else:
                outcomes = ((pnl + win, prob * p), (pnl - lose, prob * (1 - p)))
            for value, q in outcomes:
                if q == 0:
                    continue
                stop = stopped
                if not stopped:
                    if below(value, floor_of(peak), touch):
                        failed_max += q
                        continue
                    if daily is not None and below(value, open_ - daily,
                                                   touch or not rules.daily_loss_fails):
                        if rules.daily_loss_fails:
                            failed_daily += q
                            continue
                        stop = True
                    if value >= target - 1e-9:
                        passed += q
                        weighted += q * (t + 1)
                        continue
                key = (value, peak, open_, stop)
                new[key] = new.get(key, 0.0) + q
        if (t + 1) % k == 0:          # the day ends: the trailing floor and the day's open move
            rolled: dict = {}
            for (pnl, peak, _open, _stop), prob in new.items():
                # Only what the rules read is kept, so the chain stays small.
                key = (pnl, max(peak, pnl) if rules.trailing == EOD else 0,
                       pnl if daily is not None else 0, False)
                rolled[key] = rolled.get(key, 0.0) + prob
            new = rolled
        states = new
        if not states:
            break
    running = sum(states.values())
    mean = weighted / passed if passed > 0 else math.nan
    return Odds(passed, failed_max, failed_daily, running, mean)


# =============================================================================
# From a member's own journal
# =============================================================================

@dataclass(frozen=True)
class Profile:
    trades: int
    win_rate: float
    reward_r: float       # average winning trade, in R
    loss_r: float         # average losing trade, in R (positive)


def profile_from_r(results_r: list[float]) -> Profile | None:
    """Win rate and average win and loss in R, from closed trades' R multiples. None without both kinds."""
    wins = [r for r in results_r if r > 0]
    losses = [-r for r in results_r if r < 0]
    if not wins or not losses:
        return None
    n = len(wins) + len(losses)
    return Profile(n, len(wins) / n, sum(wins) / len(wins), sum(losses) / len(losses))


# =============================================================================
# Chart rows
# =============================================================================

# A constructed month: the same daily results judged by three kinds of floor.
EXAMPLE_DAYS = (600, 900, -400, 1200, 300, -900, 800, -1500, 700, 500, -600, 1100)


def floors_rows() -> list[dict]:
    """Balance and three floors on the constructed month, for a 50 000 $ account and a 2 000 $ maximum loss."""
    base = Ruleset(id="exemple", firm="", product="", account=50_000, target_pct=100, max_loss_pct=4,
                   trailing=STATIC, lock_at_start=False, daily_loss_pct=None, daily_loss_fails=True,
                   min_days=0)
    trail = Ruleset(**{**base.__dict__, "trailing": EOD})
    locked = Ruleset(**{**base.__dict__, "trailing": EOD, "lock_at_start": True})
    rows, balance, peak = [], 50_000.0, 50_000.0
    rows.append({"jour": 0, "solde": balance, "fixe": max_floor(base, peak),
                 "suiveur": max_floor(trail, peak), "verrouille": max_floor(locked, peak)})
    for day, pnl in enumerate(EXAMPLE_DAYS, start=1):
        balance += pnl
        peak = max(peak, balance)
        rows.append({"jour": day, "solde": balance, "fixe": max_floor(base, peak),
                     "suiveur": max_floor(trail, peak), "verrouille": max_floor(locked, peak)})
    return rows


ODDS_RISKS = (0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0)
ODDS_PROFILES = ((0.45, 1.5), (0.40, 1.5))


def odds_rows() -> list[dict]:
    """Probability of passing FTMO's 2-Step first phase, by risk per trade, for two profiles."""
    rules = RULESETS["ftmo-2-step"]
    rows = []
    for risk in ODDS_RISKS:
        row = {"risque": risk}
        for p, r in ODDS_PROFILES:
            row[f"p{int(p * 100)}"] = round(pass_odds(rules, win_rate=p, reward_r=r, risk_pct=risk).passed * 100, 1)
        rows.append(row)
    return rows
