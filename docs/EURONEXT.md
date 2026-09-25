# Euronext Paris

French shares and euro-quoted trackers, and what adding them does to the rest of
the numbers.

---

## 1. What is in the catalogue

Thirty-one CAC 40 names, three euro-quoted trackers, and Capital B on Euronext
Growth. They appear under **Paris — CAC 40** and **Paris — ETFs & Growth** in
Build → Browse, and the search box resolves company names:

| You type | You get |
|---|---|
| `lvmh`, `louis vuitton`, `vuitton`, `mc` | `MC.PA` |
| `capital b`, `the blockchain group`, `altbg` | `ALTBG.PA` |
| `total`, `totalenergies` | `TTE.PA` |
| `socgen`, `société générale` | `GLE.PA` |
| `msci world`, `cw8` | `CW8.PA` |

Matching is exact, not fuzzy. A near miss resolves to nothing rather than to the
wrong company — a portfolio quietly containing a share you did not choose is
worse than a search that finds nothing, because every figure afterwards is about
that share.

Anything not in the catalogue can still be typed as a Yahoo symbol directly:
the Euronext mnemonic plus `.PA`, so Air France-KLM is `AF.PA`.

### The symbols have not been checked against Yahoo

The environment this was written in has no network route to any market data
host, so every symbol here follows Yahoo's documented convention and none of
them was confirmed to return data. The app reports by name any symbol that
fails to download, so a wrong one is visible the first time you use it rather
than silently missing.

To check one before relying on it:

```python
import yfinance as yf
print(yf.Ticker("ALTBG.PA").history(period="1mo").tail())
```

An empty frame means the symbol is wrong or the listing has moved. Please open
an issue with the right one.

---

## 2. Capital B

`ALTBG.PA`, formerly The Blockchain Group. It is catalogued deliberately
unlike the CAC 40 names:

* **liquidity 30** out of 100, against 88 for LVMH. The health score weights
  liquidity at 25%, so a large position in it will visibly pull the score down.
  That is the intended behaviour: a position you cannot exit in a falling market
  is not the size you think it is.
* **risk level "Very High"**, and the description says why — the balance sheet
  holds bitcoin and issuance funds more of it, so the share is a leveraged claim
  on bitcoin rather than a French small cap that happens to be in the sector.

Expect its drawdowns to dominate any portfolio it is more than a few percent of.
The app will tell you that through the concentration and risk-contribution
figures; it is worth looking at them before sizing.

---

## 3. Currency

This is the part that changes numbers you already had.

Euronext quotes in euros. Everything else in the catalogue — SPY, Apple,
bitcoin — quotes in dollars. A portfolio holding both is holding two different
kinds of money, and adding them together without a rate produces a return
nobody earned.

**The app converts prices into one base currency before computing any return.**
The currency is chosen in the sidebar, under Analysis Mode. Changing it drops
the current analysis and re-runs it, because the figures genuinely differ: a
euro investor and a dollar investor holding the same shares did not earn the
same thing.

### Why prices and not returns

A local return and an exchange-rate move **compound**, they do not add:

```
true return in base = (1 + local return) × (1 + fx return) − 1
```

The cross term is small over a day and the size of a year's performance over a
year. Converting the price level and differencing afterwards gets it right by
construction; adjusting a return afterwards is where the cross term goes
missing. `tests/test_currency.py` asserts the difference numerically rather than
describing it.

### What the app tells you

* Converted lines are named in a caption under the overview, with the currency
  they came from.
* An asset whose exchange rate could not be loaded is **removed from the
  portfolio** and named in red, on every page. It is not passed through in its
  own currency: one unconverted column silently added to the others makes every
  figure on the page meaningless, and nothing downstream could detect it.
* Rates are forward-filled across days an exchange was shut and a currency
  market was not. They are never back-filled — a made-up rate before the first
  quote would rewrite the start of the window, so a rate that does not cover at
  least 95% of the price history is refused instead.

### Two traps this handles

**London is quoted in pence.** A `.L` price of 2,450 is £24.50. Treated as
pounds it overstates the position a hundredfold, and nothing about the resulting
portfolio looks wrong. The quote unit `GBp` carries its own divisor and is
converted to pounds before any rate is applied.

**A euro-quoted US tracker is still dollar risk.** `ESE.PA` prices the S&P 500
in euros, and the app converts nothing because it is already in euros — but the
underlying earnings are in dollars. The currency exposure is unhedged, not
absent. The catalogue entry says so; the arithmetic cannot know.

### Stress tests convert too, at the rates of their own window

The crisis scenarios download their own price history, so they source the
exchange rates for 2008, 2020 and 2022 separately. Pricing a 2008 scenario at
today's euro would report a loss nobody had. A window whose rates cannot be
sourced is skipped rather than shown unconverted.

---

## 4. A shorter window than you asked for

A covariance over a period when one asset did not exist is not a weaker figure;
there is nothing to covary with. So the analysis is computed over the span every
holding actually traded in, and the overview says which holding set the start
when one of them did.

This matters more with Euronext than it did before. Capital B listed recently,
and before this the missing days were **back-filled** — a constant price, which
is a run of zero returns. The share would have been credited with a year of
perfect calm: its volatility, its drawdown and its correlation with everything
else all too low, which makes a portfolio look better diversified than it is.

If the window comes back shorter than you wanted, drop the youngest holding or
accept the shorter history. There is no third option that is honest.

---

## 5. What is not handled

**Dividends.** Prices come from Yahoo's adjusted close, which folds dividends
back in for most listings. Where it does not, a high-yield name like
TotalEnergies or Engie will look worse than it was. This is not new with
Euronext; it is more visible here because French yields are higher.

**Withholding tax and PEA eligibility.** The app models neither. A PEA changes
the after-tax return of exactly these shares, and none of the figures here are
after tax.

**Small-cap liquidity, beyond the score.** The liquidity number feeds the health
score. Nothing models the spread you would actually pay on `ALTBG.PA`, which on
a bad day is the difference between the price on screen and the price you get.
