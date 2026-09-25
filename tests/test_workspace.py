"""
The working portfolio survives a restart.

This is the claim the feature exists to make, so it is tested the way the claim
is worded: put an allocation into a running app, throw the app away, start a new
one against the same database, and look for the allocation.

`AppTest.from_file` builds a fresh script run with its own session state, which
is exactly what a restarted process gives a returning user — the database on
disk and nothing in memory. A test that merely called `save_workspace` and
`load_workspace` would prove the store works and prove nothing about whether the
app ever calls it.

Run with:  python tests/test_workspace.py
"""

from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["SENSITOR_DB_PATH"] = os.path.join(
    tempfile.mkdtemp(prefix="sensitor-workspace-"), "test.db")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from streamlit.testing.v1 import AppTest  # noqa: E402

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "portfolio_optimizer_saas.py")

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok    {name}")
    else:
        FAILURES.append(f"{name}: {detail}")
        print(f"  FAIL  {name}  {detail}")


def store():
    from sensitor.database import Store
    return Store(os.environ["SENSITOR_DB_PATH"])


def token_for(email: str) -> str:
    from sensitor.core.auth import Auth
    return Auth(store()).sign_in(email).token


class FakeAnalyzer:
    """
    Stands in for a priced portfolio.

    Present in these runs for one reason: without it the app would try to
    download prices for the restored allocation, and a test that reaches the
    network is a test that fails for reasons which have nothing to do with it.
    """

    base_currency = "USD"
    currency_report: dict = {}

    def __init__(self, weights):
        index = pd.bdate_range("2023-01-02", periods=300)
        rng = np.random.default_rng(3)
        self.tickers = list(weights)
        self.weights = dict(weights)
        self.returns = pd.DataFrame(
            {t: rng.normal(0.0004, 0.011, len(index)) for t in weights}, index=index)
        self.initial_value = 100_000
        w = np.array([weights[t] for t in self.tickers])
        self.portfolio_returns = self.returns @ w
        self.portfolio_values = self.initial_value * (1 + self.portfolio_returns).cumprod()


def run(email, *, token=None, analyzer=None, page="overview", **state):
    app = AppTest.from_file(APP, default_timeout=180)
    app.session_state["authenticated"] = True
    app.session_state["user_email"] = email
    app.session_state["session_token"] = token or token_for(email)
    app.session_state["user_tier"] = "pro"
    app.session_state["page"] = page
    if analyzer is not None:
        app.session_state["current_portfolio"] = analyzer
    for key, value in state.items():
        app.session_state[key] = value
    app.run()
    return app


# =============================================================================

ALICE = "alice@example.com"
BOB = "bob@example.com"

PARIS = {"MC.PA": 0.5, "ALTBG.PA": 0.2, "AAPL": 0.3}


def test_a_restart_keeps_the_portfolio() -> None:
    print("\nAn allocation survives a restart")

    alice_token = token_for(ALICE)

    # Session one: somebody builds a portfolio. Nothing is pressed to save it.
    first = run(ALICE, token=alice_token, analyzer=FakeAnalyzer(PARIS),
                selected_tickers=list(PARIS), weights=dict(PARIS),
                base_currency="EUR", user_profile="aggressive")
    check("the first run renders", not first.exception,
          str(first.exception[0].value)[:300] if first.exception else "")

    saved = store().load_workspace(ALICE)
    check("the allocation was written down without being asked",
          saved is not None and saved.holdings == PARIS,
          str(saved.holdings if saved else None))
    check("with the base currency", saved is not None and saved.base_currency == "EUR")
    check("and the risk profile", saved is not None and saved.profile == "aggressive")

    # Session two is a different process as far as the app is concerned: a new
    # script run, empty session state, the same database on disk.
    second = run(ALICE, token=alice_token, analyzer=FakeAnalyzer(PARIS))
    check("the second run renders", not second.exception,
          str(second.exception[0].value)[:300] if second.exception else "")
    check("the tickers came back",
          sorted(second.session_state["selected_tickers"]) == sorted(PARIS),
          str(second.session_state.get("selected_tickers")))
    check("so did the weights", second.session_state["weights"] == PARIS)
    check("and the currency", second.session_state["base_currency"] == "EUR")
    check("and the profile", second.session_state["user_profile"] == "aggressive")


def test_an_empty_session_does_not_erase_the_row() -> None:
    """
    The failure this guards against is the one that would make the feature
    worse than useless: a restart whose first run compares an empty session
    against a full row and saves the empty one over it.
    """
    print("\nA fresh session does not overwrite what it is about to restore")

    before = store().load_workspace(ALICE)
    check("there is something to lose", before is not None and before.holdings)

    run(ALICE, analyzer=FakeAnalyzer(PARIS))
    after = store().load_workspace(ALICE)
    check("it is still there after a plain visit",
          after is not None and after.holdings == before.holdings,
          str(after.holdings if after else None))


def test_a_change_is_persisted() -> None:
    """
    Edited the way a person edits: inside a session that has already restored.

    Seeding `selected_tickers` on a *fresh* run would prove nothing, because a
    fresh run restores over it — which is correct, and is what a browser opening
    for the first time actually does.
    """
    print("\nAn edit is written down")

    changed = {"OR.PA": 0.6, "SAN.PA": 0.4}
    app = run(ALICE, analyzer=FakeAnalyzer(PARIS))
    check("the session restored before the edit",
          sorted(app.session_state["selected_tickers"]) == sorted(PARIS))

    app.session_state["selected_tickers"] = list(changed)
    app.session_state["weights"] = dict(changed)
    app.run()
    check("the edited run renders", not app.exception,
          str(app.exception[0].value)[:300] if app.exception else "")

    saved = store().load_workspace(ALICE)
    check("the new allocation replaced the old one",
          saved is not None and saved.holdings == changed, str(saved.holdings if saved else None))
    check("one row per person, not a pile of drafts",
          store()._read("SELECT COUNT(*) AS n FROM workspace WHERE user_email = ?",
                        (ALICE,))[0]["n"] == 1)


def test_one_persons_portfolio_is_not_anothers() -> None:
    print("\nIsolation")

    bobs = {"QQQ": 1.0}
    run(BOB, analyzer=FakeAnalyzer(bobs), selected_tickers=list(bobs), weights=dict(bobs))

    check("Bob's workspace is his own",
          store().load_workspace(BOB).holdings == bobs)
    check("and Alice's is untouched",
          store().load_workspace(ALICE).holdings == {"OR.PA": 0.6, "SAN.PA": 0.4})

    # Bob signs in on a machine where Alice was last. He must not see her book.
    bobs_session = run(BOB, analyzer=FakeAnalyzer(bobs))
    check("Bob's session restores Bob's allocation",
          sorted(bobs_session.session_state["selected_tickers"]) == ["QQQ"],
          str(bobs_session.session_state.get("selected_tickers")))


def test_signed_out_writes_nothing() -> None:
    print("\nNobody signed in, nothing written")

    app = AppTest.from_file(APP, default_timeout=180)
    app.session_state["page"] = "overview"
    app.session_state["selected_tickers"] = ["SPY"]
    app.session_state["weights"] = {"SPY": 1.0}
    app.run()

    check("an anonymous session renders", not app.exception,
          str(app.exception[0].value)[:300] if app.exception else "")
    rows = store()._read("SELECT user_email FROM workspace", ())
    check("and files nothing under a blank address",
          all(row["user_email"] for row in rows), str([r["user_email"] for r in rows]))


def main() -> int:
    test_a_restart_keeps_the_portfolio()
    test_an_empty_session_does_not_erase_the_row()
    test_a_change_is_persisted()
    test_one_persons_portfolio_is_not_anothers()
    test_signed_out_writes_nothing()

    print(f"\n{len(FAILURES)} failures")
    for failure in FAILURES:
        print(f"  - {failure}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
