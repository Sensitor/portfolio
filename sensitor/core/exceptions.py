"""
Exception hierarchy.

One base class so a caller can catch everything this package raises without
catching unrelated errors, and specific subclasses so it can distinguish the
cases it knows how to handle — a missing data feed is recoverable, an invalid
portfolio is a caller bug.
"""

from __future__ import annotations


class SensitorError(Exception):
    """Base for every error raised by this package."""


class DataUnavailableError(SensitorError):
    """
    A required data source could not be reached or returned nothing usable.

    Recoverable by design: the app degrades to portfolio-only figures rather than
    failing, so this is raised only where a caller can act on it.
    """


class InsufficientHistoryError(SensitorError):
    """Not enough observations for the requested statistic to mean anything."""


class InvalidPortfolioError(SensitorError):
    """Weights, holdings or tickers that cannot describe a portfolio."""


class StorageError(SensitorError):
    """The database could not be opened, read or written."""


class IntegrationError(SensitorError):
    """An external platform (broker, terminal, provider) refused or failed."""
