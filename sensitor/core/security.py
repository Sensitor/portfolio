"""
Password hashing and session tokens.

Pure functions over bytes and strings. No database, no Streamlit, no
configuration — which is what makes them testable in isolation and reusable by
the API later.

Choices, and why
----------------
**scrypt, from the standard library.** It is memory-hard, so a stolen database
cannot be attacked with a rented GPU nearly as cheaply as one hashed with
SHA-256 or PBKDF2. It ships with Python, so this adds no dependency to a project
a user installs on their own machine. The parameters below cost roughly 16 MB
and a few tens of milliseconds per hash — slow enough to matter to an attacker
with the file, fast enough that a person signing in does not notice.

**The stored hash carries its own parameters.** `scrypt$16384$8$1$<salt>$<key>`.
Raising the cost later must not invalidate every existing password, and it will
not: verification reads the parameters from the stored string, so old hashes keep
verifying at their old cost and are upgraded on the next successful sign-in.

**Session tokens are stored hashed.** The token goes to the client; only its
SHA-256 is written down. A leaked database then yields no usable session, which
is the same reason passwords are not stored either. SHA-256 is right here and
scrypt is not: a token is 32 random bytes, so there is no dictionary to attack
and nothing to slow down.

**Every comparison is timing-safe.** `hmac.compare_digest` throughout. A
byte-by-byte `==` on a token leaks its prefix to anyone willing to measure, and
a session token is a bearer credential.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

# scrypt cost. `n` is the work factor and the memory driver: 2**14 blocks of
# 128 * r bytes is about 16 MB. Raise `n` over time; old hashes keep their own.
SCRYPT_N = 16_384
SCRYPT_R = 8
SCRYPT_P = 1
KEY_BYTES = 32
SALT_BYTES = 16

TOKEN_BYTES = 32          # 256 bits of entropy in a session token

# Minimum a password may be. Deliberately a length floor and nothing else: a
# composition rule ("one capital, one digit, one symbol") reliably produces
# `Password1!` and reliably annoys everyone, while length is what actually costs
# an attacker anything.
MIN_PASSWORD_LENGTH = 8


class PasswordError(ValueError):
    """A password that cannot be accepted, with a reason worth showing."""


# =============================================================================
# PASSWORDS
# =============================================================================

def hash_password(password: str, *, salt: bytes | None = None,
                  n: int = SCRYPT_N, r: int = SCRYPT_R, p: int = SCRYPT_P) -> str:
    """
    A self-describing scrypt hash: `scrypt$n$r$p$salt$key`, all hex.

    The parameters travel with the hash so a future increase in cost does not
    lock anyone out of their own account.
    """
    if not isinstance(password, str) or not password:
        raise PasswordError("a password is required")
    salt = salt or secrets.token_bytes(SALT_BYTES)
    key = hashlib.scrypt(password.encode("utf-8"), salt=salt,
                         n=n, r=r, p=p, dklen=KEY_BYTES)
    return f"scrypt${n}${r}${p}${salt.hex()}${key.hex()}"


def verify_password(password: str, stored: str | None) -> bool:
    """
    Whether a password matches a stored hash.

    Returns False rather than raising on a malformed or missing hash: a user row
    with no credential is a user who cannot sign in, not a crash. Never leaks
    which of the two was wrong, and never raises differently for a bad hash than
    for a bad password — both are just False.
    """
    if not password or not stored:
        return False
    try:
        scheme, n, r, p, salt_hex, key_hex = stored.split("$")
        if scheme != "scrypt":
            return False
        candidate = hashlib.scrypt(
            password.encode("utf-8"), salt=bytes.fromhex(salt_hex),
            n=int(n), r=int(r), p=int(p), dklen=len(bytes.fromhex(key_hex)),
        )
    except (ValueError, TypeError, MemoryError):
        return False
    return hmac.compare_digest(candidate, bytes.fromhex(key_hex))


def needs_rehash(stored: str | None, *, n: int = SCRYPT_N, r: int = SCRYPT_R,
                 p: int = SCRYPT_P) -> bool:
    """
    Whether a stored hash was made with weaker parameters than current.

    Called after a *successful* sign-in, which is the only moment the plaintext
    is available to rehash with. A password nobody uses is never upgraded, and
    that is correct — it is also never verified.
    """
    if not stored:
        return False
    try:
        scheme, stored_n, stored_r, stored_p, _, _ = stored.split("$")
    except ValueError:
        return True
    if scheme != "scrypt":
        return True
    return (int(stored_n), int(stored_r), int(stored_p)) < (n, r, p)


def check_password_strength(password: str) -> None:
    """Raise `PasswordError` when a password is too weak to accept."""
    if not password or len(password) < MIN_PASSWORD_LENGTH:
        raise PasswordError(
            f"a password must be at least {MIN_PASSWORD_LENGTH} characters"
        )
    if password.strip() != password:
        raise PasswordError("a password cannot start or end with a space")


# =============================================================================
# SESSION TOKENS
# =============================================================================

def new_token() -> str:
    """A fresh session token. Given to the client; never written down as-is."""
    return secrets.token_urlsafe(TOKEN_BYTES)


def token_fingerprint(token: str) -> str:
    """
    The SHA-256 of a token, which is what the database stores.

    A stolen database then yields no usable session. Fast hashing is right for a
    token and wrong for a password: 32 random bytes have no dictionary behind
    them, so there is nothing for a slow hash to protect against.
    """
    return hashlib.sha256((token or "").encode("utf-8")).hexdigest()


def tokens_match(token: str, fingerprint: str) -> bool:
    """Timing-safe comparison of a presented token against a stored digest."""
    return hmac.compare_digest(token_fingerprint(token), fingerprint or "")
