"""
Operator commands for accounts, for deployments without an e-mail server.

    python -m sensitor.core.admin reset-link someone@example.com
    python -m sensitor.core.admin verify-link someone@example.com

Prints a single-use link (reset: valid one hour; verification: 48 hours) that
the operator sends to the account holder by another channel. Uses the same
database as the app (SENSITOR_DB_URL / SENSITOR_DB_PATH) and the same
SENSITOR_PUBLIC_URL as the e-mails. Nothing is printed for an unknown address.
"""

from __future__ import annotations

import sys

from ..database import Store
from . import mailer
from .auth import MULTI, Auth


def main(argv: list[str]) -> int:
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
