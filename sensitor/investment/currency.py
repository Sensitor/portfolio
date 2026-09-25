"""
Quote currencies, and converting a price history into one base currency.

**Why this exists.** Until Euronext was added, every instrument in the app was
quoted in dollars, so "the portfolio returned 14%" needed no qualification. The
moment LVMH sits next to Apple that stops being true: their price series are in
different money, and a naive `pct_change()` over the pair computes a return no
investor could have earned. The euro/dollar rate moved by roughly a fifth
between 2021 and 2023 — larger than most of the risk figures this app reports.

So prices are converted **before** returns are derived, never after. That
ordering is the whole point:

    converted = price_eur × EURUSD           then  pct_change()   ← correct
    return_eur = pct_change(price_eur)       then  × something    ← wrong

The second is wrong because a return and an FX rate compound, they do not add:
the true dollar return is `(1+r_local)(1+r_fx) - 1`. Converting the level series
gets that for free and cannot be got subtly wrong later.

**Nothing here does I/O.** The FX series is passed in. That keeps the module
importable from a test with no network — which is the only way this code got
verified at all, since the environment it was written in cannot reach Yahoo.
"""

from __future__ import annotations

import pandas as pd

# =============================================================================
# WHAT A TICKER IS QUOTED IN
# =============================================================================

# Yahoo exchange suffix -> quote currency. Only the suffixes this app is likely
# to see; an unknown suffix falls through to `DEFAULT_CURRENCY` rather than
# guessing, and `is_known_suffix` lets a caller find out which happened.
SUFFIX_CURRENCY: dict[str, str] = {
    # Euronext and the euro area
    ".PA": "EUR",    # Paris
    ".AS": "EUR",    # Amsterdam
    ".BR": "EUR",    # Brussels
    ".LS": "EUR",    # Lisbon
    ".IR": "EUR",    # Dublin
    ".MI": "EUR",    # Milan
    ".MC": "EUR",    # Madrid
    ".DE": "EUR",    # Xetra
    ".F": "EUR",     # Frankfurt
    ".VI": "EUR",    # Vienna
    ".HE": "EUR",    # Helsinki
    # Elsewhere
    ".L": "GBp",     # London — quoted in PENCE, not pounds. See below.
    ".SW": "CHF",
    ".ST": "SEK",
    ".OL": "NOK",
    ".CO": "DKK",
    ".TO": "CAD",
    ".V": "CAD",
    ".AX": "AUD",
    ".NZ": "NZD",
    ".T": "JPY",
    ".HK": "HKD",
    ".SI": "SGD",
    ".SA": "BRL",
}

DEFAULT_CURRENCY = "USD"

# The currencies a portfolio can be denominated in. Deliberately short: each one
# needs a rate against every quote currency actually held, and offering a base
# the app cannot source a rate for is offering a failure.
BASE_CURRENCIES = ("USD", "EUR", "GBP", "CHF", "CAD")

CURRENCY_SYMBOL = {
    "USD": "$", "EUR": "€", "GBP": "£", "CHF": "CHF ", "CAD": "CA$",
    "JPY": "¥", "SEK": "kr ", "NOK": "kr ", "DKK": "kr ", "AUD": "A$",
    "NZD": "NZ$", "HKD": "HK$", "SGD": "S$", "BRL": "R$",
}

# London quotes in pence. A price of 2,450 is £24.50, and treating it as pounds
# overstates the position by a factor of a hundred — which does not show up as
# an error, it shows up as a portfolio that looks fine and is wrong. The unit is
# carried as its own pseudo-currency so the divide happens in exactly one place.
PENCE = {"GBp": ("GBP", 100.0), "ZAc": ("ZAR", 100.0), "ILA": ("ILS", 100.0)}


def quote_currency(ticker: str, overrides: dict | None = None) -> str:
    """
    The currency a ticker's price is expressed in.

    `overrides` wins, then the exchange suffix, then the default. Crypto pairs
    (`BTC-USD`) name their currency in the symbol, and an FX symbol (`EURUSD=X`)
    is not an instrument anyone holds — it is reported as its own quote so a
    caller can refuse it rather than converting a rate by a rate.
    """
    if not ticker:
        return DEFAULT_CURRENCY

    symbol = ticker.strip().upper()
    if overrides:
        # Case-insensitive on the caller's table, because a ticker typed by hand
        # arrives in whatever case the person used.
        for key, value in overrides.items():
            if key.upper() == symbol:
                return value

    if symbol.endswith("=X"):
        return "FX"

    # Crypto: the pair's second leg is the quote currency.
    if "-" in symbol:
        tail = symbol.rsplit("-", 1)[-1]
        if len(tail) == 3 and tail.isalpha():
            return tail

    for suffix, currency in SUFFIX_CURRENCY.items():
        if symbol.endswith(suffix.upper()):
            return currency

    return DEFAULT_CURRENCY


def is_known_suffix(ticker: str) -> bool:
    """Whether the ticker carries an exchange suffix this module recognises."""
    symbol = (ticker or "").strip().upper()
    return any(symbol.endswith(s.upper()) for s in SUFFIX_CURRENCY)


def settlement_currency(quote: str) -> tuple[str, float]:
    """
    The real currency behind a quote unit, and the divisor to reach it.

    `("GBp")` is pence, so it returns `("GBP", 100)`. Everything else is itself
    over one.
    """
    if quote in PENCE:
        return PENCE[quote]
    return quote, 1.0


def currency_symbol(code: str) -> str:
    """A prefix for display. An unknown code is shown as itself, not guessed."""
    if not code:
        return "$"
    return CURRENCY_SYMBOL.get(code.upper(), f"{code.upper()} ")


# =============================================================================
# WHICH RATE TO ASK FOR
# =============================================================================

def fx_candidates(quote: str, base: str) -> list[tuple[str, bool]]:
    """
    The Yahoo FX symbols that would convert `quote` into `base`, best first.

    Each entry is `(symbol, invert)`. `EURUSD=X` is dollars per euro, so euros
    become dollars by multiplying and dollars become euros by dividing — the
    same series either way, which is why `invert` travels with it rather than
    the caller being expected to remember the convention.

    Two candidates are returned because Yahoo carries both directions for major
    pairs but not reliably for every cross; a caller tries them in order.
    """
    settled, _ = settlement_currency(quote)
    settled, base = settled.upper(), base.upper()
    if settled == base:
        return []
    return [(f"{settled}{base}=X", False), (f"{base}{settled}=X", True)]


def pairs_needed(tickers, base: str, overrides: dict | None = None) -> dict[str, str]:
    """
    Quote currency -> the first FX symbol to try, for a whole portfolio.

    Returns only the currencies that actually need converting, so a portfolio
    already denominated in its base asks for nothing.
    """
    needed: dict[str, str] = {}
    for ticker in tickers:
        quote = quote_currency(ticker, overrides)
        if quote == "FX":
            continue
        candidates = fx_candidates(quote, base)
        if candidates:
            needed[quote] = candidates[0][0]
    return needed


# =============================================================================
# CONVERSION
# =============================================================================

# How much of the price history a rate must actually cover before it is used.
# Below this the series is refused rather than back-filled: back-filling invents
# a constant exchange rate for the uncovered stretch, and a made-up rate at the
# start of the window silently rewrites the total return.
MIN_COVERAGE = 0.95


def naive_dates(obj):
    """
    Put a Series or DataFrame onto naive, midnight-normalised dates.

    Every join in this module and in the analyzer goes through here first, and
    that is not tidiness — it is the difference between working and raising.

    Yahoo returns **timezone-aware** timestamps, and the offset depends on the
    instrument: a Paris share comes back in Europe/Paris, a US share in
    America/New_York, a crypto pair in UTC. Two consequences, both of which
    reached production:

    * Multiplying a tz-aware price series by a tz-naive rate series raises
      `Cannot join tz-naive with tz-aware DatetimeIndex`. A portfolio of LVMH
      and bitcoin crashed on exactly that.
    * Even between two tz-aware series, different offsets mean the same trading
      day carries different timestamps, so a join intersects on almost nothing
      and the frame comes back full of holes.

    Dropping the clock and keeping the date fixes both, and loses nothing: this
    app works in daily closes, where the time of day is an artefact of the
    exchange, not information.
    """
    if obj is None or len(obj) == 0:
        return obj
    out = obj.copy()
    index = pd.DatetimeIndex(out.index)
    if index.tz is not None:
        # `tz_localize(None)` — drop the offset and keep the local wall time —
        # not `tz_convert(None)`, which would move to UTC first.
        #
        # A daily bar is stamped at midnight in the exchange's own timezone, so
        # the local date *is* the trading date. Converting to UTC turns a Paris
        # session stamped 00:00+01:00 into 23:00 the previous day, and the whole
        # French half of a portfolio slides back by one day against the American
        # half. That is worse than the crash this function was written to fix,
        # because it does not raise.
        index = index.tz_localize(None)
    out.index = index.normalize()
    return out[~out.index.duplicated(keep="last")].sort_index()


def align_rate(rate: pd.Series, index: pd.Index) -> pd.Series | None:
    """
    Put an FX series onto a price series' dates.

    Forward-filled, never back-filled. Currency markets and stock exchanges keep
    different holidays, so a few gaps are ordinary and the last known rate is the
    honest answer for them. A gap *before* the first quoted rate is not
    ordinary — there is no last known rate — so if that leaves the series short
    of `MIN_COVERAGE` this returns None and the caller reports a missing rate
    instead of pricing part of the window at a rate nobody quoted.
    """
    if rate is None or len(rate) == 0 or index is None or len(index) == 0:
        return None

    series = naive_dates(rate)

    target = pd.DatetimeIndex(index)
    if target.tz is not None:
        target = target.tz_localize(None)
    target = target.normalize()

    aligned = series.reindex(series.index.union(target)).ffill().reindex(target)
    covered = float(aligned.notna().mean()) if len(aligned) else 0.0
    if covered < MIN_COVERAGE:
        return None
    return aligned


def convert_prices(prices: pd.DataFrame, base: str, rates: dict,
                   overrides: dict | None = None) -> tuple[pd.DataFrame, dict]:
    """
    Convert a price frame into one base currency.

    `rates` maps a quote currency to its series against `base`, already oriented
    so that `price × rate` is the converted price. A currency with no usable
    rate has its columns **dropped**, not passed through: a column left in its
    own currency would be added to the others by the weighting step, and the
    resulting portfolio return would be a number with no meaning that nothing
    downstream could detect.

    Returns the converted frame and a report naming what was converted, what was
    dropped and why — the caller is expected to show the report, because a
    portfolio quietly missing its French half is worse than one that fails.
    """
    report = {"base": base, "converted": {}, "unconverted": [], "dropped": {},
              "pence": []}
    if prices is None or prices.empty:
        return prices, report

    # The rates arriving here are naive-dated; the prices may not be. Normalise
    # once, at the top, so the multiplication below cannot be the place where a
    # timezone mismatch surfaces.
    prices = naive_dates(prices)

    out = {}
    for column in prices.columns:
        quote = quote_currency(str(column), overrides)
        settled, divisor = settlement_currency(quote)
        series = prices[column]

        if divisor != 1.0:
            # Pence (or cents) to the major unit, before any rate is applied.
            series = series / divisor
            report["pence"].append(str(column))

        if settled.upper() == base.upper():
            out[column] = series
            report["unconverted"].append(str(column))
            continue

        rate = rates.get(quote) if quote in rates else rates.get(settled)
        aligned = align_rate(rate, series.index) if rate is not None else None
        if aligned is None:
            report["dropped"][str(column)] = settled
            continue

        out[column] = series * aligned
        report["converted"][str(column)] = settled

    if not out:
        return prices.iloc[:, :0], report
    return pd.DataFrame(out, index=prices.index), report


def mixed_currencies(tickers, overrides: dict | None = None) -> list[str]:
    """The distinct settlement currencies a set of tickers is quoted in."""
    seen = []
    for ticker in tickers:
        quote = quote_currency(ticker, overrides)
        if quote == "FX":
            continue
        settled, _ = settlement_currency(quote)
        if settled not in seen:
            seen.append(settled)
    return seen
