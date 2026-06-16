"""MarketMind AI Dashboard - Alpha Vantage API Client"""
from __future__ import annotations
import logging
from typing import Optional

from config import settings
from cache.cache_manager import cache
from data.http_client import get_data_http_client

logger = logging.getLogger(__name__)

BASE_URL = settings.ALPHA_VANTAGE_BASE_URL


async def alpha_vantage_request(function: str, **params) -> Optional[dict]:
    """Make an authenticated request to Alpha Vantage API with caching."""
    if not settings.ALPHA_VANTAGE_API_KEY:
        logger.warning("Alpha Vantage API key not set — cannot make request")
        return None

    all_params = {"function": function, "apikey": settings.ALPHA_VANTAGE_API_KEY}
    all_params.update(params)

    cache_key = f"av:{function}:{str(sorted(params.items()))}"

    cached = cache.get(cache_key)
    if cached:
        logger.debug(f"Alpha Vantage cache hit: {cache_key}")
        return cached

    try:
        client = get_data_http_client()
        response = await client.get(BASE_URL, params=all_params)
        response.raise_for_status()
        data = response.json()

        # Alpha Vantage returns error messages as json with "Error Message" or "Note" key
        if "Error Message" in data:
            logger.error(f"Alpha Vantage error: {data['Error Message']}")
            return None
        if "Note" in data:
            logger.warning(f"Alpha Vantage rate limit: {data['Note']}")
            return None

        cache.set(cache_key, data, ttl_seconds=settings.CACHE_TTL_FUNDAMENTALS)
        return data
    except Exception as e:
        logger.error(f"Alpha Vantage request failed ({function}): {e}")
        stale, is_stale = cache.get_with_meta(cache_key)
        if is_stale and stale:
            return stale
        return None


async def get_company_overview(symbol: str) -> Optional[dict]:
    """Get company overview: description, sector, PE, market cap, etc."""
    data = await alpha_vantage_request("OVERVIEW", symbol=symbol.upper())
    if data and data.get("Symbol"):
        return {
            "symbol": data.get("Symbol", ""),
            "name": data.get("Name", ""),
            "description": data.get("Description", "")[:500],
            "sector": data.get("Sector", ""),
            "industry": data.get("Industry", ""),
            "market_cap": data.get("MarketCapitalization"),
            "pe_ratio": data.get("PERatio"),
            "peg_ratio": data.get("PEGRatio"),
            "pb_ratio": data.get("PriceToBookRatio"),
            "eps": data.get("EPS"),
            "revenue_ttm": data.get("RevenueTTM"),
            "gross_margin": data.get("GrossProfitTTM"),
            "dividend_yield": data.get("DividendYield"),
            "beta": data.get("Beta"),
            "52_week_high": data.get("52WeekHigh"),
            "52_week_low": data.get("52WeekLow"),
            "analyst_target": data.get("AnalystTargetPrice"),
        }
    return None


async def get_global_quote(symbol: str) -> Optional[dict]:
    """Get latest stock price (fallback to Finnhub)."""
    data = await alpha_vantage_request("GLOBAL_QUOTE", symbol=symbol.upper())
    if data and data.get("Global Quote"):
        q = data["Global Quote"]
        return {
            "symbol": q.get("01. symbol", ""),
            "price": float(q.get("05. price", 0)),
            "change": float(q.get("09. change", 0)),
            "change_percent": float(q.get("10. change percent", "0%").replace("%", "")),
        }
    return None


async def get_treasury_yield() -> Optional[dict]:
    """Get 10-year Treasury yield."""
    data = await alpha_vantage_request("TREASURY_YIELD", interval="monthly", maturity="10year")
    if data and data.get("data"):
        latest = data["data"][0]
        return {
            "date": latest.get("date"),
            "yield": float(latest.get("value", 0)),
        }
    return None


async def get_fed_funds_rate() -> Optional[dict]:
    """Get Federal Funds Rate."""
    data = await alpha_vantage_request("FEDERAL_FUNDS_RATE", interval="monthly")
    if data and data.get("data"):
        latest = data["data"][0]
        return {
            "date": latest.get("date"),
            "rate": float(latest.get("value", 0)),
        }
    return None


async def get_sector_performance() -> Optional[dict]:
    """Get sector performance data."""
    data = await alpha_vantage_request("SECTOR")
    if not data:
        return None

    result = {}
    for sector, change_str in data.items():
        if sector.startswith("Rank"):
            # Extract sector name from Rank key
            name = sector.replace("Rank A: ", "").replace("Rank B: ", "").replace("Real-Time", "").strip()
            try:
                result[name] = float(change_str.replace("%", ""))
            except (ValueError, AttributeError):
                pass
    return result
