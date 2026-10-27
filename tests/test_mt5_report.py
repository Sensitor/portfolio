"""
The MetaTrader 5 history report, imported without a terminal, and the setups
the journal offers.

    python tests/test_mt5_report.py

The reports are constructed (tests/fixtures/mt5_report.py) on the layout of the
file the terminal exports: UTF-16 HTML with a hidden filler cell and a merged
« Profit » cell, and the same rows in an XLSX workbook with French labels.
"""

from __future__ import annotations

import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from html import unescape

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ["SENSITOR_DB_PATH"] = os.path.join(tempfile.mkdtemp(prefix="sensitor-mt5-report-"), "r.db")
os.environ["SENSITOR_AUTH"] = "multi"

from streamlit.testing.v1 import AppTest  # noqa: E402

from fixtures.mt5_report import HEADER_FR, html_report, positions, special_positions, xlsx_report  # noqa: E402

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sensitor_app.py")
CHECKS: list[tuple[str, bool, str]] = []


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


def run(route: dict, tok: str | None = None) -> AppTest:
    app = AppTest.from_file(APP, default_timeout=180)
    app.session_state["ac_route"] = route
    if tok:
        app.session_state["session_token"] = tok
    app.run()
    return app


def page_text(app: AppTest) -> str:
    return unescape("\n".join(m.value for m in app.markdown if not m.value.lstrip().startswith("<style")))


def error(app: AppTest) -> str:
    return str(app.exception[0].value)[:300] if app.exception else ""


def main() -> int:
    from sensitor.integrations import mt5, mt5_report as R, sync
    from sensitor.trading import setups as TS

    print("\nReading the report")
    rows = positions(datetime(2026, 1, 20, 12, 0))
    html = R.read(html_report(rows), "ReportHistory-51234567.html", clock=2.0)
    check("the HTML report, in UTF-16: three closed positions, the account and its currency",
          len(html.trades) == 3 and html.account_login == "51234567" and html.currency == "EUR" and not html.skipped,
          str((len(html.trades), html.account_login, html.currency, html.skipped)))
    xlsx = R.read(xlsx_report(rows), "ReportHistory-51234567.xlsx", clock=2.0)
    check("the Excel report with French labels reads the same trades",
          [(t.id, t.symbol, t.entry_price, t.exit_price, t.stop_loss, t.gross_pnl) for t in xlsx.trades]
          == [(t.id, t.symbol, t.entry_price, t.exit_price, t.stop_loss, t.gross_pnl) for t in html.trades])
    first, gold, cable = html.trades
    check("ids are the terminal sync's own, so a report and a sync never duplicate a trade",
          first.id == mt5.trade_id(1001, "mt5-51234567") == "mt5-51234567-1001" and first.source == "mt5")
    check("direction, prices, stop, target and result are the report's",
          first.direction.value == "long" and gold.direction.value == "short" and first.entry_price == 1.08
          and first.exit_price == 1.083 and first.stop_loss == 1.078 and first.take_profit == 1.084
          and first.gross_pnl == 300.0 and first.commission == -7.0 and gold.swap == -1.2)
    check("a number grouped with a space is read whole", gold.entry_price == 2350.5)
    check("with its stop, a trade has an R: +300 over a risk of 0.002 per 1.0 lot at 100 000 per point",
          abs(first.r_multiple - (300.0 - 7.0) / (0.002 * 100_000)) < 1e-9, str(first.r_multiple))
    check("without a stop, no R is made up", cable.stop_loss is None and cable.r_multiple is None)
    check("the server's offset moves the times to UTC",
          first.opened_at == datetime.strptime(rows[0][0], "%Y.%m.%d %H:%M:%S") - timedelta(hours=2))

    print("\nThe broker's clock")
    check("New York + 7 is UTC+2 in winter and UTC+3 in summer, on the American dates",
          R.server_offset(datetime(2026, 1, 15, 10), R.NY_PLUS_7) == 2
          and R.server_offset(datetime(2026, 7, 15, 10), R.NY_PLUS_7) == 3
          and R.server_offset(datetime(2026, 3, 9, 10), R.NY_PLUS_7) == 3
          and R.server_offset(datetime(2026, 11, 2, 10), R.NY_PLUS_7) == 2)
    summer = positions(datetime(2026, 7, 20, 12, 0))
    ny = R.read(html_report(summer), clock=R.NY_PLUS_7)
    check("a summer trade read on New York + 7 is three hours behind the server clock",
          ny.trades[0].opened_at == datetime.strptime(summer[0][0], "%Y.%m.%d %H:%M:%S") - timedelta(hours=3))

    print("\nThe layout of a real export")
    special = R.read(html_report(rows + special_positions(datetime(2026, 1, 20, 12, 0))), clock=2.0)
    check("the filler cell sits in data rows only, and the values stay under their header",
          len(special.trades) == 5 and special.trades[0].exit_price == 1.083 and special.trades[0].take_profit == 1.084)
    check("the « Open Positions » and « Results » tables are not read as trades",
          all(t.symbol != "EURUSD" or t.id.endswith("1001") for t in special.trades))
    protected, partial_pos = special.trades[3], special.trades[4]
    check("a last stop in profit is a protection, not a risk: no R is made up for it",
          protected.stop_loss is None and protected.r_multiple is None and protected.raw["last_stop"] == 4178.90
          and special.protective_stops == 1)
    check("a stop on the losing side is kept", partial_pos.stop_loss == 85510.0 and partial_pos.r_multiple is not None)
    check("« 0.15 / 0.2 »: a position partly closed is read for its closed part",
          partial_pos.raw["partly_closed"] == {"closed": 0.15, "opened": 0.2} and partial_pos.gross_pnl == 288.37)
    check("prices keep the report's digits", partial_pos.entry_price == 84515.11)
    check("the stop rule, both ways", R.risk_stop(mt5.DEAL_TYPE_BUY, 100.0, 99.0) == 99.0
          and R.risk_stop(mt5.DEAL_TYPE_BUY, 100.0, 100.0) is None and R.risk_stop(mt5.DEAL_TYPE_SELL, 100.0, 99.0) is None
          and R.risk_stop(mt5.DEAL_TYPE_SELL, 100.0, 101.0) == 101.0 and R.risk_stop(mt5.DEAL_TYPE_BUY, 100.0, None) is None)

    print("\nWhat it refuses, and what it skips")
    for label, raw in (("an empty file", b""), ("a page with no Positions table", b"<html><table><tr><td>x</td></tr></table></html>"),
                       ("a broken Excel file", b"PK\x03\x04 not a zip")):
        try:
            R.read(raw, "x.xlsx" if raw.startswith(b"PK") else "x.html")
            refused = False
        except R.ReportError:
            refused = True
        check(f"refuses {label}, with a reason", refused)
    bad = [r[:] for r in rows]
    bad[1][3] = "balance"
    partial = R.read(html_report(bad), clock=2.0)
    check("an incomplete line is skipped and named, the others are read",
          len(partial.trades) == 2 and partial.skipped and "incomplète" in partial.skipped[0][1])
    unlabelled = R.read(html_report(rows, account="A. Trader"), clock=2.0, currency="USD")
    check("without the account line, the currency asked for is used and ids are still stable",
          unlabelled.currency == "USD" and unlabelled.trades[0].id == "mt5-1001")

    print("\nImporting: the same merge as a sync")
    email = "rapport@example.com"
    result = sync.sync_trades(R.ReportSource(html), store(), email, since=min(t.opened_at for t in html.trades))
    check("three trades added, the account recorded", result.added == 3
          and any(a.id == "mt5-51234567" for a in store().list_accounts(email)))
    store().save_trade(email, store().get_trade(email, first.id).annotated(notes="Sortie trop tôt.",
                                                                            setups=["ote", "bos"]))
    again = sync.sync_trades(R.ReportSource(xlsx), store(), email, since=min(t.opened_at for t in xlsx.trades))
    kept = store().get_trade(email, first.id)
    check("the same history imported again, from the other format: no duplicate, annotations kept",
          len(store().list_trades(email)) == 3 and again.added == 0 and kept.notes == "Sortie trop tôt."
          and kept.setups == ["ote", "bos"])
    fixed = kept.annotated(stop_loss=1.0790, raw={**kept.raw, "stop_by_member": True})
    store().save_trade(email, fixed)
    sync.sync_trades(R.ReportSource(html), store(), email, since=min(t.opened_at for t in html.trades))
    after = store().get_trade(email, first.id)
    check("an initial stop the member wrote survives a new import, which only knows the last stop",
          after.stop_loss == 1.0790 and after.raw.get("stop_by_member") is True, str((after.stop_loss, after.raw)))

    print("\nThe entry page")
    member = token("membre@example.com")
    app = run({"page": "journal_add"}, member)
    body = page_text(app)
    check("the page leads with the MetaTrader 5 report and its four steps",
          not app.exception and body.index("Importer depuis MetaTrader 5") < body.index("Saisir un trade")
          and "Boîte à outils" in body and "Historique" in body and "Open XML" in body, error(app))
    check("the clock defaults to New York + 7", app.selectbox(key="jr_report_clock").value == "ny+7")
    recent = positions()
    app.file_uploader(key="jr_report").set_value(("ReportHistory-51234567.html", html_report(recent), "text/html"))
    app.run()
    check("a dropped report says what it found before anything is written",
          "<b>3</b> positions clôturées trouvées (compte 51234567, EUR)" in page_text(app)
          and not store().list_trades("membre@example.com"),
          page_text(app)[-400:])
    [b for b in app.button if b.key == "jr_report_go"][0].click().run()
    saved = store().list_trades("membre@example.com")
    said = " ".join(m.value for m in app.success)
    check("« Importer » writes the trades to that member's journal and says so",
          len(saved) == 3 and "Import terminé : 3 ajoutés" in said, said or error(app))
    check("nothing reaches another member", not store().list_trades("autre@example.com"))
    dash = run({"page": "journal"}, member)
    check("the imported trades are reviewed on the dashboard", not dash.exception
          and "Ce que vos écarts vous ont coûté" in page_text(dash), error(dash))
    cable_id = next(t.id for t in saved if t.symbol == "GBPUSD")
    sheet = run({"page": "journal_trade", "trade": cable_id}, member)
    check("an imported trade offers its initial stop", any(n.key == f"jr_an_stop_{cable_id}" for n in sheet.number_input))
    sheet.number_input(key=f"jr_an_stop_{cable_id}").set_value(1.2800).run()
    [b for b in sheet.button if b.label == "Enregistrer les annotations"][0].click().run()
    check("a stop on the wrong side is refused, and nothing is saved",
          "du côté de la perte" in " ".join(e.value for e in sheet.error)
          and store().get_trade("membre@example.com", cable_id).stop_loss is None)
    sheet = run({"page": "journal_trade", "trade": cable_id}, member)
    sheet.number_input(key=f"jr_an_stop_{cable_id}").set_value(1.2680).run()
    [b for b in sheet.button if b.label == "Enregistrer les annotations"][0].click().run()
    fixed = store().get_trade("membre@example.com", cable_id)
    check("with its initial stop, the trade gets its R and keeps it as the member's",
          fixed.stop_loss == 1.268 and fixed.r_multiple is not None and fixed.raw.get("stop_by_member") is True,
          str((fixed.stop_loss, fixed.r_multiple)))

    print("\nSetups")
    check("the entry form offers the shorthand first", [o for o in app.multiselect(key="jr_e_setups").options][:6]
          == ["OTE", "BOS", "CHoCH", "FVG", "iFVG", "Expansion 50 %"], str(app.multiselect(key="jr_e_setups").options[:6]))
    check("News is offered", "News" in app.multiselect(key="jr_e_setups").options)
    check("every setup label is short, without a long name", all(len(TS.setup_label(k, "fr")) <= 20 for k in TS.SETUPS))

    failures = [c for c in CHECKS if not c[1]]
    print(f"\n{len(CHECKS)} checks, {len(failures)} failures")
    for name, _, detail in failures:
        print(f"  FAIL  {name}   {detail}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
