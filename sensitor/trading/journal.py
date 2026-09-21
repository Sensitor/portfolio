"""
The journal — a queryable collection of trades.

Filtering, sorting, searching and the derived views the pages need, over an
in-memory list of `Trade`. Persistence is a separate concern: a repository loads
trades, hands them here, and this module never knows where they came from. That
is what lets the same journal serve a Streamlit page, an API endpoint and a test
fixture.

`TradeJournal` is deliberately immutable in the filtering sense — every filter
returns a new journal rather than mutating in place, so a page can hold the full
set and derive views from it without the views interfering with each other.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from . import analytics, performance, psychology, risk
from .models import Direction, Session, Trade
from .setups import canonical_mistakes, canonical_setups


@dataclass
class TradeFilter:
    """
    Every dimension the brief asks to filter by, in one object.

    A dataclass rather than keyword arguments because the UI builds a filter
    across several widgets and passes it around; assembling it piecemeal into a
    function call would scatter that state.
    """

    symbols: list[str] | None = None
    directions: list[Direction] | None = None
    setups: list[str] | None = None
    sessions: list[Session] | None = None
    timeframes: list[str] | None = None
    weekdays: list[int] | None = None
    months: list[int] | None = None
    regimes: list[str] | None = None
    mistakes: list[str] | None = None
    accounts: list[str] | None = None

    date_from: date | None = None
    date_to: date | None = None

    min_r: float | None = None
    max_r: float | None = None
    min_risk: float | None = None
    max_risk: float | None = None
    min_duration_minutes: float | None = None
    max_duration_minutes: float | None = None

    only_wins: bool = False
    only_losses: bool = False
    only_with_stop: bool = False
    search: str | None = None

    def matches(self, trade: Trade) -> bool:
        """Whether one trade passes every active criterion."""
        if self.symbols and trade.symbol not in self.symbols:
            return False
        if self.directions and trade.direction not in self.directions:
            return False
        if self.sessions and trade.session not in self.sessions:
            return False
        if self.timeframes and trade.timeframe not in self.timeframes:
            return False
        if self.accounts and trade.account_id not in self.accounts:
            return False
        if self.regimes and trade.market_regime not in self.regimes:
            return False

        if self.setups:
            wanted = set(canonical_setups(self.setups))
            if not wanted & set(canonical_setups(trade.setups)):
                return False
        if self.mistakes:
            wanted = set(canonical_mistakes(self.mistakes))
            if not wanted & set(canonical_mistakes(trade.mistakes)):
                return False

        opened = trade.opened_at
        if self.weekdays and opened.weekday() not in self.weekdays:
            return False
        if self.months and opened.month not in self.months:
            return False
        if self.date_from and opened.date() < self.date_from:
            return False
        if self.date_to and opened.date() > self.date_to:
            return False

        r = trade.r_multiple
        if self.min_r is not None and (r is None or r < self.min_r):
            return False
        if self.max_r is not None and (r is None or r > self.max_r):
            return False

        risk_amount = trade.risk_amount
        if self.only_with_stop and risk_amount is None:
            return False
        if self.min_risk is not None and (risk_amount is None or risk_amount < self.min_risk):
            return False
        if self.max_risk is not None and (risk_amount is None or risk_amount > self.max_risk):
            return False

        duration = trade.duration_minutes
        if self.min_duration_minutes is not None and (
                duration is None or duration < self.min_duration_minutes):
            return False
        if self.max_duration_minutes is not None and (
                duration is None or duration > self.max_duration_minutes):
            return False

        if self.only_wins and trade.is_win is not True:
            return False
        if self.only_losses and trade.is_win is not False:
            return False

        if self.search:
            needle = self.search.lower()
            haystack = " ".join(str(part or "") for part in (
                trade.symbol, trade.notes, trade.entry_reason, trade.exit_reason,
                " ".join(trade.setups), " ".join(trade.mistakes),
            )).lower()
            if needle not in haystack:
                return False

        return True

    @property
    def is_active(self) -> bool:
        """Whether anything is actually being filtered."""
        default = TradeFilter()
        return any(getattr(self, f.name) != getattr(default, f.name)
                   for f in self.__dataclass_fields__.values())


@dataclass
class TradeJournal:
    """A collection of trades with the analytics attached."""

    trades: list[Trade] = field(default_factory=list)

    # ── Collection protocol ──────────────────────────────────────────────────

    def __len__(self) -> int:
        return len(self.trades)

    def __iter__(self):
        return iter(self.trades)

    def __bool__(self) -> bool:
        return bool(self.trades)

    # ── Views ────────────────────────────────────────────────────────────────

    def filter(self, criteria: TradeFilter) -> "TradeJournal":
        """A new journal with only the matching trades."""
        return TradeJournal([t for t in self.trades if criteria.matches(t)])

    def closed(self) -> "TradeJournal":
        return TradeJournal(analytics.closed(self.trades))

    def open(self) -> "TradeJournal":
        return TradeJournal([t for t in self.trades if not t.is_closed])

    def sorted_by(self, key: str = "closed_at", descending: bool = True) -> "TradeJournal":
        """
        Ordered copy. Trades missing the key sort last regardless of direction —
        an open trade has no close time and should not lead the list.
        """
        def sort_key(trade):
            value = getattr(trade, key, None)
            if hasattr(trade, key) is False:
                value = None
            return (value is None, value if value is not None else 0)

        try:
            ordered = sorted(self.trades, key=sort_key, reverse=descending)
        except TypeError:
            ordered = list(self.trades)
        return TradeJournal(ordered)

    def recent(self, n: int = 20) -> "TradeJournal":
        return TradeJournal(self.sorted_by("closed_at").trades[:n])

    def since(self, moment: datetime) -> "TradeJournal":
        return TradeJournal([t for t in self.trades if t.opened_at >= moment])

    def last_days(self, days: int) -> "TradeJournal":
        if not self.trades:
            return TradeJournal([])
        latest = max(t.opened_at for t in self.trades)
        return self.since(latest - timedelta(days=days))

    def get(self, trade_id: str) -> Trade | None:
        return next((t for t in self.trades if t.id == trade_id), None)

    # ── Vocabulary present in this journal ───────────────────────────────────

    def symbols(self) -> list[str]:
        return sorted({t.symbol for t in self.trades})

    def setups(self) -> list[str]:
        found: set[str] = set()
        for trade in self.trades:
            found.update(canonical_setups(trade.setups))
        return sorted(found)

    def mistakes(self) -> list[str]:
        found: set[str] = set()
        for trade in self.trades:
            found.update(canonical_mistakes(trade.mistakes))
        return sorted(found)

    def timeframes(self) -> list[str]:
        return sorted({t.timeframe for t in self.trades if t.timeframe})

    def accounts(self) -> list[str]:
        return sorted({t.account_id for t in self.trades if t.account_id})

    def date_range(self) -> tuple[date, date] | None:
        if not self.trades:
            return None
        opens = [t.opened_at.date() for t in self.trades]
        return min(opens), max(opens)

    # ── Analytics ────────────────────────────────────────────────────────────

    def metrics(self) -> dict:
        return analytics.compute_metrics(self.trades)

    def equity_curve(self, starting_balance: float = 0.0) -> list[dict]:
        return analytics.equity_curve(self.trades, starting_balance)

    def r_curve(self) -> list[dict]:
        return analytics.r_curve(self.trades)

    def daily_pnl(self) -> list[dict]:
        return analytics.daily_pnl(self.trades)

    def breakdown(self, dimension: str, lang: str = "en") -> list[dict]:
        """
        Any supported breakdown by name, so a page can drive it from a selectbox
        without a mapping of its own.
        """
        table = {
            "symbol": performance.by_symbol,
            "direction": performance.by_direction,
            "setup": performance.by_setup,
            "combination": performance.by_setup_combination,
            "session": performance.by_session,
            "weekday": performance.by_weekday,
            "month": performance.by_month,
            "hour": performance.by_hour,
            "timeframe": performance.by_timeframe,
            "regime": performance.by_regime,
            "risk_band": performance.by_risk_band,
        }
        builder = table.get(dimension)
        return builder(self.trades, lang) if builder else []

    def risk(self) -> dict:
        return risk.summary(self.trades)

    def psychology(self, lang: str = "en") -> dict:
        return psychology.summary(self.trades, lang)

    def validate(self) -> list[dict]:
        """Every trade with a data problem, and what the problem is."""
        from .models import validate as validate_trade
        out = []
        for trade in self.trades:
            problems = validate_trade(trade)
            if problems:
                out.append({"id": trade.id, "symbol": trade.symbol,
                            "problems": problems})
        return out

    # ── Mutation ─────────────────────────────────────────────────────────────

    def add(self, trade: Trade) -> "TradeJournal":
        """A new journal with the trade appended, replacing any with the same id."""
        remaining = [t for t in self.trades if t.id != trade.id]
        return TradeJournal(remaining + [trade])

    def merge(self, other) -> "TradeJournal":
        """
        Union by trade id, with the incoming trade winning.

        This is what a re-sync needs: pulling the same week from the broker twice
        must not double every trade, and a trade edited in the journal keeps its
        annotations only if the caller merges in the right order.
        """
        by_id = {t.id: t for t in self.trades}
        for trade in other:
            by_id[trade.id] = trade
        return TradeJournal(sorted(by_id.values(), key=lambda t: t.opened_at))

    def annotate(self, trade_id: str, **changes) -> "TradeJournal":
        """A new journal with one trade's journal fields updated."""
        out = []
        for trade in self.trades:
            out.append(trade.annotated(**changes) if trade.id == trade_id else trade)
        return TradeJournal(out)

    # ── Serialisation ────────────────────────────────────────────────────────

    def to_dicts(self) -> list[dict]:
        return [t.to_dict() for t in self.trades]

    @classmethod
    def from_dicts(cls, rows) -> "TradeJournal":
        return cls([Trade.from_dict(row) for row in rows])
