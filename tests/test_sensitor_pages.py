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


def _session_for(email: str) -> str:
    """
    A real session token for the harness.

    Identity is resolved from the token the app issued, not from `user_email`.
    Without this every persistence page renders its sign-in wall, and a harness
    that only watches for exceptions would call that a pass.
    """
    from sensitor.core.auth import Auth
    from sensitor.database import Store
    return Auth(Store(os.environ["SENSITOR_DB_PATH"])).sign_in(email).token


class FakeAnalyzer:
    """Minimal stand-in exposing exactly what `Context` reads off the real one."""

    def __init__(self, returns_df: pd.DataFrame, weights: dict, initial_value=100_000,
                 base_currency="USD"):
        # The pages read the base currency off the analyzer to decide whether a
        # dollar-quoted benchmark needs converting, so the stand-in has to carry
        # one too.
        self.base_currency = base_currency
        self.currency_report = {}
        self.window_report = {}
        self.tickers = list(returns_df.columns)
        self.weights = dict(weights)
        self.returns = returns_df
        self.initial_value = initial_value
        w = np.array([weights[t] for t in self.tickers])
        self.portfolio_returns = returns_df @ w
        self.portfolio_values = initial_value * (1 + self.portfolio_returns).cumprod()


def make_portfolio(tickers_weights: dict, days: int = 760, seed: int = 11,
                   base_currency: str = "USD") -> FakeAnalyzer:
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
    return FakeAnalyzer(pd.DataFrame(data, index=index), tickers_weights,
                        base_currency=base_currency)


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
    app.session_state["session_token"] = _session_for("harness@example.com")
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

    # Edge case: a euro-denominated portfolio. Every benchmark in the list is
    # dollar-quoted, so this is the path that converts one — including the
    # branch where the rate cannot be sourced and the page must fall back to
    # portfolio-only figures rather than raise.
    in_euros = make_portfolio({"MC.PA": 0.4, "AAPL": 0.35, "BTC-USD": 0.25},
                              base_currency="EUR")
    for page in PAGES:
        checks += 1
        app = run_page(page, in_euros, lang="fr")
        if app.exception:
            failures.append(("euro base", page, str(app.exception[0].value)[:400]))
            print(f"  FAIL  {page:12s} euro base")
        else:
            print(f"  ok    {page:12s} euro base")

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
    checks += _simulation_flow(failures)
    checks += _deep_link_flow(failures)
    checks += _carnet_flow(failures)

    print(f"\n{checks} render checks, {len(failures)} failures")
    for scenario, page, error in failures:
        print(f"\n--- {page} / {scenario} ---\n{error}")
    return 1 if failures else 0


def _simulation_flow(failures) -> int:
    """
    Build a simulated portfolio from the sliders and press « Analyse ».

    The render harness above injects a ready-made analyzer, so it never reaches
    the button that builds one. That is how a NameError in this branch shipped:
    every page rendered, and the one action that leads to them failed.
    """
    import numpy as np
    from sensitor.investment import portfolio as engine

    class FakeTicker:
        def __init__(self, symbol):
            self.symbol = symbol

        def history(self, start=None, **_):
            rng = np.random.default_rng(abs(hash(self.symbol)) % 2**31)
            index = pd.bdate_range("2024-01-02", periods=400)
            return pd.DataFrame({"Close": 100 * (1 + rng.normal(0.0004, 0.011, 400)).cumprod()}, index=index)

    original = engine.yf.Ticker
    engine.yf.Ticker = FakeTicker
    checks = 0
    try:
        app = AppTest.from_file(APP, default_timeout=240)
        app.session_state["authenticated"] = True
        app.session_state["user_email"] = "builder@example.com"
        app.session_state["session_token"] = _session_for("builder@example.com")
        app.session_state["user_tier"] = "pro"
        app.session_state["language"] = "en"
        app.session_state["user_profile"] = "balanced"
        app.session_state["analysis_mode"] = "simulation"
        app.session_state["selected_tickers"] = ["SPY", "AGG"]
        app.session_state["weights"] = {"SPY": 0.6, "AGG": 0.4}
        app.session_state["unanalysed_holdings"] = {"OLD": 1.0}
        app.session_state["page"] = "new_analysis"
        app.run()
        app.slider(key="ws_SPY").set_value(60.0)
        app.slider(key="ws_AGG").set_value(40.0)
        app.run()
        next(b for b in app.button if b.label == "Analyse Portfolio").click().run()
        state = {k: app.session_state[k] for k in ("page", "current_portfolio", "unanalysed_holdings")
                 if k in app.session_state}
        built = getattr(state.get("current_portfolio"), "tickers", [])
        for label, ok, detail in (
                ("simulation: « Analyse » runs without an exception", not app.exception,
                 str(app.exception[0].value)[:200] if app.exception else ""),
                ("simulation: it opens the overview", state.get("page") == "overview", str(state.get("page"))),
                ("simulation: the analysed book is the one built", sorted(built) == ["AGG", "SPY"], str(built)),
                ("simulation: no stale « not analysed » notice", state.get("unanalysed_holdings") == {}, "")):
            checks += 1
            print(f"  {'ok  ' if ok else 'FAIL'}  {label}")
            if not ok:
                failures.append(f"{label}: {detail}")
    finally:
        engine.yf.Ticker = original
    return checks


def _deep_link_flow(failures) -> int:
    """The platform opens the journal or the portfolio with `?page=`; nothing else is honoured."""
    checks = 0
    for requested, expected in (("trading_overview", "trading_overview"), ("trading_journal", "trading_journal"),
                                ("overview", "overview"), ("advisor", "overview"), ("../../etc", "overview")):
        app = AppTest.from_file(APP, default_timeout=240)
        app.query_params["page"] = requested
        app.run()
        landed = app.session_state["page"] if "page" in app.session_state else None
        ok = landed == expected and not app.exception
        checks += 1
        label = f"deep link « {requested} » opens « {expected} »"
        print(f"  {'ok  ' if ok else 'FAIL'}  {label}")
        if not ok:
            failures.append(f"{label}: got {landed}")
    return checks


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
        app.session_state["session_token"] = _session_for(email)
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


def _carnet_flow(failures) -> int:
    """
    Step 3 of the « Carnet de bord » direction, on the analytics application: the
    palette is the Carnet's, no colour outside it is left in the legacy script,
    performance curves carry end labels, a drawdown is a hatched risk zone, and
    the overview carries a « Lecture » margin built from computed figures.
    """
    import re
    from sensitor.ui import charts as C
    from sensitor.ui import themes as T

    checks = 0

    def check(label, ok, detail=""):
        nonlocal checks
        checks += 1
        print(f"  {'ok  ' if ok else 'FAIL'}  carnet       {label}")
        if not ok:
            failures.append(("carnet", label, detail or "failed"))

    check("paper, ink and plan tokens",
          (T.BG_DEEP, T.SURFACE, T.INK, T.ACCENT, T.POS, T.NEG, T.WARNING)
          == ("#F3F0E8", "#FFFDF8", "#0F1B26", "#1F4A72", "#22604A", "#9A3A2C", "#855615"))
    check("gain and loss are distinct", T.POS != T.NEG)
    check("fade() keeps the token's colour", T.fade("#1F4A72", 0.2) == "rgba(31,74,114,0.2)")

    # Every hex literal left in the legacy script belongs to the Carnet.
    allowed = {"#1F4A72", "#59636B", "#0F1B26", "#33414D", "#22604A", "#855615",
               "#9A3A2C", "#FFFDF8", "#9C5A1E", "#EEE9DD", "#F3E0DA", "#F2E7D2",
               "#E1E9F1", "#DDEBE2", "#D8D2C3", "#2F6A9E"}
    with open(APP, encoding="utf-8") as fh:
        legacy = fh.read()
    stray = sorted({h.upper() for h in re.findall(r"#[0-9a-fA-F]{6}\b", legacy)} - allowed)
    check("legacy script uses Carnet colours only", not stray, ", ".join(stray))

    # Section titles are set in Newsreader, in the case they were written in.
    upper_calls = []
    pages_dir = os.path.join(os.path.dirname(APP), "sensitor", "pages")
    for name in sorted(os.listdir(pages_dir)):
        if name.endswith(".py"):
            with open(os.path.join(pages_dir, name), encoding="utf-8") as fh:
                for line in fh:
                    if re.match(r"\s*section\(", line) and ".upper()" in line:
                        upper_calls.append(name)
    check("section titles are not forced to capitals", not upper_calls, ", ".join(upper_calls))

    index = pd.date_range("2024-01-01", periods=60, freq="B")
    a = pd.Series(np.linspace(100, 130, 60), index=index)
    b = pd.Series(np.linspace(100, 129, 60), index=index)
    fig = C.cumulative_performance({"Portfolio": a, "Benchmark": b}, value_prefix="$")
    notes = fig.layout.annotations
    check("one end label per series", len(notes) == 2)
    check("end labels carry the last values",
          {"$130", "$129"} <= {n.text.split("</span> ")[-1] for n in notes})
    ys = sorted(n.y for n in notes)
    check("close end labels are pushed apart", ys[1] - ys[0] > 1.0)
    many = {f"S{i}": a + i for i in range(5)}
    check("no end labels beyond four series",
          len(C.cumulative_performance(many).layout.annotations) == 0)

    dd = pd.Series(np.minimum(0, np.sin(np.linspace(0, 6, 60))) * 0.05, index=index)
    trace = C.underwater(dd).data[0]
    check("drawdown is a hatched zone", trace.fillpattern.shape == "-")
    with open(T.__file__, encoding="utf-8") as fh:
        check("the hatch is turned to 30 degrees",
              ".js-plotly-plot pattern {{ transform: rotate(-30deg); }}" in fh.read())

    analyzer = make_portfolio(SCENARIOS["diversified (7 assets)"])
    for lang, label, word in (("fr", "Lecture", "sur la période"),
                              ("en", "Reading", "over")):
        app = run_page("overview", analyzer, lang=lang)
        markup = " ".join(m.value for m in app.markdown)
        ok = (not app.exception and "snr-reading" in markup
              and label in markup and word in markup)
        check(f"overview carries the reading margin [{lang}]", ok,
              str(app.exception[0].value)[:300] if app.exception else "")
    return checks


if __name__ == "__main__":
    raise SystemExit(main())
