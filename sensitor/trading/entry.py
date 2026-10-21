"""
Entering trades by hand or from a spreadsheet, in the member's own terms.

A trader knows how much they risked and where their stop was; few know their
instrument's contract size or point value. So a trade is entered with the risk
in money, and the position size is derived from it: `size = risk / |entry −
stop|`. That is exactly what makes R correct for any instrument, the same way
the MT5 connector stores size in money per price unit.

Times are entered in Paris time, as a French trader reads them on the screen,
and stored in UTC, which is what the session windows use.

Spreadsheets come from French Excel as often as from anywhere else, so the
importer accepts « ; » or « , » as separator and a decimal comma, and reports
each bad row with its line number instead of refusing the file.

No Streamlit, no database.
"""

from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from .models import Direction, Trade, validate
from .setups import canonical_mistakes, canonical_setups

PARIS = ZoneInfo("Europe/Paris")
MAX_ROWS = 2000

TEMPLATE_COLUMNS = ("ouverture", "fermeture", "symbole", "sens", "entree", "stop", "objectif",
                    "sortie", "risque", "resultat", "setup", "erreurs", "notes")
TEMPLATE_EXAMPLE = ("2026-10-20 09:15", "2026-10-20 10:40", "EURUSD", "achat", "1,0850", "1,0835",
                    "1,0880", "1,0880", "100", "", "fvg", "", "Exemple : supprimez cette ligne")

_PROBLEMS = {
    "size must be positive": "la taille de position est nulle",
    "entry price must be positive": "le prix d'entrée doit être positif",
    "closed before it opened": "la fermeture précède l'ouverture",
    "stop loss is on the wrong side of the entry": "le stop est du mauvais côté de l'entrée",
    "take profit is on the wrong side of the entry": "l'objectif est du mauvais côté de l'entrée",
}


def template_csv() -> str:
    """The import template, with one example row, in the « ; » and decimal-comma dialect."""
    out = io.StringIO()
    writer = csv.writer(out, delimiter=";")
    writer.writerow(TEMPLATE_COLUMNS)
    writer.writerow(TEMPLATE_EXAMPLE)
    return out.getvalue()


def paris_to_utc(moment: datetime) -> datetime:
    """A naive time read on a Paris screen, as an aware UTC time."""
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=PARIS)
    return moment.astimezone(timezone.utc)


def to_paris(moment: datetime) -> datetime:
    return moment.astimezone(PARIS) if moment.tzinfo else moment


def build_trade(*, symbol: str, direction, opened_at: datetime, closed_at: datetime,
                entry: float, exit: float, stop: float | None = None, target: float | None = None,
                risk: float | None = None, result: float | None = None, setups=(), mistakes=(),
                notes: str = "", emotion: str | None = None, currency: str = "EUR",
                trade_id: str | None = None) -> Trade:
    """
    One closed trade from what a trader knows. Raises ValueError, in French, when
    the figures cannot make a trade.

    With a stop, the risk in money is required: it sets the size, hence R. The
    result is then computed from the prices, unless the broker's net result is
    given, which wins (it includes the costs). Without a stop the result is
    required, and R stays undefined, as everywhere else in the journal.
    """
    symbol = (symbol or "").strip().upper()
    if not symbol:
        raise ValueError("le symbole est obligatoire")
    try:
        side = Direction.parse(_side(direction))
    except ValueError:
        raise ValueError("le sens doit être achat ou vente") from None
    for name, value in (("le prix d'entrée", entry), ("le prix de sortie", exit)):
        if value is None or value <= 0:
            raise ValueError(f"{name} doit être positif")
    if stop is not None and stop <= 0:
        stop = None
    if target is not None and target <= 0:
        target = None
    opened, closed = paris_to_utc(opened_at), paris_to_utc(closed_at)

    if stop is not None:
        distance = abs(entry - stop)
        if distance <= 0:
            raise ValueError("le stop ne peut pas être au prix d'entrée")
        if risk is None or risk <= 0:
            raise ValueError("avec un stop, indiquez le risque engagé en argent")
        size = risk / distance
    else:
        if result is None:
            raise ValueError("sans stop, indiquez le résultat en argent")
        size = 1.0
    gross = result if result is not None else (exit - entry) * side.sign * size

    trade = Trade(
        id=trade_id or f"m-{uuid.uuid4().hex[:12]}", symbol=symbol, direction=side,
        entry_price=float(entry), size=size, opened_at=opened, exit_price=float(exit),
        closed_at=closed, stop_loss=stop, take_profit=target, gross_pnl=gross,
        account_id="manuel", account_currency=currency, setups=canonical_setups(setups),
        mistakes=canonical_mistakes(mistakes), notes=(notes or "").strip()[:2000] or None,
        emotion_before=emotion or None, source="manual",
    )
    problems = validate(trade)
    if problems:
        raise ValueError(_PROBLEMS.get(problems[0], problems[0]))
    return trade


def _side(value) -> str:
    text = str(value or "").strip().lower()
    return {"achat": "long", "acheter": "long", "a": "long", "vente": "short", "vendre": "short",
            "v": "short"}.get(text, text)


def _number(text: str, name: str, *, required: bool = False) -> float | None:
    raw = (text or "").strip().replace(" ", "").replace(" ", "")
    if not raw:
        if required:
            raise ValueError(f"{name} manquant")
        return None
    if "," in raw and "." in raw:
        raw = raw.replace(".", "").replace(",", ".") if raw.rfind(",") > raw.rfind(".") else raw.replace(",", "")
    else:
        raw = raw.replace(",", ".")
    raw = raw.replace("−", "-")
    try:
        return float(raw)
    except ValueError:
        raise ValueError(f"{name} illisible : « {text.strip()} »") from None


_FORMATS = ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y %H:%M:%S",
            "%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S", "%Y.%m.%d %H:%M", "%Y.%m.%d %H:%M:%S")


def _moment(text: str, name: str) -> datetime:
    raw = (text or "").strip()
    for fmt in _FORMATS:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    raise ValueError(f"{name} illisible : « {raw} » (format attendu : 2026-10-20 09:15)")


def _tags(text: str) -> list[str]:
    return [t.strip() for t in (text or "").replace("|", ",").replace("/", ",").split(",") if t.strip()]


def parse_csv(text: str, *, currency: str = "EUR") -> tuple[list[Trade], list[tuple[int, str]]]:
    """
    Trades from a spreadsheet in the template's columns, and the rows that could
    not be read, each with its line number and the reason.

    Columns are matched by name, case and accents aside, so a reordered file
    reads the same. Ids are derived from the row's content, so importing the same
    file twice updates the trades instead of duplicating them.
    """
    text = text.lstrip("﻿")
    if not text.strip():
        return [], [(1, "le fichier est vide")]
    sample = text.splitlines()[0]
    delimiter = ";" if sample.count(";") >= sample.count(",") else ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    columns = {_key(c): c for c in (reader.fieldnames or [])}
    missing = [c for c in ("ouverture", "fermeture", "symbole", "sens", "entree", "sortie") if c not in columns]
    if missing:
        return [], [(1, "colonnes manquantes : " + ", ".join(missing))]

    trades, errors = [], []
    for line, row in enumerate(reader, start=2):
        if line - 1 > MAX_ROWS:
            errors.append((line, f"au-delà de {MAX_ROWS} lignes, le reste du fichier est ignoré"))
            break
        cell = {k: (row.get(original) or "") for k, original in columns.items()}
        if not any(v.strip() for v in cell.values()):
            continue
        try:
            fields = dict(
                symbol=cell.get("symbole", ""), direction=cell.get("sens", ""),
                opened_at=_moment(cell.get("ouverture", ""), "ouverture"),
                closed_at=_moment(cell.get("fermeture", ""), "fermeture"),
                entry=_number(cell.get("entree", ""), "entrée", required=True),
                exit=_number(cell.get("sortie", ""), "sortie", required=True),
                stop=_number(cell.get("stop", ""), "stop"),
                target=_number(cell.get("objectif", ""), "objectif"),
                risk=_number(cell.get("risque", ""), "risque"),
                result=_number(cell.get("resultat", ""), "résultat"),
                setups=_tags(cell.get("setup", "")), mistakes=_tags(cell.get("erreurs", "")),
                notes=cell.get("notes", ""), currency=currency,
            )
            digest = uuid.uuid5(uuid.NAMESPACE_URL, "|".join(
                str(fields[k]) for k in ("symbol", "direction", "opened_at", "entry", "exit"))).hex[:12]
            trades.append(build_trade(**fields, trade_id=f"csv-{digest}"))
        except ValueError as exc:
            errors.append((line, str(exc)))
    return trades, errors


def _key(name: str) -> str:
    import unicodedata
    plain = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode()
    return plain.strip().lower().replace(" ", "_").replace("é", "e")
