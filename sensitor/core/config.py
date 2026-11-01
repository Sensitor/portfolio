"""
Application configuration.

Values that come from the environment, in one place, read once at import. Nothing
here imports Streamlit, so the same configuration serves the app, the report
generator and a future API.

Phase 1 defines the surface; the legacy entry point still owns its own copies of
the Stripe and tier settings and is migrated onto these in Phase 2, so that no
behaviour changes while the structure moves.
"""

from __future__ import annotations

import os

# ── Product ──────────────────────────────────────────────────────────────────
PRODUCT_NAME = "Sensitor Portfolio Intelligence"
PRODUCT_SHORT = "Sensitor"
VERSION = "5.0.0"

# ── Market data ──────────────────────────────────────────────────────────────
# Cache lifetime for price downloads. Long enough that a session of clicking
# around never re-hits the provider, short enough that a day's prices are fresh.
MARKET_CACHE_TTL = int(os.getenv("SENSITOR_MARKET_CACHE_TTL", "3600"))

# ── Analytics defaults ───────────────────────────────────────────────────────
TRADING_DAYS = 252
DEFAULT_RISK_FREE_RATE = float(os.getenv("SENSITOR_RISK_FREE_RATE", "0.04"))

# ── Persistence ──────────────────────────────────────────────────────────────
DB_PATH = os.getenv("SENSITOR_DB_PATH", "sensitor_data.db")

# ── Access ───────────────────────────────────────────────────────────────────
# No billing: no paid plan exists before a regulatory review (CLAUDE.md).

# Comma-separated addresses granted Premium at sign-in, as a « config »
# entitlement (`core.auth`). Lowercase, like every stored address.
# PRO_EMAILS=alice@x.com,bob@y.com
PRO_EMAILS = frozenset(
    e.strip().lower() for e in os.getenv("PRO_EMAILS", "").split(",") if e.strip()
)

# Levels, capabilities and limits are in `core.permissions`.
