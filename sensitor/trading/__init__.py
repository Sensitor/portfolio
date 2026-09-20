"""
Trading engine — active trading analytics.

Pure computation over Sensitor's own `Trade` model. No Streamlit, no database,
no broker SDK: a connector normalises a platform's format into `Trade`, and
everything above that point is platform-agnostic, which is what lets MT4,
cTrader or a CSV export arrive later without touching this code.

    models       the Trade model, direction and session, validation
    setups       setup and mistake taxonomies, tag folding
    analytics    P&L, win rate, profit factor, expectancy, R, drawdown, streaks
    performance  the same metrics sliced by symbol, setup, session, weekday...
    risk         exposure, sizing consistency, stop discipline, losing runs
    psychology   behavioural comparisons, framed as correlations
    journal      a queryable collection with the analytics attached

Three conventions hold throughout, and they are what make the numbers honest:
sample size travels with every statistic; undefined stays undefined rather than
becoming zero; money is net of commission and swap.
"""

from . import analytics, journal, models, performance, psychology, risk, setups
from .journal import TradeFilter, TradeJournal
from .models import Direction, Session, Trade

__all__ = [
    "analytics", "journal", "models", "performance", "psychology", "risk", "setups",
    "Trade", "TradeJournal", "TradeFilter", "Direction", "Session",
]
