"""
The newsletter provider, Brevo, over its HTTP API (v3), with the standard library.

Optional. With these two settings, a confirmed subscription is added to a Brevo
list and an unsubscription removes it; Brevo then sends the campaigns, with its
own unsubscribe link, and keeps its own record. Without them, Sensitor keeps the
list alone and an administrator can export the confirmed addresses.

    SENSITOR_BREVO_API_KEY   the API key (secret: environment or Streamlit secrets only)
    SENSITOR_BREVO_LIST_ID   the numeric id of the list

The endpoints are Brevo's documented contact routes (`POST /v3/contacts`,
`PUT /v3/contacts/{email}`); they have not been exercised against a live
account from this repository, and the tests use a fake opener.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.brevo.com/v3"
TIMEOUT = 10.0
log = logging.getLogger(__name__)


def configured() -> bool:
    return bool(os.getenv("SENSITOR_BREVO_API_KEY", "").strip() and _list_id() is not None)


def _list_id() -> int | None:
    try:
        return int(os.getenv("SENSITOR_BREVO_LIST_ID", "").strip())
    except ValueError:
        return None


def _call(method: str, path: str, body: dict, opener) -> bool:
    request = urllib.request.Request(
        f"{API}{path}", data=json.dumps(body).encode("utf-8"), method=method,
        headers={"api-key": os.getenv("SENSITOR_BREVO_API_KEY", "").strip(), "accept": "application/json",
                 "content-type": "application/json"})
    try:
        with opener(request, timeout=TIMEOUT) as response:
            return 200 <= getattr(response, "status", 200) < 300
    except urllib.error.HTTPError as exc:
        log.warning("newsletter provider refused the request: HTTP %s", exc.code)
    except (urllib.error.URLError, OSError) as exc:
        log.warning("newsletter provider unreachable: %s", type(exc).__name__)
    return False


def subscribe(email: str, *, opener=urllib.request.urlopen) -> bool:
    """Add a confirmed address to the list. False when not configured or refused; never raises."""
    if not configured():
        return False
    return _call("POST", "/contacts", {"email": email, "listIds": [_list_id()], "updateEnabled": True}, opener)


def unsubscribe(email: str, *, opener=urllib.request.urlopen) -> bool:
    """Take an address off the list. False when not configured or refused; never raises."""
    if not configured():
        return False
    return _call("PUT", f"/contacts/{urllib.parse.quote(email, safe='')}", {"unlinkListIds": [_list_id()]}, opener)
