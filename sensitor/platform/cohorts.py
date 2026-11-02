"""
Cohorts and workshops: checking what an administrator writes, and the calendar.

A cohort groups accompanied members; a workshop is a session for one cohort, at
a date and time, with a place (a video call link or an address) that only the
cohort's members see. Times are entered in Paris time and stored in UTC. The
`.ics` file lets a member add a workshop to their own calendar.

No Streamlit, no database.
"""

from __future__ import annotations

import datetime as _dt
from zoneinfo import ZoneInfo

PARIS = ZoneInfo("Europe/Paris")
MAX_TITLE, MAX_SUMMARY, MAX_PLACE = 120, 1200, 300
DURATIONS = (30, 45, 60, 90, 120)
DASHES = (chr(0x2014), chr(0x2013))


class CohortError(ValueError):
    """What is wrong with the form, in French, for the page to show."""


def _text(value: str, limit: int, what: str, *, required: bool = True) -> str:
    text = " ".join((value or "").split()) if "\n" not in (value or "") else (value or "").strip()
    if required and not text:
        raise CohortError(f"{what} est obligatoire.")
    if len(text) > limit:
        raise CohortError(f"{what} dépasse {limit} caractères.")
    if any(d in text for d in DASHES):
        raise CohortError(f"{what} contient un tiret long : utilisez une virgule ou deux-points.")
    return text


def clean_cohort(title: str, summary: str, starts_on: _dt.date, ends_on: _dt.date | None) -> dict:
    if ends_on is not None and ends_on < starts_on:
        raise CohortError("La fin précède le début.")
    return {"title": _text(title, MAX_TITLE, "Le titre"), "summary": _text(summary, MAX_SUMMARY, "Le résumé",
                                                                             required=False),
            "starts_on": starts_on.isoformat(), "ends_on": ends_on.isoformat() if ends_on else None}


def to_utc(day: _dt.date, time: _dt.time) -> str:
    """A date and a time entered in Paris time, as the UTC text the store keeps."""
    local = _dt.datetime.combine(day, time).replace(tzinfo=PARIS)
    return local.astimezone(_dt.timezone.utc).isoformat(timespec="seconds")


def paris(stamp: str) -> _dt.datetime:
    return _dt.datetime.fromisoformat(stamp).astimezone(PARIS)


def clean_workshop(title: str, summary: str, day: _dt.date, time: _dt.time, duration: int, place: str) -> dict:
    if duration not in DURATIONS:
        raise CohortError("Durée inconnue.")
    place = (place or "").strip()
    if place.lower().startswith(("javascript:", "data:")):
        raise CohortError("Ce lien n'est pas accepté.")
    return {"title": _text(title, MAX_TITLE, "Le titre"), "summary": _text(summary, MAX_SUMMARY, "Le résumé",
                                                                             required=False),
            "starts_at": to_utc(day, time), "duration_minutes": int(duration),
            "place": _text(place, MAX_PLACE, "Le lieu", required=False)}


MONTHS = ("janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre",
          "novembre", "décembre")
DAYS = ("lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche")


def when_label(stamp: str) -> str:
    """« mardi 4 novembre 2026 à 19 h 00 », in Paris time."""
    moment = paris(stamp)
    return (f"{DAYS[moment.weekday()]} {moment.day} {MONTHS[moment.month - 1]} {moment.year} "
            f"à {moment.hour} h {moment.minute:02d}")


def upcoming(workshops: list[dict], now: str) -> tuple[list[dict], list[dict]]:
    """(to come, past), the next first and the latest past first; a cancelled one stays where it falls."""
    ahead = sorted((w for w in workshops if w["starts_at"] >= now), key=lambda w: w["starts_at"])
    behind = sorted((w for w in workshops if w["starts_at"] < now), key=lambda w: w["starts_at"], reverse=True)
    return ahead, behind


def _ics_text(text: str) -> str:
    return (text or "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def _ics_stamp(moment: _dt.datetime) -> str:
    return moment.astimezone(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def ics(workshop: dict, cohort_title: str, *, domain: str = "sensitor") -> str:
    """One workshop as an iCalendar file (RFC 5545), in UTC, lines folded at 75 octets."""
    start = _dt.datetime.fromisoformat(workshop["starts_at"])
    end = start + _dt.timedelta(minutes=int(workshop["duration_minutes"]))
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Sensitor//Ateliers//FR", "CALSCALE:GREGORIAN",
             "BEGIN:VEVENT", f"UID:atelier-{workshop['id']}@{domain}", f"DTSTAMP:{_ics_stamp(start)}",
             f"DTSTART:{_ics_stamp(start)}", f"DTEND:{_ics_stamp(end)}",
             f"SUMMARY:{_ics_text(workshop['title'] + ' · ' + cohort_title)}",
             f"DESCRIPTION:{_ics_text(workshop.get('summary') or '')}"]
    if workshop.get("place"):
        lines.append(f"LOCATION:{_ics_text(workshop['place'])}")
    if workshop.get("status") == "cancelled":
        lines.append("STATUS:CANCELLED")
    lines += ["END:VEVENT", "END:VCALENDAR"]
    return "\r\n".join(_fold(line) for line in lines) + "\r\n"


def _fold(line: str) -> str:
    raw = line.encode("utf-8")
    if len(raw) <= 75:
        return line
    parts, current = [], b""
    for char in line:
        piece = char.encode("utf-8")
        if len(current) + len(piece) > (75 if not parts else 74):
            parts.append(current.decode("utf-8"))
            current = b""
        current += piece
    parts.append(current.decode("utf-8"))
    return "\r\n ".join(parts)
