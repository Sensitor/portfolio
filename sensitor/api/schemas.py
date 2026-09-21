"""
Request and response shapes.

Deliberately thin. These describe what the API *returns*; they do not compute
anything and they do not restate a metric's definition. The engine decides what
a profit factor is and when it is undefined — the schema's job is to admit that
`None` is a legitimate value for it and to say so in the OpenAPI document, so a
mobile client knows to render a dash rather than crash on a null.

Every optional-looking field here is optional for a reason that lives in the
engine:

* `profit_factor` is None when there are no losses — a division with no
  denominator, not an infinity.
* `avg_r`, `total_r` and `expectancy_r` are None when no trade had a stop, and
  `r_coverage` says what share of the book the R figures describe.
* `max_drawdown_pct` is None when the peak was at or below zero.

A client that treats those as zero will draw a confident wrong number, which is
the whole failure this project keeps designing against.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


# =============================================================================
# AUTH
# =============================================================================

class SignInRequest(BaseModel):
    email: str
    password: str | None = None
    api_key: str | None = Field(
        default=None,
        description="Single-user deployments only: the value of SENSITOR_API_TOKEN.",
    )


class SessionResponse(BaseModel):
    token: str
    email: str
    expires_days: int


class MeResponse(BaseModel):
    email: str
    tier: str
    display_name: str | None = None
    last_login_at: str | None = None


# =============================================================================
# META
# =============================================================================

class MetaResponse(BaseModel):
    product: str
    version: str
    schema_version: int
    auth_mode: str = Field(description="'single' or 'multi'.")
    issues_sessions: bool = Field(
        description="False when a single-user deployment has no API key configured, "
                    "in which case no session can be obtained.")


# =============================================================================
# TRADING
# =============================================================================

class TradeOut(BaseModel):
    """
    One trade, as the engine's own `Trade.to_dict()` produces it.

    Derived values travel with it — R multiple, risk, duration, session — so a
    client never recomputes them and never disagrees with the app about what a
    trade was worth.
    """

    id: str
    symbol: str
    direction: str
    entry_price: float
    exit_price: float | None = None
    size: float
    stop_loss: float | None = None
    take_profit: float | None = None
    opened_at: str | None = None
    closed_at: str | None = None
    gross_pnl: float | None = None
    commission: float = 0.0
    swap: float = 0.0
    pnl: float | None = None
    r_multiple: float | None = None
    r_multiple_gross: float | None = None
    risk_amount: float | None = None
    planned_rr: float | None = None
    duration_minutes: float | None = None
    session: str | None = None
    account_id: str | None = None
    account_currency: str = "USD"
    setups: list[str] = []
    mistakes: list[str] = []
    timeframe: str | None = None
    market_regime: str | None = None
    setup_quality: int | None = None
    confidence: int | None = None
    entry_reason: str | None = None
    exit_reason: str | None = None
    emotion_before: str | None = None
    emotion_during: str | None = None
    emotion_after: str | None = None
    discipline: int | None = None
    notes: str | None = None
    source: str = "manual"

    model_config = {"extra": "allow"}


class TradesPage(BaseModel):
    trades: list[TradeOut]
    total: int
    limit: int
    offset: int


class TradingMetrics(BaseModel):
    n: int
    n_wins: int | None = None
    n_losses: int | None = None
    n_scratch: int | None = None
    net_pnl: float | None = None
    gross_profit: float | None = None
    gross_loss: float | None = None
    total_costs: float | None = None
    win_rate: float | None = None
    profit_factor: float | None = Field(
        default=None, description="None when there are no losing trades.")
    expectancy: float | None = None
    avg_win: float | None = None
    avg_loss: float | None = None
    payoff_ratio: float | None = None
    best_trade: float | None = None
    worst_trade: float | None = None
    avg_r: float | None = Field(
        default=None, description="None when no trade had a stop.")
    total_r: float | None = None
    r_coverage: float | None = Field(
        default=None, description="Share of trades the R figures describe.")
    n_with_r: int | None = None
    max_drawdown: float | None = None
    max_drawdown_r: float | None = None
    max_win_streak: int | None = None
    max_loss_streak: int | None = None
    current_streak: int | None = None
    avg_holding_minutes: float | None = None
    median_holding_minutes: float | None = None
    first_trade: datetime | None = None
    last_trade: datetime | None = None
    symbols: int | None = None

    model_config = {"extra": "allow"}


class CurvePoint(BaseModel):
    at: datetime
    equity: float


class DayPnL(BaseModel):
    date: str
    pnl: float
    n: int


class BreakdownRow(BaseModel):
    key: str
    label: str
    n: int
    reliable: bool = Field(
        description="False below the sample threshold. A client should mark "
                    "these rather than rank them alongside the rest.")
    net_pnl: float | None = None
    win_rate: float | None = None
    expectancy: float | None = None
    profit_factor: float | None = None
    avg_r: float | None = None
    total_r: float | None = None


class Finding(BaseModel):
    """
    A psychology finding, phrased by the engine and passed through verbatim.

    The `en` and `fr` sentences are not assembled here and must not be
    paraphrased by a client: each one states that it is a correlation and
    carries its sample size, and the test suite asserts both. A client that
    shortens it into a verdict would undo that.
    """

    key: str
    level: str
    en: str
    fr: str
    n: int
    interpretation: str = "correlation"


# =============================================================================
# PORTFOLIOS
# =============================================================================

class PortfolioOut(BaseModel):
    id: int
    name: str
    holdings: dict[str, float]
    mode: str
    currency: str
    notes: str | None = None
    client_name: str | None = None
    created_at: str
    updated_at: str


class SnapshotOut(BaseModel):
    id: int
    portfolio_id: int
    taken_at: str
    total_value: float | None = None
    weights: dict[str, float] = {}
    metrics: dict = {}


class SavePortfolioRequest(BaseModel):
    name: str
    holdings: dict[str, float]
    mode: str = "simulation"
    currency: str = "$"
    notes: str | None = None
    client_name: str | None = None


class Deleted(BaseModel):
    deleted: bool
    detail: str | None = None
