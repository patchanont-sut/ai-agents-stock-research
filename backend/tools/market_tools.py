"""MarketMind AI Dashboard - Market Data Tools"""
from __future__ import annotations
import logging

from core.tool_registry import tool, tool_registry
from data.finnhub_client import (
    get_stock_quote as finnhub_quote,
    get_company_profile as finnhub_profile,
    get_company_basic_financials as finnhub_financials,
    lookup_symbol as finnhub_lookup,
)
from data.alpha_vantage_client import (
    get_company_overview as av_overview,
    get_global_quote as av_quote,
)

logger = logging.getLogger(__name__)


@tool(
    name="get_stock_price",
    description="Get current stock price, daily change, and basic price data for a symbol",
)
async def get_stock_price(symbol: str) -> dict:
    """Get current stock price from Finnhub, with Alpha Vantage fallback."""
    symbol = symbol.upper()
    
    # Try Finnhub first
    quote = await finnhub_quote(symbol)
    if quote:
        return {
            "symbol": symbol,
            "price": quote["current_price"],
            "change": quote.get("change"),
            "change_percent": quote.get("change_percent"),
            "high": quote.get("high"),
            "low": quote.get("low"),
            "open": quote.get("open"),
            "previous_close": quote.get("previous_close"),
            "source": "Finnhub",
        }

    # Fallback to Alpha Vantage
    av = await av_quote(symbol)
    if av:
        return {
            "symbol": symbol,
            "price": av["price"],
            "change": av.get("change"),
            "change_percent": av.get("change_percent"),
            "high": None,
            "low": None,
            "open": None,
            "previous_close": None,
            "source": "Alpha Vantage",
        }

    return {"symbol": symbol, "price": None, "error": "Unable to fetch stock price"}


@tool(
    name="get_company_profile",
    description="Get company profile: name, sector, industry, market cap, and description",
)
async def get_company_profile(symbol: str) -> dict:
    """Get company profile from both Finnhub and Alpha Vantage, merge results."""
    symbol = symbol.upper()

    profile = await finnhub_profile(symbol)
    overview = await av_overview(symbol)

    result = {
        "symbol": symbol,
        "name": "",
        "sector": "",
        "industry": "",
        "market_cap": None,
        "exchange": "",
        "currency": "USD",
        "description": "",
        "website": "",
        "logo": "",
    }

    if profile:
        result.update({
            "name": profile.get("name", result["name"]) or (overview and overview.get("name", "")),
            "sector": profile.get("sector", ""),
            "market_cap": profile.get("market_cap"),
            "exchange": profile.get("exchange", ""),
            "currency": profile.get("currency", "USD"),
        })

    if overview:
        result["name"] = result["name"] or overview.get("name", "")
        result["sector"] = result["sector"] or overview.get("sector", "")
        result["industry"] = result["industry"] or overview.get("industry", "")
        result["description"] = overview.get("description", "")
        result["pe_ratio"] = overview.get("pe_ratio")
        result["peg_ratio"] = overview.get("peg_ratio")
        result["beta"] = overview.get("beta")
        result["eps"] = overview.get("eps")
        result["dividend_yield"] = overview.get("dividend_yield")

    return result


@tool(
    name="get_basic_financials",
    description="Get basic financial metrics: P/E ratio, P/B ratio, EPS, ROA, ROE, Beta, market cap",
)
async def get_basic_financials(symbol: str) -> dict:
    """Get basic financials from Finnhub + Alpha Vantage."""
    symbol = symbol.upper()
    fin = await finnhub_financials(symbol)
    av = await av_overview(symbol)

    result = {
        "symbol": symbol,
        "pe_ratio": None,
        "pb_ratio": None,
        "eps": None,
        "roe": None,
        "roa": None,
        "beta": None,
        "market_cap": None,
        "dividend_yield": None,
        "source": "none",
    }

    if fin:
        result.update({
            "pe_ratio": fin.get("pe_ratio") or result["pe_ratio"],
            "pb_ratio": fin.get("pb_ratio") or result["pb_ratio"],
            "eps": fin.get("eps") or result["eps"],
            "roe": fin.get("roe") or result["roe"],
            "roa": fin.get("roa") or result["roa"],
            "beta": fin.get("beta") or result["beta"],
            "market_cap": fin.get("market_cap") or result["market_cap"],
            "dividend_yield": fin.get("dividend_yield") or result["dividend_yield"],
        })
        result["source"] = "Finnhub"

    if av:
        result["pe_ratio"] = result["pe_ratio"] or av.get("pe_ratio")
        result["pb_ratio"] = result["pb_ratio"] or av.get("pb_ratio")
        result["eps"] = result["eps"] or av.get("eps")
        result["beta"] = result["beta"] or av.get("beta")
        result["dividend_yield"] = result["dividend_yield"] or av.get("dividend_yield")
        if av.get("market_cap"):
            result["market_cap"] = result["market_cap"] or av["market_cap"]
        if result["source"] == "none":
            result["source"] = "Alpha Vantage"
        elif av:
            result["source"] = "Finnhub + Alpha Vantage"

    return result


@tool(
    name="lookup_symbol",
    description="Search for stock symbols by company name or ticker. Returns matching symbols.",
)
async def lookup_symbol(query: str) -> dict:
    """Search for stock symbols."""
    results = await finnhub_lookup(query)
    return {
        "query": query,
        "total_results": len(results),
        "results": results,
    }


# Register tools
tool_registry.register(get_stock_price)
tool_registry.register(get_company_profile)
tool_registry.register(get_basic_financials)
tool_registry.register(lookup_symbol)