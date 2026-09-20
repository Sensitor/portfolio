"""
Investment engine — long-term portfolio analytics.

Pure computation: no Streamlit, no I/O. Everything here takes pandas/numpy in and
returns plain containers, which is what lets the same functions serve the
Streamlit pages, the report generator and a future API without duplication.
"""

from . import analytics, health, optimize, montecarlo, stress, xray

__all__ = ["analytics", "health", "optimize", "montecarlo", "stress", "xray"]
