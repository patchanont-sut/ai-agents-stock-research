"""MarketMind AI Dashboard - Finnhub API Client"""
from __future__ import annotations
import logging
from typing import Optional

from config import settings
from cache.cache_manager import cache
from data.http_client import get_data_http_client

logger = logging.getLogger(__name__)

BASE_URL = settings.FINNHUB_BASE_URL


async def finnhub_request(endpoint: str, params: dict = None) -> Optional[dict]:
    """Make an authenticated request to Finnhub API with caching."""
    if not settings.FINNHUB_API_KEY:
        logger.warning("Finnhub API key not set — cannot make request")
        return None

    params = params or {}
    params["token"] = settings.FINNHUB_API_KEY

    # Build cache key
    cache_key = f"finnhub:{endpoint}:{str(sorted(params.items()))}"
    cache_ttl = settings.CACHE_TTL_PRICE if "quote" in endpoint else settings.CACHE_TTL_NEWS

    cached = cache.get(cache_key)
    if cached:
        logger.debug(f"Finnhub cache hit: {cache_key}")
        return cached

    try:
        client = get_data_http_client()
        response = await client.get(f"{BASE_URL}{endpoint}", params=params)
        response.raise_for_status()
        data = response.json()
        cache.set(cache_key, data, ttl_seconds=cache_ttl)
        return data
    except Exception as e:
        logger.error(f"Finnhub request failed ({endpoint}): {e}")
        stale_data, is_stale = cache.get_with_meta(cache_key)
        if is_stale and stale_data:
            logger.info(f"Using stale Finnhub cache for: {cache_key}")
            return stale_data
        return None


async def get_stock_quote(symbol: str) -> Optional[dict]:
    """Get current stock quote: price, change, high, low, open."""
    data = await finnhub_request("/quote", {"symbol": symbol.upper()})
    if data and data.get("c"):  # "c" = current price
        return {
            "symbol": symbol.upper(),
            "current_price": data.get("c"),
            "change": data.get("d"),
            "change_percent": data.get("dp"),
            "high": data.get("h"),
            "low": data.get("l"),
            "open": data.get("o"),
            "previous_close": data.get("pc"),
        }
    return None


async def get_company_profile(symbol: str) -> Optional[dict]:
    """Get company profile: name, sector, market cap, etc."""
    data = await finnhub_request("/stock/profile2", {"symbol": symbol.upper()})
    if data:
        return {
            "symbol": symbol.upper(),
            "name": data.get("name", ""),
            "sector": data.get("finnhubIndustry", ""),
            "market_cap": data.get("marketCapitalization"),
            "logo": data.get("logo", ""),
            "exchange": data.get("exchange", ""),
            "currency": data.get("currency", "USD"),
            "country": data.get("country", ""),
            "weburl": data.get("weburl", ""),
        }
    return None


async def get_company_news(
    symbol: str, from_date: str = None, to_date: str = None
) -> list[dict]:
    """Get recent company news from Finnhub."""
    from datetime import datetime, timedelta
    if not to_date:
        to_date = datetime.now().strftime("%Y-%m-%d")
    if not from_date:
        from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    data = await finnhub_request(
        "/company-news",
        {"symbol": symbol.upper(), "from": from_date, "to": to_date},
    )
    if isinstance(data, list):
        articles = []
        for item in data[:settings.MAX_NEWS_ARTICLES]:
            articles.append({
                "title": item.get("headline", ""),
                "url": item.get("url", ""),
                "source": item.get("source", "Finnhub"),
                "published_at": datetime.fromtimestamp(item.get("datetime", 0)) if item.get("datetime") else None,
                "snippet": item.get("summary", "")[:300],
            })
        return articles
    return []


async def get_company_basic_financials(symbol: str) -> Optional[dict]:
    """Get basic financial metrics from Finnhub."""
    data = await finnhub_request("/stock/metric", {"symbol": symbol.upper()})
    if data and data.get("metric"):
        m = data["metric"]
        return {
            "pe_ratio": m.get("peBasicExclExtraTTM") or m.get("peTTM"),
            "pb_ratio": m.get("pbAnnual"),
            "eps": m.get("epsBasicExclExtraItemsTTM") or m.get("epsInclExtraItemsTTM"),
            "roa": m.get("roaRfy"),
            "roe": m.get("roeRfy"),
            "revenue_per_share": m.get("revenuePerShareTTM"),
            "beta": m.get("beta"),
            "market_cap": m.get("marketCapitalization"),
            "dividend_yield": m.get("dividendYieldIndicatedAnnual"),
        }
    return None


async def get_market_indices() -> Optional[dict]:
    """Get S&P500 (^GSPC), NASDAQ (^IXIC) and VIX data."""
    result = {}
    for symbol, label in [
        ("^GSPC", "sp500"),
        ("^IXIC", "nasdaq"),
        ("^VIX", "vix"),
    ]:
        quote = await get_stock_quote(symbol)
        if quote:
            result[label] = {
                "price": quote["current_price"],
                "change_percent": quote["change_percent"],
            }
    return result if result else None


async def lookup_symbol(query: str) -> list[dict]:
    """Search for stock symbols by name."""
    data = await finnhub_request("/search", {"q": query})
    if data and data.get("result"):
        results = []
        for item in data["result"][:10]:
            results.append({
                "symbol": item.get("symbol", ""),
                "name": item.get("description", ""),
                "type": item.get("type", ""),
            })
        return results
    return []
