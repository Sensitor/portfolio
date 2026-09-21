"""
Small shared helpers.

Only things genuinely used across domains live here. Anything specific to
investing, trading or the UI belongs in that domain, not in a utility bucket.
"""

from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> str:
    """UTC timestamp, second precision — the format every stored record uses."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def safe_div(numerator, denominator, default=0.0):
    """Division that returns `default` instead of raising on a zero divisor."""
    try:
        if not denominator:
            return default
        return numerator / denominator
    except (TypeError, ZeroDivisionError):
        return default


def clamp(value, low, high):
    return max(low, min(high, value))


def jsonable(value):
    """
    Coerce numpy scalars and other odd types to plain JSON types.

    Anything it cannot place becomes a string rather than failing the call: a
    record with one stringified field is worth more than no record.
    """
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return str(value)
