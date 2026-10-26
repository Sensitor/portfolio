"""
The MetaTrader 5 history report, read without a terminal.

MetaTrader 5 exports an account's history from the Toolbox: the « History »
tab, right click, « Report », then « HTML » or « Open XML (MS Office Excel
2007) ». The file is the same in every language of the terminal, apart from its
labels, and its « Positions » table holds one line per closed position:

    Time | Position | Symbol | Type | Volume | Price | S / L | T / P | Time | Price | Commission | Swap | Profit

The table is found by its shape rather than its words: a header of thirteen
cells whose seventh and eighth are « S / L » and « T / P » (the « Orders » table
has eleven, « Open Positions » twelve), then the lines below it whose first and
ninth cells are times. Columns are matched by position in that header, so a
hidden filler cell or a merged « Profit » cell moves nothing.

Each line becomes the two deals the terminal would have returned for it, an in
and an out, and goes through `mt5.build_trade`: the same trade ids as a live
synchronisation (`mt5-<account>-<position>`), so importing a report and later
syncing the terminal, or importing the same report twice, never duplicates a
trade; and the same rules for the price-per-point and the times, which the
report gives on the broker's server clock.

No Streamlit, no network. HTML is read with the standard library, and so is
the XLSX file, which is a zip of XML.
"""

from __future__ import annotations

import html as _html
import io
import re
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from xml.etree import ElementTree
from zoneinfo import ZoneInfo

from . import mt5

NEW_YORK = ZoneInfo("America/New_York")
NY_PLUS_7 = "ny+7"      # server clock = New York + 7 h: UTC+2 in winter, UTC+3 in summer

COLUMNS = ("opened", "position", "symbol", "type", "volume", "open_price", "sl", "tp", "closed", "close_price",
           "commission", "swap", "profit")
TIME_FORMATS = ("%Y.%m.%d %H:%M:%S", "%Y.%m.%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M",
                "%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M")
BUY = ("buy", "achat", "kauf", "compra", "acquisto")
SELL = ("sell", "vente", "verkauf", "venta", "vendita")
MAX_BYTES = 20 * 1024 * 1024


class ReportError(ValueError):
    """The file is not a MetaTrader 5 history report this module can read; the message says why."""


@dataclass
class Report:
    trades: list
    account_login: str | None
    currency: str | None
    skipped: list[tuple[int, str]] = field(default_factory=list)    # (line in the table, reason)

    @property
    def account_id(self) -> str | None:
        return f"mt5-{self.account_login}" if self.account_login else None


# =============================================================================
# Reading the file into rows of (column, text)
# =============================================================================

class _Rows(HTMLParser):
    """Table rows as [(column, text)], columns counted with every colspan, hidden cells included."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows: list[list[tuple[int, str]]] = []
        self.text: list[str] = []
        self._row = None
        self._cell = None
        self._col = 0

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._row, self._col = [], 0
        elif tag in ("td", "th") and self._row is not None:
            span = dict(attrs).get("colspan") or "1"
            self._cell = {"col": self._col, "span": int(span) if str(span).isdigit() else 1, "text": []}

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None and self._row is not None:
            text = " ".join("".join(self._cell["text"]).split())
            if text:
                self._row.append((self._cell["col"], text))
            self._col += self._cell["span"]
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if self._row:
                self.rows.append(self._row)
            self._row = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell["text"].append(data)
        self.text.append(data)


def _decode(raw: bytes) -> str:
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16")
    if len(raw) > 4 and raw[1:4:2] == b"\x00\x00":        # UTF-16 LE without its mark
        return raw.decode("utf-16-le", errors="replace")
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1")


def _html_rows(raw: bytes) -> tuple[list, str]:
    parser = _Rows()
    parser.feed(_decode(raw))
    return parser.rows, " ".join(parser.text)


_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def _column(ref: str) -> int:
    letters = re.match(r"[A-Z]+", ref or "A").group(0)
    n = 0
    for c in letters:
        n = n * 26 + ord(c) - 64
    return n - 1


def _xlsx_rows(raw: bytes) -> tuple[list, str]:
    try:
        book = zipfile.ZipFile(io.BytesIO(raw))
    except zipfile.BadZipFile as exc:
        raise ReportError("ce fichier Excel est illisible") from exc
    names = book.namelist()
    shared = []
    if "xl/sharedStrings.xml" in names:
        for item in ElementTree.fromstring(book.read("xl/sharedStrings.xml")).findall("m:si", _NS):
            shared.append("".join(t.text or "" for t in item.iter(f"{{{_NS['m']}}}t")))
    sheets = sorted(n for n in names if n.startswith("xl/worksheets/sheet") and n.endswith(".xml"))
    if not sheets:
        raise ReportError("ce fichier Excel ne contient aucune feuille")
    rows, words = [], []
    for sheet in sheets:
        for row in ElementTree.fromstring(book.read(sheet)).iter(f"{{{_NS['m']}}}row"):
            cells = []
            for cell in row.findall("m:c", _NS):
                kind = cell.get("t")
                if kind == "inlineStr":
                    text = "".join(t.text or "" for t in cell.iter(f"{{{_NS['m']}}}t"))
                else:
                    value = cell.find("m:v", _NS)
                    text = value.text if value is not None and value.text is not None else ""
                    if kind == "s" and text.isdigit() and int(text) < len(shared):
                        text = shared[int(text)]
                text = " ".join(str(text).split())
                if text:
                    cells.append((_column(cell.get("r")), text))
                    words.append(text)
            if cells:
                rows.append(cells)
    return rows, " ".join(words)


# =============================================================================
# Values
# =============================================================================

def _time(text: str) -> datetime | None:
    text = (text or "").strip()
    for fmt in TIME_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    try:                                               # an Excel serial date
        serial = float(text)
    except ValueError:
        return None
    if 20000 < serial < 80000:
        return datetime(1899, 12, 30) + timedelta(days=serial)
    return None


def _number(text: str | None) -> float | None:
    if text is None:
        return None
    cleaned = re.sub(r"[\s  ]", "", str(text)).replace("−", "-")
    if not cleaned:
        return None
    if "," in cleaned and "." not in cleaned:
        cleaned = cleaned.replace(",", ".")
    else:
        cleaned = cleaned.replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _side(text: str) -> int | None:
    word = (text or "").strip().lower()
    if word.startswith(BUY):
        return mt5.DEAL_TYPE_BUY
    if word.startswith(SELL):
        return mt5.DEAL_TYPE_SELL
    return None


def _is_positions_header(cells) -> bool:
    texts = [t for _c, t in cells]
    if len(texts) != len(COLUMNS) or _time(texts[0]):
        return False
    slash = [re.sub(r"\s", "", t.lower()) for t in texts[6:8]]
    return slash == ["s/l", "t/p"]


# =============================================================================
# The report
# =============================================================================

def server_offset(server_time: datetime, clock) -> float:
    """
    Hours the broker's server clock runs ahead of UTC at `server_time`.

    `clock` is a fixed offset in hours, or `NY_PLUS_7` for the convention most
    forex brokers follow: the server shows New York time plus seven hours, so
    that every trading day closes at midnight. It is UTC+2 in winter and UTC+3 in
    summer, switching on the American daylight saving dates, and a fixed offset
    would put half a year of trades an hour off, and some in the wrong session.
    """
    if clock != NY_PLUS_7:
        return float(clock or 0.0)
    new_york = (server_time - timedelta(hours=7)).replace(tzinfo=NEW_YORK)
    return 7 + new_york.utcoffset().total_seconds() / 3600


def read(raw: bytes, filename: str = "", *, clock=NY_PLUS_7, currency: str | None = None) -> Report:
    """
    Every closed position of a MetaTrader 5 history report, as journal trades.

    `clock` is the broker server's clock: `NY_PLUS_7`, or a fixed offset from UTC
    in hours, as for a live sync (see `server_offset`). `currency` is used when
    the report does not state the account currency.
    """
    if not raw:
        raise ReportError("le fichier est vide")
    if len(raw) > MAX_BYTES:
        raise ReportError("le fichier dépasse 20 Mo")
    is_xlsx = raw[:2] == b"PK" or filename.lower().endswith(".xlsx")
    rows, text = _xlsx_rows(raw) if is_xlsx else _html_rows(raw)

    found = re.search(r"\b(\d{4,12})\s*\(\s*([A-Z]{3})\b", _html.unescape(text))
    login = found.group(1) if found else None
    account_currency = (found.group(2) if found else None) or currency or "USD"
    account_id = f"mt5-{login}" if login else None

    trades, skipped, header = [], [], None
    for index, cells in enumerate(rows):
        if _is_positions_header(cells):
            header = [c for c, _t in cells]
            continue
        if header is None:
            continue
        by_col = dict(cells)
        values = dict(zip(COLUMNS, (by_col.get(c) for c in header)))
        opened, closed = _time(values["opened"]), _time(values["closed"])
        if not opened:
            header = None                              # the table has ended
            continue
        line = index + 1
        side, position = _side(values["type"]), _number(values["position"])
        volume, entry, exit_ = _number(values["volume"]), _number(values["open_price"]), _number(values["close_price"])
        if not closed:
            skipped.append((line, "position encore ouverte"))
            continue
        if side is None or not position or not volume or entry is None or exit_ is None:
            skipped.append((line, "ligne incomplète (sens, volume ou prix manquant)"))
            continue
        out_side = mt5.DEAL_TYPE_SELL if side == mt5.DEAL_TYPE_BUY else mt5.DEAL_TYPE_BUY
        stamp = lambda t: t.replace(tzinfo=timezone.utc).timestamp()     # noqa: E731
        common = {"position_id": int(position), "symbol": values["symbol"] or "", "volume": volume,
                  "magic": 0, "comment": "", "fee": 0.0}
        deals = [
            {**common, "ticket": int(position) * 10, "order": int(position), "type": side,
             "entry": mt5.DEAL_ENTRY_IN, "price": entry, "time": stamp(opened), "time_msc": stamp(opened) * 1000,
             "commission": _number(values["commission"]) or 0.0, "swap": 0.0, "profit": 0.0},
            {**common, "ticket": int(position) * 10 + 1, "order": int(position), "type": out_side,
             "entry": mt5.DEAL_ENTRY_OUT, "price": exit_, "time": stamp(closed), "time_msc": stamp(closed) * 1000,
             "commission": 0.0, "swap": _number(values["swap"]) or 0.0, "profit": _number(values["profit"]) or 0.0},
        ]
        stop, target = _number(values["sl"]), _number(values["tp"])
        trade = mt5.build_trade(int(position), deals, stop=stop or None, take_profit=target or None,
                                account_id=account_id, currency=account_currency,
                                offset_hours=server_offset(opened, clock))
        if trade is None:
            skipped.append((line, "position non clôturée"))
            continue
        trade.raw["imported_from"] = "report"
        trades.append(trade)

    if not trades and not skipped:
        raise ReportError("aucun tableau « Positions » trouvé : exportez le rapport depuis l'onglet Historique du "
                          "terminal (clic droit, Rapport), au format HTML ou Excel")
    return Report(trades, login, account_currency, skipped)


@dataclass
class ReportSource:
    """A report as a synchronisation source, so it goes through the same merge as the terminal."""

    report: Report
    name: str = "Rapport MetaTrader 5"

    def account(self):
        if not self.report.account_id:
            return None
        return mt5.BrokerAccount(id=self.report.account_id, name=self.report.account_login or self.name,
                                 broker="MetaTrader 5", currency=self.report.currency or "USD")

    def fetch_trades(self, since=None, until=None):
        return list(self.report.trades)
