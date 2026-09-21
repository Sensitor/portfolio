"""
Dependencies every route shares: the store, the auth service, and the caller.

The one rule this file exists to enforce: **the user comes from the bearer
token, never from the request.** No path parameter, no query string and no body
field names whose data is being asked for. `current_user` is the only way a
route learns an identity, so an endpoint physically cannot be written to serve
`/portfolios?user=someone-else` — there is nothing to pass.

That is the same session the Streamlit app issues. One credential store, one
verification path: a token created by signing in through the UI works here, and
one issued here works there. A second authentication mechanism for the API
would be a second place to get it wrong.
"""

from __future__ import annotations

import os
from functools import lru_cache

from fastapi import Depends, Header, HTTPException, status

from ..core.auth import Auth
from ..database import Store

# A pre-shared key for single-user mode. See `single_user_key_ok` below.
API_TOKEN_ENV = "SENSITOR_API_TOKEN"


@lru_cache(maxsize=1)
def get_store() -> Store:
    """
    One store for the process.

    Cached because `Store` owns a connection and a lock. The lock is what makes
    it safe for the threadpool a sync FastAPI route runs in, which is the same
    reason the Streamlit app shares one.
    """
    return Store()


def get_auth(store: Store = Depends(get_store)) -> Auth:
    return Auth(store)


def bearer_token(authorization: str | None = Header(default=None)) -> str | None:
    """The token from an `Authorization: Bearer …` header, if there is one."""
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        return None
    return token.strip() or None


def current_user(token: str | None = Depends(bearer_token),
                 auth: Auth = Depends(get_auth)) -> str:
    """
    The signed-in user's email, or 401.

    Every route that touches user data depends on this. The value it returns is
    then passed to a `Store` method that scopes its query by it — the two
    together are what make one account's data unreachable from another's, and
    neither is sufficient alone.
    """
    email = auth.resolve(token) if token else None
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="a valid bearer token is required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return email


def optional_user(token: str | None = Depends(bearer_token),
                  auth: Auth = Depends(get_auth)) -> str | None:
    """For routes that answer differently when signed in, but do not require it."""
    return auth.resolve(token) if token else None


def single_user_key_ok(presented: str | None) -> bool:
    """
    Whether a single-user deployment will issue a session for this request.

    In single-user mode the Streamlit app treats an email as a filing label:
    type it, and your data opens. That is defensible for a text box on your own
    machine and indefensible for an HTTP endpoint, which is reachable by anyone
    who can route a packet to it.

    So the API does not inherit that behaviour. In single-user mode it issues a
    session only when `SENSITOR_API_TOKEN` is set and the request presents it —
    a deliberate, documented, single-tenant key, which is exactly what a phone
    on your own network needs. With the variable unset, the API issues no
    sessions at all rather than handing one to whoever asks.
    """
    configured = (os.getenv(API_TOKEN_ENV) or "").strip()
    if not configured:
        return False
    import hmac
    return hmac.compare_digest(configured, (presented or "").strip())


def single_user_key_configured() -> bool:
    return bool((os.getenv(API_TOKEN_ENV) or "").strip())
