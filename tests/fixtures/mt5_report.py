"""
Constructed MetaTrader 5 history reports, for tests/test_mt5_report.py.

Built the way the terminal writes its « Report » export, from the layout of the
HTML file MT5 produces: a header block, then the « Positions » table (thirteen
visible columns, a hidden filler cell after « Type », « Profit » merged over two
columns), then « Orders » and « Deals », in UTF-16 with a byte order mark. The
XLSX version puts the same rows in a worksheet. The account, names and figures
are invented.
"""

from __future__ import annotations

import io
import zipfile
from datetime import datetime, timedelta

HEADER_EN = ["Time", "Position", "Symbol", "Type", "Volume", "Price", "S / L", "T / P", "Time", "Price",
             "Commission", "Swap", "Profit"]
HEADER_FR = ["Heure", "Position", "Symbole", "Type", "Volume", "Prix", "S / L", "T / P", "Heure", "Prix",
             "Commission", "Swap", "Profit"]


def positions(now: datetime | None = None) -> list[list[str]]:
    """Three closed positions in the last three weeks, on server time."""
    now = (now or datetime.utcnow()).replace(microsecond=0)
    def t(days, hours):
        return (now - timedelta(days=days, hours=hours)).strftime("%Y.%m.%d %H:%M:%S")
    return [
        [t(20, 6), "1001", "EURUSD", "buy", "1", "1.08000", "1.07800", "1.08400", t(20, 4), "1.08300", "-7.00",
         "0.00", "300.00"],
        [t(12, 5), "1002", "XAUUSD", "sell", "0.5", "2 350.50", "2 360.50", "", t(12, 3), "2 360.50", "-3.50",
         "-1.20", "-500.00"],
        [t(3, 9), "1003", "GBPUSD", "buy", "0.2", "1.27000", "", "", t(3, 7), "1.27250", "-1.40", "0.00",
         "50.00"],
    ]


def html_report(rows=None, *, header=HEADER_EN, account="51234567 (EUR, Broker-Live, real, Hedge)") -> bytes:
    rows = positions() if rows is None else rows
    def tr(cells, tag="td"):
        out = []
        for i, c in enumerate(cells):
            if i == 4:
                out.append('<td class="hidden" colspan="8"></td>')
            span = ' colspan="2"' if i == 12 else ""
            out.append(f"<{tag}{span}>{c}</{tag}>")
        return '<tr align="right">' + "".join(out) + "</tr>"
    body = "".join(tr(r) for r in rows)
    doc = (
        "<html><head><title>51234567: Trade History Report</title></head><body><table>"
        '<tr><th colspan="14"><div><b>Trade History Report</b></div></th></tr>'
        f'<tr><th colspan="4">Name:</th><th colspan="10"><b>A. Trader</b></th></tr>'
        f'<tr><th colspan="4">Account:</th><th colspan="10"><b>{account}</b></th></tr>'
        '<tr><th colspan="4">Company:</th><th colspan="10"><b>Broker Ltd</b></th></tr>'
        '<tr><td colspan="14"><div><b>Positions</b></div></td></tr>'
        + tr(header, "td") + body +
        '<tr><td colspan="14"><div><b>Orders</b></div></td></tr>'
        "<tr><td>Open Time</td><td>Order</td><td>Symbol</td><td>Type</td><td>Volume</td><td>Price</td>"
        "<td>S / L</td><td>T / P</td><td>Time</td><td>State</td><td>Comment</td></tr>"
        "<tr><td>2025.03.10 09:00:00</td><td>1001</td><td>EURUSD</td><td>buy</td><td>1 / 1</td><td>1.08</td>"
        "<td></td><td></td><td>2025.03.10 09:00:00</td><td>filled</td><td></td></tr>"
        '<tr><td colspan="14"><div><b>Deals</b></div></td></tr>'
        "</table></body></html>"
    )
    return b"\xff\xfe" + doc.encode("utf-16-le")


def xlsx_report(rows=None, *, header=HEADER_FR, account="51234567 (EUR, Broker-Live, real, Hedge)") -> bytes:
    rows = positions() if rows is None else rows
    strings: list[str] = []
    def ref(text):
        if text not in strings:
            strings.append(text)
        return strings.index(text)
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    sheet_rows = [["Rapport d'historique des transactions"], ["Compte:", account], ["Positions"], header, *rows]
    xml_rows = []
    for r, cells in enumerate(sheet_rows, start=1):
        cols = []
        for i, value in enumerate(cells):
            if value == "":
                continue
            col = i if i < 4 else i + 1          # a blank column after « Type », as the filler cell
            cols.append(f'<c r="{letters[col]}{r}" t="s"><v>{ref(value)}</v></c>')
        xml_rows.append(f'<row r="{r}">{"".join(cols)}</row>')
    ns = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
    sheet = f'<?xml version="1.0" encoding="UTF-8"?><worksheet {ns}><sheetData>{"".join(xml_rows)}</sheetData></worksheet>'
    shared = (f'<?xml version="1.0" encoding="UTF-8"?><sst {ns}>'
              + "".join(f"<si><t>{s.replace('&', '&amp;')}</t></si>" for s in strings) + "</sst>")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as book:
        book.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types/>')
        book.writestr("xl/worksheets/sheet1.xml", sheet)
        book.writestr("xl/sharedStrings.xml", shared)
    return buffer.getvalue()
