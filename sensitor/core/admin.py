"""
Operator commands for accounts, for deployments without an e-mail server.

    python -m sensitor.core.admin reset-link someone@example.com
    python -m sensitor.core.admin verify-link someone@example.com
    python -m sensitor.core.admin set-role someone@example.com coach|member
    python -m sensitor.core.admin set-tier someone@example.com free|premium
    python -m sensitor.core.admin check

reset-link and verify-link print a single-use link (reset: valid one hour;
verification: 48 hours) that the operator sends to the account holder by
another channel. set-role makes an account a coach, who answers the trade
review requests, or a member again. set-tier sets the access level by hand:
there is no billing. check lists what a deployment still lacks before it opens to
members (durable database, passwords, e-mails, public address, legal pages),
and exits 1 while anything is missing. Uses the same database as the app (SENSITOR_DB_URL /
SENSITOR_DB_PATH) and the same SENSITOR_PUBLIC_URL as the e-mails. Nothing is
changed or printed for an unknown address.
"""

from __future__ import annotations

import sys

from ..database import Store
from . import mailer
from .auth import MULTI, Auth


ROLES = {"coach": "coach", "member": ""}
TIERS = ("free", "premium")


def _set(argv: list[str]) -> int:
    command, email, value = argv
    store = Store()
    if not store.get_user(email):
        print("Aucun compte pour cette adresse.")
        return 1
    if command == "set-role":
        if value not in ROLES:
            print("Rôle attendu : coach ou member.")
            return 2
        store.set_role(email, ROLES[value])
        print(f"{email} : rôle {value}.")
    else:
        if value not in TIERS:
            print("Niveau attendu : free ou premium.")
            return 2
        store.set_tier(email, value)
        print(f"{email} : niveau {value}.")
    return 0


def checks() -> list[tuple[bool, str]]:
    """(ok, what) for each condition of an opening to members; reads the environment and the database."""
    import os

    from ..database import connection, postgres
    from ..platform import legal
    from .auth import auth_mode

    out = []
    target = connection.target()
    durable = postgres.is_url(target)
    out.append((durable, "Base PostgreSQL configurée (SENSITOR_DB_URL)" if durable
                else f"Base SQLite locale ({target}) : elle est effacée à chaque redémarrage sur Streamlit Cloud"))
    try:
        store = Store()
        store.list_users()
        out.append((True, "Base joignable"))
    except Exception as exc:                                     # noqa: BLE001
        reason = postgres.explain(exc, target) if durable else type(exc).__name__
        out.append((False, f"Base injoignable. {reason}"))
    out.append((auth_mode() == MULTI, "Comptes avec mot de passe (SENSITOR_AUTH=multi)" if auth_mode() == MULTI
                else "Mode sans mot de passe (SENSITOR_AUTH=single) : n'importe quelle adresse ouvre un compte"))
    out.append((mailer.configured(), "Envoi d'e-mails configuré (SENSITOR_SMTP_*)" if mailer.configured()
                else "Pas d'envoi d'e-mails : ni vérification d'adresse, ni mot de passe oublié"))
    url = os.getenv("SENSITOR_PUBLIC_URL", "").strip()
    out.append((url.startswith("https://"), f"Adresse publique {url}" if url.startswith("https://")
                else "SENSITOR_PUBLIC_URL absente ou sans https : les liens des e-mails pointeraient ailleurs"))
    gaps = legal.missing()
    out.append((not gaps, "Informations de l'éditeur complètes" if not gaps
                else f"Pages légales : {len(gaps)} information(s) à compléter dans content/legal/editeur.toml"))
    reviewed = bool(legal.details().get("relu"))
    out.append((reviewed, "Textes légaux relus" if reviewed
                else "Textes légaux non relus par un juriste (relu = false)"))
    return out


def _check() -> int:
    results = checks()
    for ok, what in results:
        print(f"  {'ok  ' if ok else 'À FAIRE'}  {what}")
    missing = sum(1 for ok, _ in results if not ok)
    print(f"\n{len(results) - missing} sur {len(results)} conditions remplies.")
    return 1 if missing else 0


def main(argv: list[str]) -> int:
    if argv == ["check"]:
        return _check()
    if len(argv) == 3 and argv[0] in ("set-role", "set-tier"):
        return _set(argv)
    if len(argv) != 2 or argv[0] not in ("reset-link", "verify-link"):
        print(__doc__.strip())
        return 2
    command, email = argv
    auth = Auth(Store(), mode=MULTI)
    if command == "reset-link":
        token = auth.request_password_reset(email, limited=False)     # the operator is not rate-limited
        page = "reset"
    else:
        token = auth.request_verification(email, limited=False)
        page = "verify"
    if not token:
        print("Aucun compte pour cette adresse.")
        return 1
    print(mailer.link(page, token))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
