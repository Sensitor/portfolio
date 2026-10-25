"""
Operator commands for accounts, for deployments without an e-mail server.

    python -m sensitor.core.admin reset-link someone@example.com
    python -m sensitor.core.admin verify-link someone@example.com
    python -m sensitor.core.admin set-role someone@example.com coach|member
    python -m sensitor.core.admin set-tier someone@example.com free|premium

reset-link and verify-link print a single-use link (reset: valid one hour;
verification: 48 hours) that the operator sends to the account holder by
another channel. set-role makes an account a coach, who answers the trade
review requests, or a member again. set-tier sets the access level by hand:
there is no billing. Uses the same database as the app (SENSITOR_DB_URL /
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
        user = store.get_user(email)
        store.upsert_user(email, tier=value, display_name=user.get("display_name"))
        print(f"{email} : niveau {value}.")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) == 3 and argv[0] in ("set-role", "set-tier"):
        return _set(argv)
    if len(argv) != 2 or argv[0] not in ("reset-link", "verify-link"):
        print(__doc__.strip())
        return 2
    command, email = argv
    auth = Auth(Store(), mode=MULTI)
    if command == "reset-link":
        token = auth.request_password_reset(email)
        page = "reset"
    else:
        token = auth.request_verification(email)
        page = "verify"
    if not token:
        print("Aucun compte avec mot de passe pour cette adresse." if page == "reset"
              else "Aucun compte pour cette adresse.")
        return 1
    print(mailer.link(page, token))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
