"""
Session plumbing for the Sensitor platform: secrets, store, identity, the
Academy catalogue and navigation.

Identity follows the rule the portfolio app already enforces: the signed-in user
is resolved from the session token on every run, never read from a widget. The
same `Store` and `Auth` are used, so one account works in both apps.

Navigation is held in session state and mirrored into the URL query string, so
the address bar shows where you are and a shared link to a public lesson opens
that lesson.

Staying signed in across reloads
--------------------------------
A reload starts a new Streamlit session, which knows nothing of the last one.
The session token is therefore also kept in a cookie (`sensitor_session`),
written from the page by a small script and read back from the request through
`st.context.cookies` when a new session starts. The cookie holds the same token
the session table knows only by its fingerprint; it expires with the session
(30 days), is cleared on sign-out, and every session can be revoked at once
from the account page. It is not HttpOnly — Streamlit offers no way to set a
server-side cookie — which is acceptable here because every piece of text the
app renders is escaped.
"""

from __future__ import annotations

import json
import os

import streamlit as st
import streamlit.components.v1 as components

from ...academy.content import Catalog, cached_catalog
from .. import spaces

SECRET_KEYS = (
    "SENSITOR_DB_URL", "SENSITOR_DB_PATH", "SENSITOR_AUTH",
    "SENSITOR_ACADEMY_PREVIEW", "SENSITOR_TOOLS_URL", "SENSITOR_PUBLIC_URL",
    "SENSITOR_SMTP_HOST", "SENSITOR_SMTP_PORT", "SENSITOR_SMTP_USER",
    "SENSITOR_SMTP_PASSWORD", "SENSITOR_MAIL_FROM",
)
COOKIE = "sensitor_session"
COOKIE_OP = "ac_cookie_op"

ROUTE_KEY = "ac_route"
TOKEN_KEY = "session_token"
ROUTE_FIELDS = ("course", "lesson", "quiz", "resource", "token", "trade", "review", "session", "asset")


def tools_url() -> str:
    """Address of the separate analytics app, when the deployment states one."""
    return os.getenv("SENSITOR_TOOLS_URL", "").strip()


def mirror_secrets() -> None:
    """Copy Streamlit secrets into the environment; a real env var always wins."""
    try:
        available = st.secrets
    except Exception:                                    # noqa: BLE001
        return
    for key in SECRET_KEYS:
        try:
            if key in available and not os.getenv(key):
                os.environ[key] = str(available[key])
        except Exception:                                # noqa: BLE001
            continue


def _store():
    """The process's one store, shared with the analyzer pages the platform reuses (`pages._shared`)."""
    from ...pages._shared import open_store
    return open_store()


_STORE_ERROR: list[str] = []          # why the last opening failed; no secret in it (`postgres.explain`)


def get_store():
    """The shared store, or None if the database cannot be opened."""
    try:
        store = _store()
    except Exception as exc:                             # noqa: BLE001
        from ...database import connection, postgres
        target = connection.target()
        _STORE_ERROR[:] = [postgres.explain(exc, target) if postgres.is_url(target)
                           else f"Fichier de base de données illisible : {type(exc).__name__}."]
        return None
    _STORE_ERROR.clear()
    return store


def store_error() -> str:
    """Why the database could not be opened, for the page that says so; empty when it is open."""
    return _STORE_ERROR[0] if _STORE_ERROR else ""


def get_auth():
    from ...core.auth import Auth
    store = get_store()
    return Auth(store) if store is not None else None


def catalog() -> Catalog:
    """
    Content is the same for everyone; the cache holds no user data.

    `SENSITOR_ACADEMY_CONTENT` points the app at another content tree. It exists
    for the tests, which render fixture lessons; a deployment leaves it unset.
    """
    return cached_catalog(os.getenv("SENSITOR_ACADEMY_CONTENT") or None)


def tier(email: str | None) -> str:
    """The signed-in member's tier, read fresh from the store; « free » for a visitor."""
    store = get_store()
    user = store.get_user(email) if email and store is not None else None
    return str((user or {}).get("tier") or "free")


def _cookie_token() -> str | None:
    try:
        value = st.context.cookies.get(COOKIE)
    except Exception:                                    # noqa: BLE001
        return None
    return value if isinstance(value, str) and value else None


def current_user() -> str | None:
    """
    The verified email behind this session, or None.

    The token comes from session state, or — on the first run after a reload —
    from the cookie. A cookie whose session has expired or been revoked is
    cleared rather than retried on every run.
    """
    auth = get_auth()
    if auth is None:
        return None
    token = st.session_state.get(TOKEN_KEY)
    from_cookie = False
    if not token and not st.session_state.get("ac_cookie_checked"):
        st.session_state["ac_cookie_checked"] = True
        token = _cookie_token()
        from_cookie = bool(token)
    if not token:
        return None
    email = auth.resolve(token)
    if email:
        st.session_state[TOKEN_KEY] = token
        return email
    st.session_state.pop(TOKEN_KEY, None)
    if from_cookie:
        st.session_state[COOKIE_OP] = ("clear", None)
    return None


def remember(token: str) -> None:
    from ...core.auth import SESSION_DAYS
    st.session_state[TOKEN_KEY] = token
    st.session_state[COOKIE_OP] = ("set", token, SESSION_DAYS * 86_400)


def flush_cookie() -> None:
    """Write or clear the session cookie, once, at the end of a run."""
    op = st.session_state.pop(COOKIE_OP, None)
    if not op:
        return
    if op[0] == "set":
        value, age = json.dumps(op[1]), int(op[2])
    else:
        value, age = json.dumps(""), 0
    components.html(
        "<script>(function(){try{const d=window.parent.document;"
        "const secure=window.parent.location.protocol==='https:'?'; Secure':'';"
        f"d.cookie='{COOKIE}='+encodeURIComponent({value})+'; Max-Age={age}; Path=/; SameSite=Lax'+secure;"
        "}catch(e){}})();</script>", height=0)


def multi_user() -> bool:
    from ...core.auth import is_multi_user
    return is_multi_user()


def sign_in(email: str, password: str | None):
    auth = get_auth()
    result = auth.sign_in(email, password) if auth else None
    if result:
        remember(result.token)
    return result


def sign_up(email: str, password: str | None):
    auth = get_auth()
    result = auth.sign_up(email, password) if auth else None
    if result:
        remember(result.token)
    return result


def sign_out() -> None:
    auth = get_auth()
    if auth is not None:
        auth.sign_out(st.session_state.get(TOKEN_KEY))
    # Everything the session holds goes, not only the token: the portfolio being
    # analysed, the real holdings and their prices, the journal's filters, the
    # forms. On a shared browser the next person must start from nothing, and
    # the analyzer pages would otherwise file what is left under their account.
    # Only the page being shown stays.
    for key in list(st.session_state):
        if key != ROUTE_KEY:
            del st.session_state[key]
    st.session_state[COOKIE_OP] = ("clear", None)


# ── Navigation ───────────────────────────────────────────────────────────────

def route() -> dict:
    if ROUTE_KEY not in st.session_state:
        params = st.query_params
        initial = {"page": spaces.resolve_page(params.get("page"))}
        for field in ROUTE_FIELDS:
            if params.get(field):
                initial[field] = params.get(field)
        st.session_state[ROUTE_KEY] = initial
    current = st.session_state[ROUTE_KEY]
    current["page"] = spaces.resolve_page(current.get("page"))
    return current


def go(page: str, **fields) -> None:
    """Navigate. Call from a button handler or follow with `st.rerun()`."""
    target = {"page": spaces.resolve_page(page), **{k: v for k, v in fields.items() if v}}
    st.session_state[ROUTE_KEY] = target
    st.query_params.clear()
    if target["page"] != "home":
        st.query_params.update(target)
    st.session_state["ac_scroll_top"] = True


def link(label: str, page: str, *, key: str, kind: str = "secondary",
         help: str | None = None, disabled: bool = False, width="content", **fields) -> None:
    """A button that navigates."""
    st.button(label, key=key, type=kind, help=help, disabled=disabled, width=width,
              on_click=go, args=(page,), kwargs=fields)
