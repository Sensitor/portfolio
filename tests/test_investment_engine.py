"""
Engine tests that need no Streamlit runtime.

This suite exists because of the V2 Phase 2 extraction. Before it, the analyzer
called `st.progress` and `st.warning` while computing, so testing it meant
standing up a Streamlit app; the reference data lived in the same 3,900-line UI
module, so importing a sector mapping pulled in the entire interface.

Every assertion below runs against a poisoned `streamlit` import, which proves
the layering rule rather than just asserting it in a docstring.

Run with:  python tests/test_investment_engine.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Poison Streamlit before anything else imports. Any engine module that reaches
# for it now fails loudly here instead of silently coupling the layers again.
sys.modules["streamlit"] = None  # type: ignore[assignment]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from sensitor.core import config, utils  # noqa: E402
from sensitor.core.exceptions import SensitorError  # noqa: E402
from sensitor.investment import analytics as A  # noqa: E402
from sensitor.investment import assets, portfolio  # noqa: E402

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok    {name}")
    else:
        FAILURES.append(f"{name}: {detail}")
        print(f"  FAIL  {name}  {detail}")


# =============================================================================
# LAYERING
# =============================================================================

def test_no_streamlit_in_engine() -> None:
    print("\nlayering")
    check("engine imports with streamlit poisoned", True)

    # Parse rather than grep: the fetch_data docstring *mentions* st.progress and
    # st.warning to explain what it replaced, and a text search would flag that
    # prose as a violation. Only real attribute access on a name `st` counts.
    import ast
    import inspect
    tree = ast.parse(inspect.getsource(portfolio))
    streamlit_calls = [
        f"st.{node.attr}"
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "st"
    ]
    check("analyzer module makes no st.* calls", not streamlit_calls,
          str(streamlit_calls))

    for module in (A, assets, portfolio, config, utils):
        check(f"{module.__name__} has no streamlit attribute",
              not hasattr(module, "st"))


# =============================================================================
# REFERENCE DATA
# =============================================================================

def test_assets() -> None:
    print("\nreference data")
    check("asset library is populated", len(assets.ASSET_INFO) > 30,
          f"{len(assets.ASSET_INFO)} entries")
    check("model portfolios present", len(assets.MODEL_PORTFOLIOS) >= 5)

    bad_weights = [
        name for name, spec in assets.MODEL_PORTFOLIOS.items()
        if abs(sum(spec["allocation"].values()) - 1.0) > 1e-6
    ]
    check("every model portfolio sums to 100%", not bad_weights, str(bad_weights))

    missing_fr = [
        ticker for ticker, info in assets.ASSET_INFO.items()
        if not info.get("description_fr")
    ]
    check("every library entry has a French description", not missing_fr,
          f"{len(missing_fr)} missing")

    catalogue = {t for group in assets.POPULAR_ASSETS.values() for t in group.values()}
    unmapped = [t for t in catalogue if t not in assets.SECTOR_MAPPING]
    check("every searchable ticker has a sector", not unmapped, str(unmapped))


# =============================================================================
# ANALYZER
# =============================================================================

class _FakeTicker:
    """Stands in for yfinance. Raises for tickers the fixture marks as dead."""

    dead: set[str] = set()
    rows = 300

    def __init__(self, symbol):
        self.symbol = symbol

    def history(self, start=None, **_):
        if self.symbol in self.dead:
            raise RuntimeError("Too Many Requests. Rate limited.")
        rng = np.random.default_rng(abs(hash(self.symbol)) % 2**31)
        index = pd.bdate_range("2023-01-02", periods=self.rows)
        prices = 100 * (1 + rng.normal(0.0004, 0.011, self.rows)).cumprod()
        return pd.DataFrame({"Close": prices}, index=index)


def _with_fake_yfinance(fn):
    original = portfolio.yf.Ticker
    portfolio.yf.Ticker = _FakeTicker
    try:
        return fn()
    finally:
        portfolio.yf.Ticker = original
        _FakeTicker.dead = set()


def test_analyzer() -> None:
    print("\nanalyzer")
    weights = {"SPY": 0.5, "QQQ": 0.3, "GLD": 0.2}

    def run_clean():
        analyzer = portfolio.PortfolioAnalyzer(list(weights), dict(weights))
        seen: list[tuple[float, str]] = []
        errors: list[tuple[str, str]] = []
        ok = analyzer.fetch_data(
            progress=lambda f, label: seen.append((f, label)),
            on_error=lambda t, m: errors.append((t, m)),
        )
        return analyzer, ok, seen, errors

    analyzer, ok, seen, errors = _with_fake_yfinance(run_clean)
    check("fetch_data succeeds", ok is True)
    check("no errors reported on a clean run", not errors, str(errors))
    check("progress was reported", len(seen) >= len(weights))
    check("progress ends at 1.0", seen and abs(seen[-1][0] - 1.0) < 1e-9,
          str(seen[-1] if seen else None))
    check("progress never exceeds 1.0", all(f <= 1.0 + 1e-9 for f, _ in seen))

    check("returns computed", analyzer.returns.shape[1] == 3)
    check("portfolio series aligned",
          len(analyzer.portfolio_returns) == len(analyzer.returns))
    check("weights renormalised to 1",
          abs(sum(analyzer.weights.values()) - 1.0) < 1e-9)

    # fetch_data with no callbacks at all — the API/test path.
    def run_silent():
        a = portfolio.PortfolioAnalyzer(list(weights), dict(weights))
        return a, a.fetch_data()

    silent, ok_silent = _with_fake_yfinance(run_silent)
    check("fetch_data works with no callbacks", ok_silent is True)

    # A dead ticker is skipped, reported, and its weight redistributed.
    def run_with_dead():
        _FakeTicker.dead = {"QQQ"}
        a = portfolio.PortfolioAnalyzer(list(weights), dict(weights))
        errs: list[tuple[str, str]] = []
        result = a.fetch_data(on_error=lambda t, m: errs.append((t, m)))
        return a, result, errs

    partial, ok_partial, errs = _with_fake_yfinance(run_with_dead)
    check("survives a failed download", ok_partial is True)
    check("the failure was reported", [t for t, _ in errs] == ["QQQ"], str(errs))
    check("dead ticker dropped", "QQQ" not in partial.weights)
    check("surviving weights renormalise to 1",
          abs(sum(partial.weights.values()) - 1.0) < 1e-9,
          str(partial.weights))

    metrics = analyzer.calculate_metrics()
    for key in ("total_return", "annual_return", "volatility", "sharpe", "max_drawdown"):
        check(f"metrics expose {key}", key in metrics)
    check("volatility is positive", metrics["volatility"] > 0)

    health = analyzer.calculate_health_score()
    check("health score in range", 0 <= health["total"] <= 100, str(health["total"]))

    robustness = analyzer.calculate_robustness_index()
    check("robustness score in range", 0 <= robustness["total"] <= 100)

    optimal = analyzer.optimize_portfolio()
    check("optimiser returns a full allocation",
          abs(sum(optimal["weights"].values()) - 1.0) < 1e-6)

    check("legacy alias still resolves",
          portfolio.UltimatePortfolioAnalyzer is portfolio.PortfolioAnalyzer)


# =============================================================================
# CORE
# =============================================================================

def test_core() -> None:
    print("\ncore")
    check("tier resolves to free by default", config.resolve_tier("nobody@x.com") == "free")
    check("unknown tier falls back to free limits",
          config.tier_limits("nonsense") == config.TIER_LIMITS["free"])
    check("exceptions share one base",
          issubclass(config and SensitorError, Exception))

    check("safe_div guards zero", utils.safe_div(1, 0, default=-1) == -1)
    check("safe_div divides", utils.safe_div(10, 4) == 2.5)
    check("clamp bounds", utils.clamp(11, 0, 10) == 10 and utils.clamp(-1, 0, 10) == 0)
    check("jsonable handles numpy",
          utils.jsonable({"a": np.float64(1.5), "b": [np.int64(2)]}) == {"a": 1.5, "b": [2]})
    check("jsonable never raises",
          isinstance(utils.jsonable({"x": object()})["x"], str))


# =============================================================================
# ANALYTICS FACADE
# =============================================================================

def test_analytics_facade() -> None:
    print("\nanalytics facade")
    from sensitor.investment import performance as P
    from sensitor.investment import risk as R

    check("facade re-exports performance", A.perf_stats is P.perf_stats)
    check("facade re-exports risk", A.risk_contribution is R.risk_contribution)
    check("facade advertises its surface", len(A.__all__) >= 20)

    missing = [name for name in A.__all__ if not hasattr(A, name)]
    check("every advertised name resolves", not missing, str(missing))


def main() -> int:
    test_no_streamlit_in_engine()
    test_assets()
    test_analyzer()
    test_core()
    test_analytics_facade()

    print(f"\n{len(FAILURES)} failures")
    for failure in FAILURES:
        print(f"  - {failure}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
