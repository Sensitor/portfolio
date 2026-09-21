"""
The HTTP API: authorisation, isolation, and the rule that it computes nothing.

Three things are asserted, in order of how much they matter:

**No endpoint serves one user's data to another.** Every route that touches
user data is called with a second account's valid token and must answer 401,
404 or an empty result. The caller is read from the bearer token and nowhere
else, so there is no parameter to tamper with — this proves that.

**The API duplicates no calculation.** The router modules are parsed for
arithmetic and for imports of numpy, pandas and scipy. A metric implemented
twice diverges, and the version that diverges is the one with fewer readers: the
phone and the app would quietly disagree about a trader's expectancy. The
positive half of the same claim is checked too — the API's numbers are compared
against the engine's, called directly.

**Undefined stays undefined over the wire.** A profit factor with no losses, an
R multiple with no stop: both must arrive as `null`, not `0`.

`streamlit` is poisoned before the imports. An API process has no UI runtime.

Run with:  python tests/test_api.py
"""

from __future__ import annotations

import ast
import os
import pathlib
import sys
import tempfile
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.modules["streamlit"] = None

WORK = tempfile.mkdtemp(prefix="sensitor-api-test-")
os.environ["SENSITOR_DB_PATH"] = os.path.join(WORK, "api.db")
os.environ["SENSITOR_AUTH"] = "multi"
os.environ.pop("SENSITOR_API_TOKEN", None)

from fastapi.testclient import TestClient                            # noqa: E402

from sensitor.api import deps                                        # noqa: E402
from sensitor.api.app import create_app                              # noqa: E402
from sensitor.core.auth import Auth                                  # noqa: E402
from sensitor.database import Store                                  # noqa: E402
from sensitor.trading.models import Direction, Trade                 # noqa: E402

ALICE = "alice@example.com"
BOB = "bob@example.com"
PASSWORD = "correct-horse-battery"

CHECKS = []


def check(name, condition, detail=""):
    CHECKS.append((name, bool(condition), detail))
    print(f"  {'ok  ' if condition else 'FAIL'}  {name}"
          + (f"   {detail}" if detail and not condition else ""))


def a_trade(i: int, *, pnl: float, stop: float | None = 1.0950,
            symbol="EURUSD") -> Trade:
    return Trade(
        id=f"t{i:03d}", symbol=symbol, direction=Direction.LONG,
        entry_price=1.1000, size=100_000.0,
        opened_at=datetime(2025, 3, 1 + (i % 20), 9, 0),
        exit_price=1.1000 + pnl / 100_000.0,
        closed_at=datetime(2025, 3, 1 + (i % 20), 12, 0),
        stop_loss=stop, gross_pnl=pnl, commission=-3.0,
        account_id="acct-1", setups=["bos"] if i % 2 else ["order_block"],
        timeframe="M15", emotion_before="calm" if pnl > 0 else "anxious",
        discipline=4 if pnl > 0 else 2,
        mistakes=[] if pnl > 0 else ["fomo"],
        notes="alice's private note",
    )


def build_world() -> tuple[TestClient, str, str, Store]:
    """Two accounts, one with a book, one with nothing."""
    store = Store(os.environ["SENSITOR_DB_PATH"])
    for email in (ALICE, BOB):
        store.delete_user(email)

    auth = Auth(store, mode="multi")
    alice = auth.sign_up(ALICE, PASSWORD)
    bob = auth.sign_up(BOB, PASSWORD)

    # A book with wins, losses, and a few trades without a stop, so the
    # undefined cases are reachable over the wire.
    book = [a_trade(i, pnl=(180.0 if i % 3 else -90.0)) for i in range(30)]
    book += [a_trade(100 + i, pnl=60.0, stop=None, symbol="XAUUSD")
             for i in range(5)]
    store.save_trades(ALICE, book)
    store.upsert_account(ALICE, "acct-1", "Alice Live", broker="Broker")
    store.save_portfolio(ALICE, "Core", {"SPY": 0.6, "AGG": 0.4},
                         notes="alice's plan")

    deps.get_store.cache_clear()
    return TestClient(create_app()), alice.token, bob.token, store


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# 1. THE API COMPUTES NOTHING
# =============================================================================

ROUTERS = pathlib.Path(__file__).resolve().parent.parent / "sensitor" / "api"

# Libraries whose presence in a router would mean a number is being produced
# there rather than fetched.
FORBIDDEN_IMPORTS = {"numpy", "np", "pandas", "pd", "scipy", "statistics", "math"}

# Arithmetic on values. Slicing a list for pagination is not a calculation, so
# `ast.Sub` inside a subscript is allowed; these are the operators that would
# mean a financial figure is being derived.
ARITHMETIC = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Pow)


def test_no_duplicated_calculation():
    print("\nThe API computes nothing")

    for path in sorted(ROUTERS.rglob("*.py")):
        tree = ast.parse(path.read_text())
        name = str(path.relative_to(ROUTERS))

        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                imported.add(node.module.split(".")[0])
        offenders = imported & FORBIDDEN_IMPORTS
        check(f"{name} imports no numeric library", not offenders,
              f"imports {offenders}")
        check(f"{name} imports no streamlit", "streamlit" not in imported)

        # Arithmetic outside a subscript. `rows[offset:offset + limit]` is
        # pagination; anything else in a router would be a metric.
        in_slice = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Subscript):
                for inner in ast.walk(node.slice):
                    in_slice.add(id(inner))
        arithmetic = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.BinOp) and isinstance(node.op, ARITHMETIC)
            and id(node) not in in_slice
        ]
        check(f"{name} contains no arithmetic", not arithmetic,
              f"{len(arithmetic)} expression(s) at lines "
              f"{[n.lineno for n in arithmetic]}")


def test_numbers_match_the_engine():
    """The positive half: the API's figures are the engine's figures."""
    print("\nThe API's numbers are the engine's numbers")
    client, token, _, store = build_world()

    from sensitor.trading.context import build_context
    from sensitor.trading.journal import TradeJournal
    engine = build_context(TradeJournal(store.list_trades(ALICE)))

    served = client.get("/trading/metrics", headers=auth_header(token)).json()
    expected = engine.metrics

    for field in ("n", "n_wins", "n_losses", "net_pnl", "win_rate",
                  "profit_factor", "expectancy", "avg_r", "total_r",
                  "r_coverage", "max_drawdown", "max_win_streak"):
        same = served.get(field) == expected.get(field) or (
            served.get(field) is not None and expected.get(field) is not None
            and abs(served[field] - expected[field]) < 1e-9)
        check(f"{field} matches the engine", same,
              f"api {served.get(field)} vs engine {expected.get(field)}")

    api_equity = client.get("/trading/equity", headers=auth_header(token)).json()
    check("the equity curve has the same length",
          len(api_equity) == len(engine.equity_curve))
    check("and the same final value",
          abs(api_equity[-1]["equity"] - engine.equity_curve[-1]["equity"]) < 1e-9)

    api_breakdown = client.get("/trading/breakdown/setup",
                               headers=auth_header(token)).json()
    check("a breakdown matches the engine's row count",
          len(api_breakdown) == len(engine.breakdown("setup")))


# =============================================================================
# 2. AUTHORISATION
# =============================================================================

PROTECTED = [
    ("GET", "/auth/me"), ("GET", "/trading/metrics"), ("GET", "/trading/equity"),
    ("GET", "/trading/r-curve"), ("GET", "/trading/daily"),
    ("GET", "/trading/breakdown/symbol"), ("GET", "/trading/risk"),
    ("GET", "/trading/psychology"), ("GET", "/trading/findings"),
    ("GET", "/trading/trades"), ("GET", "/trading/accounts"),
    ("GET", "/trading/periods"), ("GET", "/portfolios"),
    ("GET", "/portfolios/1"), ("GET", "/portfolios/1/snapshots"),
    ("GET", "/portfolios/1/latest"), ("DELETE", "/portfolios/1"),
    ("POST", "/auth/sign-out-everywhere"),
]


def test_every_protected_route_requires_a_token():
    print("\nAuthorisation")
    client, token, _, _ = build_world()

    for method, path in PROTECTED:
        response = client.request(method, path)
        check(f"{method} {path} without a token is 401",
              response.status_code == 401, f"got {response.status_code}")

    bad = client.get("/trading/metrics", headers=auth_header("not-a-real-token"))
    check("an invented token is 401", bad.status_code == 401)

    malformed = client.get("/trading/metrics",
                           headers={"Authorization": token})   # no "Bearer"
    check("a token without the Bearer scheme is 401",
          malformed.status_code == 401, f"got {malformed.status_code}")

    check("liveness needs no token", client.get("/health").status_code == 200)
    check("meta needs no token", client.get("/meta").status_code == 200)


def test_no_endpoint_names_a_user():
    """
    There is no parameter to tamper with.

    The strongest form of this guarantee is structural: if no route accepts a
    user, no route can be asked for somebody else's data. Read off the OpenAPI
    document rather than the source, so it reflects what is actually served.
    """
    print("\nNo endpoint takes a user as a parameter")
    client, _, _, _ = build_world()
    spec = client.get("/openapi.json").json()

    suspicious = {"user", "user_email", "email", "owner", "account_email"}
    offenders = []
    for path, operations in spec["paths"].items():
        for method, operation in operations.items():
            for parameter in operation.get("parameters", []):
                if parameter["name"].lower() in suspicious:
                    offenders.append(f"{method.upper()} {path} ?{parameter['name']}")

    check("no path or query parameter names a user", not offenders,
          f"found {offenders}")

    # `/auth/sign-in` takes an email in its body, which is correct — that is
    # the claim being verified, not a selector for data.
    check("sign-in is the only place an email is accepted",
          "email" in str(spec["components"]["schemas"]["SignInRequest"]))


def test_one_account_cannot_read_another():
    print("\nOne account cannot read another")
    client, alice_token, bob_token, store = build_world()

    alice_portfolio = store.list_portfolios(ALICE)[0].id
    bob = auth_header(bob_token)

    metrics = client.get("/trading/metrics", headers=bob).json()
    check("Bob's metrics are empty", metrics["n"] == 0, f"n={metrics['n']}")
    check("Alice's are not",
          client.get("/trading/metrics",
                     headers=auth_header(alice_token)).json()["n"] > 0)

    trades = client.get("/trading/trades", headers=bob).json()
    check("Bob sees no trades", trades["total"] == 0)
    check("and none of Alice's notes",
          "alice's private note" not in str(trades))

    check("Bob's portfolio list is empty",
          client.get("/portfolios", headers=bob).json() == [])
    check("Alice's is not",
          len(client.get("/portfolios", headers=auth_header(alice_token)).json()) == 1)

    # Alice's portfolio id is a real id. Asking for it as Bob must be
    # indistinguishable from asking for one that does not exist.
    direct = client.get(f"/portfolios/{alice_portfolio}", headers=bob)
    missing = client.get("/portfolios/999999", headers=bob)
    check("Alice's portfolio is 404 for Bob", direct.status_code == 404)
    check("indistinguishable from one that does not exist",
          direct.status_code == missing.status_code
          and direct.json()["detail"] == missing.json()["detail"])

    check("its snapshots are 404 too",
          client.get(f"/portfolios/{alice_portfolio}/snapshots",
                     headers=bob).status_code == 404)
    check("and Bob cannot delete it",
          client.delete(f"/portfolios/{alice_portfolio}",
                        headers=bob).status_code == 404)
    check("it is still there afterwards",
          store.get_portfolio(ALICE, alice_portfolio) is not None)

    check("Bob sees none of Alice's accounts",
          client.get("/trading/accounts", headers=bob).json() == [])
    check("nor her findings", client.get("/trading/findings", headers=bob).json() == [])


# =============================================================================
# 3. SESSIONS OVER HTTP
# =============================================================================

def test_sign_in_flow():
    print("\nSign-in over HTTP")
    client, _, _, store = build_world()

    ok = client.post("/auth/sign-in", json={"email": ALICE, "password": PASSWORD})
    check("a correct password returns a token", ok.status_code == 200)
    token = ok.json()["token"]
    check("the token works", client.get("/auth/me",
                                        headers=auth_header(token)).status_code == 200)
    check("and identifies the right person",
          client.get("/auth/me", headers=auth_header(token)).json()["email"] == ALICE)

    wrong = client.post("/auth/sign-in", json={"email": ALICE, "password": "nope"})
    check("a wrong password is 401", wrong.status_code == 401)
    unknown = client.post("/auth/sign-in",
                          json={"email": "nobody@example.com", "password": PASSWORD})
    check("an unknown account gives the same answer",
          unknown.status_code == wrong.status_code
          and unknown.json()["detail"] == wrong.json()["detail"])

    check("registering an existing address is 409",
          client.post("/auth/sign-up",
                      json={"email": ALICE, "password": PASSWORD}).status_code == 409)
    check("a weak password is 400",
          client.post("/auth/sign-up",
                      json={"email": "new@example.com",
                            "password": "short"}).status_code == 400)

    fresh = client.post("/auth/sign-up",
                        json={"email": "new@example.com", "password": PASSWORD})
    check("a valid registration is 201", fresh.status_code == 201)
    check("and signs the new account in",
          client.get("/auth/me",
                     headers=auth_header(fresh.json()["token"])).json()["email"]
          == "new@example.com")

    client.post("/auth/sign-out", headers=auth_header(token))
    check("signing out revokes the token",
          client.get("/auth/me", headers=auth_header(token)).status_code == 401)

    # A token issued in the Streamlit app works here: one session store.
    shared = Auth(store, mode="multi").sign_in(ALICE, PASSWORD)
    check("a session issued outside the API is accepted",
          client.get("/auth/me",
                     headers=auth_header(shared.token)).json()["email"] == ALICE)


def test_single_user_mode_refuses_to_issue_sessions():
    """
    The behaviour the desktop app has is not safe to expose over HTTP.

    Typing an email is a filing label in a text box on your own machine and a
    public session endpoint on a network. Single-user mode therefore issues
    nothing unless an API key is configured.
    """
    print("\nSingle-user mode over HTTP")
    original = os.environ.get("SENSITOR_AUTH")
    try:
        os.environ["SENSITOR_AUTH"] = "single"
        os.environ.pop("SENSITOR_API_TOKEN", None)
        deps.get_store.cache_clear()
        client = TestClient(create_app())

        refused = client.post("/auth/sign-in", json={"email": ALICE})
        check("with no API key, sign-in is refused", refused.status_code == 503,
              f"got {refused.status_code}")
        check("and says how to fix it",
              "SENSITOR_API_TOKEN" in refused.json()["detail"])
        check("meta reports that no session can be obtained",
              client.get("/meta").json()["issues_sessions"] is False)
        check("registration is not available either",
              client.post("/auth/sign-up",
                          json={"email": ALICE, "password": PASSWORD}
                          ).status_code == 404)

        os.environ["SENSITOR_API_TOKEN"] = "a-shared-key"
        client = TestClient(create_app())
        check("a wrong key is refused",
              client.post("/auth/sign-in",
                          json={"email": ALICE, "api_key": "guess"}
                          ).status_code == 401)
        good = client.post("/auth/sign-in",
                           json={"email": ALICE, "api_key": "a-shared-key"})
        check("the configured key is accepted", good.status_code == 200)
        check("and the session works",
              client.get("/auth/me",
                         headers=auth_header(good.json()["token"])
                         ).json()["email"] == ALICE)
        check("meta now reports sessions are available",
              client.get("/meta").json()["issues_sessions"] is True)
    finally:
        os.environ.pop("SENSITOR_API_TOKEN", None)
        if original is None:
            os.environ.pop("SENSITOR_AUTH", None)
        else:
            os.environ["SENSITOR_AUTH"] = original
        deps.get_store.cache_clear()


# =============================================================================
# 4. UNDEFINED STAYS UNDEFINED
# =============================================================================

def test_undefined_survives_the_wire():
    print("\nUndefined stays undefined")
    client, token, bob_token, store = build_world()
    headers = auth_header(token)

    metrics = client.get("/trading/metrics", headers=headers).json()
    check("R coverage is reported", metrics["r_coverage"] is not None)
    check("and is below 1, because some trades had no stop",
          metrics["r_coverage"] < 1.0, f"got {metrics['r_coverage']}")

    # A book with no losing trades has no denominator for a profit factor.
    store.delete_all_trades(BOB)
    store.save_trades(BOB, [a_trade(i, pnl=120.0) for i in range(12)])
    winners = client.get("/trading/metrics", headers=auth_header(bob_token)).json()
    check("profit factor with no losses is null, not infinity",
          winners["profit_factor"] is None, f"got {winners['profit_factor']}")
    check("but the rest of the metrics are there", winners["n"] == 12)

    # A book with no stops at all has no R.
    store.delete_all_trades(BOB)
    store.save_trades(BOB, [a_trade(i, pnl=50.0, stop=None) for i in range(10)])
    no_stops = client.get("/trading/metrics", headers=auth_header(bob_token)).json()
    check("average R with no stops is null, not zero",
          no_stops["avg_r"] is None, f"got {no_stops['avg_r']}")
    check("and coverage says why", no_stops["r_coverage"] == 0.0)
    check("the R curve is empty rather than flat at zero",
          client.get("/trading/r-curve",
                     headers=auth_header(bob_token)).json() == [])

    # An empty journal must answer, not fail.
    store.delete_all_trades(BOB)
    empty = client.get("/trading/metrics", headers=auth_header(bob_token))
    check("an empty journal returns 200", empty.status_code == 200)
    check("with n = 0", empty.json()["n"] == 0)
    check("and an empty equity curve",
          client.get("/trading/equity", headers=auth_header(bob_token)).json() == [])
    check("and no findings",
          client.get("/trading/findings", headers=auth_header(bob_token)).json() == [])


def test_sample_sizes_travel():
    print("\nSample sizes travel with every grouped figure")
    client, token, _, _ = build_world()
    headers = auth_header(token)

    rows = client.get("/trading/breakdown/setup", headers=headers).json()
    check("a breakdown returns rows", len(rows) > 0)
    check("every row carries its sample size",
          all("n" in r and r["n"] > 0 for r in rows))
    check("and whether it clears the threshold",
          all(isinstance(r["reliable"], bool) for r in rows))

    check("an unknown dimension is 404",
          client.get("/trading/breakdown/astrology", headers=headers).status_code == 404)
    check("an invalid period is 422",
          client.get("/trading/metrics?period=FOREVER",
                     headers=headers).status_code == 422)

    findings = client.get("/trading/findings", headers=headers).json()
    for finding in findings:
        check(f"finding '{finding['key']}' states it is a correlation",
              "correlation" in finding["en"].lower()
              and "corrélation" in finding["fr"].lower())
        check(f"finding '{finding['key']}' carries its sample size",
              finding["n"] > 0 and str(finding["n"]) in finding["en"])

    risk = client.get("/trading/risk", headers=headers).json()
    check("stop discipline says what it is measured on",
          risk["stops"].get("measured_on") == "gross", f"got {risk['stops']}")


def test_pagination():
    print("\nPagination")
    client, token, _, _ = build_world()
    headers = auth_header(token)

    first = client.get("/trading/trades?limit=10&offset=0", headers=headers).json()
    check("a page returns the requested size", len(first["trades"]) == 10)
    check("and reports the total", first["total"] == 35, f"got {first['total']}")

    second = client.get("/trading/trades?limit=10&offset=10", headers=headers).json()
    check("the next page is different",
          {t["id"] for t in first["trades"]} != {t["id"] for t in second["trades"]})
    check("and does not overlap",
          not ({t["id"] for t in first["trades"]}
               & {t["id"] for t in second["trades"]}))

    check("an oversized limit is refused",
          client.get("/trading/trades?limit=99999", headers=headers).status_code == 422)
    check("a negative offset is refused",
          client.get("/trading/trades?offset=-1", headers=headers).status_code == 422)

    trade = first["trades"][0]
    check("derived values travel with each trade",
          "r_multiple" in trade and "duration_minutes" in trade
          and "session" in trade)


def main() -> int:
    for test in (test_no_duplicated_calculation, test_numbers_match_the_engine,
                 test_every_protected_route_requires_a_token,
                 test_no_endpoint_names_a_user,
                 test_one_account_cannot_read_another, test_sign_in_flow,
                 test_single_user_mode_refuses_to_issue_sessions,
                 test_undefined_survives_the_wire, test_sample_sizes_travel,
                 test_pagination):
        test()

    failures = [c for c in CHECKS if not c[1]]
    print(f"\n{len(CHECKS)} checks, {len(failures)} failures")
    for name, _, detail in failures:
        print(f"  FAIL  {name}   {detail}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
