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

# ── Billing and entitlements ─────────────────────────────────────────────────
STRIPE_PAYMENT_LINK = os.getenv("STRIPE_PAYMENT_LINK", "")
PRO_PRICE_MONTHLY = 9.99

# Comma-separated emails granted Pro: PRO_EMAILS=alice@x.com,bob@y.com
PRO_EMAILS = frozenset(
    e.strip().lower() for e in os.getenv("PRO_EMAILS", "").split(",") if e.strip()
)

TIER_LIMITS = {
    "free": {"max_assets": 5, "can_optimize": False,
             "can_stress_test": False, "label": "Free"},
    "pro": {"max_assets": 50, "can_optimize": True,
            "can_stress_test": True, "label": "Pro"},
}


def resolve_tier(email: str) -> str:
    """
    Entitlement for an email address.

    Matching is lowercase so a user who types their address with different
    capitalisation than the environment variable still gets what they paid for.
    """
    return "pro" if (email or "").strip().lower() in PRO_EMAILS else "free"


def tier_limits(tier: str) -> dict:
    return TIER_LIMITS.get(tier, TIER_LIMITS["free"])
