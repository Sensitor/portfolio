"""
The internal trade model.

This is Sensitor's own shape for a trade, and the reason it exists is the brief's
hardest constraint: nothing above the connector layer may depend on a broker's
object format. MT5 hands back `TradeDeal` named tuples with `entry`, `type` and
`magic` fields; cTrader, IBKR and a CSV export all use different names, units and
sign conventions. Each gets a normaliser that produces a `Trade`, and the engine,
the analytics, the database and the UI only ever see `Trade`.

Two decisions worth stating, because they are where trading journals usually go
quietly wrong:

**A missing stop means R is undefined, not zero.** R multiple is P&L divided by
the amount risked, and the amount risked comes from the stop distance. A trade
entered without a stop has no denominator. Returning 0R would drag every average
toward zero and make a reckless book look disciplined; `None` keeps it out of the
statistics and lets the UI report the coverage.

**P&L is net by default.** `pnl` includes commission and swap. Gross P&L is
available separately, but the number the trader actually lived with is the net
one, so that is what the metrics use unless asked otherwise.

No Streamlit, no database, no broker SDK.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from enum import Enum


class Direction(str, Enum):
    """Trade side. Stored as a string so it survives JSON round-trips."""

    LONG = "long"
    SHORT = "short"

    @property
    def sign(self) -> int:
        return 1 if self is Direction.LONG else -1

    @classmethod
    def parse(cls, value) -> "Direction":
        """
        Accept the many spellings brokers use.

        MT5 encodes side as 0/1, some CSV exports as BUY/SELL, others as B/S.
        Anything unrecognised raises rather than defaulting to long — silently
        guessing the side would invert a trade's entire P&L.
        """
        if isinstance(value, Direction):
            return value
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return cls.LONG if int(value) == 0 else cls.SHORT
        text = str(value).strip().lower()
        if text in {"long", "buy", "b", "0", "bought"}:
            return cls.LONG
        if text in {"short", "sell", "s", "1", "sold"}:
            return cls.SHORT
        raise ValueError(f"unrecognised trade direction: {value!r}")


class Session(str, Enum):
    """Market session a trade was opened in."""

    ASIA = "asia"
    LONDON = "london"
    NEW_YORK = "new_york"
    OVERLAP = "overlap"          # London and New York both open
    OFF_HOURS = "off_hours"


# Session windows in UTC, as [start_hour, end_hour).
#
# These are fixed UTC windows, which is an approximation: London and New York
# shift by an hour relative to UTC twice a year for daylight saving, and the two
# do not switch on the same dates. Handling that properly needs each exchange's
# calendar. The windows below are the conventional ones used by retail platforms
# and are accurate for most of the year; anything derived from them is labelled
# as the session a trade *opened* in, never as an exchange-verified fact.
SESSION_WINDOWS = {
    Session.ASIA: (0, 8),
    Session.LONDON: (7, 16),
    Session.NEW_YORK: (12, 21),
}
OVERLAP_WINDOW = (12, 16)

SESSION_LABELS = {
    Session.ASIA: {"en": "Asia", "fr": "Asie"},
    Session.LONDON: {"en": "London", "fr": "Londres"},
    Session.NEW_YORK: {"en": "New York", "fr": "New York"},
    Session.OVERLAP: {"en": "London/NY overlap", "fr": "Chevauchement Londres/NY"},
    Session.OFF_HOURS: {"en": "Off hours", "fr": "Hors séance"},
}


def session_for(moment: datetime | None) -> Session:
    """
    Which session a timestamp falls in.

    The overlap wins when both London and New York are open, because "London/NY"
    is the distinction traders actually reason about — reporting such a trade as
    plain London would hide the busiest window of the day.
    """
    if moment is None:
        return Session.OFF_HOURS
    hour = moment.astimezone(timezone.utc).hour if moment.tzinfo else moment.hour

    if OVERLAP_WINDOW[0] <= hour < OVERLAP_WINDOW[1]:
        return Session.OVERLAP
    for session, (start, end) in SESSION_WINDOWS.items():
        if start <= hour < end:
            return session
    return Session.OFF_HOURS


def session_label(session: Session, lang: str = "en") -> str:
    return SESSION_LABELS.get(session, {}).get(lang, str(session))


# =============================================================================
# TRADE
# =============================================================================

@dataclass
class Trade:
    """
    One closed or open position, in Sensitor's own terms.

    Prices and money are in the account's currency. `size` is whatever unit the
    instrument trades in — lots for FX, contracts for futures, shares for equity —
    and is only ever used multiplicatively, so the unit does not need to be
    normalised across instruments as long as it is consistent per instrument.
    """

    # ── Identity ─────────────────────────────────────────────────────────────
    id: str
    symbol: str
    direction: Direction

    # ── Execution ────────────────────────────────────────────────────────────
    entry_price: float
    size: float
    opened_at: datetime
    exit_price: float | None = None
    closed_at: datetime | None = None

    stop_loss: float | None = None
    take_profit: float | None = None

    # ── Money ────────────────────────────────────────────────────────────────
    # `gross_pnl` is what the broker reported before costs. When a broker gives
    # only a net figure, the normaliser puts it here and leaves costs at zero.
    gross_pnl: float | None = None
    commission: float = 0.0
    swap: float = 0.0

    account_id: str | None = None
    account_currency: str = "USD"

    # ── Strategy context ─────────────────────────────────────────────────────
    setups: list[str] = field(default_factory=list)
    timeframe: str | None = None
    market_regime: str | None = None
    setup_quality: int | None = None        # 1-5
    confidence: int | None = None           # 1-5
    entry_reason: str | None = None
    exit_reason: str | None = None

    # ── Psychology ───────────────────────────────────────────────────────────
    emotion_before: str | None = None
    emotion_during: str | None = None
    emotion_after: str | None = None
    discipline: int | None = None           # 1-5
    mistakes: list[str] = field(default_factory=list)
    notes: str | None = None

    # ── Attachments ──────────────────────────────────────────────────────────
    image_pre: str | None = None
    image_post: str | None = None
    image_annotated: str | None = None

    # ── Provenance ───────────────────────────────────────────────────────────
    source: str = "manual"                  # manual · mt5 · csv · ...
    raw: dict = field(default_factory=dict, repr=False)

    # ── Derived ──────────────────────────────────────────────────────────────

    @property
    def is_closed(self) -> bool:
        return self.exit_price is not None and self.closed_at is not None

    @property
    def pnl(self) -> float | None:
        """
        Net profit and loss, after commission and swap.

        Falls back to computing from prices when the broker gave no figure, which
        is the case for manually entered trades.
        """
        gross = self.gross_pnl
        if gross is None:
            if not self.is_closed:
                return None
            gross = (self.exit_price - self.entry_price) * self.direction.sign * self.size
        return gross + self.commission + self.swap

    @property
    def costs(self) -> float:
        """Commission plus swap. Normally negative."""
        return self.commission + self.swap

    @property
    def risk_amount(self) -> float | None:
        """
        Money at risk at entry, from the stop distance.

        `None` when no stop was set — see the module docstring on why that must
        not become zero.
        """
        if self.stop_loss is None:
            return None
        distance = abs(self.entry_price - self.stop_loss)
        if distance <= 0:
            return None
        return distance * self.size

    @property
    def r_multiple(self) -> float | None:
        """Result expressed in units of the amount risked. `None` without a stop."""
        risk = self.risk_amount
        pnl = self.pnl
        if risk is None or pnl is None or risk <= 0:
            return None
        return pnl / risk

    @property
    def r_multiple_gross(self) -> float | None:
        """
        Result in R from price movement alone, before commission and swap.

        `r_multiple` is the net figure and is the right one for expectancy: costs
        are part of what the trader keeps. This one answers a different question —
        *did the stop hold?* — and costs must be excluded from it, because a trade
        stopped out at exactly -1R gross lands past -1R net purely through
        commission. Judging stop discipline on the net figure flags almost every
        loss as a breach, which is how a correct-looking metric ends up telling a
        trader their stops do not work when they do.
        """
        risk = self.risk_amount
        if risk is None or risk <= 0 or not self.is_closed:
            return None
        gross = (self.exit_price - self.entry_price) * self.direction.sign * self.size
        return gross / risk

    @property
    def planned_rr(self) -> float | None:
        """Reward-to-risk the trade was set up for, from the stop and target."""
        if self.stop_loss is None or self.take_profit is None:
            return None
        risk = abs(self.entry_price - self.stop_loss)
        reward = abs(self.take_profit - self.entry_price)
        return reward / risk if risk > 0 else None

    @property
    def duration(self) -> timedelta | None:
        if not self.is_closed:
            return None
        return self.closed_at - self.opened_at

    @property
    def duration_minutes(self) -> float | None:
        span = self.duration
        return span.total_seconds() / 60 if span else None

    @property
    def session(self) -> Session:
        return session_for(self.opened_at)

    @property
    def is_win(self) -> bool | None:
        pnl = self.pnl
        return None if pnl is None else pnl > 0

    @property
    def return_pct(self) -> float | None:
        """P&L as a share of the notional entered."""
        notional = abs(self.entry_price * self.size)
        pnl = self.pnl
        if not notional or pnl is None:
            return None
        return pnl / notional

    # ── Serialisation ────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """
        Flat dict for storage or transport.

        Derived values are included so a consumer that cannot import this module —
        the API's JSON response, a spreadsheet export — still sees R multiple and
        duration rather than having to recompute them.
        """
        return {
            "id": self.id,
            "symbol": self.symbol,
            "direction": self.direction.value,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "size": self.size,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "gross_pnl": self.gross_pnl,
            "commission": self.commission,
            "swap": self.swap,
            "pnl": self.pnl,
            "r_multiple": self.r_multiple,
            "r_multiple_gross": self.r_multiple_gross,
            "risk_amount": self.risk_amount,
            "planned_rr": self.planned_rr,
            "duration_minutes": self.duration_minutes,
            "session": self.session.value,
            "account_id": self.account_id,
            "account_currency": self.account_currency,
            "setups": list(self.setups),
            "timeframe": self.timeframe,
            "market_regime": self.market_regime,
            "setup_quality": self.setup_quality,
            "confidence": self.confidence,
            "entry_reason": self.entry_reason,
            "exit_reason": self.exit_reason,
            "emotion_before": self.emotion_before,
            "emotion_during": self.emotion_during,
            "emotion_after": self.emotion_after,
            "discipline": self.discipline,
            "mistakes": list(self.mistakes),
            "notes": self.notes,
            "image_pre": self.image_pre,
            "image_post": self.image_post,
            "image_annotated": self.image_annotated,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Trade":
        """Rebuild from `to_dict`, ignoring the derived keys."""
        def _dt(value):
            if not value:
                return None
            return value if isinstance(value, datetime) else datetime.fromisoformat(value)

        return cls(
            id=str(data["id"]),
            symbol=str(data["symbol"]),
            direction=Direction.parse(data["direction"]),
            entry_price=float(data["entry_price"]),
            size=float(data["size"]),
            opened_at=_dt(data["opened_at"]),
            exit_price=_opt_float(data.get("exit_price")),
            closed_at=_dt(data.get("closed_at")),
            stop_loss=_opt_float(data.get("stop_loss")),
            take_profit=_opt_float(data.get("take_profit")),
            gross_pnl=_opt_float(data.get("gross_pnl")),
            commission=float(data.get("commission") or 0.0),
            swap=float(data.get("swap") or 0.0),
            account_id=data.get("account_id"),
            account_currency=data.get("account_currency") or "USD",
            setups=list(data.get("setups") or []),
            timeframe=data.get("timeframe"),
            market_regime=data.get("market_regime"),
            setup_quality=_opt_int(data.get("setup_quality")),
            confidence=_opt_int(data.get("confidence")),
            entry_reason=data.get("entry_reason"),
            exit_reason=data.get("exit_reason"),
            emotion_before=data.get("emotion_before"),
            emotion_during=data.get("emotion_during"),
            emotion_after=data.get("emotion_after"),
            discipline=_opt_int(data.get("discipline")),
            mistakes=list(data.get("mistakes") or []),
            notes=data.get("notes"),
            image_pre=data.get("image_pre"),
            image_post=data.get("image_post"),
            image_annotated=data.get("image_annotated"),
            source=data.get("source") or "manual",
            raw=dict(data.get("raw") or {}),
        )

    def annotated(self, **changes) -> "Trade":
        """A copy with journal fields changed — trades are treated as immutable."""
        return replace(self, **changes)


def _opt_float(value):
    return None if value is None or value == "" else float(value)


def _opt_int(value):
    return None if value is None or value == "" else int(value)


# =============================================================================
# VALIDATION
# =============================================================================

def validate(trade: Trade) -> list[str]:
    """
    Problems that would make a trade's statistics wrong, as plain messages.

    Returns a list rather than raising: a journal should import a messy CSV and
    then show the reader what is questionable, not refuse the whole file over one
    bad row.
    """
    problems = []

    if trade.size <= 0:
        problems.append("size must be positive")
    if trade.entry_price <= 0:
        problems.append("entry price must be positive")
    if trade.is_closed and trade.closed_at < trade.opened_at:
        problems.append("closed before it opened")

    if trade.stop_loss is not None:
        beyond = (trade.stop_loss >= trade.entry_price if trade.direction is Direction.LONG
                  else trade.stop_loss <= trade.entry_price)
        if beyond:
            problems.append("stop loss is on the wrong side of the entry")

    if trade.take_profit is not None:
        beyond = (trade.take_profit <= trade.entry_price if trade.direction is Direction.LONG
                  else trade.take_profit >= trade.entry_price)
        if beyond:
            problems.append("take profit is on the wrong side of the entry")

    for name, value in (("setup quality", trade.setup_quality),
                        ("confidence", trade.confidence),
                        ("discipline", trade.discipline)):
        if value is not None and not 1 <= value <= 5:
            problems.append(f"{name} must be between 1 and 5")

    return problems
