"""
Session plumbing for the Academy app: secrets, store, identity, catalogue and
navigation.

Identity follows the rule the portfolio app already enforces: the signed-in user
is resolved from the session token on every run, never read from a widget. The
same `Store` and `Auth` are used, so one account works in both apps.

Navigation is held in session state and mirrored into the URL query string, so
the address bar shows where you are and a shared link to a public lesson opens
that lesson. A page reload starts a new Streamlit session and therefore signs
the visitor out — the same limitation as the portfolio app, documented in
docs/ACADEMY.md.
"""

from __future__ import annotations

import os

import streamlit as st

from ..content import Catalog, cached_catalog

SECRET_KEYS = (
    "SENSITOR_DB_URL", "SENSITOR_DB_PATH", "SENSITOR_AUTH",
    "SENSITOR_ACADEMY_PREVIEW",
)

ROUTE_KEY = "ac_route"
TOKEN_KEY = "session_token"
PAGES = ("home", "paths", "course", "lesson", "quiz", "library", "lab",
         "progress", "account")
ROUTE_FIELDS = ("course", "lesson", "quiz", "resource")


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


@st.cache_resource(show_spinner=False)
def _store():
    from ...database import Store
    return Store()


def get_store():
    """The shared store, or None if the database cannot be opened."""
    try:
        return _store()
    except Exception:                                    # noqa: BLE001
        return None


def get_auth():
    from ...core.auth import Auth
    store = get_store()
    return Auth(store) if store is not None else None


def catalog() -> Catalog:
    """Content is the same for everyone; the cache holds no user data."""
    return cached_catalog()


def current_user() -> str | None:
    auth = get_auth()
    token = st.session_state.get(TOKEN_KEY)
    if auth is None or not token:
        return None
    email = auth.resolve(token)
    if not email:
        st.session_state.pop(TOKEN_KEY, None)
    return email


def multi_user() -> bool:
    from ...core.auth import is_multi_user
    return is_multi_user()


def sign_in(email: str, password: str | None):
    auth = get_auth()
    result = auth.sign_in(email, password) if auth else None
    if result:
        st.session_state[TOKEN_KEY] = result.token
    return result


def sign_up(email: str, password: str | None):
    auth = get_auth()
    result = auth.sign_up(email, password) if auth else None
    if result:
        st.session_state[TOKEN_KEY] = result.token
    return result


def sign_out() -> None:
    auth = get_auth()
    if auth is not None:
        auth.sign_out(st.session_state.get(TOKEN_KEY))
    for key in list(st.session_state):
        if key == TOKEN_KEY or key.startswith("quiz::") or key.startswith("ex::"):
            del st.session_state[key]


# ── Navigation ───────────────────────────────────────────────────────────────

def route() -> dict:
    if ROUTE_KEY not in st.session_state:
        params = st.query_params
        page = params.get("page", "home")
        initial = {"page": page if page in PAGES else "home"}
        for field in ROUTE_FIELDS:
            if params.get(field):
                initial[field] = params.get(field)
        st.session_state[ROUTE_KEY] = initial
    return st.session_state[ROUTE_KEY]


def go(page: str, **fields) -> None:
    """Navigate. Call from a button handler or follow with `st.rerun()`."""
    target = {"page": page, **{k: v for k, v in fields.items() if v}}
    st.session_state[ROUTE_KEY] = target
    st.query_params.clear()
    if page != "home":
        st.query_params.update(target)
    st.session_state["ac_scroll_top"] = True


def link(label: str, page: str, *, key: str, kind: str = "secondary",
         help: str | None = None, disabled: bool = False, width="content", **fields) -> None:
    """A button that navigates."""
    st.button(label, key=key, type=kind, help=help, disabled=disabled, width=width,
              on_click=go, args=(page,), kwargs=fields)
