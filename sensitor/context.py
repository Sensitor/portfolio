"""
Analysis context — one object the pages share.

Every Sensitor page needs the same derived quantities (period-sliced returns,
performance stats, risk contribution, look-through, health, signals). Streamlit
reruns the whole script on every interaction, so recomputing these per page would
mean doing the same work several times per click.

`Context` computes each quantity at most once per rerun and caches it on the
instance. It also keeps the page layer decoupled from the existing
`UltimatePortfolioAnalyzer`: pages read `ctx.returns_df`, not analyzer internals,
so the underlying engine can change without touching the UI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import analytics as A
from . import health as H
from . import optimize as O
from . import signals as S
from . import xray as X


@dataclass
class Context:
    analyzer: Any
    lang: str = "en"
    profile: str = "balanced"
    period: str = "MAX"
    is_real: bool = False
    current_value: float | None = None
    currency: str = "$"
    frontier_bounds: tuple = O.DEFAULT_BOUNDS
    asset_info: dict = field(default_factory=dict)
    sector_map: dict = field(default_factory=dict)
    geo_map: dict = field(default_factory=dict)
    _cache: dict = field(default_factory=dict, repr=False)

    # ── Raw series ───────────────────────────────────────────────────────────

    @property
    def weights(self) -> dict:
        return dict(self.analyzer.weights)

    @property
    def tickers(self) -> list:
        return list(self.analyzer.tickers)

    @property
    def full_returns_df(self):
        return self.analyzer.returns

    @property
    def full_portfolio_returns(self):
        return self.analyzer.portfolio_returns

    @property
    def returns_df(self):
        """Asset returns sliced to the selected period."""
        return self._memo("returns_df", lambda: A.slice_period(self.full_returns_df, self.period))

    @property
    def portfolio_returns(self):
        """Portfolio returns sliced to the selected period."""
        return self._memo(
            "portfolio_returns",
            lambda: A.slice_period(self.full_portfolio_returns, self.period),
        )

    @property
    def values(self):
        """
        Portfolio value path over the selected period.

        In real-portfolio mode the path is scaled so its final point equals the
        actual holdings value, making the chart read in the user's own money rather
        than in an arbitrary simulated base.
        """
        return self._memo("values", self._compute_values)

    def _compute_values(self):
        cumulative = A.cumulative(self.portfolio_returns)
        if self.is_real and self.current_value and float(cumulative.iloc[-1]) != 0:
            return self.current_value * (cumulative / cumulative.iloc[-1])
        base = getattr(self.analyzer, "initial_value", 100_000)
        return base * cumulative

    @property
    def start_value(self) -> float:
        values = self.values
        return float(values.iloc[0]) if len(values) else 0.0

    @property
    def end_value(self) -> float:
        values = self.values
        return float(values.iloc[-1]) if len(values) else 0.0

    # ── Derived analytics ────────────────────────────────────────────────────

    @property
    def stats(self) -> dict:
        return self._memo("stats", lambda: A.perf_stats(self.portfolio_returns))

    @property
    def concentration(self) -> dict:
        return self._memo("concentration", lambda: A.concentration(self.weights))

    @property
    def risk_contribution(self):
        return self._memo(
            "risk_contribution", lambda: A.risk_contribution(self.returns_df, self.weights)
        )

    @property
    def correlation(self):
        return self._memo("correlation", lambda: self.returns_df.corr())

    @property
    def avg_correlation(self) -> float:
        return self._memo("avg_corr", lambda: A.avg_pairwise_correlation(self.returns_df))

    @property
    def diversification_ratio(self) -> float:
        return self._memo(
            "div_ratio", lambda: A.diversification_ratio(self.returns_df, self.weights)
        )

    @property
    def drawdown(self) -> dict:
        return self._memo("drawdown", lambda: A.drawdown_summary(self.portfolio_returns))

    @property
    def var(self) -> dict:
        return self._memo("var95", lambda: A.var_cvar(self.portfolio_returns, 0.95))

    @property
    def var99(self) -> dict:
        return self._memo("var99", lambda: A.var_cvar(self.portfolio_returns, 0.99))

    @property
    def distribution(self) -> dict:
        return self._memo("distribution", lambda: A.distribution_stats(self.portfolio_returns))

    @property
    def attribution(self):
        return self._memo(
            "attribution", lambda: A.return_contribution(self.returns_df, self.weights)
        )

    @property
    def xray(self) -> dict:
        return self._memo("xray", lambda: X.look_through(
            self.weights, self.asset_info, self.sector_map, self.geo_map
        ))

    @property
    def n_asset_classes(self) -> int:
        classes = {k: v for k, v in self.xray.get("asset_class", {}).items() if v > 0.01}
        return max(len(classes), 1)

    @property
    def health(self) -> dict:
        return self._memo("health", lambda: H.compute_health(
            portfolio_returns=self.portfolio_returns,
            returns_df=self.returns_df,
            weights=self.weights,
            asset_info=self.asset_info,
            n_asset_classes=self.n_asset_classes,
            profile=self.profile,
        ))

    @property
    def dna(self) -> dict:
        return self._memo("dna", lambda: H.portfolio_dna(
            health=self.health, xray=self.xray, stats=self.stats,
            weights=self.weights, asset_info=self.asset_info,
        ))

    @property
    def signals(self) -> list:
        return self._memo("signals", lambda: S.evaluate(
            weights=self.weights,
            returns_df=self.returns_df,
            portfolio_returns=self.portfolio_returns,
            xray=self.xray,
            stats=self.stats,
            rc_df=self.risk_contribution,
            conc=self.concentration,
            asset_info=self.asset_info,
            sector_map=self.sector_map,
            geo_map=self.geo_map,
        ))

    @property
    def frontier(self) -> dict:
        """
        Efficient frontier over the selected window.

        Computed here rather than in the page because the solver runs ~40 times
        and Streamlit reruns the script on every widget interaction.
        """
        return self._memo("frontier", lambda: O.efficient_frontier(
            self.returns_df, self.weights, bounds=self.frontier_bounds
        ))

    @property
    def available_periods(self) -> list:
        return A.available_periods(self.full_portfolio_returns)

    # ── Guards ───────────────────────────────────────────────────────────────

    @property
    def has_history(self) -> bool:
        returns = self.portfolio_returns
        return returns is not None and len(returns) >= 20

    @property
    def is_single_asset(self) -> bool:
        return len(self.tickers) < 2

    # ── Internals ────────────────────────────────────────────────────────────

    def _memo(self, key, compute):
        if key not in self._cache:
            self._cache[key] = compute()
        return self._cache[key]

    def set_period(self, period: str) -> None:
        """Change the window and drop every period-dependent cached value."""
        if period != self.period:
            self.period = period
            self._cache.clear()

    def set_frontier_bounds(self, bounds: tuple) -> None:
        """Change the position cap; only the frontier depends on it."""
        if tuple(bounds) != tuple(self.frontier_bounds):
            self.frontier_bounds = tuple(bounds)
            self._cache.pop("frontier", None)


def build_context(analyzer, *, lang, profile, period, asset_info, sector_map, geo_map,
                  is_real=False, current_value=None, currency="$") -> Context | None:
    """Build a Context, or None if the analyzer has no usable return series."""
    if analyzer is None or getattr(analyzer, "portfolio_returns", None) is None:
        return None
    if len(analyzer.portfolio_returns) < 5:
        return None
    return Context(
        analyzer=analyzer, lang=lang, profile=profile, period=period,
        is_real=is_real, current_value=current_value, currency=currency,
        asset_info=asset_info, sector_map=sector_map, geo_map=geo_map,
    )
