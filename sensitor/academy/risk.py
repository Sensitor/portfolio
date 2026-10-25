"""
Risk-management calculations for the lab and the lessons.

What is computed, and what is not
---------------------------------
* **Risk amount** — `equity × risk % / 100`. Valid for any instrument, in the
  account currency.
* **Stop distance and reward-to-risk** — pure price arithmetic, valid for any
  instrument.
* **Position size** — only when an `InstrumentSpec` is supplied. Converting a
  price distance into money needs the contract size (units per lot) and, when
  the instrument is quoted in another currency than the account, the conversion
  rate. Those come from the broker's contract specification. This module ships
  **no** specification of its own: a size computed from an invented contract
  size would be a confident wrong number, which is worse than no number.
* **Losing streaks** — the equity path after consecutive losses, and the
  probability of meeting a streak in a series of trades. The probability assumes
  independent trades with a constant win rate; that assumption is stated next to
  every figure that uses it.

Spread, commission, swap and slippage are not included in the position size.
The page says so; a stop can also be filled worse than its level in a gap.

Inputs are validated and every rejection names the field, in French, so the
page can put the message next to the input that caused it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from decimal import ROUND_FLOOR, Decimal

LONG = "long"
SHORT = "short"


class RiskInputError(ValueError):
    """Invalid inputs. `errors` maps a field name to a French message."""

    def __init__(self, errors: dict[str, str]):
        self.errors = errors
        super().__init__("; ".join(f"{k} : {v}" for k, v in errors.items()))


@dataclass(frozen=True)
class InstrumentSpec:
    """
    What one lot is, as stated by the broker.

    `contract_size` — units of the instrument per 1.0 lot.
    `quote_to_account` — value of one unit of the quote currency in the account
    currency (1.0 when they are the same).
    `lot_step` / `min_lot` — the broker's volume increment and minimum, when known.
    `pip_size` — the price increment called a pip, when the instrument uses one.
    """

    contract_size: float
    quote_to_account: float = 1.0
    lot_step: float | None = None
    min_lot: float | None = None
    pip_size: float | None = None
    label: str = ""

    @property
    def value_per_point(self) -> float:
        """Account-currency value of a 1.0 price move on 1.0 lot."""
        return self.contract_size * self.quote_to_account


@dataclass(frozen=True)
class PositionSize:
    raw_lots: float
    lots: float
    units: float
    effective_risk: float
    value_per_point: float
    below_minimum: bool


@dataclass(frozen=True)
class RiskPlan:
    direction: str
    equity: float
    risk_pct: float
    risk_amount: float
    entry: float
    stop: float
    stop_distance: float
    stop_distance_pct: float
    target: float | None = None
    target_distance: float | None = None
    reward_to_risk: float | None = None
    planned_reward: float | None = None
    stop_distance_pips: float | None = None
    position: PositionSize | None = None
    notes: tuple[str, ...] = field(default_factory=tuple)


def risk_amount(equity: float, risk_pct: float) -> float:
    """Money at risk on one position: equity × risk % / 100."""
    errors = {}
    _positive(errors, "equity", equity, "Le capital doit être strictement positif.")
    if not _finite(risk_pct) or not 0 < risk_pct <= 100:
        errors["risk_pct"] = "Le risque par position doit être compris entre 0 % (exclu) et 100 %."
    if errors:
        raise RiskInputError(errors)
    return equity * risk_pct / 100


def plan(*, equity: float, risk_pct: float, entry: float, stop: float,
         direction: str, target: float | None = None,
         spec: InstrumentSpec | None = None) -> RiskPlan:
    errors: dict[str, str] = {}
    _positive(errors, "equity", equity, "Le capital doit être strictement positif.")
    if not _finite(risk_pct) or not 0 < risk_pct <= 100:
        errors["risk_pct"] = "Le risque par position doit être compris entre 0 % (exclu) et 100 %."
    _positive(errors, "entry", entry, "Le prix d'entrée doit être strictement positif.")
    _positive(errors, "stop", stop, "Le stop doit être strictement positif.")
    if direction not in (LONG, SHORT):
        errors["direction"] = "Le sens doit être « achat » ou « vente »."
    if target is not None:
        _positive(errors, "target", target, "L'objectif doit être strictement positif.")

    if not errors:
        if stop == entry:
            errors["stop"] = "Le stop ne peut pas être égal au prix d'entrée."
        elif direction == LONG and stop > entry:
            errors["stop"] = "À l'achat, le stop se place sous le prix d'entrée."
        elif direction == SHORT and stop < entry:
            errors["stop"] = "À la vente, le stop se place au-dessus du prix d'entrée."
        if target is not None:
            if direction == LONG and target <= entry:
                errors["target"] = "À l'achat, l'objectif se place au-dessus du prix d'entrée."
            elif direction == SHORT and target >= entry:
                errors["target"] = "À la vente, l'objectif se place sous le prix d'entrée."

    if spec is not None:
        _positive(errors, "contract_size", spec.contract_size,
                  "La taille de contrat doit être strictement positive.")
        _positive(errors, "quote_to_account", spec.quote_to_account,
                  "Le taux de conversion doit être strictement positif.")
        if spec.lot_step is not None:
            _positive(errors, "lot_step", spec.lot_step, "Le pas de volume doit être strictement positif.")
        if spec.min_lot is not None:
            _positive(errors, "min_lot", spec.min_lot, "Le volume minimum doit être strictement positif.")
        if spec.pip_size is not None:
            _positive(errors, "pip_size", spec.pip_size, "La taille du pip doit être strictement positive.")

    if errors:
        raise RiskInputError(errors)

    amount = equity * risk_pct / 100
    distance = abs(entry - stop)
    target_distance = abs(target - entry) if target is not None else None
    rr = target_distance / distance if target_distance is not None else None

    position = None
    pips = None
    if spec is not None:
        position = position_size(amount, distance, spec)
        if spec.pip_size:
            pips = distance / spec.pip_size

    notes = ["Taille de position hors spread, commission, swap et glissement."]
    if position is not None and position.below_minimum:
        notes.append("Le volume calculé est inférieur au minimum indiqué : la position "
                      "ne peut pas être ouverte sans dépasser le risque prévu.")
    return RiskPlan(direction=direction, equity=equity, risk_pct=risk_pct,
                    risk_amount=amount, entry=entry, stop=stop,
                    stop_distance=distance, stop_distance_pct=distance / entry * 100,
                    target=target, target_distance=target_distance,
                    reward_to_risk=rr, planned_reward=amount * rr if rr is not None else None,
                    stop_distance_pips=pips, position=position, notes=tuple(notes))


def position_size(amount: float, stop_distance: float, spec: InstrumentSpec) -> PositionSize:
    """
    Lots such that a stop-out loses `amount`, rounded **down** to the lot step.

    Rounding down is the only direction that keeps the realised risk at or under
    the plan; the effective risk after rounding is returned so the difference is
    visible.
    """
    per_lot = stop_distance * spec.value_per_point
    raw = amount / per_lot
    lots = raw
    if spec.lot_step:
        step = Decimal(str(spec.lot_step))
        # Prices are binary floats: 1.0745 − 1.0705 is 0.004000000000000115, so
        # 60 / 400 comes out as 0.14999999999999958 and a bare floor would give
        # 0.14 lot instead of 0.15. Rounding to nine places first removes that
        # noise without ever rounding a genuine 0.1499 up.
        steps = (Decimal(repr(round(raw, 9))) / step).to_integral_value(rounding=ROUND_FLOOR)
        lots = float(steps * step)
    below = bool(spec.min_lot and lots < spec.min_lot - 1e-12)
    return PositionSize(raw_lots=raw, lots=lots, units=lots * spec.contract_size,
                        effective_risk=lots * per_lot,
                        value_per_point=spec.value_per_point, below_minimum=below)


# =============================================================================
# LOSING STREAKS
# =============================================================================

@dataclass(frozen=True)
class StreakPoint:
    losses: int
    equity: float
    drawdown_pct: float
    recovery_pct: float          # gain needed from here to return to the start


def losing_streak(equity: float, risk_pct: float, losses: int, *,
                  compounding: bool = True) -> list[StreakPoint]:
    """
    Equity after 0…`losses` consecutive full-risk losses.

    `compounding=True` risks the percentage of *current* equity each time (the
    usual fixed-fractional rule); `False` risks the same amount every time.
    """
    risk_amount(equity, risk_pct)
    if not isinstance(losses, int) or losses < 0:
        raise RiskInputError({"losses": "Le nombre de pertes doit être un entier positif."})
    rate = risk_pct / 100
    points = []
    for k in range(losses + 1):
        value = equity * (1 - rate) ** k if compounding else max(0.0, equity - k * equity * rate)
        drawdown = 1 - value / equity
        points.append(StreakPoint(k, value, drawdown * 100, recovery_needed(drawdown) * 100))
    return points


def recovery_needed(drawdown: float) -> float:
    """Gain, as a fraction, needed to recover from a drawdown given as a fraction."""
    if not 0 <= drawdown <= 1:
        raise ValueError("drawdown doit être une fraction entre 0 et 1")
    if drawdown == 1:
        return math.inf
    return 1 / (1 - drawdown) - 1


def streak_probability(trades: int, streak: int, win_rate: float) -> float:
    """
    Probability of at least one run of `streak` or more consecutive losses in
    `trades` independent trades, each won with probability `win_rate`.

    Exact, by dynamic programming over the length of the current losing run.
    Independence and a constant win rate are assumptions, not facts about
    markets — real results cluster, which usually makes long streaks *more*
    likely than this figure.
    """
    errors = {}
    if not isinstance(trades, int) or trades < 1:
        errors["trades"] = "Le nombre de trades doit être un entier ≥ 1."
    if not isinstance(streak, int) or streak < 1:
        errors["streak"] = "La longueur de série doit être un entier ≥ 1."
    if not _finite(win_rate) or not 0 <= win_rate <= 1:
        errors["win_rate"] = "Le taux de réussite doit être compris entre 0 et 100 %."
    if errors:
        raise RiskInputError(errors)
    if streak > trades:
        return 0.0
    loss = 1 - win_rate
    runs = [0.0] * streak          # probability of being on a run of length i, not yet hit
    runs[0] = 1.0
    hit = 0.0
    for _ in range(trades):
        nxt = [0.0] * streak
        for length, p in enumerate(runs):
            if not p:
                continue
            nxt[0] += p * win_rate
            if length + 1 >= streak:
                hit += p * loss
            else:
                nxt[length + 1] += p * loss
        runs = nxt
    return min(1.0, hit)


def _finite(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _positive(errors: dict, name: str, value, message: str) -> None:
    if not _finite(value) or value <= 0:
        errors[name] = message
