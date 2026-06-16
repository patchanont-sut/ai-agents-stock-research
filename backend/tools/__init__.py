"""MarketMind AI Dashboard - Tools Module
Each tool module registers itself with tool_registry upon import.
"""
from . import news_tools, market_tools, macro_tools  # noqa: F401 — side-effect: registers tools
