"""MarketMind AI Dashboard - Macro Economic Tools"""
from __future__ import annotations
import logging

from core.tool_registry import tool, tool_registry
from data.finnhub_client import get_market_indices
from data.alpha_vantage_client import get_treasury_yield, get_fed_funds_rate

logger = logging.getLogger(__name__)


@tool(
    name="get_macro_data",
    description="Get macro market data: S&P 500 change, NASDAQ change, VIX index, 10-year Treasury yield, Fed Funds rate",
)
async def get_macro_data() -> dict:
    """Fetch current macro indicators from multiple sources."""
    result = {
        "sp500": None,
        "nasdaq": None,
        "vix": None,
        "treasury_10y": None,
        "fed_funds_rate": None,
        "sources": [],
    }

    # Market indices (Finnhub)
    indices = await get_market_indices()
    if indices:
        if "sp500" in indices:
            result["sp500"] = indices["sp500"]
            result["sources"].append("Finnhub")
        if "nasdaq" in indices:
            result["nasdaq"] = indices["nasdaq"]
        if "vix" in indices:
            result["vix"] = indices["vix"]

    # Treasury yield (Alpha Vantage)
    treasury = await get_treasury_yield()
    if treasury:
        result["treasury_10y"] = treasury.get("yield")
        result["treasury_10y_date"] = treasury.get("date")
        result["sources"].append("Alpha Vantage")

    # Fed Funds Rate (Alpha Vantage)
    fed = await get_fed_funds_rate()
    if fed:
        result["fed_funds_rate"] = fed.get("rate")
        result["fed_funds_date"] = fed.get("date")

    return result


# Register
tool_registry.register(get_macro_data)