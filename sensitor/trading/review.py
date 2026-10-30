"""
The automatic review: each trade judged against the member's own written plan.

A plan is a handful of rules a trader commits to before the session: a stop on
every trade, a maximum risk, a minimum reward-to-risk, the sessions and setups
they trade, how many trades a day, when to stop for the day. This module checks
every trade of a journal against those rules and reports, for a period, how
often the plan was followed and what the departures added up to in R.

Three conventions, the same as the rest of the trading engine:

**Unknown stays unknown.** A rule that cannot be checked, because the plan does
not state it or the trade lacks the figure it needs, is « non vérifiable », never
a pass. A trade without a target has no planned reward-to-risk; it is not
counted as respecting the minimum.

**The member's own rules, nothing else.** The review does not judge an entry,
a market reading or an outcome. It answers one question per rule: was the rule
written in the plan respected on this trade? Mistakes the member recorded on a
trade (a moved stop, a revenge trade) count as departures because the member
said so; nothing is inferred from price data.

**Every figure carries its sample.** A compliance rate over four trades is
shown as « 3 sur 4 », and the cost of departures is reported with the number of
trades behind it.

Each rule points to the Academy lesson that teaches it, so a breach leads to the
lesson that corrects it. Targets use the `spaces.parse_target` form.

No Streamlit, no database.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date

from .analytics import closed
from .models import Session, Trade
from .setups import MISTAKES, SETUPS, canonical_mistakes, canonical_setups, mistake_label

OK = "ok"
FAIL = "fail"
NA = "na"

# A risk within 5 % of the maximum is a rounding of the position size, not a breach.
RISK_TOLERANCE = 1.05

SESSION_CHOICES = (Session.ASIA.value, Session.LONDON.value, Session.NEW_YORK.value)
SESSION_NAMES = {"asia": "Asie", "london": "Londres", "new_york": "New York",
                 "overlap": "Chevauchement Londres et New York", "off_hours": "Hors séance"}
SESSION_PHRASES = {"asia": "pendant la séance asiatique", "london": "pendant la séance de Londres",
                   "new_york": "pendant la séance de New York",
                   "overlap": "pendant le chevauchement de Londres et New York",
                   "off_hours": "en dehors des séances"}

# Mistakes that, recorded by the member, mean the plan was not followed. Hesitation
# and an early exit are recorded too, but they are execution remarks, not rule breaks.
BREAKING_MISTAKES = ("fomo", "revenge", "overtrading", "moved_stop", "oversized", "no_stop",
                     "off_plan", "averaged_down")


@dataclass(frozen=True)
class Rule:
    id: str
    label: str
    lesson: str                 # target, « lesson:course/lesson »
    lesson_title: str


RULES: dict[str, Rule] = {r.id: r for r in (
    Rule("stop", "Un stop sur chaque trade", "lesson:premiers-pas/budget-de-risque",
         "Le budget de risque"),
    Rule("risk", "Le risque maximum par trade", "lesson:processus-de-trading/limites-de-risque",
         "Les limites qui protègent le compte"),
    Rule("rr", "Le rapport gain sur risque minimum", "lesson:risque-dans-la-duree/esperance",
         "L'espérance : ce que rapporte un trade en moyenne"),
    Rule("session", "Les séances du plan", "lesson:processus-de-trading/preparer-seance",
         "Préparer sa séance"),
    Rule("setup", "Un setup du plan", "lesson:processus-de-trading/plan-de-trading",
         "Écrire son plan de trading"),
    Rule("daily_count", "Le nombre de trades par jour", "lesson:decider-sous-incertitude/suractivite",
         "La suractivité"),
    Rule("daily_loss", "La limite de perte du jour", "lesson:risque-dans-la-duree/limites-de-perte",
         "Limites journalières et règles de prop firm"),
    Rule("pause", "La pause après des pertes d'affilée", "lesson:decider-sous-incertitude/revanche",
         "Le trade pour se refaire"),
    Rule("declared", "Les écarts notés sur le trade", "lesson:processus-de-trading/executer-seance",
         "Exécuter et gérer ses trades"),
)}

# The lesson for each recorded mistake, more precise than the generic « declared » one.
MISTAKE_LESSONS = {
    "fomo": ("lesson:decider-sous-incertitude/fomo", "La peur de rater le mouvement"),
    "revenge": ("lesson:decider-sous-incertitude/revanche", "Le trade pour se refaire"),
    "overtrading": ("lesson:decider-sous-incertitude/suractivite", "La suractivité"),
    "moved_stop": ("lesson:processus-de-trading/executer-seance", "Exécuter et gérer ses trades"),
    "oversized": ("lesson:processus-de-trading/limites-de-risque", "Les limites qui protègent le compte"),
    "no_stop": ("lesson:premiers-pas/budget-de-risque", "Le budget de risque"),
    "off_plan": ("lesson:processus-de-trading/plan-de-trading", "Écrire son plan de trading"),
    "averaged_down": ("lesson:processus-de-trading/limites-de-risque",
                      "Les limites qui protègent le compte"),
}


# =============================================================================
# THE PLAN
# =============================================================================

@dataclass(frozen=True)
class TradingPlan:
    """
    The rules a member writes down. Every field is optional: a rule left empty
    is simply not checked, and the review says so.
    """

    capital: float | None = None            # account size, in the account currency
    currency: str = "EUR"
    risk_pct: float | None = 1.0            # maximum risk per trade, % of capital
    require_stop: bool = True
    min_rr: float | None = 1.5              # minimum planned reward-to-risk
    sessions: tuple[str, ...] = ()          # empty: any session
    setups: tuple[str, ...] = ()            # empty: any declared setup
    require_setup: bool = True
    max_trades_per_day: int | None = 3
    daily_loss_r: float | None = 2.0        # stop for the day once this many R are lost
    pause_after_losses: int | None = 2      # stop for the day after this many losses in a row

    @property
    def max_risk(self) -> float | None:
        if self.capital and self.risk_pct:
            return self.capital * self.risk_pct / 100
        return None

    def to_dict(self) -> dict:
        data = asdict(self)
        data["sessions"] = list(self.sessions)
        data["setups"] = list(self.setups)
        return data

    @classmethod
    def from_dict(cls, data: dict | None) -> "TradingPlan":
        return clean_plan(data or {})


DEFAULT_PLAN = TradingPlan()


def _positive(value, name: str, *, integer: bool = False, upper: float | None = None):
    if value in (None, "", 0):
        return None
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a number")
    try:
        number = int(value) if integer else float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a number") from None
    if integer and float(value) != number:
        raise ValueError(f"{name} must be a whole number")
    if number <= 0:
        raise ValueError(f"{name} must be positive")
    if upper is not None and number > upper:
        raise ValueError(f"{name} is too large")
    return number


def clean_plan(data: dict) -> TradingPlan:
    """Check a plan before it is stored or used. Raises ValueError with the field at fault."""
    sessions = tuple(dict.fromkeys(str(s) for s in data.get("sessions") or ()))
    if not set(sessions) <= set(SESSION_CHOICES):
        raise ValueError("unknown session")
    setups = tuple(dict.fromkeys(canonical_setups(data.get("setups") or ())))
    currency = str(data.get("currency") or "EUR").upper()
    if currency not in ("EUR", "USD", "GBP", "CHF"):
        raise ValueError("unknown currency")
    return TradingPlan(
        capital=_positive(data.get("capital"), "capital", upper=1e12),
        currency=currency,
        risk_pct=_positive(data.get("risk_pct"), "risk_pct", upper=100),
        require_stop=bool(data.get("require_stop", True)),
        min_rr=_positive(data.get("min_rr"), "min_rr", upper=100),
        sessions=sessions,
        setups=setups,
        require_setup=bool(data.get("require_setup", True)),
        max_trades_per_day=_positive(data.get("max_trades_per_day"), "max_trades_per_day",
                                     integer=True, upper=1000),
        daily_loss_r=_positive(data.get("daily_loss_r"), "daily_loss_r", upper=1000),
        pause_after_losses=_positive(data.get("pause_after_losses"), "pause_after_losses",
                                     integer=True, upper=1000),
    )


def plan_sentences(plan: TradingPlan) -> list[str]:
    """The plan read back as short sentences, in the order the review checks it."""
    out = []
    if plan.require_stop:
        out.append("Chaque trade a un stop dès l'entrée.")
    if plan.risk_pct:
        money = (f", soit {_amount(plan.max_risk)} {_symbol(plan.currency)}"
                 if plan.max_risk else "")
        out.append(f"Je risque au plus {_num(plan.risk_pct)} % du capital par trade{money}.")
    if plan.min_rr:
        out.append(f"Je vise au moins {_num(plan.min_rr)} fois le risque.")
    if plan.sessions:
        out.append("Je trade seulement : " + ", ".join(SESSION_NAMES[s] for s in plan.sessions) + ".")
    if plan.setups:
        out.append("Mes setups : " + ", ".join(SETUPS[s][1] if s in SETUPS else s
                                              for s in plan.setups) + ".")
    elif plan.require_setup:
        out.append("Chaque trade porte le setup qui l'a déclenché.")
    if plan.max_trades_per_day:
        out.append(f"Au plus {plan.max_trades_per_day} trade{'s' if plan.max_trades_per_day > 1 else ''} par jour.")
    if plan.daily_loss_r:
        out.append(f"J'arrête la journée après {_num(plan.daily_loss_r)} R de perte.")
    if plan.pause_after_losses:
        out.append(f"J'arrête la journée après {plan.pause_after_losses} pertes d'affilée.")
    return out


# =============================================================================
# ONE TRADE
# =============================================================================

@dataclass(frozen=True)
class Check:
    rule: str
    status: str                 # ok · fail · na
    detail: str
    lesson: str = ""
    lesson_title: str = ""

    @property
    def label(self) -> str:
        return RULES[self.rule].label


@dataclass(frozen=True)
class TradeReview:
    trade_id: str
    checks: tuple[Check, ...]

    @property
    def evaluated(self) -> tuple[Check, ...]:
        return tuple(c for c in self.checks if c.status != NA)

    @property
    def failed(self) -> tuple[Check, ...]:
        return tuple(c for c in self.checks if c.status == FAIL)

    @property
    def passed(self) -> int:
        return sum(1 for c in self.checks if c.status == OK)

    @property
    def score(self) -> float | None:
        """Share of the checkable rules that were respected; None when nothing was checkable."""
        n = len(self.evaluated)
        return self.passed / n if n else None

    @property
    def followed(self) -> bool | None:
        """Every checkable rule respected. None when no rule could be checked."""
        if not self.evaluated:
            return None
        return not self.failed

    def to_dict(self) -> dict:
        return {"trade_id": self.trade_id, "score": self.score, "followed": self.followed,
                "checks": [asdict(c) for c in self.checks]}

    @classmethod
    def from_dict(cls, data: dict) -> "TradeReview":
        return cls(trade_id=str(data.get("trade_id", "")),
                   checks=tuple(Check(**c) for c in data.get("checks", ()) if c.get("rule") in RULES))


def _check(rule: str, status: str, detail: str) -> Check:
    r = RULES[rule]
    return Check(rule, status, detail, r.lesson if status == FAIL else "",
                 r.lesson_title if status == FAIL else "")


def _day(trade: Trade) -> date:
    return trade.opened_at.date()


def _loss(trade: Trade) -> bool:
    r = trade.r_multiple
    if r is not None:
        return r < 0
    return trade.pnl is not None and trade.pnl < 0


def review_trade(trade: Trade, plan: TradingPlan, day_trades: list[Trade] | None = None) -> TradeReview:
    """
    Check one trade against the plan.

    `day_trades` are the other trades opened the same day, which the daily rules
    need; without them those rules are not checkable.
    """
    checks = []

    # Stop.
    if plan.require_stop:
        if trade.stop_loss is None or trade.risk_amount is None:
            checks.append(_check("stop", FAIL, "Aucun stop renseigné à l'entrée."))
        else:
            checks.append(_check("stop", OK, "Stop renseigné à l'entrée."))
    else:
        checks.append(_check("stop", NA, "Le plan ne l'exige pas."))

    # Risk.
    limit = plan.max_risk
    risk = trade.risk_amount
    symbol = _symbol(plan.currency)
    if limit is None:
        checks.append(_check("risk", NA, "Capital ou risque maximum non renseigné dans le plan."))
    elif risk is None:
        checks.append(_check("risk", NA, "Sans stop, le risque engagé est inconnu."))
    elif risk <= limit * RISK_TOLERANCE:
        checks.append(_check("risk", OK, f"{_amount(risk)} {symbol} risqués, pour un maximum de "
                                         f"{_amount(limit)} {symbol}."))
    else:
        checks.append(_check("risk", FAIL, f"{_amount(risk)} {symbol} risqués, soit "
                                           f"{_num(risk / limit)} fois le maximum de {_amount(limit)} {symbol}."))

    # Reward to risk.
    rr = trade.planned_rr
    if not plan.min_rr:
        checks.append(_check("rr", NA, "Le plan ne fixe pas de minimum."))
    elif rr is None:
        checks.append(_check("rr", NA, "Objectif ou stop non renseigné : rapport inconnu."))
    elif rr + 1e-9 >= plan.min_rr:
        checks.append(_check("rr", OK, f"{_num(rr)} prévu, pour un minimum de {_num(plan.min_rr)}."))
    else:
        checks.append(_check("rr", FAIL, f"{_num(rr)} prévu, sous le minimum de {_num(plan.min_rr)}."))

    # Session.
    session = trade.session
    if not plan.sessions:
        checks.append(_check("session", NA, "Le plan ne restreint pas les séances."))
    else:
        allowed = set(plan.sessions)
        inside = (session.value in allowed or
                  (session is Session.OVERLAP and bool(allowed & {"london", "new_york"})))
        phrase = SESSION_PHRASES[session.value]
        checks.append(_check("session", OK if inside else FAIL,
                             f"Ouvert {phrase}." if inside else f"Ouvert {phrase}, hors du plan."))

    # Setup. A trade imported from the broker carries no setup until the trader
    # annotates it: that is a blank to fill, not a trade taken without a setup.
    tags = canonical_setups(trade.setups)
    if not tags and trade.source == "mt5" and (plan.setups or plan.require_setup):
        checks.append(_check("setup", NA, "Importé sans setup : annotez ce trade pour le vérifier."))
    elif plan.setups:
        hit = [s for s in tags if s in plan.setups]
        if hit:
            checks.append(_check("setup", OK, f"Setup du plan : {_setup_names(hit)}."))
        elif tags:
            checks.append(_check("setup", FAIL, f"{_setup_names(tags)} : absent du plan."))
        else:
            checks.append(_check("setup", FAIL, "Aucun setup renseigné."))
    elif plan.require_setup:
        checks.append(_check("setup", OK if tags else FAIL,
                             f"Setup renseigné : {_setup_names(tags)}." if tags else "Aucun setup renseigné."))
    else:
        checks.append(_check("setup", NA, "Le plan ne l'exige pas."))

    # Daily rules: the trades of the same day, in the order they were opened.
    same_day = None
    if day_trades is not None:
        same_day = [t for t in day_trades if _day(t) == _day(trade) and t.id != trade.id] + [trade]
        same_day.sort(key=lambda t: (t.opened_at, t.id))
    if not plan.max_trades_per_day:
        checks.append(_check("daily_count", NA, "Le plan ne fixe pas de maximum."))
    elif same_day is None:
        checks.append(_check("daily_count", NA, "Les autres trades du jour ne sont pas connus."))
    else:
        rank = next(i for i, t in enumerate(same_day, start=1) if t.id == trade.id)
        checks.append(_check("daily_count", OK if rank <= plan.max_trades_per_day else FAIL,
                             f"Trade n° {rank} de la journée, pour un maximum de {plan.max_trades_per_day}."))

    earlier = [] if same_day is None else [
        t for t in same_day if t.id != trade.id and t.is_closed and t.closed_at <= trade.opened_at]
    earlier.sort(key=lambda t: (t.closed_at, t.id))
    if not plan.daily_loss_r:
        checks.append(_check("daily_loss", NA, "Le plan ne fixe pas de limite."))
    elif same_day is None:
        checks.append(_check("daily_loss", NA, "Les autres trades du jour ne sont pas connus."))
    else:
        lost = sum(t.r_multiple for t in earlier if t.r_multiple is not None)
        if lost <= -plan.daily_loss_r + 1e-9:
            checks.append(_check("daily_loss", FAIL, f"Ouvert après {_num(-lost)} R de perte dans la "
                                                     f"journée, au-delà de la limite de {_num(plan.daily_loss_r)} R."))
        elif not earlier:
            checks.append(_check("daily_loss", OK, "Aucun trade clôturé plus tôt dans la journée."))
        else:
            checks.append(_check("daily_loss", OK, f"Résultat du jour avant ce trade : {_signed(lost)} R."))

    if not plan.pause_after_losses:
        checks.append(_check("pause", NA, "Le plan ne fixe pas de pause."))
    elif same_day is None:
        checks.append(_check("pause", NA, "Les autres trades du jour ne sont pas connus."))
    else:
        run = 0
        for t in reversed(earlier):
            if not _loss(t):
                break
            run += 1
        if run >= plan.pause_after_losses:
            checks.append(_check("pause", FAIL, f"Ouvert juste après {run} pertes d'affilée, sans la pause "
                                                f"prévue après {plan.pause_after_losses}."))
        else:
            checks.append(_check("pause", OK, "Pas de série de pertes juste avant ce trade."
                                              if not run else f"{run} perte juste avant, sous le seuil de pause."))

    # What the member recorded about themselves.
    breaking = [m for m in canonical_mistakes(trade.mistakes) if m in BREAKING_MISTAKES]
    if breaking:
        first = breaking[0]
        lesson, title = MISTAKE_LESSONS.get(first, (RULES["declared"].lesson, RULES["declared"].lesson_title))
        names = ", ".join(mistake_label(m, "fr").lower() for m in breaking)
        checks.append(Check("declared", FAIL, f"Écart noté sur ce trade : {names}.", lesson, title))
    else:
        checks.append(_check("declared", OK, "Aucun écart noté sur ce trade."))

    return TradeReview(trade.id, tuple(checks))


def review_journal(trades, plan: TradingPlan) -> dict[str, TradeReview]:
    """Every closed trade, reviewed with the trades of its day. Keyed by trade id."""
    done = closed(trades)
    by_day: dict[date, list[Trade]] = {}
    for t in done:
        by_day.setdefault(_day(t), []).append(t)
    return {t.id: review_trade(t, plan, by_day[_day(t)]) for t in done}


# =============================================================================
# A PERIOD
# =============================================================================

@dataclass(frozen=True)
class RuleTally:
    rule: str
    label: str
    breaches: int
    checked: int
    cost_r: float               # R of the trades that broke this rule
    lesson: str
    lesson_title: str


@dataclass(frozen=True)
class PlanReport:
    n: int                      # closed trades in the period
    n_checked: int              # trades with at least one checkable rule
    n_followed: int             # trades that respected every checkable rule
    followed_r: float           # sum of R of those, over the trades with an R
    departed_r: float           # sum of R of the trades that broke a rule
    n_followed_r: int
    n_departed_r: int
    tallies: tuple[RuleTally, ...] = field(default=())

    @property
    def compliance(self) -> float | None:
        return self.n_followed / self.n_checked if self.n_checked else None

    @property
    def priority(self) -> RuleTally | None:
        """The rule whose breaches cost the most R; by breach count when none cost anything."""
        broken = [t for t in self.tallies if t.breaches]
        if not broken:
            return None
        return min(broken, key=lambda t: (t.cost_r, -t.breaches))


def report(trades, reviews: dict[str, TradeReview]) -> PlanReport:
    done = [t for t in closed(trades) if t.id in reviews]
    checked = [t for t in done if reviews[t.id].followed is not None]
    followed = [t for t in checked if reviews[t.id].followed]
    departed = [t for t in checked if not reviews[t.id].followed]
    fr = [t.r_multiple for t in followed if t.r_multiple is not None]
    dr = [t.r_multiple for t in departed if t.r_multiple is not None]

    tallies = []
    for rule in RULES.values():
        relevant = [(t, c) for t in done for c in reviews[t.id].checks if c.rule == rule.id and c.status != NA]
        if not relevant:
            continue
        broke = [(t, c) for t, c in relevant if c.status == FAIL]
        cost = sum(t.r_multiple for t, _ in broke if t.r_multiple is not None)
        # The lesson most often pointed to by the breaches: for recorded mistakes it
        # is the lesson of the mistake that comes back most, not a generic one.
        lessons = [(c.lesson, c.lesson_title) for _, c in broke if c.lesson]
        lesson, title = (max(set(lessons), key=lessons.count) if lessons
                         else (rule.lesson, rule.lesson_title))
        tallies.append(RuleTally(rule.id, rule.label, len(broke), len(relevant), cost, lesson, title))
    tallies.sort(key=lambda t: (-t.breaches, t.cost_r))
    return PlanReport(n=len(done), n_checked=len(checked), n_followed=len(followed),
                      followed_r=sum(fr), departed_r=sum(dr), n_followed_r=len(fr),
                      n_departed_r=len(dr), tallies=tuple(tallies))


def plan_curves(trades, reviews: dict[str, TradeReview]) -> list[dict]:
    """
    Two cumulative curves in R, trade by trade, in closing order: the journal as
    traded, and the journal with every trade that broke the plan set to zero.
    Trades without an R (no stop) are left out of both, and counted by the caller.
    """
    rows, traded, plan_only = [], 0.0, 0.0
    ordered = sorted((t for t in closed(trades) if t.id in reviews and t.r_multiple is not None),
                     key=lambda t: (t.closed_at, t.id))
    for i, t in enumerate(ordered, start=1):
        departed = reviews[t.id].followed is False
        traded += t.r_multiple
        plan_only += 0.0 if departed else t.r_multiple
        rows.append({"n": i, "trade_id": t.id, "closed_at": t.closed_at, "r": t.r_multiple,
                     "realise": round(traded, 10), "plan": round(plan_only, 10), "ecart": departed})
    return rows


def daily_r(trades) -> dict[date, tuple[float, int]]:
    """R summed per closing day, with the number of trades; trades without an R are left out."""
    out: dict[date, tuple[float, int]] = {}
    for t in closed(trades):
        if t.r_multiple is None:
            continue
        day = t.closed_at.date()
        total, n = out.get(day, (0.0, 0))
        out[day] = (total + t.r_multiple, n + 1)
    return out


# =============================================================================
# FORMATTING (French, no dependency on the UI)
# =============================================================================

def _num(value: float, decimals: int = 2) -> str:
    text = f"{value:,.{decimals}f}".rstrip("0").rstrip(".") if decimals else f"{value:,.0f}"
    return text.replace(",", " ").replace(".", ",")


def _signed(value: float) -> str:
    return ("+" if value > 0 else "−" if value < 0 else "") + _num(abs(value))


def _amount(value: float) -> str:
    return f"{value:,.2f}".replace(",", " ").replace(".", ",").removesuffix(",00")


def _symbol(currency: str) -> str:
    return {"EUR": "€", "USD": "$", "GBP": "£"}.get(currency, currency)


def _setup_names(keys) -> str:
    return ", ".join(SETUPS[k][1] if k in SETUPS else k for k in keys)


__all__ = ["TradingPlan", "DEFAULT_PLAN", "clean_plan", "plan_sentences", "Check", "TradeReview",
           "review_trade", "review_journal", "RuleTally", "PlanReport", "report", "plan_curves",
           "daily_r", "RULES", "MISTAKES", "OK", "FAIL", "NA"]
