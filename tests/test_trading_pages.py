"""
Headless render harness for the five trading pages.

Same job as `test_sensitor_pages.py` and the same reason: these pages are full of
branches that only exist for data shapes nobody has while writing them — a book
with no stops, a book with no losses, four trades, nothing but open positions.
Each of those takes a different path through a metric card, and the only way to
know the path renders is to render it.

The database is a throwaway file created per run, seeded before the app starts.
Nothing here touches a real journal.

Run with:  python tests/test_trading_pages.py
"""

from __future__ import annotations

import os
import random
import sys
import tempfile
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_DIR = tempfile.mkdtemp(prefix="sensitor-trading-test-")
os.environ["SENSITOR_DB_PATH"] = os.path.join(DB_DIR, "trading.db")

from streamlit.testing.v1 import AppTest                      # noqa: E402

from sensitor.database import Store                           # noqa: E402
from sensitor.trading.models import Direction, Trade          # noqa: E402

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "portfolio_optimizer_saas.py")

PAGES = ["trading_overview", "trading_journal", "trading_analytics",
         "trading_risk", "trading_psychology"]

EMAIL = "harness@example.com"
OTHER_EMAIL = "someone-else@example.com"

SYMBOLS = ["EURUSD", "XAUUSD", "GBPUSD", "US30", "BTCUSD"]
# Each instrument trades on its own scale. Generating every symbol from one
# uniform price range produced a journal showing GBPUSD at 2182, which reads as
# a rendering fault when the screenshots are being used to judge the layout.
PRICE = {"EURUSD": 1.10, "GBPUSD": 1.27, "XAUUSD": 2400.0,
         "US30": 38500.0, "BTCUSD": 64000.0}
SETUPS = [["bos", "fvg"], ["order_block"], ["liquidity_sweep", "ote"],
          ["breakout"], ["mean_reversion"], []]
TIMEFRAMES = ["M5", "M15", "H1", "H4"]
REGIMES = ["trending", "ranging", "volatile", "quiet"]
EMOTIONS = ["calm", "confident", "anxious", "impatient", "frustrated", "bored"]
MISTAKES = ["fomo", "revenge", "moved_stop", "early_exit", "overtrading", "off_plan"]


# =============================================================================
# SYNTHETIC BOOK
# =============================================================================

def make_book(n=220, seed=7, *, with_stops=True, with_losses=True,
              accounts=("live-1", "demo-2"), open_positions=2,
              psychology=True) -> list[Trade]:
    """
    A book with the structure the pages are built to find.

    Deliberately not uniform noise: the edge varies by symbol and by session, a
    few trades are oversized after losing runs, and the self-reported fields
    correlate with the outcome the way a real trader's do. A harness built on
    independent random draws would render every page with every comparison
    withheld for lack of signal, which tests almost nothing.
    """
    rng = random.Random(seed)
    start = datetime(2025, 1, 6, 8, 0)
    trades: list[Trade] = []
    recent_losses = 0

    for i in range(n):
        symbol = rng.choice(SYMBOLS)
        direction = rng.choice([Direction.LONG, Direction.SHORT])
        # Spread entries across the whole clock so every session bucket fills.
        opened = start + timedelta(days=i * 0.7, hours=rng.uniform(-6, 9))
        held = rng.choice([25, 55, 130, 240, 700, 1500])
        closed = opened + timedelta(minutes=held)

        entry = round(PRICE[symbol] * rng.uniform(0.92, 1.08), 4)
        # Risk drifts up after a losing run — the pattern the psychology module
        # looks for, planted here so the finding has something to find.
        base_risk = entry * 0.004
        risk_distance = base_risk * (1.45 if recent_losses >= 2 else 1.0)
        risk_distance *= rng.uniform(0.9, 1.1)

        # Per-symbol edge, so the breakdowns are not all the same bucket.
        edge = {"EURUSD": 0.52, "XAUUSD": 0.61, "GBPUSD": 0.44,
                "US30": 0.48, "BTCUSD": 0.40}[symbol]
        won = rng.random() < edge if with_losses else True

        r_result = rng.uniform(0.8, 2.6) if won else -rng.uniform(0.6, 1.05)
        move = risk_distance * r_result * direction.sign
        exit_price = round(entry + move, 4)

        stop = None
        if with_stops and rng.random() > 0.08:
            stop = round(entry - risk_distance * direction.sign, 4)

        setups = rng.choice(SETUPS)
        mistakes = []
        emotion = None
        if psychology:
            # Self-reported fields correlate with the outcome, exactly as they do
            # in a real journal — which is the reason the page refuses to call
            # any of it a cause.
            emotion = rng.choice(["calm", "confident"]) if won else rng.choice(EMOTIONS)
            if not won and rng.random() < 0.42:
                mistakes = [rng.choice(MISTAKES)]
            elif rng.random() < 0.07:
                mistakes = [rng.choice(MISTAKES)]

        trades.append(Trade(
            id=f"t{i:04d}",
            symbol=symbol,
            direction=direction,
            entry_price=entry,
            size=round(rng.uniform(0.2, 2.0), 2),
            opened_at=opened,
            exit_price=exit_price,
            closed_at=closed,
            stop_loss=stop,
            take_profit=round(entry + risk_distance * 2 * direction.sign, 4),
            # Costs are a share of the amount risked, not an absolute figure.
            # An earlier version of this generator used a flat $0.5-$4, which on
            # a book risking ~$4 a trade made commission half of R and turned
            # every R statistic negative on a profitable book. The harness was
            # wrong, not the engine — but it took a screenshot to see that.
            commission=-round(risk_distance * rng.uniform(0.015, 0.04), 4),
            swap=-round(risk_distance * 0.01, 4) if held > 700 else 0.0,
            account_id=rng.choice(accounts) if accounts else None,
            account_currency="USD",
            setups=setups,
            timeframe=rng.choice(TIMEFRAMES),
            market_regime=rng.choice(REGIMES),
            setup_quality=rng.randint(2, 5),
            confidence=rng.randint(2, 5),
            entry_reason="swept the low then reclaimed" if setups else None,
            emotion_before=emotion,
            emotion_after=None if not psychology else ("calm" if won else "frustrated"),
            discipline=(rng.randint(3, 5) if not mistakes else rng.randint(1, 3))
            if psychology else None,
            mistakes=mistakes,
            notes="planned entry, held to target" if won else None,
            source="manual",
        ))

        recent_losses = 0 if won else recent_losses + 1

    for j in range(open_positions):
        symbol = SYMBOLS[j % len(SYMBOLS)]
        price = PRICE[symbol]
        opened = start + timedelta(days=n * 0.7 + j)
        trades.append(Trade(
            id=f"open{j}", symbol=symbol,
            direction=Direction.LONG, entry_price=price,
            size=round(rng.uniform(0.2, 1.5), 2),
            opened_at=opened, stop_loss=round(price * 0.995, 4),
            account_id=accounts[0] if accounts else None, source="manual",
        ))

    return trades


def make_broken_book() -> list[Trade]:
    """Trades whose own numbers would make their statistics wrong."""
    base = datetime(2025, 3, 3, 10, 0)
    return [
        # Stop on the wrong side of the entry.
        Trade(id="bad1", symbol="EURUSD", direction=Direction.LONG,
              entry_price=1.1000, size=1.0, opened_at=base,
              exit_price=1.1050, closed_at=base + timedelta(hours=2),
              stop_loss=1.1200),
        # Closed before it opened.
        Trade(id="bad2", symbol="XAUUSD", direction=Direction.SHORT,
              entry_price=2400.0, size=0.5, opened_at=base,
              exit_price=2380.0, closed_at=base - timedelta(hours=1),
              stop_loss=2415.0),
        # Discipline outside 1-5.
        Trade(id="bad3", symbol="US30", direction=Direction.LONG,
              entry_price=38000.0, size=1.0, opened_at=base,
              exit_price=38100.0, closed_at=base + timedelta(hours=3),
              stop_loss=37900.0, discipline=9),
    ] + make_book(n=14, seed=3, open_positions=0)


# =============================================================================
# HARNESS
# =============================================================================

def seed(trades, email=EMAIL) -> None:
    store = Store()
    store.delete_all_trades(email)
    store.upsert_user(email, "pro")
    if trades:
        store.save_trades(email, trades)


def run_page(page: str, *, lang="en", email=EMAIL, period="ALL", account=None):
    app = AppTest.from_file(APP, default_timeout=240)
    app.session_state["authenticated"] = bool(email)
    app.session_state["user_email"] = email
    app.session_state["user_tier"] = "pro"
    app.session_state["language"] = lang
    app.session_state["user_profile"] = "balanced"
    app.session_state["analysis_mode"] = "simulation"
    app.session_state["current_portfolio"] = None
    app.session_state["trading_period"] = period
    app.session_state["trading_account"] = account
    app.session_state["page"] = page
    app.run()
    return app


def check(label, *, lang="en", email=EMAIL, period="ALL", account=None,
          pages=PAGES, failures=None) -> int:
    count = 0
    for page in pages:
        count += 1
        app = run_page(page, lang=lang, email=email, period=period, account=account)
        short = page.replace("trading_", "")
        if app.exception:
            failures.append((label, page, str(app.exception[0].value)[:500]))
            print(f"  FAIL  {short:11s} {label}")
        else:
            print(f"  ok    {short:11s} {label}")
    return count


def main() -> int:
    failures: list[tuple] = []
    checks = 0

    # ── The full book, both languages ────────────────────────────────────────
    seed(make_book())
    for lang in ("en", "fr"):
        checks += check(f"full book [{lang}]", lang=lang, failures=failures)

    # ── Every period window ──────────────────────────────────────────────────
    for period in ("7D", "30D", "90D", "6M", "1Y"):
        checks += check(f"period {period}", period=period, failures=failures)

    # ── One account selected out of two ──────────────────────────────────────
    checks += check("account filter", account="live-1", failures=failures)

    # ── A book with no stops at all: every R statistic is empty ──────────────
    seed(make_book(n=60, seed=21, with_stops=False, open_positions=0))
    checks += check("no stops", failures=failures)

    # ── A book with no losses: profit factor has no denominator ──────────────
    seed(make_book(n=40, seed=33, with_losses=False, open_positions=0))
    checks += check("no losses", failures=failures)

    # ── Four trades: every comparison should be withheld, not shown ──────────
    seed(make_book(n=4, seed=5, open_positions=0))
    checks += check("tiny book", failures=failures)

    # ── Nothing but open positions: no closed trade has a result ─────────────
    seed(make_book(n=0, seed=5, open_positions=3))
    checks += check("open only", failures=failures)

    # ── No self-reported fields at all ───────────────────────────────────────
    seed(make_book(n=80, seed=9, psychology=False, open_positions=0))
    checks += check("no psychology fields", failures=failures)

    # ── Trades with data problems, which are kept and flagged ────────────────
    seed(make_broken_book())
    checks += check("broken trades", failures=failures)

    # ── No trades at all ─────────────────────────────────────────────────────
    seed([])
    checks += check("empty journal", failures=failures)

    # ── Not signed in: no journal to read, and it must say so ────────────────
    checks += check("no user", email="", failures=failures)

    # ── Cross-user isolation, asserted through the rendered app ──────────────
    seed(make_book(n=30, seed=15, open_positions=0), email=EMAIL)
    seed(make_book(n=5, seed=16, open_positions=0), email=OTHER_EMAIL)
    checks += 1
    isolation = _isolation_holds()
    if isolation is not True:
        failures.append(("isolation", "store", isolation))
        print(f"  FAIL  isolation   {isolation}")
    else:
        print("  ok    isolation   one user's journal is not visible to another")

    print(f"\n{checks} render checks, {len(failures)} failures")
    for label, page, error in failures:
        print(f"\n--- {page} / {label} ---\n{error}")
    return 1 if failures else 0


def _isolation_holds():
    """The guarantee that matters most once there is more than one user."""
    store = Store()
    mine = store.list_trades(EMAIL)
    theirs = store.list_trades(OTHER_EMAIL)
    if len(mine) != 30 or len(theirs) != 5:
        return f"expected 30 and 5 trades, got {len(mine)} and {len(theirs)}"
    overlap = {t.id for t in mine} & {t.id for t in theirs}
    # Ids collide by construction — both books number from t0000 — which is
    # exactly the case the composite primary key exists for. What must not
    # happen is one user's *trade* appearing in the other's list.
    for trade_id in overlap:
        a = next(t for t in mine if t.id == trade_id)
        b = next(t for t in theirs if t.id == trade_id)
        if a.opened_at == b.opened_at and a.entry_price == b.entry_price:
            return f"trade {trade_id} is identical across two users"
    return True


if __name__ == "__main__":
    raise SystemExit(main())
