"""
MetaTrader 5 connector.

The only module in the package that knows what MT5 is. Everything above it sees
`trading.models.Trade` and nothing else, which is what lets cTrader, a CSV export
or a REST broker arrive later without touching a single page or metric.

Three things make this harder than "download the history":

**MT5 reports deals, not trades.** A round turn is at least two deals — one
`DEAL_ENTRY_IN`, one `DEAL_ENTRY_OUT` — sharing a `position_id`. A scaled-in,
partially-closed position can be a dozen. Folding them back into one position,
with volume-weighted entry and exit prices, is most of this file.

**Deposits look like enormous winning trades.** Balance operations arrive in the
same history stream with a `profit` field. A $10,000 deposit imported as a trade
does not merely add a row: it becomes the best trade, the largest win, most of
the gross profit, and it drags expectancy, profit factor and the equity curve
with it. `is_trading_deal()` is the filter that stops that, and it is the single
most consequential line in the module.

**A stop of 0.0 is not a stop of zero.** MT5 writes `0.0` for "no stop attached",
and `abs(entry - 0.0) * size` is a risk the size of the whole notional, which
would make every R multiple approximately zero. Every price field from MT5 goes
through `_price()`, which maps 0.0 to None.

Nothing here imports `MetaTrader5` at module scope. The package is Windows-only
and is not a dependency of this project; it is imported inside `connect()`, so
the module is importable — and the normalisation is testable — on any machine.

Testing
-------
`MT5Connector` takes a `terminal` object. Pass anything with the handful of
methods used below and the connector never looks for the real package; the test
suite does exactly that, so no live terminal is needed to run it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from ..core.exceptions import IntegrationError
from ..trading.models import Direction, Trade

# =============================================================================
# MT5 CONSTANTS
# =============================================================================
# Mirrored rather than imported so the normalisation runs without the package.
# Values are from the MQL5 documentation and are part of MT5's wire format.

DEAL_TYPE_BUY = 0
DEAL_TYPE_SELL = 1
# Everything from 2 up is a balance operation: deposit, withdrawal, credit,
# correction, bonus, commission settlement, interest, dividend, tax.
DEAL_TYPE_BALANCE = 2

DEAL_ENTRY_IN = 0
DEAL_ENTRY_OUT = 1
DEAL_ENTRY_INOUT = 2          # reversal: closes one side and opens the other
DEAL_ENTRY_OUT_BY = 3         # closed against an opposite position

POSITION_TYPE_BUY = 0
POSITION_TYPE_SELL = 1

# Volume comparison tolerance. Brokers round lot sizes to two or three decimals,
# so a fully closed position's in and out volumes can differ in the last digit.
VOLUME_EPSILON = 1e-6


def trade_id(position_id: int, account_id: str | None) -> str:
    """
    A journal id for an MT5 position.

    Namespaced by account, because a position ticket is unique *within* an
    account and nothing more. Two accounts at the same broker will both reach
    position 12345 eventually, and the journal's primary key is
    (user_email, id) — so an id of "mt5-12345" means the second account's trade
    silently replaces the first's, and the trader loses a trade they can still
    see in their terminal.
    """
    if not account_id:
        return f"mt5-{position_id}"
    slug = "".join(c if c.isalnum() or c in "-_" else "-" for c in str(account_id))
    return f"{slug}-{position_id}"


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class MT5Config:
    """
    What is needed to reach a terminal, and how to read what it returns.

    `server_utc_offset_hours` is not optional detail. MT5 timestamps are the
    broker's server clock expressed as a Unix epoch, and most brokers run their
    server on UTC+2/UTC+3 rather than UTC. Left uncorrected, every trade lands
    two or three hours later than it happened, which silently moves a third of
    them into the wrong session bucket and makes "your best session" an artefact
    of the broker's timezone. Set it to the offset the terminal's Market Watch
    clock shows against UTC.
    """

    login: int | None = None
    password: str | None = None
    server: str | None = None
    path: str | None = None                  # terminal64.exe, when not default
    timeout_ms: int = 60_000
    portable: bool = False

    server_utc_offset_hours: float = 0.0
    account_label: str | None = None         # what to file the trades under

    def redacted(self) -> dict:
        """Loggable form. The password never appears in a log or an error."""
        return {
            "login": self.login,
            "server": self.server,
            "path": self.path,
            "server_utc_offset_hours": self.server_utc_offset_hours,
        }


@dataclass
class BrokerAccount:
    """A trading account, in Sensitor's terms rather than MT5's."""

    id: str
    name: str
    broker: str
    currency: str
    balance: float | None = None
    equity: float | None = None
    leverage: int | None = None
    raw: dict = field(default_factory=dict, repr=False)


# =============================================================================
# FIELD ACCESS
# =============================================================================

def _as_dict(record) -> dict:
    """
    One dict from whatever MT5 handed back.

    The package returns named tuples, but a mock, a pickle round trip or a
    future version may return a plain object or a dict. Accepting all three
    costs four lines and removes a whole class of connector-only failure.
    """
    if isinstance(record, dict):
        return dict(record)
    if hasattr(record, "_asdict"):
        return dict(record._asdict())
    return {k: getattr(record, k) for k in dir(record)
            if not k.startswith("_") and not callable(getattr(record, k))}


def _price(value) -> float | None:
    """
    A price field, with MT5's "absent" sentinel mapped to None.

    MT5 writes 0.0 into `sl` and `tp` when no stop or target is attached. Taken
    literally that is a stop at zero, and `risk_amount` becomes the entire
    notional — every R multiple collapses toward zero and a book with no stops
    at all reports perfect discipline.
    """
    if value is None:
        return None
    try:
        price = float(value)
    except (TypeError, ValueError):
        return None
    return price if price > 0 else None


def _number(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def is_trading_deal(deal: dict) -> bool:
    """
    Whether a deal is a trade rather than a balance operation.

    Deposits, withdrawals, credits, corrections, bonuses, commission
    settlements, interest, dividends and taxes all arrive in the same history
    stream, all carry a `profit`, and none of them is a trade. They are
    identified by a deal type at or above `DEAL_TYPE_BALANCE`; most also carry
    `position_id == 0`, which is checked as well because some brokers reuse the
    buy/sell types for corrections.
    """
    deal_type = deal.get("type")
    if deal_type is None or int(deal_type) >= DEAL_TYPE_BALANCE:
        return False
    return int(deal.get("position_id") or 0) != 0


# =============================================================================
# TIME
# =============================================================================

def _moment(deal: dict, offset_hours: float) -> datetime:
    """
    A deal's timestamp, converted from broker server time to UTC.

    `time_msc` is preferred where present: two deals on the same position can
    share a whole second, and second precision would make their order depend on
    the sort's stability rather than on when they happened.
    """
    msc = deal.get("time_msc")
    seconds = (float(msc) / 1000.0) if msc else _number(deal.get("time"))
    server_clock = datetime.fromtimestamp(seconds, tz=timezone.utc)
    return (server_clock - timedelta(hours=offset_hours)).replace(tzinfo=None)


# =============================================================================
# NORMALISATION — pure, and the part worth testing
# =============================================================================

def group_deals(deals) -> dict[int, list[dict]]:
    """Trading deals bucketed by position, each bucket in time order."""
    positions: dict[int, list[dict]] = {}
    for record in deals:
        deal = _as_dict(record)
        if not is_trading_deal(deal):
            continue
        positions.setdefault(int(deal["position_id"]), []).append(deal)
    for bucket in positions.values():
        bucket.sort(key=lambda d: (_number(d.get("time_msc")) or _number(d.get("time"))))
    return positions


def stops_from_orders(orders) -> dict[int, tuple[float | None, float | None]]:
    """
    The stop and target each position was opened with.

    Deals do not carry a stop; orders do. The *first* order on a position is the
    one that matters: a stop moved to break-even later would otherwise rewrite
    the risk the trade was actually taken with, and every R multiple computed
    from it. What the trade risked at entry is the number R is defined against.
    """
    out: dict[int, tuple[float | None, float | None]] = {}
    seen: dict[int, float] = {}
    for record in orders or ():
        order = _as_dict(record)
        position_id = int(order.get("position_id") or 0)
        if not position_id:
            continue
        stamp = _number(order.get("time_setup_msc")) or _number(order.get("time_setup"))
        if position_id in seen and stamp >= seen[position_id]:
            continue
        seen[position_id] = stamp
        out[position_id] = (_price(order.get("sl")), _price(order.get("tp")))
    return out


def _implied_point_value(entry: float, exit_price: float, volume: float,
                         sign: int, gross_pnl: float | None) -> float | None:
    """
    What one unit of price movement on one lot was worth, in account currency.

    This is the piece that makes R correct without a contract-size table or an
    exchange rate. MT5 gives volume in lots and prices in the instrument's quote
    terms, so `abs(entry - stop) * volume` is a number in quote units — for
    EURUSD at one lot, a 50-pip stop comes out as 0.005 rather than $500. Every
    risk figure and every R multiple built on that would be wrong by the
    contract size, and wrong again by the quote-to-account exchange rate for any
    instrument not quoted in the account currency.

    Rather than look either of those up, derive the factor from the broker's own
    arithmetic: it already reported what this position made in account currency,
    and the price distance it travelled is known, so their ratio is the value of
    one price unit per lot for this instrument on this account. Self-calibrating,
    exact per trade, and correct for a JPY cross on a USD account without a
    single conversion.

    Returns None when the position closed at its entry price — no movement, no
    ratio — which leaves the trade's risk unknown rather than invented.
    """
    if gross_pnl is None or not volume:
        return None
    distance = (exit_price - entry) * sign
    if abs(distance) < 1e-12:
        return None
    value = gross_pnl / (distance * volume)
    return value if value > 0 else None


def build_trade(position_id: int, deals: list[dict], *,
                stop: float | None = None, take_profit: float | None = None,
                account_id: str | None = None, currency: str = "USD",
                offset_hours: float = 0.0) -> Trade | None:
    """
    One `Trade` from one position's deals, or None when it is not closed yet.

    Entry and exit prices are volume-weighted across their side, so a position
    scaled into in three tranches reports the average price it was actually
    carried at rather than the first fill.
    """
    entries = [d for d in deals if int(d.get("entry", 0)) == DEAL_ENTRY_IN]
    exits = [d for d in deals
             if int(d.get("entry", 0)) in (DEAL_ENTRY_OUT, DEAL_ENTRY_OUT_BY,
                                           DEAL_ENTRY_INOUT)]
    if not entries or not exits:
        return None

    volume_in = sum(_number(d.get("volume")) for d in entries)
    volume_out = sum(_number(d.get("volume")) for d in exits)
    if volume_in <= 0 or volume_out + VOLUME_EPSILON < volume_in:
        # Still open, or partially closed. A partially closed position has a
        # result so far, but reporting it as a closed trade would count a
        # running position's unrealised remainder as a finished outcome.
        return None

    entry_price = sum(_number(d.get("price")) * _number(d.get("volume"))
                      for d in entries) / volume_in
    exit_price = sum(_number(d.get("price")) * _number(d.get("volume"))
                     for d in exits) / volume_out

    # Direction comes from the opening deal. The closing deal carries the
    # opposite type — a long is closed by a sell — so reading the side off the
    # exit would invert every trade in the book.
    direction = (Direction.LONG if int(entries[0].get("type", 0)) == DEAL_TYPE_BUY
                 else Direction.SHORT)

    commission = sum(_number(d.get("commission")) + _number(d.get("fee"))
                     for d in deals)
    swap = sum(_number(d.get("swap")) for d in deals)
    # MT5's `profit` is the realised result before commission and swap, which is
    # exactly what the Trade model calls `gross_pnl`.
    gross_pnl = sum(_number(d.get("profit")) for d in deals)

    point_value = _implied_point_value(entry_price, exit_price, volume_in,
                                       direction.sign, gross_pnl)
    # `size` is stored in account currency per price unit, not in lots, so that
    # `abs(entry - stop) * size` is money and R is dimensionless. The lot volume
    # is kept in `raw` for display — a journal card that says "size 100000" when
    # the trader entered one lot is not showing them their own trade.
    size = volume_in * point_value if point_value else volume_in

    symbol = str(entries[0].get("symbol") or exits[0].get("symbol") or "")

    return Trade(
        id=trade_id(position_id, account_id),
        symbol=symbol,
        direction=direction,
        entry_price=entry_price,
        exit_price=exit_price,
        size=size,
        opened_at=_moment(entries[0], offset_hours),
        closed_at=_moment(exits[-1], offset_hours),
        stop_loss=stop,
        take_profit=take_profit,
        gross_pnl=gross_pnl,
        commission=commission,
        swap=swap,
        account_id=account_id,
        account_currency=currency,
        entry_reason=(entries[0].get("comment") or None),
        exit_reason=(exits[-1].get("comment") or None),
        source="mt5",
        raw={
            "position_id": position_id,
            "volume": volume_in,
            "volume_unit": "lots",
            "point_value": point_value,
            "n_deals": len(deals),
            "scaled_in": len(entries) > 1,
            "scaled_out": len(exits) > 1,
            "tickets": [int(d.get("ticket") or 0) for d in deals],
            "magic": int(entries[0].get("magic") or 0),
        },
    )


def normalise_deals(deals, orders=None, *, account_id: str | None = None,
                    currency: str = "USD", offset_hours: float = 0.0) -> list[Trade]:
    """
    A broker's deal history as Sensitor trades, oldest first.

    Pure: no terminal, no network, no Streamlit. This is the function the test
    suite exercises against hand-written deal records with known answers, which
    is how the folding stays correct without a Windows machine in the loop.
    """
    stops = stops_from_orders(orders)
    trades = []
    for position_id, bucket in group_deals(deals).items():
        stop, take_profit = stops.get(position_id, (None, None))
        trade = build_trade(position_id, bucket, stop=stop, take_profit=take_profit,
                            account_id=account_id, currency=currency,
                            offset_hours=offset_hours)
        if trade is not None:
            trades.append(trade)
    trades.sort(key=lambda t: t.opened_at)
    return trades


def normalise_positions(positions, *, account_id: str | None = None,
                        currency: str = "USD",
                        offset_hours: float = 0.0) -> list[Trade]:
    """
    Currently open positions as open `Trade`s.

    No exit, so no result: they are carried for the journal's open-positions
    table and excluded from every metric. `size` stays in lots here — with no
    exit there is no realised P&L to calibrate a point value against, and
    guessing one would put a fabricated risk figure on a live position.
    """
    out = []
    for record in positions or ():
        position = _as_dict(record)
        direction = (Direction.LONG
                     if int(position.get("type", 0)) == POSITION_TYPE_BUY
                     else Direction.SHORT)
        out.append(Trade(
            id=trade_id(
                int(position.get("ticket") or position.get("identifier") or 0),
                account_id),
            symbol=str(position.get("symbol") or ""),
            direction=direction,
            entry_price=_number(position.get("price_open")),
            size=_number(position.get("volume")),
            opened_at=_moment(position, offset_hours),
            stop_loss=_price(position.get("sl")),
            take_profit=_price(position.get("tp")),
            swap=_number(position.get("swap")),
            account_id=account_id,
            account_currency=currency,
            source="mt5",
            raw={"open": True, "volume": _number(position.get("volume")),
                 "volume_unit": "lots"},
        ))
    return out


# =============================================================================
# CONNECTOR
# =============================================================================

class MT5Connector:
    """
    A live MetaTrader 5 terminal, behind a broker-agnostic surface.

    Usable as a context manager, which is the form to prefer — `initialize()`
    holds a handle on the terminal and a connector that raises before
    `shutdown()` leaves it held.

        with MT5Connector(config) as broker:
            trades = broker.fetch_trades(since=date(2025, 1, 1))
    """

    def __init__(self, config: MT5Config, terminal=None):
        self.config = config
        self._terminal = terminal            # injected in tests
        self._connected = False
        self._account: BrokerAccount | None = None

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def _load_terminal(self):
        """
        Import the MT5 package, late and with a message worth reading.

        Imported here rather than at module scope on purpose: `MetaTrader5` ships
        only for Windows and is not a dependency of this project, so a top-level
        import would make this module — and the package that re-exports it —
        unimportable on the machine most of this code is written on.
        """
        if self._terminal is not None:
            return self._terminal
        try:
            import MetaTrader5                      # noqa: N813
        except ImportError as exc:                  # pragma: no cover - platform
            raise IntegrationError(
                "The MetaTrader5 package is not installed. It is published for "
                "Windows only; on macOS or Linux, export your history to CSV or "
                "run the terminal in a Windows VM."
            ) from exc
        self._terminal = MetaTrader5
        return self._terminal

    def connect(self) -> BrokerAccount:
        """Open the terminal, log in if asked to, and return the account."""
        terminal = self._load_terminal()
        config = self.config

        kwargs = {"timeout": config.timeout_ms, "portable": config.portable}
        if config.path:
            kwargs["path"] = config.path
        if config.login:
            kwargs.update(login=int(config.login), password=config.password,
                          server=config.server)

        if not terminal.initialize(**kwargs):
            raise IntegrationError(
                f"MetaTrader 5 refused the connection: {self._last_error()}. "
                f"Settings: {config.redacted()}"
            )
        self._connected = True

        # `initialize` can succeed against a terminal that is open but not
        # logged in, and every subsequent call then returns an empty tuple —
        # indistinguishable from "you have no trades". Reading the account is
        # what turns that into an error instead of an empty journal.
        account = self.account()
        if account is None:
            self.disconnect()
            raise IntegrationError(
                "Connected to the terminal but no account is logged in. "
                "Sign in to the account in MetaTrader 5, or supply a login, "
                "password and server."
            )
        return account

    def disconnect(self) -> None:
        if self._connected and self._terminal is not None:
            self._terminal.shutdown()
        self._connected = False

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *exc_info):
        self.disconnect()
        return False

    def _last_error(self) -> str:
        try:
            code, description = self._terminal.last_error()
            return f"{description} (code {code})"
        except Exception:                            # noqa: BLE001
            return "no error detail available"

    def _require(self) -> None:
        if not self._connected:
            raise IntegrationError("Not connected. Call connect() first.")

    # ── Reads ────────────────────────────────────────────────────────────────

    def account(self) -> BrokerAccount | None:
        """The logged-in account, or None when the terminal has none."""
        info = self._terminal.account_info()
        if info is None:
            return None
        data = _as_dict(info)
        login = str(data.get("login") or "")
        self._account = BrokerAccount(
            id=self.config.account_label or f"mt5-{login}",
            name=str(data.get("name") or login),
            broker=str(data.get("company") or data.get("server") or "MetaTrader 5"),
            currency=str(data.get("currency") or "USD"),
            balance=_number(data.get("balance"), None) if "balance" in data else None,
            equity=_number(data.get("equity"), None) if "equity" in data else None,
            leverage=int(data.get("leverage") or 0) or None,
            raw=data,
        )
        return self._account

    def fetch_trades(self, since: datetime, until: datetime | None = None) -> list[Trade]:
        """
        Closed trades in a window, already normalised.

        The window is widened by a day at the front before it is sent to the
        terminal: a position opened on the 1st and closed on the 5th is returned
        by MT5 only if the *deal* falls in the range, and a caller asking for
        "since the 2nd" should still get the closing deal that belongs to it.
        Trades are filtered back to the requested window on close time.
        """
        self._require()
        until = until or datetime.now(timezone.utc).replace(tzinfo=None)
        window_start = since - timedelta(days=1)

        deals = self._terminal.history_deals_get(window_start, until)
        if deals is None:
            raise IntegrationError(
                f"MetaTrader 5 could not return the deal history: {self._last_error()}"
            )
        orders = self._terminal.history_orders_get(window_start, until) or ()

        account = self._account or self.account()
        trades = normalise_deals(
            deals, orders,
            account_id=account.id if account else None,
            currency=account.currency if account else "USD",
            offset_hours=self.config.server_utc_offset_hours,
        )
        return [t for t in trades if t.closed_at and t.closed_at >= since]

    def fetch_open_positions(self) -> list[Trade]:
        self._require()
        positions = self._terminal.positions_get()
        account = self._account or self.account()
        return normalise_positions(
            positions,
            account_id=account.id if account else None,
            currency=account.currency if account else "USD",
            offset_hours=self.config.server_utc_offset_hours,
        )

    def fetch_all(self, since: datetime, until: datetime | None = None) -> list[Trade]:
        """Closed trades and open positions in one list."""
        return self.fetch_trades(since, until) + self.fetch_open_positions()
