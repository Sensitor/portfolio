"""
Currency conversion, over synthetic prices and synthetic exchange rates.

Everything here runs with no network, which is not a convenience — it is the
only reason this code is checked at all. The environment it was written in has
no route to any market data host, so a test that needed Yahoo would be a test
that never ran.

The property the suite is really defending is the *order of operations*:
prices are converted and then differenced, never differenced and then adjusted.
A return and an exchange-rate move compound, they do not add, and the two
orderings differ by the cross term — small over a day, and the size of a year's
performance over a year.

Run with:  python tests/test_currency.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# The layering rule, asserted rather than assumed.
sys.modules["streamlit"] = None  # type: ignore[assignment]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from sensitor.investment import assets  # noqa: E402
from sensitor.investment import currency as FX  # noqa: E402
from sensitor.investment.portfolio import PortfolioAnalyzer  # noqa: E402

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok    {name}")
    else:
        FAILURES.append(f"{name}: {detail}")
        print(f"  FAIL  {name}  {detail}")


def close(a, b, tol=1e-9) -> bool:
    return abs(float(a) - float(b)) <= tol


# =============================================================================
# FIXTURES
# =============================================================================

DAYS = pd.bdate_range("2024-01-01", periods=120)


def ramp(start: float, drift: float, n: int = len(DAYS), seed: int = 0) -> pd.Series:
    """A deterministic price path. Seeded, so a failure is reproducible."""
    rng = np.random.default_rng(seed)
    steps = 1 + drift + rng.normal(0, 0.004, n)
    return pd.Series(start * np.cumprod(steps), index=DAYS[:n])


def loaders(prices: dict, rates: dict):
    """Price and FX loaders over dictionaries, in place of Yahoo."""
    def price_loader(ticker, start):
        series = prices.get(ticker)
        return None if series is None else series.rename(ticker)

    def fx_loader(pair, start):
        return rates.get(pair)

    return price_loader, fx_loader


# =============================================================================
# WHAT A TICKER IS QUOTED IN
# =============================================================================

def test_quote_currency() -> None:
    print("\nQuote currency")

    check("a Paris suffix is euros", FX.quote_currency("MC.PA") == "EUR")
    check("so is Amsterdam", FX.quote_currency("ASML.AS") == "EUR")
    check("a bare US ticker is dollars", FX.quote_currency("AAPL") == "USD")
    check("lower case resolves the same", FX.quote_currency("mc.pa") == "EUR")
    check("a crypto pair names its own quote", FX.quote_currency("BTC-USD") == "USD")
    check("and a euro-quoted one too", FX.quote_currency("BTC-EUR") == "EUR")
    check("an unknown suffix falls back to the default",
          FX.quote_currency("XYZ.ZZ") == "USD")
    check("an FX symbol is not an instrument", FX.quote_currency("EURUSD=X") == "FX")

    # The trap this whole pseudo-currency exists for.
    check("London is pence, not pounds", FX.quote_currency("VOD.L") == "GBp")
    check("and pence carry their divisor", FX.settlement_currency("GBp") == ("GBP", 100.0))
    check("a real currency divides by one", FX.settlement_currency("EUR") == ("EUR", 1.0))

    check("the catalogue's own table wins over the suffix",
          FX.quote_currency("MC.PA", {"MC.PA": "USD"}) == "USD")
    check("every Euronext entry is declared as euros",
          set(assets.QUOTE_CURRENCY.values()) == {"EUR"},
          str(set(assets.QUOTE_CURRENCY.values())))


def test_pairs() -> None:
    print("\nWhich rate to ask for")

    check("euros into dollars is EURUSD, upright",
          FX.fx_candidates("EUR", "USD")[0] == ("EURUSD=X", False))
    check("dollars into euros is the same series, inverted",
          FX.fx_candidates("USD", "EUR")[0] == ("USDEUR=X", False)
          and FX.fx_candidates("USD", "EUR")[1] == ("EURUSD=X", True))
    check("a currency needs no rate against itself", FX.fx_candidates("EUR", "EUR") == [])
    check("pence route through pounds",
          FX.fx_candidates("GBp", "USD")[0] == ("GBPUSD=X", False))

    needed = FX.pairs_needed(["AAPL", "MC.PA", "SPY"], "USD", assets.QUOTE_CURRENCY)
    check("only the foreign currency is requested", needed == {"EUR": "EURUSD=X"}, str(needed))
    check("a portfolio in its own base asks for nothing",
          FX.pairs_needed(["AAPL", "SPY"], "USD", assets.QUOTE_CURRENCY) == {})

    check("the distinct currencies of a mixed book are reported",
          FX.mixed_currencies(["AAPL", "MC.PA", "VOD.L"], assets.QUOTE_CURRENCY)
          == ["USD", "EUR", "GBP"])


# =============================================================================
# ALIGNING A RATE ONTO A PRICE SERIES
# =============================================================================

def test_alignment() -> None:
    print("\nAligning a rate")

    prices = ramp(100, 0.0005, seed=1)

    # A rate quoted on fewer days than the exchange traded: ordinary, and the
    # last known rate is the honest answer.
    sparse = pd.Series(1.10, index=DAYS[::3])
    aligned = FX.align_rate(sparse, prices.index)
    check("a sparse rate forward-fills onto every price date",
          aligned is not None and len(aligned) == len(prices) and aligned.notna().all())

    # A rate that starts inside the window has no earlier value to carry back.
    late = pd.Series(1.10, index=DAYS[60:])
    check("a rate starting mid-window is refused rather than back-filled",
          FX.align_rate(late, prices.index) is None)

    # Timezone-aware rates are what yfinance actually returns.
    tz_aware = pd.Series(1.10, index=pd.DatetimeIndex(DAYS).tz_localize("UTC"))
    check("a timezone-aware rate still aligns",
          FX.align_rate(tz_aware, prices.index) is not None)

    check("an empty rate aligns to nothing", FX.align_rate(pd.Series(dtype=float),
                                                           prices.index) is None)


# =============================================================================
# THE CONVERSION ITSELF
# =============================================================================

def test_convert_prices() -> None:
    print("\nConverting prices")

    eur = ramp(700, 0.0004, seed=2)
    usd = ramp(180, 0.0004, seed=3)
    rate = pd.Series(np.linspace(1.05, 1.25, len(DAYS)), index=DAYS)

    frame = pd.DataFrame({"MC.PA": eur, "AAPL": usd})
    out, report = FX.convert_prices(frame, "USD", {"EUR": rate}, assets.QUOTE_CURRENCY)

    check("the euro line is multiplied by the rate",
          close(out["MC.PA"].iloc[10], eur.iloc[10] * rate.iloc[10], 1e-6))
    check("the dollar line is untouched", close(out["AAPL"].iloc[10], usd.iloc[10], 1e-9))
    check("the report names what was converted", report["converted"] == {"MC.PA": "EUR"})
    check("and what needed nothing", report["unconverted"] == ["AAPL"])
    check("and drops nothing when the rate is there", report["dropped"] == {})

    # Pence. A £24.50 share quoted as 2450.
    pence = pd.Series(2450.0, index=DAYS)
    gbp_rate = pd.Series(1.27, index=DAYS)
    out2, report2 = FX.convert_prices(pd.DataFrame({"VOD.L": pence}), "USD",
                                      {"GBp": gbp_rate})
    check("pence become pounds before the rate is applied",
          close(out2["VOD.L"].iloc[0], 24.50 * 1.27, 1e-9),
          f"got {out2['VOD.L'].iloc[0]}")
    check("and the division is reported", report2["pence"] == ["VOD.L"])

    # No rate: the column goes, and says so.
    out3, report3 = FX.convert_prices(frame, "USD", {}, assets.QUOTE_CURRENCY)
    check("a column with no rate is dropped, not passed through",
          "MC.PA" not in out3.columns and "AAPL" in out3.columns)
    check("and the drop is reported with its currency",
          report3["dropped"] == {"MC.PA": "EUR"}, str(report3["dropped"]))


def test_compounding() -> None:
    """
    The reason prices are converted rather than returns.

    A 1% local gain on a day the euro gained 1% is a 2.01% dollar gain, not 2%.
    The cross term is the whole argument for doing it in this order, so it is
    asserted numerically rather than described in a comment.
    """
    print("\nReturns compound with the rate")

    index = pd.bdate_range("2024-01-01", periods=3)
    eur_price = pd.Series([100.0, 101.0, 101.0], index=index)
    rate = pd.Series([1.00, 1.01, 1.01], index=index)

    out, _ = FX.convert_prices(pd.DataFrame({"X.PA": eur_price}), "USD", {"EUR": rate})
    converted_return = out["X.PA"].pct_change().iloc[1]

    local_return = eur_price.pct_change().iloc[1]        # 0.01
    fx_return = rate.pct_change().iloc[1]                # 0.01
    compounded = (1 + local_return) * (1 + fx_return) - 1   # 0.0201
    added = local_return + fx_return                        # 0.0200

    check("the converted return is the compounded one",
          close(converted_return, compounded, 1e-12),
          f"{converted_return!r} vs {compounded!r}")
    check("which is not the sum of the two", not close(compounded, added, 1e-12))
    check("and the difference is the cross term",
          close(compounded - added, local_return * fx_return, 1e-12))


# =============================================================================
# THE ANALYZER
# =============================================================================

def test_analyzer_unchanged_for_dollars() -> None:
    """
    A dollar portfolio in dollars must behave exactly as it did before any of
    this existed. The feature is worthless if it moves numbers nobody asked it
    to touch.
    """
    print("\nA dollar book is untouched")

    prices = {"AAPL": ramp(180, 0.0006, seed=4), "SPY": ramp(450, 0.0004, seed=5)}
    price_loader, fx_loader = loaders(prices, {})

    analyzer = PortfolioAnalyzer(["AAPL", "SPY"], {"AAPL": 0.5, "SPY": 0.5},
                                 base_currency="USD")
    ok = analyzer.fetch_data(price_loader=price_loader, fx_loader=fx_loader)

    expected = pd.DataFrame(prices).pct_change().dropna() @ np.array([0.5, 0.5])

    check("it loads", ok)
    check("nothing is reported as shortening the window",
          analyzer.window_report["shortened"] is False)
    check("no rate was requested", analyzer.currency_report["converted"] == {})
    check("the returns are the unconverted ones",
          np.allclose(analyzer.portfolio_returns.values, expected.values))


def test_analyzer_converts() -> None:
    print("\nA mixed book is converted")

    eur = ramp(700, 0.0004, seed=6)
    usd = ramp(180, 0.0006, seed=7)
    rate = pd.Series(np.linspace(1.05, 1.25, len(DAYS)), index=DAYS)

    price_loader, fx_loader = loaders({"MC.PA": eur, "AAPL": usd},
                                      {"EURUSD=X": rate})

    analyzer = PortfolioAnalyzer(["MC.PA", "AAPL"], {"MC.PA": 0.5, "AAPL": 0.5},
                                 base_currency="USD")
    ok = analyzer.fetch_data(price_loader=price_loader, fx_loader=fx_loader)

    check("it loads", ok)
    check("both assets survive", set(analyzer.tickers) == {"MC.PA", "AAPL"})
    check("the euro line was converted",
          analyzer.currency_report["converted"] == {"MC.PA": "EUR"})
    check("the stored price is in dollars",
          close(analyzer.data["MC.PA"].iloc[5], eur.iloc[5] * rate.iloc[5], 1e-6))

    # The same book, priced in euros instead, must differ — if the base currency
    # changed nothing, nothing would be converting.
    price_loader2, fx_loader2 = loaders({"MC.PA": eur, "AAPL": usd},
                                        {"USDEUR=X": 1.0 / rate})
    in_euros = PortfolioAnalyzer(["MC.PA", "AAPL"], {"MC.PA": 0.5, "AAPL": 0.5},
                                 base_currency="EUR")
    in_euros.fetch_data(price_loader=price_loader2, fx_loader=fx_loader2)
    check("the euro-based book converted the dollar line instead",
          in_euros.currency_report["converted"] == {"AAPL": "USD"})

    total_usd = float((1 + analyzer.portfolio_returns).prod())
    total_eur = float((1 + in_euros.portfolio_returns).prod())
    check("and the two bases give different total returns",
          not close(total_usd, total_eur, 1e-6),
          f"USD {total_usd:.4f} vs EUR {total_eur:.4f}")


def test_analyzer_inverted_pair() -> None:
    """Yahoo carries `EURUSD=X` but not always the reverse; the fallback inverts."""
    print("\nThe inverted fallback")

    eur = ramp(700, 0.0004, seed=8)
    usd = ramp(180, 0.0006, seed=9)
    rate = pd.Series(np.linspace(1.05, 1.25, len(DAYS)), index=DAYS)

    # Only the EUR->USD series exists; a euro-based portfolio must invert it.
    price_loader, fx_loader = loaders({"MC.PA": eur, "AAPL": usd},
                                      {"EURUSD=X": rate})
    analyzer = PortfolioAnalyzer(["MC.PA", "AAPL"], {"MC.PA": 0.5, "AAPL": 0.5},
                                 base_currency="EUR")
    ok = analyzer.fetch_data(price_loader=price_loader, fx_loader=fx_loader)

    check("it loads from the inverted pair", ok)
    check("the dollar line is divided by the rate",
          close(analyzer.data["AAPL"].iloc[5], usd.iloc[5] / rate.iloc[5], 1e-6),
          f"got {analyzer.data['AAPL'].iloc[5]}")


def test_analyzer_drops_without_a_rate() -> None:
    print("\nA missing rate drops the asset and says so")

    eur = ramp(700, 0.0004, seed=10)
    usd = ramp(180, 0.0006, seed=11)
    price_loader, fx_loader = loaders({"MC.PA": eur, "AAPL": usd}, {})  # no rates at all

    errors = []
    analyzer = PortfolioAnalyzer(["MC.PA", "AAPL"], {"MC.PA": 0.3, "AAPL": 0.7},
                                 base_currency="USD")
    ok = analyzer.fetch_data(price_loader=price_loader, fx_loader=fx_loader,
                             on_error=lambda t, m: errors.append((t, m)))

    check("the portfolio still loads", ok)
    check("the unconvertible asset is gone", analyzer.tickers == ["AAPL"])
    check("the surviving weight is renormalised to one",
          close(sum(analyzer.weights.values()), 1.0, 1e-12))
    check("and it is reported by name",
          any("MC.PA" in str(t) for t, _ in errors), str(errors))
    check("the report says which currency failed",
          analyzer.currency_report["dropped"] == {"MC.PA": "EUR"})

    # Everything unconvertible: a failure, not an empty portfolio that renders.
    only_eur, only_fx = loaders({"MC.PA": eur}, {})
    empty = PortfolioAnalyzer(["MC.PA"], {"MC.PA": 1.0}, base_currency="USD")
    check("a book with nothing convertible fails rather than returning empty",
          empty.fetch_data(price_loader=only_eur, fx_loader=only_fx) is False)


def test_common_window() -> None:
    """
    A recently listed share must not be credited with a calm it never had.

    Before this, missing prices were back-filled: an asset that floated a year
    into the window got a constant price for the year before, which is a run of
    zero returns. Its volatility, its drawdown and its correlation with
    everything else all came out too low — the direction that makes a portfolio
    look better diversified than it is.
    """
    print("\nThe shared window")

    from sensitor.investment.portfolio import _common_window

    old = ramp(100, 0.0004, seed=20)
    young = ramp(10, 0.0030, n=60, seed=21)
    young.index = DAYS[len(DAYS) - 60:]

    frame = pd.concat([old.rename("OLD"), young.rename("NEW.PA")], axis=1)
    trimmed, report = _common_window(frame)

    check("the frame starts where the newest listing does",
          trimmed.index[0] == young.index[0], str(trimmed.index[0]))
    check("and says which holding set the start",
          report["limited_by"] == "NEW.PA", str(report["limited_by"]))
    check("nothing before the listing survives", len(trimmed) == 60, str(len(trimmed)))
    check("no price was invented",
          trimmed["NEW.PA"].notna().all() and trimmed["OLD"].notna().all())

    # The property that matters: a back-filled series would have produced a run
    # of exact zeros at the front.
    returns = trimmed.pct_change().dropna()
    zeros = int((returns["NEW.PA"] == 0).sum())
    check("and the young asset has no invented flat stretch", zeros == 0, f"{zeros} zero returns")

    analyzer = PortfolioAnalyzer(["OLD", "NEW.PA"], {"OLD": 0.5, "NEW.PA": 0.5},
                                 base_currency="USD")
    price_loader, fx_loader = loaders(
        {"OLD": old, "NEW.PA": young},
        {"EURUSD=X": pd.Series(1.10, index=DAYS)})
    ok = analyzer.fetch_data(price_loader=price_loader, fx_loader=fx_loader)
    check("the analyzer loads on the shared window", ok)
    check("and reports what shortened it",
          analyzer.window_report["limited_by"] == "NEW.PA")
    check("and that it was shortened at all",
          analyzer.window_report["shortened"] is True)
    # The comparison that makes the point: the same data handled the old way.
    back_filled = frame.ffill().bfill().pct_change().dropna()
    honest = float(analyzer.returns["NEW.PA"].std())
    diluted = float(back_filled["NEW.PA"].std())
    # Strictly greater, not greater by some factor: how far the back-filled
    # figure falls depends on how much of the window the asset was absent for,
    # and asserting a ratio would be asserting a property of the fixture.
    check("the young asset's volatility is not diluted by invented history",
          honest > diluted,
          f"honest {honest:.5f} vs back-filled {diluted:.5f}")
    check("because the back-filled version invented a flat stretch",
          int((back_filled["NEW.PA"] == 0).sum()) >= 50,
          str(int((back_filled["NEW.PA"] == 0).sum())))


def test_symbol_resolution() -> None:
    print("\nResolving what somebody typed")

    check("a company name resolves", assets.resolve_symbol("LVMH") == "MC.PA")
    check("case and accents do not matter", assets.resolve_symbol("hermes") == "RMS.PA")
    check("the new name of Capital B resolves",
          assets.resolve_symbol("capital b") == "ALTBG.PA")
    check("so does the old one",
          assets.resolve_symbol("The Blockchain Group") == "ALTBG.PA")
    check("a bare mnemonic resolves", assets.resolve_symbol("altbg") == "ALTBG.PA")
    check("a full symbol passes through", assets.resolve_symbol("MC.PA") == "MC.PA")
    check("nonsense resolves to nothing, not to a guess",
          assets.resolve_symbol("qwertyuiop") is None)
    check("a US ticker is not claimed by the Paris table",
          assets.resolve_symbol("AAPL") is None)

    check("search finds a name by fragment",
          ("LVMH (MC.PA)", "MC.PA") in assets.search_paris("lvm"))
    check("search on nothing returns nothing", assets.search_paris("   ") == [])

    check("Capital B is catalogued as illiquid",
          assets.ASSET_INFO["ALTBG.PA"]["liquidity"] <= 40)
    check("and as very high risk",
          assets.ASSET_INFO["ALTBG.PA"]["risk_level"] == "Very High")
    check("every Paris entry has a French description",
          all(info.get("description_fr") for info in assets.EURONEXT_PARIS.values()))
    check("and a sector the mapping knows",
          all(t in assets.SECTOR_MAPPING for t in assets.EURONEXT_PARIS))

    # Every single name was booked as large cap until Euronext Growth arrived.
    from sensitor.investment import xray

    def cap(ticker):
        return xray.resolve_profile(ticker, assets.ASSET_INFO,
                                    assets.SECTOR_MAPPING,
                                    assets.GEOGRAPHY_MAPPING)["market_cap"]

    check("a Euronext Growth small cap is not booked as large cap",
          cap("ALTBG.PA") == {"Small Cap": 1.0}, str(cap("ALTBG.PA")))
    check("a mid cap is its own bucket", cap("RNO.PA") == {"Mid Cap": 1.0})
    check("a CAC 40 name is still large cap", cap("MC.PA") == {"Large Cap": 1.0})
    check("and a ticker with no declared bucket keeps the old default",
          cap("AAPL") == {"Large Cap": 1.0})
    check("the French geography resolves",
          xray.resolve_profile("MC.PA", assets.ASSET_INFO, assets.SECTOR_MAPPING,
                               assets.GEOGRAPHY_MAPPING)["geography"] == {"France": 1.0})


def main() -> int:
    test_quote_currency()
    test_pairs()
    test_alignment()
    test_convert_prices()
    test_compounding()
    test_analyzer_unchanged_for_dollars()
    test_analyzer_converts()
    test_analyzer_inverted_pair()
    test_analyzer_drops_without_a_rate()
    test_common_window()
    test_symbol_resolution()

    total = sum(1 for _ in FAILURES)
    print(f"\n{total} failures")
    for failure in FAILURES:
        print(f"  - {failure}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
