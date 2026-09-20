"""
Headless render harness for the Sensitor pages.

Runs the real Streamlit script through `AppTest` with a synthetic portfolio in
session state and asserts that every page renders without raising. This catches
the failure mode that matters most in a Streamlit app: a page that looks fine in
review and throws on a shape, an empty frame or a missing key at render time.

Run with:  python tests/test_sensitor_pages.py
"""

from __future__ import annotations

import os
import sys
import tempfile

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Persistence pages write to SQLite. Point them at a throwaway file so a test run
# can never touch a real database.
os.environ.setdefault(
    "SENSITOR_DB_PATH",
    os.path.join(tempfile.mkdtemp(prefix="sensitor-test-"), "test.db"),
)

from streamlit.testing.v1 import AppTest  # noqa: E402

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "portfolio_optimizer_saas.py")

PAGES = ["overview", "performance", "health", "xray", "risk", "stress",
         "optimize", "simulator", "copilot", "portfolios", "reports", "advisor"]


class FakeAnalyzer:
    """Minimal stand-in exposing exactly what `Context` reads off the real one."""

    def __init__(self, returns_df: pd.DataFrame, weights: dict, initial_value=100_000):
        self.tickers = list(returns_df.columns)
        self.weights = dict(weights)
        self.returns = returns_df
        self.initial_value = initial_value
        w = np.array([weights[t] for t in self.tickers])
        self.portfolio_returns = returns_df @ w
        self.portfolio_values = initial_value * (1 + self.portfolio_returns).cumprod()


def make_portfolio(tickers_weights: dict, days: int = 760, seed: int = 11) -> FakeAnalyzer:
    rng = np.random.default_rng(seed)
    index = pd.bdate_range("2022-06-01", periods=days)
    vols = {"SPY": 0.010, "QQQ": 0.013, "NVDA": 0.030, "GLD": 0.008,
            "BTC-USD": 0.036, "AGG": 0.003, "TLT": 0.009, "VXUS": 0.009,
            "EEM": 0.012, "SCHD": 0.008, "AAPL": 0.017}
    market = rng.normal(0.0004, 0.009, days)
    data = {}
    for ticker in tickers_weights:
        vol = vols.get(ticker, 0.014)
        idiosyncratic = rng.normal(0.0003, vol, days)
        beta = 0.2 if ticker in ("GLD", "AGG", "TLT") else 0.8
        data[ticker] = beta * market + (1 - beta) * idiosyncratic
    return FakeAnalyzer(pd.DataFrame(data, index=index), tickers_weights)


SCENARIOS = {
    "diversified (7 assets)": {
        "SPY": 0.28, "QQQ": 0.17, "NVDA": 0.08, "VXUS": 0.12,
        "AGG": 0.15, "GLD": 0.10, "BTC-USD": 0.10,
    },
    "concentrated (2 assets)": {"NVDA": 0.72, "SPY": 0.28},
    "single asset": {"SPY": 1.0},
    "all bonds": {"AGG": 0.6, "TLT": 0.4},
    "unknown tickers": {"ZZZZ": 0.5, "SPY": 0.5},
}

SHORT_HISTORY = 12  # days — below the 20-day guard


def run_page(page: str, analyzer, *, lang="en", mode="simulation", real_value=None,
             profile="balanced", period="MAX"):
    app = AppTest.from_file(APP, default_timeout=180)
    app.session_state["authenticated"] = True
    app.session_state["user_email"] = "harness@example.com"
    app.session_state["user_tier"] = "pro"
    app.session_state["language"] = lang
    app.session_state["user_profile"] = profile
    app.session_state["analysis_mode"] = mode
    app.session_state["current_portfolio"] = analyzer
    app.session_state["real_portfolio_total_value"] = real_value
    app.session_state["sensitor_period"] = period
    app.session_state["page"] = page
    app.run()
    return app


def main() -> int:
    failures = []
    checks = 0

    for scenario, weights in SCENARIOS.items():
        analyzer = make_portfolio(weights)
        for lang in ("en", "fr"):
            for page in PAGES:
                checks += 1
                app = run_page(page, analyzer, lang=lang)
                if app.exception:
                    failures.append((f"{scenario} [{lang}]", page,
                                     str(app.exception[0].value)[:400]))
                    print(f"  FAIL  {page:12s} {scenario} [{lang}]")
                else:
                    print(f"  ok    {page:12s} {scenario} [{lang}]")

    # Edge case: no portfolio loaded at all.
    for page in PAGES:
        checks += 1
        app = run_page(page, None)
        if app.exception:
            failures.append(("no portfolio", page, str(app.exception[0].value)[:400]))
            print(f"  FAIL  {page:12s} no portfolio")
        else:
            print(f"  ok    {page:12s} no portfolio")

    # Edge case: history far too short for the statistics to mean anything.
    short = make_portfolio({"SPY": 0.5, "QQQ": 0.5}, days=SHORT_HISTORY)
    for page in PAGES:
        checks += 1
        app = run_page(page, short)
        if app.exception:
            failures.append(("short history", page, str(app.exception[0].value)[:400]))
            print(f"  FAIL  {page:12s} short history")
        else:
            print(f"  ok    {page:12s} short history")

    # Edge case: real-portfolio mode, where the value path is rescaled.
    real = make_portfolio({"SPY": 0.4, "BTC-USD": 0.35, "GLD": 0.25})
    for page in PAGES:
        checks += 1
        app = run_page(page, real, mode="real", real_value=48_250.0, lang="fr")
        if app.exception:
            failures.append(("real mode", page, str(app.exception[0].value)[:400]))
            print(f"  FAIL  {page:12s} real mode")
        else:
            print(f"  ok    {page:12s} real mode")

    # Edge case: every risk profile, since the health score reads tolerance from it.
    profiles = make_portfolio({"SPY": 0.5, "NVDA": 0.3, "GLD": 0.2})
    for profile in ("safe", "balanced", "aggressive"):
        checks += 1
        app = run_page("health", profiles, profile=profile)
        if app.exception:
            failures.append((f"profile {profile}", "health", str(app.exception[0].value)[:400]))
            print(f"  FAIL  health       profile {profile}")
        else:
            print(f"  ok    health       profile {profile}")

    # ── The persistence flows, driven through their buttons ─────────────────
    # A render check never clicks anything, so every call inside an
    # `if st.button(...)` body is unexercised by the 159 above — which is where
    # the store's signatures are actually used.
    checks += _persistence_flow(failures)

    print(f"\n{checks} render checks, {len(failures)} failures")
    for scenario, page, error in failures:
        print(f"\n--- {page} / {scenario} ---\n{error}")
    return 1 if failures else 0


def _persistence_flow(failures) -> int:
    """Save a portfolio, snapshot it, open its history, delete it."""
    from sensitor.database import Store

    email = "flow@example.com"
    analyzer = make_portfolio({"SPY": 0.6, "AGG": 0.4})
    store = Store(os.environ["SENSITOR_DB_PATH"])
    store.delete_user(email)

    def fresh(page="portfolios"):
        app = AppTest.from_file(APP, default_timeout=240)
        app.session_state["authenticated"] = True
        app.session_state["user_email"] = email
        app.session_state["user_tier"] = "pro"
        app.session_state["language"] = "en"
        app.session_state["user_profile"] = "balanced"
        app.session_state["analysis_mode"] = "simulation"
        app.session_state["current_portfolio"] = analyzer
        app.session_state["sensitor_period"] = "MAX"
        app.session_state["page"] = page
        return app

    def buttons(app, prefix):
        return [b for b in app.button if (b.key or "").startswith(prefix)]

    def step(label, condition, detail=""):
        if condition:
            print(f"  ok    flow         {label}")
        else:
            failures.append(("persistence flow", label, detail or "failed"))
            print(f"  FAIL  flow         {label}")

    checks = 0

    app = fresh()
    app.run()
    app.text_input(key="pf_name").set_value("Flow Book").run()
    buttons(app, "pf_save")[0].click().run()
    saved = store.list_portfolios(email)
    checks += 1
    step("save writes a portfolio and its first snapshot",
         len(saved) == 1 and len(store.list_snapshots(email, saved[0].id)) == 1,
         f"{len(saved)} portfolios")
    if not saved:
        return checks
    portfolio_id = saved[0].id

    app = fresh()
    app.run()
    buttons(app, "pf_snap_")[0].click().run()
    checks += 1
    step("the snapshot button appends to the history",
         not app.exception and len(store.list_snapshots(email, portfolio_id)) == 2,
         str(app.exception[0].value)[:200] if app.exception else "")

    app = fresh()
    app.run()
    buttons(app, "pf_hist_")[0].click().run()
    checks += 1
    step("the history view renders",
         not app.exception,
         str(app.exception[0].value)[:200] if app.exception else "")

    app = fresh()
    app.run()
    buttons(app, "pf_del_")[0].click().run()
    confirm = buttons(app, "pf_del2_")
    checks += 1
    step("delete asks for confirmation first", bool(confirm))
    if confirm:
        confirm[0].click().run()
        orphans = store._read(
            "SELECT COUNT(*) AS n FROM snapshots WHERE portfolio_id NOT IN "
            "(SELECT id FROM portfolios)")[0]["n"]
        checks += 1
        step("delete removes the portfolio and leaves no orphaned snapshots",
             not app.exception and not store.list_portfolios(email)
             and int(orphans) == 0,
             f"orphans {orphans}")

    return checks


if __name__ == "__main__":
    raise SystemExit(main())
