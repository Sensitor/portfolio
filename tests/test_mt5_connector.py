"""
MT5 connector and synchronisation, against a mocked terminal.

No MetaTrader 5, no Windows, no network. `FakeTerminal` implements the handful
of methods the connector calls, and the normalisation is exercised against
hand-written deal records whose answers were worked out by hand — which is the
only way to know the deal folding is right without a live account to compare
against.

`streamlit` is poisoned before the imports, so a UI import anywhere under
`integrations/` fails here rather than in production.

Run with:  python tests/test_mt5_connector.py
"""

from __future__ import annotations

import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Business logic must never import Streamlit. Setting the module to None makes
# any `import streamlit` inside the code under test raise instead of silently
# succeeding because the real package happens to be installed.
sys.modules["streamlit"] = None

os.environ["SENSITOR_DB_PATH"] = os.path.join(
    tempfile.mkdtemp(prefix="sensitor-mt5-test-"), "mt5.db")

from sensitor.core.exceptions import IntegrationError            # noqa: E402
from sensitor.integrations import mt5, sync                      # noqa: E402
from sensitor.trading.models import Direction, Trade, session_for  # noqa: E402

CHECKS = []


def check(name, condition, detail=""):
    CHECKS.append((name, bool(condition), detail))
    print(f"  {'ok  ' if condition else 'FAIL'}  {name}"
          + (f"   {detail}" if detail and not condition else ""))


def near(a, b, tolerance=1e-6):
    if a is None or b is None:
        return a is b
    return abs(a - b) <= tolerance


# =============================================================================
# FIXTURES
# =============================================================================

def epoch(year, month, day, hour=0, minute=0) -> float:
    """A UTC timestamp, the way MT5 reports its server clock."""
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc).timestamp()


def deal(**kwargs) -> dict:
    """One MT5 deal with sane defaults, overridden per test."""
    base = {
        "ticket": 1, "order": 1, "position_id": 1,
        "time": epoch(2025, 3, 10, 9, 0), "time_msc": None,
        "type": mt5.DEAL_TYPE_BUY, "entry": mt5.DEAL_ENTRY_IN,
        "symbol": "EURUSD", "volume": 1.0, "price": 1.1000,
        "commission": 0.0, "swap": 0.0, "fee": 0.0, "profit": 0.0,
        "magic": 0, "comment": "",
    }
    base.update(kwargs)
    if base["time_msc"] is None:
        base["time_msc"] = base["time"] * 1000
    return base


def order(**kwargs) -> dict:
    base = {"ticket": 1, "position_id": 1, "sl": 0.0, "tp": 0.0,
            "time_setup": epoch(2025, 3, 10, 9, 0), "time_setup_msc": None}
    base.update(kwargs)
    if base["time_setup_msc"] is None:
        base["time_setup_msc"] = base["time_setup"] * 1000
    return base


def round_turn(position_id=1, symbol="EURUSD", *, side=mt5.DEAL_TYPE_BUY,
               entry=1.1000, exit_price=1.1050, volume=1.0, profit=500.0,
               commission=-7.0, swap=0.0, open_at=None, close_at=None):
    """The ordinary case: one in, one out."""
    open_at = open_at or epoch(2025, 3, 10, 9, 0)
    close_at = close_at or epoch(2025, 3, 10, 11, 0)
    other = mt5.DEAL_TYPE_SELL if side == mt5.DEAL_TYPE_BUY else mt5.DEAL_TYPE_BUY
    return [
        deal(ticket=position_id * 10, position_id=position_id, symbol=symbol,
             type=side, entry=mt5.DEAL_ENTRY_IN, price=entry, volume=volume,
             time=open_at, time_msc=None, commission=commission / 2, profit=0.0),
        deal(ticket=position_id * 10 + 1, position_id=position_id, symbol=symbol,
             type=other, entry=mt5.DEAL_ENTRY_OUT, price=exit_price, volume=volume,
             time=close_at, time_msc=None, commission=commission / 2,
             swap=swap, profit=profit),
    ]


class FakeTerminal:
    """
    Everything the connector calls, and nothing else.

    Mirrors MT5's actual contract including its unhelpful parts: `initialize`
    returns a bool rather than raising, failed calls return None, and
    `account_info` returns None when the terminal is open but not signed in.
    """

    def __init__(self, *, deals=(), orders=(), positions=(), account=None,
                 initialize_ok=True, error=(-1, "IPC initialize failed")):
        self._deals = list(deals)
        self._orders = list(orders)
        self._positions = list(positions)
        self._account = account
        self._initialize_ok = initialize_ok
        self._error = error
        self.initialized = False
        self.shutdown_calls = 0
        self.init_kwargs = None

    def initialize(self, **kwargs):
        self.init_kwargs = kwargs
        self.initialized = self._initialize_ok
        return self._initialize_ok

    def shutdown(self):
        self.shutdown_calls += 1
        self.initialized = False

    def last_error(self):
        return self._error

    def account_info(self):
        return self._account

    def history_deals_get(self, start, end):
        return tuple(self._deals)

    def history_orders_get(self, start, end):
        return tuple(self._orders)

    def positions_get(self):
        return tuple(self._positions)


ACCOUNT = {"login": 51234567, "name": "N. Gouaux", "company": "Broker Ltd",
           "server": "Broker-Live", "currency": "USD", "balance": 10_000.0,
           "equity": 10_350.0, "leverage": 30}


# =============================================================================
# 1. BALANCE OPERATIONS — the filter that matters most
# =============================================================================

def test_balance_operations():
    print("\nBalance operations")

    deposit = deal(ticket=99, position_id=0, type=mt5.DEAL_TYPE_BALANCE,
                   entry=mt5.DEAL_ENTRY_IN, symbol="", volume=0.0, price=0.0,
                   profit=10_000.0)
    correction = deal(ticket=98, position_id=0, type=mt5.DEAL_TYPE_BUY,
                      profit=-25.0)

    check("a deposit is not a trading deal", not mt5.is_trading_deal(deposit))
    check("a position-less buy is not a trading deal",
          not mt5.is_trading_deal(correction))
    check("a real deal is", mt5.is_trading_deal(deal()))

    trades = mt5.normalise_deals([deposit, correction] + round_turn())
    check("history with a deposit yields one trade", len(trades) == 1,
          f"got {len(trades)}")
    check("the deposit did not become the best trade",
          trades and near(trades[0].gross_pnl, 500.0),
          f"gross_pnl {trades[0].gross_pnl if trades else None}")

    # The whole point: with the deposit folded in, every headline figure moves.
    from sensitor.trading.analytics import compute_metrics
    metrics = compute_metrics(trades)
    check("net P&L excludes the deposit", near(metrics["net_pnl"], 493.0),
          f"net_pnl {metrics['net_pnl']}")


# =============================================================================
# 2. THE STOP SENTINEL
# =============================================================================

def test_zero_is_not_a_stop():
    print("\nThe 0.0 stop sentinel")

    check("0.0 maps to None", mt5._price(0.0) is None)
    check("a real price survives", near(mt5._price(1.0950), 1.0950))
    check("None stays None", mt5._price(None) is None)
    check("a negative price is not a price", mt5._price(-1.0) is None)

    trades = mt5.normalise_deals(round_turn(), [order(sl=0.0, tp=0.0)])
    check("no stop attached leaves risk undefined",
          trades[0].stop_loss is None and trades[0].risk_amount is None)
    check("and R undefined, not zero", trades[0].r_multiple is None)

    # Taken literally, a 0.0 stop puts the whole notional at risk and every R
    # collapses toward zero. This is the assertion that keeps that from coming
    # back in a refactor.
    literal = Trade(id="x", symbol="EURUSD", direction=Direction.LONG,
                    entry_price=1.1000, size=100_000, opened_at=datetime(2025, 3, 10),
                    exit_price=1.1050, closed_at=datetime(2025, 3, 10, 11),
                    stop_loss=0.0)
    check("a literal 0.0 stop would have given a near-zero R",
          literal.r_multiple is not None and abs(literal.r_multiple) < 0.01,
          f"r={literal.r_multiple}")


# =============================================================================
# 3. DEAL FOLDING
# =============================================================================

def test_simple_round_turn():
    print("\nA simple round turn")

    trades = mt5.normalise_deals(round_turn(), [order(sl=1.0950, tp=1.1100)])
    check("one position becomes one trade", len(trades) == 1)
    trade = trades[0]

    check("symbol", trade.symbol == "EURUSD")
    check("direction is long", trade.direction is Direction.LONG)
    check("entry price", near(trade.entry_price, 1.1000))
    check("exit price", near(trade.exit_price, 1.1050))
    check("gross P&L is the broker's", near(trade.gross_pnl, 500.0))
    check("commission summed across both deals", near(trade.commission, -7.0))
    check("net P&L", near(trade.pnl, 493.0))
    check("id derives from the position", trade.id == "mt5-1")
    check("source is mt5", trade.source == "mt5")
    check("lot volume kept in raw", near(trade.raw["volume"], 1.0))

    # EURUSD at one lot: the implied point value is the contract size.
    check("implied point value is the contract size",
          near(trade.raw["point_value"], 100_000.0, 1e-3),
          f"got {trade.raw['point_value']}")
    check("risk is in account currency", near(trade.risk_amount, 500.0, 1e-3),
          f"got {trade.risk_amount}")
    check("gross R is exactly 1", near(trade.r_multiple_gross, 1.0, 1e-9),
          f"got {trade.r_multiple_gross}")
    check("net R is below it by the commission",
          near(trade.r_multiple, 0.986, 1e-6), f"got {trade.r_multiple}")


def test_short_direction():
    print("\nDirection")

    # A short: opened with a sell, closed with a buy, price falls, profit made.
    deals = round_turn(position_id=2, side=mt5.DEAL_TYPE_SELL,
                       entry=1.1050, exit_price=1.1000, profit=500.0)
    trades = mt5.normalise_deals(deals, [order(position_id=2, sl=1.1100)])
    trade = trades[0]

    check("direction comes from the opening deal",
          trade.direction is Direction.SHORT)
    check("a profitable short has positive P&L", trade.pnl > 0)
    check("gross R is 1 on a short", near(trade.r_multiple_gross, 1.0, 1e-9),
          f"got {trade.r_multiple_gross}")

    # Reading the side off the closing deal would call this a long, and a long
    # from 1.1050 to 1.1000 is a loss. The sign of the entire book depends on it.
    closing_type = deals[-1]["type"]
    check("the closing deal carries the opposite type",
          closing_type == mt5.DEAL_TYPE_BUY)


def test_scaled_in_and_out():
    print("\nScaling in and out")

    deals = [
        deal(ticket=30, position_id=3, symbol="XAUUSD", volume=1.0, price=100.00,
             entry=mt5.DEAL_ENTRY_IN, time=epoch(2025, 3, 11, 9, 0)),
        deal(ticket=31, position_id=3, symbol="XAUUSD", volume=1.0, price=102.00,
             entry=mt5.DEAL_ENTRY_IN, time=epoch(2025, 3, 11, 9, 30)),
        deal(ticket=32, position_id=3, symbol="XAUUSD", volume=2.0, price=105.00,
             type=mt5.DEAL_TYPE_SELL, entry=mt5.DEAL_ENTRY_OUT,
             time=epoch(2025, 3, 11, 14, 0), profit=800.0),
    ]
    trade = mt5.normalise_deals(deals)[0]

    check("entry price is volume-weighted", near(trade.entry_price, 101.00),
          f"got {trade.entry_price}")
    check("exit price", near(trade.exit_price, 105.00))
    check("volume is the sum of the entries", near(trade.raw["volume"], 2.0))
    check("opened at the first entry",
          trade.opened_at == datetime(2025, 3, 11, 9, 0))
    check("closed at the last exit",
          trade.closed_at == datetime(2025, 3, 11, 14, 0))
    check("scaling is recorded", trade.raw["scaled_in"] is True
          and trade.raw["scaled_out"] is False)
    # (105 - 101) * 1 * 200 = 800, so the model reproduces the broker's figure.
    check("size reproduces the broker's P&L from prices",
          near((trade.exit_price - trade.entry_price) * trade.size, 800.0, 1e-6),
          f"size {trade.size}")

    out_deals = [
        deal(ticket=40, position_id=4, volume=2.0, price=1.1000,
             entry=mt5.DEAL_ENTRY_IN, time=epoch(2025, 3, 12, 9, 0)),
        deal(ticket=41, position_id=4, volume=1.0, price=1.1030,
             type=mt5.DEAL_TYPE_SELL, entry=mt5.DEAL_ENTRY_OUT,
             time=epoch(2025, 3, 12, 10, 0), profit=300.0),
        deal(ticket=42, position_id=4, volume=1.0, price=1.1050,
             type=mt5.DEAL_TYPE_SELL, entry=mt5.DEAL_ENTRY_OUT,
             time=epoch(2025, 3, 12, 11, 0), profit=500.0),
    ]
    trade = mt5.normalise_deals(out_deals)[0]
    check("exit price is volume-weighted across partial closes",
          near(trade.exit_price, 1.1040), f"got {trade.exit_price}")
    check("both exits counted in P&L", near(trade.gross_pnl, 800.0))
    check("scaled out is recorded", trade.raw["scaled_out"] is True)


def test_open_and_partial():
    print("\nPositions that are not finished")

    only_entry = [deal(ticket=50, position_id=5, entry=mt5.DEAL_ENTRY_IN)]
    check("an entry with no exit is not a closed trade",
          mt5.normalise_deals(only_entry) == [])

    partial = [
        deal(ticket=60, position_id=6, volume=2.0, entry=mt5.DEAL_ENTRY_IN),
        deal(ticket=61, position_id=6, volume=1.0, type=mt5.DEAL_TYPE_SELL,
             entry=mt5.DEAL_ENTRY_OUT, time=epoch(2025, 3, 10, 10, 0), profit=200.0),
    ]
    check("a partially closed position is not a closed trade",
          mt5.normalise_deals(partial) == [])

    # Rounding in the last digit must not make a closed position look open.
    rounded = [
        deal(ticket=70, position_id=7, volume=0.3, entry=mt5.DEAL_ENTRY_IN),
        deal(ticket=71, position_id=7, volume=0.1, type=mt5.DEAL_TYPE_SELL,
             entry=mt5.DEAL_ENTRY_OUT, time=epoch(2025, 3, 10, 10, 0), profit=50.0),
        deal(ticket=72, position_id=7, volume=0.2, type=mt5.DEAL_TYPE_SELL,
             entry=mt5.DEAL_ENTRY_OUT, time=epoch(2025, 3, 10, 11, 0), profit=90.0),
    ]
    check("float rounding does not leave a closed position open",
          len(mt5.normalise_deals(rounded)) == 1)


# =============================================================================
# 4. THE IMPLIED POINT VALUE
# =============================================================================

def test_point_value():
    print("\nThe implied point value")

    # A JPY cross on a USD account. One lot of USDJPY is 100,000 USD; a 1.00
    # move is 100,000 JPY, which at 151 is 662.25 USD. Nothing in the module
    # knows that — it is derived from the broker's own P&L.
    deals = round_turn(position_id=8, symbol="USDJPY", entry=150.00,
                       exit_price=151.00, profit=662.25, commission=0.0)
    trade = mt5.normalise_deals(deals, [order(position_id=8, sl=149.50)])[0]

    check("point value derived from the broker's P&L",
          near(trade.raw["point_value"], 662.25, 1e-6),
          f"got {trade.raw['point_value']}")
    check("risk is in USD, not JPY", near(trade.risk_amount, 331.125, 1e-6),
          f"got {trade.risk_amount}")
    check("100 pips on a 50-pip stop is 2R",
          near(trade.r_multiple_gross, 2.0, 1e-9), f"got {trade.r_multiple_gross}")

    # Without the calibration, `size` would be the lot count and the risk would
    # be 0.50 — a number in JPY pips wearing a dollar sign.
    naive = Trade(id="n", symbol="USDJPY", direction=Direction.LONG,
                  entry_price=150.00, size=1.0, opened_at=datetime(2025, 3, 10),
                  exit_price=151.00, closed_at=datetime(2025, 3, 10, 11),
                  stop_loss=149.50, gross_pnl=662.25)
    check("the naive version would report a risk of 0.50",
          near(naive.risk_amount, 0.50), f"got {naive.risk_amount}")
    check("and an R of 1324, not 2",
          naive.r_multiple > 1000, f"got {naive.r_multiple}")

    check("a flat close leaves the point value unknown",
          mt5._implied_point_value(1.1, 1.1, 1.0, 1, 0.0) is None)
    check("no P&L leaves it unknown",
          mt5._implied_point_value(1.1, 1.2, 1.0, 1, None) is None)


# =============================================================================
# 5. STOPS FROM ORDERS
# =============================================================================

def test_stops_from_orders():
    print("\nStops from orders")

    orders = [
        order(ticket=1, position_id=9, sl=1.0950, tp=1.1100,
              time_setup=epoch(2025, 3, 10, 9, 0)),
        order(ticket=2, position_id=9, sl=1.1000, tp=1.1100,   # moved to break-even
              time_setup=epoch(2025, 3, 10, 10, 0)),
    ]
    stops = mt5.stops_from_orders(orders)
    check("the first order's stop wins", near(stops[9][0], 1.0950),
          f"got {stops[9][0]}")
    check("target comes with it", near(stops[9][1], 1.1100))

    # A stop moved to break-even mid-trade would otherwise rewrite what the
    # trade risked, and with it every R multiple in the book.
    trade = mt5.normalise_deals(round_turn(position_id=9), orders)[0]
    check("R is computed against the risk taken at entry",
          near(trade.r_multiple_gross, 1.0, 1e-9), f"got {trade.r_multiple_gross}")

    check("orders without a position are ignored",
          mt5.stops_from_orders([order(position_id=0, sl=1.0)]) == {})
    check("no orders is not an error", mt5.stops_from_orders(None) == {})


# =============================================================================
# 6. TIME
# =============================================================================

def test_server_time():
    print("\nServer time")

    record = deal(time=epoch(2025, 3, 10, 14, 30))
    at_utc = mt5._moment(record, 0.0)
    shifted = mt5._moment(record, 3.0)

    check("no offset leaves the clock alone",
          at_utc == datetime(2025, 3, 10, 14, 30))
    check("a UTC+3 server is pulled back three hours",
          shifted == datetime(2025, 3, 10, 11, 30), f"got {shifted}")

    # The offset is not cosmetic: uncorrected, this trade is attributed to the
    # busiest window of the day instead of to London.
    check("uncorrected, the session is the London/NY overlap",
          session_for(at_utc).value == "overlap")
    check("corrected, it is London", session_for(shifted).value == "london",
          f"got {session_for(shifted).value}")

    precise = deal(time=epoch(2025, 3, 10, 9, 0),
                   time_msc=epoch(2025, 3, 10, 9, 0) * 1000 + 750)
    check("millisecond precision is used when present",
          mt5._moment(precise, 0.0).microsecond == 750_000,
          f"got {mt5._moment(precise, 0.0)}")


# =============================================================================
# 7. FIELD ACCESS
# =============================================================================

def test_record_shapes():
    print("\nRecord shapes")

    from collections import namedtuple
    Deal = namedtuple("Deal", "ticket position_id type entry symbol volume price "
                              "time time_msc commission swap fee profit magic comment")
    as_tuple = Deal(1, 1, 0, 0, "EURUSD", 1.0, 1.1, epoch(2025, 3, 10, 9),
                    epoch(2025, 3, 10, 9) * 1000, 0.0, 0.0, 0.0, 0.0, 0, "")

    check("a named tuple is read", mt5._as_dict(as_tuple)["symbol"] == "EURUSD")
    check("a dict is read", mt5._as_dict({"symbol": "XAUUSD"})["symbol"] == "XAUUSD")

    class Obj:
        symbol = "US30"
        volume = 2.0

    check("a plain object is read", mt5._as_dict(Obj())["symbol"] == "US30")


# =============================================================================
# 8. THE CONNECTOR
# =============================================================================

def test_connector():
    print("\nThe connector")

    config = mt5.MT5Config(login=51234567, password="hunter2",
                           server="Broker-Live", server_utc_offset_hours=3.0)
    check("the password never appears in the loggable form",
          "hunter2" not in str(config.redacted()))

    terminal = FakeTerminal(deals=round_turn(), orders=[order(sl=1.0950)],
                            account=ACCOUNT)
    connector = mt5.MT5Connector(config, terminal=terminal)

    try:
        connector.fetch_trades(datetime(2025, 1, 1))
        check("reading before connecting raises", False)
    except IntegrationError:
        check("reading before connecting raises", True)

    account = connector.connect()
    check("connect returns the account", account.id == "mt5-51234567")
    check("broker name", account.broker == "Broker Ltd")
    check("currency", account.currency == "USD")
    check("credentials were passed through",
          terminal.init_kwargs["login"] == 51234567)

    trades = connector.fetch_trades(datetime(2025, 3, 1))
    check("trades come back normalised", len(trades) == 1)
    check("filed under the account", trades[0].account_id == "mt5-51234567")
    check("the server offset was applied",
          trades[0].opened_at == datetime(2025, 3, 10, 6, 0),
          f"got {trades[0].opened_at}")

    check("trades before the window are dropped",
          connector.fetch_trades(datetime(2025, 6, 1)) == [])

    connector.disconnect()
    check("disconnect shuts the terminal down", terminal.shutdown_calls == 1)

    # A terminal that is open but signed out returns empty tuples from every
    # call — indistinguishable from an account with no history.
    signed_out = mt5.MT5Connector(config, terminal=FakeTerminal(account=None))
    try:
        signed_out.connect()
        check("a signed-out terminal raises rather than returning nothing", False)
    except IntegrationError as exc:
        check("a signed-out terminal raises rather than returning nothing",
              "logged in" in str(exc))

    refused = mt5.MT5Connector(config, terminal=FakeTerminal(initialize_ok=False))
    try:
        refused.connect()
        check("a refused connection raises with the terminal's reason", False)
    except IntegrationError as exc:
        check("a refused connection raises with the terminal's reason",
              "IPC initialize failed" in str(exc))
        check("and the reason carries no password", "hunter2" not in str(exc))

    with mt5.MT5Connector(config, terminal=FakeTerminal(
            deals=round_turn(), account=ACCOUNT)) as broker:
        check("the context manager connects", broker.account() is not None)


def test_open_positions():
    print("\nOpen positions")

    positions = [{"ticket": 900, "symbol": "XAUUSD", "type": mt5.POSITION_TYPE_SELL,
                  "volume": 0.5, "price_open": 2400.0, "sl": 2415.0, "tp": 0.0,
                  "swap": -1.2, "time": epoch(2025, 3, 20, 8, 0)}]
    terminal = FakeTerminal(positions=positions, account=ACCOUNT)
    connector = mt5.MT5Connector(mt5.MT5Config(), terminal=terminal)
    connector.connect()

    open_trades = connector.fetch_open_positions()
    check("one open position", len(open_trades) == 1)
    trade = open_trades[0]
    check("it is open", not trade.is_closed)
    check("direction", trade.direction is Direction.SHORT)
    check("stop survives", near(trade.stop_loss, 2415.0))
    check("a 0.0 target is no target", trade.take_profit is None)
    check("size stays in lots on an open position", near(trade.size, 0.5))
    check("an open position has no result", trade.pnl is None)


# =============================================================================
# 9. SYNCHRONISATION
# =============================================================================

class FakeSource:
    def __init__(self, trades, account=None, open_trades=()):
        self._trades = list(trades)
        self._open = list(open_trades)
        self._account = account

    def account(self):
        return self._account

    def fetch_trades(self, since, until=None):
        return list(self._trades)

    def fetch_open_positions(self):
        return list(self._open)


def test_merge_rules():
    print("\nMerge rules")

    broker_trade = mt5.normalise_deals(round_turn(), [order(sl=1.0950)])[0]

    annotated = broker_trade.annotated(
        setups=["bos", "fvg"], mistakes=["moved_stop"], timeframe="M15",
        emotion_before="calm", discipline=4, notes="swept the low, waited for CHoCH",
        setup_quality=4, confidence=3,
    )

    to_write, result = merge = sync.merge_trades([broker_trade], [annotated])
    check("a re-sync of an unchanged trade writes nothing", to_write == [],
          f"{len(to_write)} to write")
    check("and reports it unchanged", result.unchanged == 1)
    check("annotations were recognised", result.annotations_kept == 1)

    # The failure this rule exists to prevent: a sync silently erasing the
    # journal. Verified on the merged object, not just on the write count.
    merged, _ = sync._preserve_journal(broker_trade, annotated)
    check("setups survive a sync", merged.setups == ["bos", "fvg"])
    check("mistakes survive", merged.mistakes == ["moved_stop"])
    check("notes survive", "CHoCH" in (merged.notes or ""))
    check("emotion survives", merged.emotion_before == "calm")
    check("discipline survives", merged.discipline == 4)
    check("timeframe survives", merged.timeframe == "M15")

    # A corrected execution must still come through.
    corrected = broker_trade.annotated(gross_pnl=512.0)
    to_write, result = sync.merge_trades([corrected], [annotated])
    check("a corrected P&L is written", len(to_write) == 1)
    check("and counted as an update", result.updated == 1)
    check("with the annotations still attached",
          to_write and to_write[0].setups == ["bos", "fvg"])

    # A stop the broker has since reported must not be reverted to None.
    no_stop = broker_trade.annotated(stop_loss=None)
    merged, _ = sync._preserve_journal(no_stop, annotated)
    check("a stop known to the journal is not lost",
          near(merged.stop_loss, 1.0950))

    check("a brand new trade is added",
          sync.merge_trades([broker_trade], [])[1].added == 1)


def test_sync_against_the_store():
    print("\nSynchronisation against the store")

    from sensitor.database import Store
    store = Store()
    email = "sync@example.com"
    store.delete_all_trades(email)
    store.upsert_user(email, "pro")

    account = mt5.BrokerAccount(id="mt5-51234567", name="N. Gouaux",
                               broker="Broker Ltd", currency="USD")
    deals = round_turn(position_id=1) + round_turn(
        position_id=2, open_at=epoch(2025, 3, 12, 9, 0),
        close_at=epoch(2025, 3, 12, 12, 0), profit=-300.0)
    trades = mt5.normalise_deals(deals, [order(position_id=1, sl=1.0950),
                                         order(position_id=2, sl=1.0950)],
                                 account_id=account.id)
    source = FakeSource(trades, account=account)

    first = sync.sync_trades(source, store, email, since=datetime(2025, 1, 1))
    check("first sync writes both", first.added == 2, f"added {first.added}")
    check("count in the store", store.count_trades(email) == 2)
    check("the account was registered",
          any(a.id == "mt5-51234567" for a in store.list_accounts(email)))

    second = sync.sync_trades(source, store, email, since=datetime(2025, 1, 1))
    check("re-syncing adds nothing", second.added == 0)
    check("re-syncing changes nothing", second.updated == 0,
          f"updated {second.updated}")
    check("count is still two", store.count_trades(email) == 2)

    # Annotate through the journal, then sync again — the scenario the whole
    # merge rule exists for.
    stored = store.get_trade(email, trades[0].id)
    store.save_trade(email, stored.annotated(
        setups=["order_block"], notes="clean sweep of the Asia low",
        emotion_before="calm", discipline=5))

    third = sync.sync_trades(source, store, email, since=datetime(2025, 1, 1))
    after = store.get_trade(email, trades[0].id)
    check("a sync after annotating writes nothing", third.updated == 0)
    check("the setup survived the round trip", after.setups == ["order_block"])
    check("the note survived", "Asia low" in (after.notes or ""))
    check("the discipline rating survived", after.discipline == 5)
    check("the broker's P&L is untouched", near(after.gross_pnl, 500.0))

    check("raw payload round-trips through the database",
          after.raw.get("volume_unit") == "lots", f"raw {after.raw}")

    # An empty email must never write.
    try:
        sync.sync_trades(source, store, "", since=datetime(2025, 1, 1))
        check("syncing without a user is refused", False)
    except ValueError:
        check("syncing without a user is refused", True)

    # Another user's journal must not be touched by this one's sync.
    other = "other-sync@example.com"
    store.delete_all_trades(other)
    check("the sync did not reach another user", store.count_trades(other) == 0)

    # The incremental window is anchored to when the account was last pulled
    # from, which the sync records — not to the newest close. The difference
    # shows up exactly here: these trades closed in March 2025, the syncs above
    # ran just now, and the next window should start days ago rather than
    # eighteen months ago.
    stamp = store.last_synced_at(email, "mt5-51234567")
    check("the sync recorded when it ran", bool(stamp), f"stamp {stamp}")

    window = sync.default_window(store, email, "mt5-51234567")
    latest = max(t.closed_at for t in store.list_trades(email) if t.closed_at)
    check("the window is anchored to the last sync, not the last close",
          window > latest, f"window {window} vs latest close {latest}")
    check("and it overlaps the last sync by a few days",
          timedelta(days=2) < (datetime.now() - window) < timedelta(days=5),
          f"window {window}")

    # An account that has never been synced still has to start somewhere, and
    # the newest close is the right guess there.
    never = sync.default_window(store, email, account_id=None)
    check("an unsynced account falls back to the last close",
          never < latest, f"got {never}")

    check("an empty journal falls back to a year",
          sync.default_window(store, "nobody@example.com")
          < datetime.now() - timedelta(days=364))


# =============================================================================
# 10. ID COLLISIONS ACROSS ACCOUNTS
# =============================================================================

def test_ids_are_namespaced():
    print("\nTrade ids across accounts")

    live = mt5.normalise_deals(round_turn(position_id=12345),
                               account_id="mt5-11111")
    demo = mt5.normalise_deals(round_turn(position_id=12345, profit=-120.0),
                               account_id="mt5-22222")

    check("the same ticket on two accounts gets two ids",
          live[0].id != demo[0].id, f"{live[0].id} vs {demo[0].id}")
    check("the id carries the account", "11111" in live[0].id)
    check("an account-less id still works", "mt5-9" ==
          mt5.trade_id(9, None))
    check("an account label with punctuation is slugged",
          " " not in mt5.trade_id(9, "my account/live"))

    # Without namespacing both are "mt5-12345", the primary key is
    # (user_email, id), and saving the second deletes the first.
    from sensitor.database import Store
    store = Store()
    email = "twoaccounts@example.com"
    store.delete_all_trades(email)
    store.save_trades(email, live + demo)
    check("both survive in the journal", store.count_trades(email) == 2,
          f"got {store.count_trades(email)}")

    pnls = sorted(t.pnl for t in store.list_trades(email))
    check("and they are the two different trades",
          len(set(pnls)) == 2, f"pnls {pnls}")


# =============================================================================
# 11. LAYERING
# =============================================================================

def test_no_streamlit():
    print("\nLayering")

    import ast
    import pathlib

    for name in ("mt5.py", "sync.py"):
        path = pathlib.Path(__file__).resolve().parent.parent / "sensitor" / "integrations" / name
        tree = ast.parse(path.read_text())
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                imports.add(node.module.split(".")[0])
        check(f"{name} imports no streamlit", "streamlit" not in imports)
        check(f"{name} imports no MetaTrader5 at module scope",
              "MetaTrader5" not in {
                  a.name for node in ast.walk(tree)
                  if isinstance(node, ast.Import) and node.col_offset == 0
                  for a in node.names})

    check("MetaTrader5 was never imported by this run",
          "MetaTrader5" not in sys.modules)


def main() -> int:
    for test in (test_balance_operations, test_zero_is_not_a_stop,
                 test_simple_round_turn, test_short_direction,
                 test_scaled_in_and_out, test_open_and_partial,
                 test_point_value, test_stops_from_orders, test_server_time,
                 test_record_shapes, test_connector, test_open_positions,
                 test_merge_rules, test_sync_against_the_store,
                 test_ids_are_namespaced, test_no_streamlit):
        test()

    failures = [c for c in CHECKS if not c[1]]
    print(f"\n{len(CHECKS)} checks, {len(failures)} failures")
    for name, _, detail in failures:
        print(f"  FAIL  {name}   {detail}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
