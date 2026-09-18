"""
Stress testing — historical crises and user-defined shocks.

Two independent methods, deliberately kept apart because they answer different
questions and carry different assumptions.

Historical replay
-----------------
Takes a real crisis window and computes what this allocation would have returned
over it, using the actual prices of the holdings that existed at the time. No
modelling — it is arithmetic on real history. The catch is coverage: Bitcoin has
no 2008, and a portfolio replayed on half its weight is not the portfolio. Every
result therefore carries the share of weight that actually had data, and the UI is
expected to show it. Below `MIN_COVERAGE` the scenario is returned as unreliable
rather than quietly reweighted onto whatever survived.

Custom shocks
-------------
The user sets a move on a few drivers (equities, tech, crypto, gold, bonds) and
each holding's response is estimated from its regression betas to those drivers.
This is a linear approximation calibrated on ordinary conditions, and it will
understate a real crash: correlations rise toward one exactly when it matters, so
diversification does less in the event than the betas suggest. That caveat is
returned with the result so the UI can state it rather than imply precision.

No Streamlit here — callers fetch prices and pass them in.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import analytics as A

MIN_COVERAGE = 0.50      # below this share of weight with data, flag as unreliable
MIN_OBSERVATIONS = 10    # trading days needed inside a window to compute anything


# =============================================================================
# HISTORICAL SCENARIOS
# =============================================================================

SCENARIOS = {
    "gfc_2008": {
        "start": "2007-10-09", "end": "2009-03-09",
        "en": "2008 Financial Crisis", "fr": "Crise Financière 2008",
        "desc_en": "Subprime collapse and the Lehman failure. The S&P 500 fell about 57% peak to trough.",
        "desc_fr": "Effondrement des subprimes et faillite de Lehman. Le S&P 500 a chuté d'environ 57% du sommet au creux.",
    },
    "covid_2020": {
        "start": "2020-02-19", "end": "2020-03-23",
        "en": "COVID Crash", "fr": "Krach COVID",
        "desc_en": "Pandemic shutdown. The fastest 30% drawdown in S&P 500 history, over 23 trading days.",
        "desc_fr": "Confinement pandémique. Le drawdown de 30% le plus rapide de l'histoire du S&P 500, en 23 séances.",
    },
    "inflation_2022": {
        "start": "2022-01-03", "end": "2022-10-12",
        "en": "2022 Rate Shock", "fr": "Choc de Taux 2022",
        "desc_en": "Fastest hiking cycle in decades. Stocks and bonds fell together, so the classic hedge failed.",
        "desc_fr": "Cycle de hausse le plus rapide depuis des décennies. Actions et obligations ont baissé ensemble : la couverture classique a échoué.",
    },
    "dotcom_2000": {
        "start": "2000-03-24", "end": "2002-10-09",
        "en": "Dot-com Crash", "fr": "Krach Internet",
        "desc_en": "Technology bubble deflating over two and a half years. The Nasdaq lost about 78%.",
        "desc_fr": "Dégonflement de la bulle technologique sur deux ans et demi. Le Nasdaq a perdu environ 78%.",
    },
    "q4_2018": {
        "start": "2018-10-01", "end": "2018-12-24",
        "en": "Q4 2018 Selloff", "fr": "Correction T4 2018",
        "desc_en": "Rate-hike fears and trade tensions produced a sharp quarter-end drawdown.",
        "desc_fr": "Craintes de hausse des taux et tensions commerciales : forte baisse en fin de trimestre.",
    },
    "crypto_winter_2022": {
        "start": "2021-11-10", "end": "2022-11-21",
        "en": "Crypto Winter", "fr": "Hiver Crypto",
        "desc_en": "Terra and FTX collapses. Bitcoin fell about 77% from its November 2021 high.",
        "desc_fr": "Effondrements de Terra et FTX. Le Bitcoin a chuté d'environ 77% depuis son sommet de novembre 2021.",
    },
    "taper_2013": {
        "start": "2013-05-21", "end": "2013-09-05",
        "en": "Taper Tantrum", "fr": "Taper Tantrum",
        "desc_en": "The Fed signalled tapering; long bonds sold off hard while equities wobbled.",
        "desc_fr": "La Fed annonce la réduction de ses achats : forte baisse des obligations longues, actions chahutées.",
    },
    "svb_2023": {
        "start": "2023-03-01", "end": "2023-03-24",
        "en": "Banking Stress 2023", "fr": "Stress Bancaire 2023",
        "desc_en": "Silicon Valley Bank failed and regional bank shares collapsed within days.",
        "desc_fr": "Faillite de la Silicon Valley Bank : effondrement des valeurs bancaires régionales en quelques jours.",
    },
}

SCENARIO_ORDER = list(SCENARIOS)


def scenario_label(key: str, lang: str = "en") -> str:
    spec = SCENARIOS.get(key, {})
    return spec.get(lang) or spec.get("en") or key


def scenario_description(key: str, lang: str = "en") -> str:
    spec = SCENARIOS.get(key, {})
    return spec.get(f"desc_{lang}") or spec.get("desc_en") or ""


def _window_return(prices: pd.Series, start: str, end: str) -> tuple[float, int] | None:
    """Total return of a price series inside a window, and how many days it had."""
    if prices is None or len(prices) == 0:
        return None
    index = pd.DatetimeIndex(prices.index)
    if index.tz is not None:
        index = index.tz_localize(None)
    series = pd.Series(prices.to_numpy(), index=index.normalize()).dropna()
    window = series.loc[(series.index >= pd.Timestamp(start)) & (series.index <= pd.Timestamp(end))]
    if len(window) < MIN_OBSERVATIONS:
        return None
    return float(window.iloc[-1] / window.iloc[0] - 1), len(window)


def historical_scenario(key: str, prices: dict, weights: dict,
                        benchmark_prices: pd.Series | None = None) -> dict | None:
    """
    Replay one crisis window on this allocation.

    `prices` is {ticker: full price Series}. Holdings with no data in the window
    are excluded and their weight is reported, so "the portfolio fell 22%" is
    always paired with how much of the portfolio that 22% actually describes.
    """
    spec = SCENARIOS.get(key)
    if not spec:
        return None

    total_weight = sum(weights.values()) or 1.0
    per_asset, covered_weight, missing = {}, 0.0, []

    for ticker, weight in weights.items():
        result = _window_return(prices.get(ticker), spec["start"], spec["end"])
        if result is None:
            missing.append(ticker)
            continue
        asset_return, _ = result
        per_asset[ticker] = asset_return
        covered_weight += weight / total_weight

    if not per_asset or covered_weight <= 0:
        return {
            "key": key, "covered": False, "coverage": 0.0,
            "missing": missing, "reliable": False,
        }

    # Renormalise across the holdings that have data. Stated, never silent.
    portfolio_return = sum(
        (weights[t] / total_weight / covered_weight) * r for t, r in per_asset.items()
    )

    benchmark_return = None
    if benchmark_prices is not None:
        bench = _window_return(benchmark_prices, spec["start"], spec["end"])
        benchmark_return = bench[0] if bench else None

    contributions = {
        t: (weights[t] / total_weight / covered_weight) * r for t, r in per_asset.items()
    }
    worst = min(contributions, key=contributions.get) if contributions else None
    best = max(contributions, key=contributions.get) if contributions else None

    return {
        "key": key,
        "covered": True,
        "coverage": covered_weight,
        "reliable": covered_weight >= MIN_COVERAGE,
        "portfolio_return": portfolio_return,
        "benchmark_return": benchmark_return,
        "relative": (portfolio_return - benchmark_return) if benchmark_return is not None else None,
        "per_asset": per_asset,
        "contributions": contributions,
        "worst_asset": worst,
        "best_asset": best,
        "missing": missing,
        "n_covered": len(per_asset),
        "start": spec["start"], "end": spec["end"],
    }


def run_all_scenarios(prices: dict, weights: dict,
                      benchmark_prices: pd.Series | None = None) -> list[dict]:
    """Every scenario with usable coverage, worst outcome first."""
    results = []
    for key in SCENARIO_ORDER:
        result = historical_scenario(key, prices, weights, benchmark_prices)
        if result and result.get("covered"):
            results.append(result)
    results.sort(key=lambda r: r.get("portfolio_return", 0.0))
    return results


# =============================================================================
# CUSTOM SHOCKS
# =============================================================================

DRIVERS = {
    "SPY": {"en": "S&P 500", "fr": "S&P 500", "default": -0.30},
    "QQQ": {"en": "Nasdaq 100", "fr": "Nasdaq 100", "default": -0.40},
    "BTC-USD": {"en": "Bitcoin", "fr": "Bitcoin", "default": -0.60},
    "GLD": {"en": "Gold", "fr": "Or", "default": 0.10},
    "AGG": {"en": "US Bonds", "fr": "Obligations US", "default": 0.05},
}

DRIVER_ORDER = list(DRIVERS)


def driver_label(ticker: str, lang: str = "en") -> str:
    spec = DRIVERS.get(ticker, {})
    return spec.get(lang) or spec.get("en") or ticker


def estimate_betas(returns_df: pd.DataFrame, driver_returns: pd.DataFrame) -> dict:
    """
    Multivariate betas of each holding to each shock driver.

    Regressing on all drivers at once matters here: equities and tech move
    together, and one-at-a-time betas would double-count the same shock. A holding
    that is itself a driver regresses to a beta of 1 on itself and ~0 elsewhere,
    which is the correct behaviour.
    """
    # Drivers and holdings routinely share tickers (a book holding SPY, shocked on
    # SPY). Concatenating without renaming produces duplicate columns, and every
    # subsequent lookup silently returns a DataFrame instead of a Series.
    driver_names = list(driver_returns.columns)
    renamed = driver_returns.rename(columns={d: f"__drv__{d}" for d in driver_names})
    joined = pd.concat([returns_df, renamed], axis=1, join="inner").dropna()
    if len(joined) < 60:
        return {}

    X = joined[[f"__drv__{d}" for d in driver_names]].to_numpy()
    design = np.column_stack([np.ones(len(X)), X])

    out = {}
    for ticker in returns_df.columns:
        y = joined[ticker].to_numpy()
        try:
            coef, _, rank, _ = np.linalg.lstsq(design, y, rcond=None)
        except np.linalg.LinAlgError:
            continue
        if rank < design.shape[1]:
            continue
        residuals = y - design @ coef
        ss_tot = float(((y - y.mean()) ** 2).sum())
        r_squared = 1 - float(residuals @ residuals) / ss_tot if ss_tot > 0 else 0.0
        out[ticker] = {
            "betas": {name: float(coef[i + 1]) for i, name in enumerate(driver_names)},
            "r_squared": r_squared,
        }
    return out


def custom_shock(weights: dict, betas: dict, shocks: dict,
                 portfolio_value: float | None = None) -> dict:
    """
    Propagate driver shocks through the estimated betas.

    Holdings with no beta estimate are excluded and reported. The result carries
    `linear_approximation=True` as a reminder that this is a first-order estimate
    from normal-period betas, not a crisis simulation.
    """
    total_weight = sum(weights.values()) or 1.0
    per_asset, covered_weight, missing = {}, 0.0, []

    for ticker, weight in weights.items():
        estimate = betas.get(ticker)
        if not estimate:
            missing.append(ticker)
            continue
        response = sum(estimate["betas"].get(driver, 0.0) * shock
                       for driver, shock in shocks.items())
        per_asset[ticker] = {
            "shock": response,
            "weight": weight / total_weight,
            "r_squared": estimate["r_squared"],
            "contribution": (weight / total_weight) * response,
        }
        covered_weight += weight / total_weight

    if not per_asset:
        return {"covered": False, "coverage": 0.0, "missing": missing}

    portfolio_shock = sum(v["contribution"] for v in per_asset.values())
    # Scale up to a full portfolio so a partially-covered book is not understated.
    if covered_weight > 0:
        portfolio_shock /= covered_weight

    ordered = sorted(per_asset.items(), key=lambda kv: kv[1]["contribution"])

    return {
        "covered": True,
        "coverage": covered_weight,
        "portfolio_shock": portfolio_shock,
        "per_asset": per_asset,
        "worst_asset": ordered[0][0] if ordered else None,
        "best_asset": ordered[-1][0] if ordered else None,
        "missing": missing,
        "value_before": portfolio_value,
        "value_after": portfolio_value * (1 + portfolio_shock) if portfolio_value else None,
        "linear_approximation": True,
        "mean_r_squared": float(np.mean([v["r_squared"] for v in per_asset.values()])),
    }


def stressed_metrics(portfolio_returns, shock: float, stats: dict | None = None) -> dict:
    """
    Portfolio statistics restated after a one-off shock.

    The shock is applied to the equity curve as a single day, so the drawdown and
    total return reflect it while volatility and the ratios keep their historical
    basis — a single event does not re-estimate a three-year volatility.
    """
    stats = stats or A.perf_stats(portfolio_returns)
    shocked = pd.concat([portfolio_returns, pd.Series([shock])], ignore_index=True)
    shocked_dd = float(A.drawdown_series(shocked).min())

    return {
        "before": {
            "total_return": stats["total_return"],
            "max_drawdown": stats["max_drawdown"],
            "volatility": stats["volatility"],
        },
        "after": {
            "total_return": (1 + stats["total_return"]) * (1 + shock) - 1,
            "max_drawdown": shocked_dd,
            "volatility": stats["volatility"],
        },
    }
