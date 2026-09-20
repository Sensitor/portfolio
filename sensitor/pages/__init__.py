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
]
