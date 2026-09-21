"""
Trading analysis context — one object the trading pages share.

The counterpart to `investment.context.Context`, and for the same reason:
Streamlit reruns the whole script on every interaction, so five pages each
recomputing the same metrics would do the work five times per click. This
computes each quantity at most once per rerun and caches it on the instance.

It also keeps the pages away from the engine's internals. A page reads
`ctx.metrics` and `ctx.equity_curve`; it never assembles a `TradeJournal` or
decides which analytics function to call. That is what lets the engine change
without touching twelve render functions.

No Streamlit here — the page layer builds one of these and passes it down.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import analytics, psychology, risk
from .journal import TradeFilter, TradeJournal

# Named windows the pages offer. "ALL" is the whole journal.
PERIODS = ["7D", "30D", "90D", "6M", "1Y", "ALL"]
_PERIOD_DAYS = {"7D": 7, "30D": 30, "90D": 90, "6M": 182, "1Y": 365}


@dataclass
class TradingContext:
    """Everything the trading pages read, computed lazily and cached."""

    journal: TradeJournal
    lang: str = "en"
    period: str = "ALL"
    currency: str = "USD"
    account_id: str | None = None
    criteria: TradeFilter = field(default_factory=TradeFilter)
    starting_balance: float = 0.0
    _cache: dict = field(default_factory=dict, repr=False)

    # ── Scoped view ──────────────────────────────────────────────────────────

    @property
    def scoped(self) -> TradeJournal:
        """
        The journal after the account, period and filter have been applied.

        Everything else in this class reads from here, so a page never has to
        remember to apply the filter — forgetting once would show a metric that
        silently disagrees with the table beneath it.
        """
        return self._memo("scoped", self._compute_scoped)

    def _compute_scoped(self) -> TradeJournal:
        journal = self.journal
        if self.account_id:
            journal = TradeJournal([t for t in journal if t.account_id == self.account_id])
        if self.period != "ALL" and self.period in _PERIOD_DAYS:
            journal = journal.last_days(_PERIOD_DAYS[self.period])
        if self.criteria.is_active:
            journal = journal.filter(self.criteria)
        return journal

    @property
    def trades(self) -> list:
        return list(self.scoped)

    @property
    def closed(self) -> TradeJournal:
        return self._memo("closed", lambda: self.scoped.closed())

    @property
    def open_trades(self) -> TradeJournal:
        return self._memo("open", lambda: self.scoped.open())

    # ── Metrics ──────────────────────────────────────────────────────────────

    @property
    def metrics(self) -> dict:
        return self._memo("metrics", lambda: analytics.compute_metrics(self.trades))

    @property
    def equity_curve(self) -> list:
        return self._memo("equity", lambda: analytics.equity_curve(
            self.trades, self.starting_balance))

    @property
    def r_curve(self) -> list:
        return self._memo("r_curve", lambda: analytics.r_curve(self.trades))

    @property
    def daily_pnl(self) -> list:
        return self._memo("daily", lambda: analytics.daily_pnl(self.trades))

    @property
    def pnl_distribution(self) -> dict:
        return self._memo("dist", lambda: analytics.pnl_distribution(self.trades))

    @property
    def r_distribution(self) -> dict:
        return self._memo("r_dist", lambda: analytics.r_distribution(self.trades))

    @property
    def holding_time(self) -> dict:
        return self._memo("holding", lambda: analytics.holding_time_summary(self.trades))

    # ── Breakdowns ───────────────────────────────────────────────────────────

    def breakdown(self, dimension: str) -> list:
        return self._memo(f"bd:{dimension}",
                          lambda: self.scoped.breakdown(dimension, self.lang))

    @property
    def risk(self) -> dict:
        return self._memo("risk", lambda: risk.summary(self.trades))

    @property
    def psychology(self) -> dict:
        return self._memo("psych", lambda: psychology.summary(self.trades, self.lang))

    @property
    def findings(self) -> list:
        return self._memo("findings", lambda: psychology.findings(self.trades, self.lang))

    # ── Vocabulary present in the unfiltered journal ─────────────────────────
    # Drawn from the full journal, not the scoped one: a filter dropdown that
    # only offers what survives the current filter cannot be widened again.

    @property
    def all_symbols(self) -> list:
        return self.journal.symbols()

    @property
    def all_setups(self) -> list:
        return self.journal.setups()

    @property
    def all_mistakes(self) -> list:
        return self.journal.mistakes()

    @property
    def all_timeframes(self) -> list:
        return self.journal.timeframes()

    @property
    def all_accounts(self) -> list:
        return self.journal.accounts()

    @property
    def available_periods(self) -> list:
        """Only the windows the journal's history can actually cover."""
        span = self.journal.date_range()
        if not span:
            return ["ALL"]
        days = (span[1] - span[0]).days
        return [p for p in PERIODS
                if p == "ALL" or _PERIOD_DAYS[p] <= days + 7] or ["ALL"]

    # ── Guards ───────────────────────────────────────────────────────────────

    @property
    def has_trades(self) -> bool:
        return len(self.journal) > 0

    @property
    def has_closed(self) -> bool:
        return self.metrics.get("n", 0) > 0

    @property
    def is_filtered(self) -> bool:
        return len(self.scoped) < len(self.journal)

    # ── Internals ────────────────────────────────────────────────────────────

    def _memo(self, key, compute):
        if key not in self._cache:
            self._cache[key] = compute()
        return self._cache[key]

    def set_period(self, period: str) -> None:
        """Change the window and drop every derived value."""
        if period != self.period:
            self.period = period
            self._cache.clear()

    def set_account(self, account_id: str | None) -> None:
        if account_id != self.account_id:
            self.account_id = account_id
            self._cache.clear()

    def set_filter(self, criteria: TradeFilter) -> None:
        self.criteria = criteria
        self._cache.clear()


def build_context(trades, *, lang="en", period="ALL", currency="USD",
                  account_id=None, criteria=None,
                  starting_balance=0.0) -> TradingContext:
    """Build a context from a list of trades or an existing journal."""
    journal = trades if isinstance(trades, TradeJournal) else TradeJournal(list(trades or []))
    return TradingContext(
        journal=journal, lang=lang, period=period, currency=currency,
        account_id=account_id, criteria=criteria or TradeFilter(),
        starting_balance=starting_balance,
    )
