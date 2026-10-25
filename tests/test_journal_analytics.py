"""
The trading analytics and the MetaTrader 5 synchronisation inside the
« Journal de trading » space, and the clock every reader puts the book on.

    python tests/test_journal_analytics.py

No terminal is ever reached: the synchronisation is given a fake MetaTrader 5
terminal through the module's `connector` seam, as tests/test_mt5_connector.py
does for the connector itself.
"""

from __future__ import annotations

import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from html import unescape

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["SENSITOR_DB_PATH"] = os.path.join(tempfile.mkdtemp(prefix="sensitor-journal-analytics-"), "j.db")
os.environ["SENSITOR_AUTH"] = "multi"

from streamlit.testing.v1 import AppTest  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "sensitor_app.py")
ANALYTICS_APP = os.path.join(ROOT, "portfolio_optimizer_saas.py")
CHECKS: list[tuple[str, bool, str]] = []
DASHES = (chr(0x2014), chr(0x2013))


def check(name: str, condition: bool, detail: str = "") -> None:
    CHECKS.append((name, bool(condition), detail))
    print(f"  {'ok  ' if condition else 'FAIL'}  {name}" + (f"   {detail}" if detail and not condition else ""))


def store():
    from sensitor.database import Store
    return Store(os.environ["SENSITOR_DB_PATH"])


def token(email: str) -> str:
    from sensitor.core.auth import Auth
    auth = Auth(store(), mode="multi")
    result = auth.sign_up(email, "un-mot-de-passe-solide")
    return result.token if result else auth.sign_in(email, "un-mot-de-passe-solide").token


def run(route: dict, tok: str | None = None, *, app_file: str = APP, state: dict | None = None) -> AppTest:
    app = AppTest.from_file(app_file, default_timeout=180)
    app.session_state["ac_route"] = route
    if tok:
        app.session_state["session_token"] = tok
    for key, value in (state or {}).items():
        app.session_state[key] = value
    app.run()
    return app


def page_text(app: AppTest) -> str:
    return unescape("\n".join(m.value for m in app.markdown if not m.value.lstrip().startswith("<style")))


def error(app: AppTest) -> str:
    return str(app.exception[0].value)[:300] if app.exception else ""


def mixed_book():
    """
    The case that broke the dashboard: trades entered in the platform, on aware
    UTC, next to trades synchronised from MetaTrader 5, on naive UTC.
    """
    from sensitor.trading import demo
    trades = demo.trades()
    platform = trades[:20]
    synced = [t.annotated(id=f"mt5-{t.id}", source="mt5", opened_at=t.opened_at.replace(tzinfo=None),
                          closed_at=t.closed_at.replace(tzinfo=None) if t.closed_at else None)
              for t in trades[20:40]]
    return platform + synced


# =============================================================================
# A fake MetaTrader 5 terminal
# =============================================================================

def epoch(moment: datetime) -> float:
    return moment.replace(tzinfo=timezone.utc).timestamp()


class FakeTerminal:
    """What the connector calls on the MetaTrader5 package, with two round turns in the last fortnight."""

    def __init__(self):
        from sensitor.integrations import mt5
        self.init_kwargs = None
        now = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
        self._deals = []
        for position, (days, side, entry, exit_, profit) in enumerate(
                ((10, mt5.DEAL_TYPE_BUY, 1.1000, 1.1050, 500.0), (4, mt5.DEAL_TYPE_SELL, 1.1100, 1.1130, -300.0)),
                start=1):
            opened = now - timedelta(days=days, hours=3)
            closed = now - timedelta(days=days, hours=1)
            other = mt5.DEAL_TYPE_SELL if side == mt5.DEAL_TYPE_BUY else mt5.DEAL_TYPE_BUY
            for ticket, kind, flow, price, at, gain in (
                    (position * 10, side, mt5.DEAL_ENTRY_IN, entry, opened, 0.0),
                    (position * 10 + 1, other, mt5.DEAL_ENTRY_OUT, exit_, closed, profit)):
                self._deals.append({"ticket": ticket, "order": ticket, "position_id": position,
                                    "time": epoch(at), "time_msc": epoch(at) * 1000, "type": kind, "entry": flow,
                                    "symbol": "EURUSD", "volume": 1.0, "price": price, "commission": -3.5,
                                    "swap": 0.0, "fee": 0.0, "profit": gain, "magic": 0, "comment": ""})

    def initialize(self, **kwargs):
        self.init_kwargs = kwargs
        return True

    def shutdown(self):
        pass

    def last_error(self):
        return (1, "ok")

    def account_info(self):
        return {"login": 51234567, "name": "Compte test", "company": "Broker Ltd", "server": "Broker-Live",
                "currency": "EUR", "balance": 10_000.0, "equity": 10_200.0, "leverage": 30}

    def history_deals_get(self, start, end):
        return tuple(self._deals)

    def history_orders_get(self, start, end):
        return ()

    def positions_get(self):
        return ()


def main() -> int:
    from sensitor.platform import spaces
    from sensitor.platform.ui import journal_analysis as JA
    from sensitor.trading.models import on_utc_clock

    print("\nOne clock for the whole book")
    book = mixed_book()
    try:
        sorted(book, key=lambda t: t.closed_at)
        broke = False
    except TypeError:
        broke = True
    check("a book mixing naive and aware times cannot be sorted as it is stored", broke)
    aware = on_utc_clock(book, aware=True)
    naive = on_utc_clock(book, aware=False)
    check("on the platform's clock, every time is aware UTC and the book sorts",
          all(t.opened_at.tzinfo is not None and t.opened_at.utcoffset() == timedelta(0) for t in aware)
          and len(sorted(aware, key=lambda t: t.closed_at)) == len(book))
    check("on the separate app's clock, every time is naive and the book sorts",
          all(t.opened_at.tzinfo is None for t in naive) and len(sorted(naive, key=lambda t: t.closed_at)) == len(book))
    check("a naive time is read as UTC: the same instant on both clocks",
          all(a.opened_at.replace(tzinfo=None) == n.opened_at for a, n in zip(aware, naive)))
    check("the stored trades are not changed, only the copies read",
          book[25].opened_at.tzinfo is None and book[0].opened_at.tzinfo is not None)

    print("\nThe space in the registry")
    space = spaces.space("journal")
    check("the four analysis pages belong to the journal space",
          {p for p, _l, _r in JA.PAGES} <= set(space.pages))
    check("MetaTrader 5 synchronisation is no longer announced as coming", not any(
        "Synchronisation MetaTrader 5" in x for x in space.planned))

    alice = token("alice@example.com")
    store().save_trades("alice@example.com", book)

    print("\nThe dashboard and the separate app, on a mixed book")
    dash = run({"page": "journal"}, alice)
    check("the dashboard renders on its default period (it raised a TypeError before)",
          not dash.exception and "Ce que vos écarts vous ont coûté" in page_text(dash), error(dash))
    for period in ("30", "all"):
        dash.radio(key="jr_period_dash").set_value(period).run()
        check(f"and on the period « {period} »", not dash.exception, error(dash))
    trades = run({"page": "journal_trades"}, alice)
    check("the list of trades renders", not trades.exception, error(trades))
    legacy = run({}, alice, app_file=ANALYTICS_APP, state={"page": "trading_overview", "language": "fr"})
    check("the separate app's trading overview renders on the same book", not legacy.exception, error(legacy))

    print("\nThe analysis pages, for a member")
    for page, label, _render in JA.PAGES:
        app = run({"page": page}, alice)
        body = page_text(app)
        check(f"{label}: renders the analysis in French, in the space's navigation",
              not app.exception and "snr-" in "\n".join(m.value for m in app.markdown)
              and {"Tableau de bord", "Performance", "Analyse", "Risque", "Comportement", "Saisir"}
              <= {b.label for b in app.button}, error(app))
        check(f"{label}: no long dash", not any(d in body for d in DASHES))
    overview = page_text(run({"page": "journal_performance"}, alice))
    check("the performance page is the analytics overview, in French", "Votre trading, sur un seul écran." in overview)

    print("\nA visitor, an empty journal, another member, the demonstration")
    visitor = run({"page": "journal_risk"})
    check("a visitor is asked to sign in, and sees no analysis",
          "Connectez-vous pour analyser vos trades." in page_text(visitor) and "snr-kpi" not in page_text(visitor)
          and not visitor.exception, error(visitor))
    bob = token("bob@example.com")
    empty = run({"page": "journal_analysis"}, bob)
    check("a member with no trades gets the journal's own empty state",
          "Votre journal est vide" in page_text(empty) and not empty.exception, error(empty))
    check("and nothing of another member's book", "EURUSD" not in page_text(empty)
          and not any(t.id.startswith("mt5-") for t in store().list_trades("bob@example.com")))
    demo_on = run({"page": "journal_behaviour"}, alice, state={"jr_demo": True})
    check("with the demonstration on the dashboard, the analyses say they read the member's own journal",
          "Vos trades, pas l'exemple" in page_text(demo_on) and not demo_on.exception, error(demo_on))

    print("\nSynchronising MetaTrader 5")
    absent = run({"page": "journal_add"}, alice)
    check("on a server without the terminal, the page says so and offers no form",
          "Pas de terminal sur ce serveur" in page_text(absent) and not any(
              t.key == "jr_mt5_password" for t in absent.text_input), error(absent))
    fake = FakeTerminal()
    from sensitor.integrations.mt5 import MT5Connector
    JA.terminal_available = lambda: True
    JA.connector = lambda config: MT5Connector(config, terminal=fake)
    erin = token("erin@example.com")
    app = run({"page": "journal_add"}, erin)
    labels = [t.label.lower() for t in app.text_input]
    check("the form asks for the investor password, read only, and nothing like a seed or a private key",
          any("mot de passe investisseur" in x for x in labels)
          and not any(w in x for x in labels for w in ("seed", "phrase", "clé privée", "private key")))
    app.text_input(key="jr_mt5_login").set_value("51234567")
    app.text_input(key="jr_mt5_password").set_value("lecture-seule-123")
    app.text_input(key="jr_mt5_server").set_value("Broker-Live")
    app.number_input(key="jr_mt5_offset").set_value(2.0)
    [b for b in app.button if b.label == "Synchroniser"][0].click().run()
    synced = store().list_trades("erin@example.com")
    check("the terminal's history is written to that member's journal",
          not app.exception and len(synced) == 2 and all(t.source == "mt5" for t in synced), error(app) or str(synced))
    check("the connector got the account, the server and the password, and the offset moved the times",
          fake.init_kwargs and fake.init_kwargs.get("login") == 51234567
          and fake.init_kwargs.get("server") == "Broker-Live" and fake.init_kwargs.get("password") == "lecture-seule-123")
    said = " ".join(m.value for m in app.success)
    check("the page reports what came back", "Synchronisation terminée" in said and "2 trades récupérés" in said, said)
    remembered = app.session_state[JA.SYNC_DEFAULTS]
    check("the password is not kept: neither in the remembered settings nor in the form",
          "lecture-seule-123" not in str(remembered) and app.text_input(key="jr_mt5_password").value in ("", None)
          and remembered.get("login") == "51234567")
    check("the synced account is listed with its last synchronisation", "dernière synchronisation" in page_text(app))
    check("nothing reaches another member", not store().list_trades("bob@example.com"))
    first = synced[0]
    store().save_trade("erin@example.com", first.annotated(notes="Entrée trop tôt."))
    again = run({"page": "journal_add"}, erin)
    [b for b in again.button if b.label == "Synchroniser"][0].click().run()
    kept = store().get_trade("erin@example.com", first.id)
    check("a second sync adds no duplicate and keeps what the member wrote",
          len(store().list_trades("erin@example.com")) == 2 and kept.notes == "Entrée trop tôt.")
    after = run({"page": "journal"}, erin)
    check("the synced trades are reviewed on the dashboard", not after.exception
          and "Ce que vos écarts vous ont coûté" in page_text(after), error(after))

    failures = [c for c in CHECKS if not c[1]]
    print(f"\n{len(CHECKS)} checks, {len(failures)} failures")
    for name, _, detail in failures:
        print(f"  FAIL  {name}   {detail}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
