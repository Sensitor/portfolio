"""
Statistics for the administrator: where accounts come from, and the funnel
from a visit to a Premium or accompanied member.

What is measured, and what is not:

* visits are counted once per browser session, by day, landing page and
  campaign source, with no cookie, no address and no identifier (`visits`);
* an account keeps the campaign tags of the link that brought it
  (`signup_sources`), recorded once at sign-up;
* the public site has no script: its links to the platform carry
  `utm_source=site`, so the accounts it brings are counted, not its readers.

Every rate is computed here from counts the store returns, and says « n/a »
when its denominator is zero rather than inventing a figure.

No Streamlit, no database.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

UTM_FIELDS = ("utm_source", "utm_medium", "utm_campaign")
_TAG = re.compile(r"[^a-z0-9_.-]")
MAX_TAG = 40


def clean_tag(value) -> str:
    """A campaign tag as stored: lowercase letters, digits, `_ . -`, 40 characters at most."""
    return _TAG.sub("", str(value or "").strip().lower())[:MAX_TAG]


def clean_utm(params) -> dict:
    """The three campaign tags from a mapping of query parameters; missing ones are empty."""
    return {field[4:]: clean_tag(params.get(field, "")) for field in UTM_FIELDS}


def rate(part: int, whole: int) -> float | None:
    return None if not whole else part / whole


def percent(value: float | None) -> str:
    """« 12,5 % », or « n/a » when there was nothing to divide by."""
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}".replace(".", ",") + " %"


@dataclass(frozen=True)
class Step:
    label: str
    count: int
    rate: float | None          # the share of `base`; None when it cannot be stated
    base: str = ""              # what the rate is a share of


def funnel(visits: int, signups: int, verified: int, premium: int, accompanied: int) -> list[Step]:
    """
    The steps over one window. Visits and sign-ups are the window's own;
    verified and premium are shares of those sign-ups (an address can be
    premium without being verified, so they are not nested), accompanied a
    share of premium. Sign-ups over visits is stated only when visits were
    counted for all of them: more accounts than visits means the counting
    started during the window, and a rate above 100 % would be a figure
    invented by the arithmetic.
    """
    per_visit = rate(signups, visits) if visits >= signups else None
    return [Step("Visites", int(visits), None),
            Step("Comptes créés", int(signups), per_visit, "des visites"),
            Step("Adresses vérifiées", int(verified), rate(verified, signups), "des comptes"),
            Step("Premium", int(premium), rate(premium, signups), "des comptes"),
            Step("Accompagnés", int(accompanied), rate(accompanied, premium), "des Premium")]
