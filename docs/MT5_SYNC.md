# MetaTrader 5 synchronisation

How the connector works, what it does to your data, and what to check when the
numbers look wrong.

---

## 1. Requirements

| | |
|---|---|
| MetaTrader 5 terminal | running, on the **same machine** as this app |
| `MetaTrader5` Python package | `pip install MetaTrader5` |
| Platform | **Windows only** — MetaQuotes publishes no macOS or Linux build |

The package is not a dependency of this project and is never imported at module
scope. `sensitor/integrations/mt5.py` imports it inside `connect()`, so the
module — and its whole normalisation layer — is importable and testable on any
machine. On macOS or Linux the app runs, the Journal renders, and only the sync
button reports that the package is missing.

## 2. Using it

Journal → **Import from MetaTrader 5**.

| Field | What to put in it |
|---|---|
| Account number / Password / Server | leave blank to use the account already signed in to the terminal |
| Terminal path | only when the terminal is not where MT5 installs it by default |
| **Server UTC offset** | the hours your terminal's Market Watch clock is ahead of UTC |
| History to fetch | days back from today; re-fetching is free |

### The offset is not optional detail

MetaTrader timestamps are the **broker's server clock**, not UTC, and most
brokers run on UTC+2 or UTC+3. Left at zero on a UTC+3 server, every trade lands
three hours late. That does not merely shift a column: the session a trade is
attributed to is decided by its UTC hour, so a third of a book moves into the
wrong bucket and "your best session" becomes a fact about the broker's timezone.
A trade opened at 11:30 London reports as the London/NY overlap instead.

Read the offset off the terminal's own clock rather than assuming — brokers
change it for daylight saving on their own schedule.

## 3. What the connector actually does

### Deals are not trades

MT5 stores **deals**. One round turn is at least two — a `DEAL_ENTRY_IN` and a
`DEAL_ENTRY_OUT` sharing a `position_id`. A position scaled into three times and
closed in two is six. The connector folds them back into one trade:

* entry and exit prices are **volume-weighted** across their side
* the open time is the first entry, the close time is the last exit
* P&L, commission, swap and fees are summed over every deal on the position
* **direction comes from the opening deal** — a long is closed by a sell, so
  reading the side off the exit inverts the entire book

A position whose exits do not yet cover its entries is **not** returned. It has
a result so far, but reporting it as closed would count a running position's
unrealised remainder as a finished outcome.

### Deposits are filtered out

Balance operations — deposits, withdrawals, credits, corrections, bonuses,
commission settlements, interest, dividends, tax — arrive in the same history
stream and every one of them carries a `profit`. A $10,000 deposit imported as a
trade becomes the best trade in the book, the largest win, most of the gross
profit, and it drags expectancy, profit factor, the win rate and the equity
curve with it.

`is_trading_deal()` rejects any deal whose type is at or above `DEAL_TYPE_BALANCE`,
and any deal with no position id. It is the single most consequential line in
the connector.

### A stop of 0.0 is not a stop at zero

MT5 writes `0.0` into `sl` and `tp` to mean "nothing attached". Taken literally,
`abs(entry - 0.0) × size` is a risk the size of the whole notional, and every R
multiple collapses toward zero — a book with no stops at all would report
flawless discipline. Every price from MT5 goes through `_price()`, which maps
`0.0` to `None`, and a trade with no stop is then correctly **excluded** from
every R statistic rather than counted as zero.

### Stops come from orders, and from the first one

Deals carry no stop; orders do. The connector reads the **earliest** order on
each position. A stop moved to break-even an hour into the trade would otherwise
rewrite what the trade risked at entry — and R is defined against the risk taken,
not the risk as last amended.

### R is correct without a contract-size table

This is the subtlest part. MT5 gives volume in **lots** and prices in the
instrument's **quote** terms. `abs(entry - stop) × volume` is therefore a number
in quote units: for EURUSD at one lot, a 50-pip stop comes out as `0.005` rather
than `$500`. Every risk figure built on that is wrong by the contract size, and
wrong again by the quote-to-account exchange rate for anything not quoted in the
account currency.

Rather than look either of those up, the connector derives the factor from the
broker's own arithmetic. The broker already reported what the position made in
account currency, and the price distance it travelled is known:

```
point_value = gross_pnl / (price_distance × volume)
size        = volume × point_value
```

`size` is then stored in **account currency per unit of price**, which makes
`abs(entry - stop) × size` money and R dimensionless. It is self-calibrating,
exact per trade, and correct for a JPY cross on a USD account without a single
conversion.

Worked example, USDJPY, one lot, long 150.00 → 151.00, broker P&L \$662.25,
stop at 149.50:

| | with calibration | without |
|---|---|---|
| risk | \$331.13 | 0.50 |
| R | **2.00** | 1324 |

The lot count is kept in the trade's `raw` payload, so the journal still shows
you the size you entered.

## 4. Re-syncing

**Safe, and designed to be run often.**

*Not duplicating* is handled by the trade id, which is derived from the broker's
own position number and namespaced by account:

```
mt5-51234567-12345
```

The account prefix matters. A position ticket is unique *within* an account, and
the journal's primary key is `(user_email, id)` — so an unprefixed `mt5-12345`
would mean your second account's trade silently replacing your first's.

*Not overwriting* is the harder half. The broker knows the prices; you know why
you took the trade. A sync that wrote the broker's record over the row would
erase your setups, mistakes, emotions, ratings and notes — the entire reason a
journal is worth keeping — and it would do it silently, on a button that looks
read-only.

So the merge is **per field, not per row**:

| Comes from the broker, always | Comes from your journal, always |
|---|---|
| symbol, direction, prices, size | setups, mistakes, timeframe, regime |
| P&L, commission, swap | setup quality, confidence, discipline |
| open and close times | emotions before / during / after |
| stop and target | notes, screenshots |

Entry and exit reasons are taken from the order comment only when you have not
written something there yourself.

One deliberate exception: if the broker now reports a stop for a trade that had
none, it is taken. That is the broker correcting its own record, not an
annotation being lost.

The incremental window starts a few days **before** the last stored close. A
position open across the previous sync's boundary had no closing deal then, and
a window beginning exactly where the last one ended would never pick it up. The
overlap costs nothing because the upsert makes a repeat a no-op.

## 5. Adding another broker

Nothing above the connector knows what MetaTrader is. To add cTrader, Interactive
Brokers or a CSV export, write a class with:

```python
def account(self) -> BrokerAccount: ...
def fetch_trades(self, since, until=None) -> list[Trade]: ...
def fetch_open_positions(self) -> list[Trade]: ...   # optional
```

and hand it to `sync.sync_trades()`. The merge rules, the idempotency, the
journal protection and every page above are unchanged. `sync.py` deliberately
imports nothing from `mt5.py`.

## 6. Testing

`tests/test_mt5_connector.py` — 128 checks, no terminal, no Windows, no network.
`FakeTerminal` implements the methods the connector calls, including MT5's
unhelpful parts: `initialize` returns a bool rather than raising, failed calls
return `None`, and `account_info()` returns `None` when the terminal is open but
signed out. The normalisation is checked against hand-written deal records whose
answers were worked out by hand.

```
python tests/test_mt5_connector.py
```

The suite also asserts that neither `mt5.py` nor `sync.py` imports Streamlit, and
that `MetaTrader5` is never imported at module scope.

## 7. When the numbers look wrong

| Symptom | Almost always |
|---|---|
| Every trade is 2–3 hours late; sessions look wrong | the server UTC offset is still 0 |
| One enormous winning trade you do not recognise | a deposit got through — check it is not a `source: manual` row you typed |
| R is empty for most trades | those trades had no stop attached; `stop_coverage` on the Risk page says how many |
| R is absurdly large or near zero | the position closed at its entry price, so no point value could be derived |
| Your notes disappeared after a sync | should be impossible — `tests/test_mt5_connector.py::test_merge_rules` asserts it. Please report it |
| "no account is logged in" | the terminal is open but signed out; MT5 then returns empty tuples from every call, which is why this is an error rather than an empty journal |
| The package will not install | it is Windows-only. Export to CSV, or run the terminal in a Windows VM |
