"""
Sign in, sign out, and who am I.

Uses the same `core.auth.Auth` the Streamlit app uses, against the same session
table. A token issued here works in the app and one issued in the app works
here — there is one credential store and one verification path.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from ...core.auth import SESSION_DAYS, Auth
from ..deps import (
    Store, bearer_token, current_user, get_auth, get_store,
    single_user_key_configured, single_user_key_ok,
)
from ..schemas import MeResponse, SessionResponse, SignInRequest

router = APIRouter(prefix="/auth", tags=["auth"])

# Failures are reported with one status and one message whatever went wrong.
# Telling a caller that the address exists but the password is wrong tells an
# attacker which addresses are registered, and that is worth more to them than
# the extra clarity is to someone who mistyped.
_REJECTED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="those credentials do not match an account",
    headers={"WWW-Authenticate": "Bearer"},
)


@router.post("/sign-in", response_model=SessionResponse)
def sign_in(body: SignInRequest, auth: Auth = Depends(get_auth)) -> SessionResponse:
    """
    Exchange credentials for a session token.

    In **multi** mode that means an email and a password. In **single** mode the
    app treats an email as a filing label, which is defensible for a text box on
    someone's own machine and indefensible over HTTP — so the API refuses unless
    `SENSITOR_API_TOKEN` is configured and presented. With it unset, this
    endpoint issues nothing at all rather than handing a session to whoever asks.
    """
    if not auth.multi_user:
        if not single_user_key_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=("this deployment runs in single-user mode and has no "
                        "SENSITOR_API_TOKEN configured, so the API issues no "
                        "sessions. Set that variable, or run with "
                        "SENSITOR_AUTH=multi."),
            )
        if not single_user_key_ok(body.api_key):
            raise _REJECTED

    result = auth.sign_in(body.email, body.password)
    if not result:
        # A locked account is told so, because the caller can do something about
        # it — waiting — and the lockout is already public knowledge to whoever
        # triggered it.
        if result.reason == "locked":
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"too many failed attempts; locked until {result.detail}",
            )
        raise _REJECTED

    return SessionResponse(token=result.token, email=result.email,
                           expires_days=auth.session_days or SESSION_DAYS)


@router.post("/sign-up", response_model=SessionResponse,
             status_code=status.HTTP_201_CREATED)
def sign_up(body: SignInRequest, auth: Auth = Depends(get_auth)) -> SessionResponse:
    """
    Create an account. Multi-user mode only.

    Single-user mode has no registration: there is one person, and the API key
    is how they identify themselves.
    """
    if not auth.multi_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="registration is only available in multi-user mode",
        )

    result = auth.sign_up(body.email, body.password)
    if not result:
        detail = {
            "already_registered": "an account already exists for that address",
            "weak_password": result.detail or "that password is too weak",
            "invalid_email": "that is not a valid email address",
        }.get(result.reason, "could not create that account")
        code = (status.HTTP_409_CONFLICT if result.reason == "already_registered"
                else status.HTTP_400_BAD_REQUEST)
        raise HTTPException(status_code=code, detail=detail)

    return SessionResponse(token=result.token, email=result.email,
                           expires_days=auth.session_days or SESSION_DAYS)


@router.post("/sign-out", status_code=status.HTTP_204_NO_CONTENT)
def sign_out(token: str | None = Depends(bearer_token),
             auth: Auth = Depends(get_auth)) -> None:
    """Revoke this session. Idempotent — an unknown token is not an error."""
    auth.sign_out(token)


@router.post("/sign-out-everywhere", status_code=status.HTTP_204_NO_CONTENT)
def sign_out_everywhere(email: str = Depends(current_user),
                        auth: Auth = Depends(get_auth)) -> None:
    """Revoke every session for the caller, including this one."""
    auth.sign_out_everywhere(email)


@router.get("/me", response_model=MeResponse)
def me(email: str = Depends(current_user),
       store: Store = Depends(get_store)) -> MeResponse:
    user = store.get_user(email) or {}
    return MeResponse(
        email=email,
        tier=user.get("tier", "free"),
        display_name=user.get("display_name"),
        last_login_at=user.get("last_login_at"),
    )
