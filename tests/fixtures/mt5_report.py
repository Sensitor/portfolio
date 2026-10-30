"""
Constructed MetaTrader 5 history reports, for tests/test_mt5_report.py.

Built on the layout of a real export (« Report », « HTML », from the History tab
of MetaTrader 5, October 2026): a header block with the account line written
with `&nbsp;`, the « Positions » table whose header has thirteen cells and whose
data rows add a hidden filler cell (`class="hidden" colspan="8"`) after « Type »,
« Profit » merged over two columns, then « Orders », « Deals », « Open Positions »
and « Results », in UTF-16 with a byte order mark. The XLSX version puts the
same rows in a worksheet. The account, names and figures are invented.
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


def special_positions(now: datetime | None = None) -> list[list[str]]:
    """A short whose last stop sits in profit, and a position partly closed (0.15 lot out of 0.2)."""
    now = (now or datetime.utcnow()).replace(microsecond=0)
    def t(days, hours):
        return (now - timedelta(days=days, hours=hours)).strftime("%Y.%m.%d %H:%M:%S")
    return [
        [t(2, 6), "1004", "XAUUSD.s", "sell", "0.1", "4178.94", "4178.90", "4148.09", t(2, 5), "4178.90", "0.00",
         "0.00", "0.36"],
        [t(1, 9), "1005", "BTCUSD", "sell", "0.15 / 0.2", "84515.11", "85510.00", "", t(1, 2), "82353.73", "0.00",
         "0.00", "288.37"],
    ]


def html_report(rows=None, *, header=HEADER_EN, account="51234567&nbsp;(EUR,&nbsp;Broker-Live,&nbsp;real,&nbsp;Hedge)") -> bytes:
    rows = positions() if rows is None else rows
    def tr(cells, *, data=True):
        out = []
        for i, c in enumerate(cells):
            if data and i == 4:
                out.append('<td class="hidden" colspan="8"></td>')
            span = ' colspan="2"' if i == 12 else ""
            klass = ' class=""' if data and i >= 4 and i != 12 else ""
            out.append(f"<td{span}{klass}>{c}</td>" if data else f'<td nowrap=""{span}><b>{c}</b></td>')
        colour = 'bgcolor="#FFFFFF" align="right"' if data else 'align="center" bgcolor="#E5F0FC"'
        return f"<tr {colour}> " + " ".join(out) + " </tr>"
    body = "".join(tr(r) for r in rows)
    doc = (
        "<html><head><title>51234567: Trade History Report</title><style>td { font: 8pt Tahoma }</style></head>"
        "<body><table>"
        '<tr align="center"><td colspan="14"><div style="font: 14pt Tahoma"><b>Trade History Report</b><br></div></td></tr>'
        '<tr align="left"><th colspan="4" nowrap="" align="right">Name:</th><th colspan="10"><b>A. Trader</b></th></tr>'
        f'<tr align="left"><th colspan="4" nowrap="" align="right">Account:</th><th colspan="10"><b>{account}</b></th></tr>'
        '<tr align="left"><th colspan="4" nowrap="" align="right">Company:</th><th colspan="10"><b>Broker Ltd</b></th></tr>'
        '<tr><td nowrap="" style="width: 140px;height: 10px"></td><td nowrap="" style="width: 60px;"></td></tr>'
        '<tr align="center"><th colspan="14" style="height: 25px"><div><b>Positions</b></div></th></tr>'
        + tr(header, data=False) + body +
        '<tr align="center"><th colspan="14"><div><b>Orders</b></div></th></tr>'
        "<tr><td>Open Time</td><td>Order</td><td>Symbol</td><td>Type</td><td>Volume</td><td>Price</td>"
        '<td>S / L</td><td>T / P</td><td>Time</td><td colspan="2">State</td><td colspan="3">Comment</td></tr>'
        "<tr><td>2025.03.10 09:00:00</td><td>1001</td><td>EURUSD</td><td>buy</td><td>1 / 1</td><td>market</td>"
        '<td></td><td></td><td>2025.03.10 09:00:00</td><td colspan="2">filled</td><td colspan="3"></td></tr>'
        '<tr align="center"><th colspan="14"><div><b>Deals</b></div></th></tr>'
        '<tr align="center"><th colspan="14"><div><b>Open Positions</b></div></th></tr>'
        "<tr><td>Time</td><td>Position</td><td>Symbol</td><td>Type</td><td>Volume</td><td>Price</td><td>S / L</td>"
        "<td>T / P</td><td>Market Price</td><td>Swap</td><td>Profit</td><td>Comment</td></tr>"
        "<tr><td>2025.03.11 09:00:00</td><td>2001</td><td>EURUSD</td><td>buy</td><td>0.05</td><td>1.09</td>"
        "<td></td><td></td><td>1.091</td><td>0.00</td><td>5.00</td><td></td></tr>"
        '<tr align="center"><th colspan="14"><div><b>Results</b></div></th></tr>'
        "<tr><td>Total Net Profit:</td><td>-150.00</td><td>Gross Profit:</td><td>350.00</td></tr>"
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
