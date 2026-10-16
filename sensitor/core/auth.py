"""
Authentication: who the person using the app actually is.

Phase 6 made the data layer enforce ownership of whatever identity was claimed.
This is the layer that decides whether the claim is true.

The two modes
-------------
**single** (the default) — the app is one person's, running on their own
machine. The email is a filing label, exactly as it has always been: type it,
and the journal filed under it opens. There is nothing to verify because there
is nobody else to verify against, and demanding a password to open your own
spreadsheet is theatre.

**multi** — the app is shared. An account has a password, sign-in verifies it,
repeated failures throttle, and a session expires. Set `SENSITOR_AUTH=multi`.

Both modes run the same code path and both issue a session. That is deliberate:
a second, simpler path for the common case is a path that does not get exercised
and therefore does not get fixed. In single mode the password check is skipped;
everything else — the session, its expiry, the revocation on sign-out — behaves
identically, so the plumbing multi-user depends on is the plumbing that runs
every day.

The mode is not silent
----------------------
`describe_mode()` exists so the UI can say which mode it is in. An access-control
mode nobody can see is how a deployment ends up open to the internet with a
text box for a login, and the person running it has no way to notice.

No Streamlit here. The service takes a store and returns plain results; the page
layer decides what to render.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .security import (
    PasswordError, check_password_strength, hash_password, needs_rehash,
    new_token, token_fingerprint, verify_password,
)

SINGLE = "single"
MULTI = "multi"

# How long a session lasts, and how many failures buy a lockout.
SESSION_DAYS = 30
RESET_MINUTES = 60
VERIFY_HOURS = 48
MAX_FAILED_LOGINS = 5
LOCKOUT_MINUTES = 15


def auth_mode() -> str:
    """
    Which mode this deployment runs in.

    Read from the environment on every call rather than captured at import, so a
    test — and an operator — can change it without reloading the package.
    Anything other than "multi" is single: an unrecognised value must not
    silently disable authentication, so the safe reading of a typo is the mode
    that asks for less, not more.
    """
    return MULTI if os.getenv("SENSITOR_AUTH", "").strip().lower() == MULTI else SINGLE


def is_multi_user() -> bool:
    return auth_mode() == MULTI


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _stamp(moment: datetime) -> str:
    return moment.isoformat(timespec="seconds")


@dataclass
class AuthResult:
    """
    The outcome of an attempt to sign in or sign up.

    `reason` is a stable key, not a sentence: the page layer translates it. A
    service that returned English would make the French UI a string-matching
    exercise.
    """

    ok: bool
    email: str | None = None
    token: str | None = None
    reason: str | None = None
    detail: str | None = None

    def __bool__(self) -> bool:
        return self.ok


class Auth:
    """
    The one place that answers "who is this?".

    Takes a store rather than importing one, so `core` stays a leaf and the API
    can hand it a different backend later.
    """

    def __init__(self, store, *, mode: str | None = None,
                 session_days: int = SESSION_DAYS):
        self.store = store
        self._mode = mode
        self.session_days = session_days

    @property
    def mode(self) -> str:
        return self._mode or auth_mode()

    @property
    def multi_user(self) -> bool:
        return self.mode == MULTI

    # ── Registration ─────────────────────────────────────────────────────────

    def sign_up(self, email: str, password: str | None = None, *,
                tier: str = "free") -> AuthResult:
        """
        Create an account.

        In multi mode a password is required and an existing account is a
        conflict. In single mode the email is a label, so this is idempotent:
        typing the same one twice opens the same journal rather than refusing.
        """
        email = _normalise(email)
        if not email or "@" not in email:
            return AuthResult(False, reason="invalid_email")

        existing = self.store.credential(email)

        if not self.multi_user:
            self.store.upsert_user(email, tier)
            return self._issue(email)

        if existing and existing.get("password_hash"):
            return AuthResult(False, email=email, reason="already_registered")

        try:
            check_password_strength(password or "")
        except PasswordError as exc:
            return AuthResult(False, email=email, reason="weak_password",
                              detail=str(exc))

        self.store.upsert_user(email, tier)
        self.store.set_password_hash(email, hash_password(password))
        return self._issue(email)

    # ── Sign in ──────────────────────────────────────────────────────────────

    def sign_in(self, email: str, password: str | None = None) -> AuthResult:
        """
        Verify a claim of identity and issue a session.

        Failure reasons are deliberately coarse. `invalid_credentials` is
        returned both for an unknown account and for a wrong password, because
        distinguishing them tells an attacker which addresses are registered —
        and that is worth more to them than it is to a user who mistyped.
        """
        email = _normalise(email)
        if not email:
            return AuthResult(False, reason="invalid_email")

        if not self.multi_user:
            self.store.upsert_user(email, self._tier_for(email))
            return self._issue(email)

        credential = self.store.credential(email)
        locked = self._locked_until(credential)
        if locked:
            return AuthResult(False, email=email, reason="locked",
                              detail=_stamp(locked))

        stored = (credential or {}).get("password_hash")
        if not verify_password(password or "", stored):
            # The failure is counted even for an address with no account, so the
            # time this takes does not depend on whether one exists.
            if credential:
                self._count_failure(email, credential)
            return AuthResult(False, email=email, reason="invalid_credentials")

        # Upgrade the stored hash while the plaintext is in hand — the only
        # moment it can be done.
        if needs_rehash(stored):
            self.store.set_password_hash(email, hash_password(password))

        self.store.record_login_success(email)
        return self._issue(email)

    def _count_failure(self, email: str, credential: dict) -> None:
        attempts = (credential.get("failed_logins") or 0) + 1
        lock = None
        if attempts >= MAX_FAILED_LOGINS:
            lock = _stamp(_now() + timedelta(minutes=LOCKOUT_MINUTES))
        self.store.record_login_failure(email, locked_until=lock)

    def _locked_until(self, credential: dict | None) -> datetime | None:
        if not credential:
            return None
        raw = credential.get("locked_until")
        if not raw:
            return None
        try:
            until = datetime.fromisoformat(raw)
        except (TypeError, ValueError):
            return None
        if until.tzinfo is None:
            until = until.replace(tzinfo=timezone.utc)
        return until if until > _now() else None

    # ── Sessions ─────────────────────────────────────────────────────────────

    def _issue(self, email: str, label: str | None = None) -> AuthResult:
        token = new_token()
        expires = _stamp(_now() + timedelta(days=self.session_days))
        self.store.create_session(email, token_fingerprint(token),
                                  expires_at=expires, label=label)
        return AuthResult(True, email=email, token=token)

    def resolve(self, token: str | None) -> str | None:
        """
        The email behind a session token, or None.

        This is what every page calls. Nothing downstream should ever take an
        email from a widget: a text input is a claim, and a session is the only
        thing that makes a claim true.
        """
        if not token:
            return None
        row = self.store.session(token_fingerprint(token))
        if not row:
            return None
        self.store.touch_session(token_fingerprint(token))
        return row["user_email"]

    def sign_out(self, token: str | None) -> None:
        if token:
            self.store.revoke_session(token_fingerprint(token))

    def sign_out_everywhere(self, email: str) -> int:
        return self.store.revoke_sessions(_normalise(email))

    # ── Passwords ────────────────────────────────────────────────────────────

    def change_password(self, email: str, current: str | None,
                        new: str) -> AuthResult:
        """
        Replace a password, then revoke every session.

        Revoking is the point. A password is usually changed because someone
        fears it is known, and a change that leaves the attacker's existing
        session alive has solved nothing.
        """
        email = _normalise(email)
        if not self.multi_user:
            return AuthResult(False, email=email, reason="not_multi_user")

        credential = self.store.credential(email)
        stored = (credential or {}).get("password_hash")
        if stored and not verify_password(current or "", stored):
            return AuthResult(False, email=email, reason="invalid_credentials")

        try:
            check_password_strength(new)
        except PasswordError as exc:
            return AuthResult(False, email=email, reason="weak_password",
                              detail=str(exc))

        self.store.set_password_hash(email, hash_password(new))
        self.store.revoke_sessions(email)
        return self._issue(email)

    # ── E-mailed tokens: password reset, address verification ───────────────
    #
    # Both are single-use, short-lived, and stored as a fingerprint only. The
    # requests never say whether an account exists: the page shows the same
    # message either way, and the token is simply not created for an unknown
    # address.

    def request_password_reset(self, email: str) -> str | None:
        """A reset token for an account that has a password, else None."""
        email = _normalise(email)
        credential = self.store.credential(email) if email else None
        if not self.multi_user or not credential or not credential.get("password_hash"):
            return None
        return self._account_token(email, "reset", timedelta(minutes=RESET_MINUTES))

    def reset_password(self, token: str, new_password: str) -> AuthResult:
        """
        Set a new password from a reset link, revoke every session, sign in.

        The token is checked before the password, and spent only once the new
        password has been accepted, so a typo in the new password does not burn
        the link.
        """
        row = self._valid_token(token, "reset")
        if row is None:
            return AuthResult(False, reason="invalid_token")
        try:
            check_password_strength(new_password or "")
        except PasswordError as exc:
            return AuthResult(False, email=row["user_email"], reason="weak_password",
                              detail=str(exc))
        if not self.store.use_account_token(token_fingerprint(token)):
            return AuthResult(False, reason="invalid_token")
        email = row["user_email"]
        self.store.set_password_hash(email, hash_password(new_password))
        self.store.revoke_sessions(email)
        self.store.record_login_success(email)
        return self._issue(email)

    def request_verification(self, email: str) -> str | None:
        email = _normalise(email)
        if not email or self.store.get_user(email) is None:
            return None
        return self._account_token(email, "verify", timedelta(hours=VERIFY_HOURS))

    def verify_email(self, token: str) -> AuthResult:
        row = self._valid_token(token, "verify")
        if row is None or not self.store.use_account_token(token_fingerprint(token)):
            return AuthResult(False, reason="invalid_token")
        self.store.set_email_verified(row["user_email"])
        return AuthResult(True, email=row["user_email"])

    def _account_token(self, email: str, purpose: str, lifetime: timedelta) -> str:
        token = new_token()
        self.store.create_account_token(email, token_fingerprint(token), purpose=purpose,
                                        expires_at=_stamp(_now() + lifetime))
        return token

    def _valid_token(self, token: str | None, purpose: str) -> dict | None:
        if not token:
            return None
        row = self.store.account_token(token_fingerprint(token), purpose)
        if not row or row.get("used_at"):
            return None
        try:
            expires = datetime.fromisoformat(row["expires_at"])
        except (TypeError, ValueError):
            return None
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return row if expires > _now() else None

    # ── Description ──────────────────────────────────────────────────────────

    def describe_mode(self, lang: str = "en") -> dict:
        """
        What the UI should tell the person about how this deployment protects
        their data. Surfaced rather than assumed.
        """
        if self.multi_user:
            return {"mode": MULTI, "verified": True, "key": "auth_mode_multi"}
        return {"mode": SINGLE, "verified": False, "key": "auth_mode_single"}

    def _tier_for(self, email: str) -> str:
        from .config import resolve_tier
        return resolve_tier(email)


def _normalise(email: str) -> str:
    return (email or "").strip().lower()
