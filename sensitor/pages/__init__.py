"""Page renderers for Sensitor Portfolio Intelligence."""

from .overview import render_overview
from .performance import render_performance
from .health import render_health
from .risk import render_risk
from .xray_page import render_xray
from .stress import render_stress
from .optimize_page import render_optimize
from .simulator import render_simulator
from .copilot_page import render_copilot
from .portfolios import render_portfolios
from .reports import render_reports
from .advisor import render_advisor

from .trading_overview import render_trading_overview
from .trading_journal import render_trading_journal
from .trading_analytics import render_trading_analytics
from .trading_risk import render_trading_risk
from .trading_psychology import render_trading_psychology

__all__ = [
    "render_overview",
    "render_performance",
    "render_health",
    "render_risk",
    "render_xray",
    "render_stress",
    "render_optimize",
    "render_simulator",
    "render_copilot",
    "render_portfolios",
    "render_reports",
    "render_advisor",
    "render_trading_overview",
    "render_trading_journal",
    "render_trading_analytics",
    "render_trading_risk",
    "render_trading_psychology",
]
