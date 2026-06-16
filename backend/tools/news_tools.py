"""MarketMind AI Dashboard - News Tools (search_news, get_company_news)"""
from __future__ import annotations
import logging
from datetime import datetime

from core.tool_registry import tool, tool_registry
from data.finnhub_client import get_company_news as finnhub_company_news
from data.google_news_client import fetch_google_news

logger = logging.getLogger(__name__)


@tool(
    name="search_news",
    description="Search recent news articles about a stock symbol from multiple sources (Google News, financial APIs)",
)
async def search_news(query: str, limit: int = 10) -> dict:
    """Search for news articles about a stock using Google News RSS."""
    articles = await fetch_google_news(query, limit=limit)
    return {
        "query": query,
        "total_results": len(articles),
        "articles": articles,
    }


@tool(
    name="get_company_news",
    description="Get recent company-specific news from financial data providers for a stock symbol",
)
async def get_company_news(symbol: str, limit: int = 10) -> dict:
    """Get company news from Finnhub (requires API key) and Google News as fallback."""
    symbol = symbol.upper()
    articles = await finnhub_company_news(symbol)

    if not articles:
        # Fallback to Google News
        articles = await fetch_google_news(f"{symbol} stock news", limit=limit)
        source = "Google News (fallback)"
    else:
        source = "Finnhub"
        articles = articles[:limit]

    return {
        "symbol": symbol,
        "total_results": len(articles),
        "source": source,
        "articles": articles,
    }


@tool(
    name="get_reddit_sentiment",
    description="Get Reddit posts about a stock symbol from r/stocks and r/investing for retail sentiment analysis",
)
async def get_reddit_sentiment(symbol: str, limit: int = 25) -> dict:
    """Fetch Reddit posts from relevant subreddits."""
    from data.reddit_client import fetch_reddit_posts

    posts = await fetch_reddit_posts(symbol)
    posts = posts[:limit]

    return {
        "symbol": symbol.upper(),
        "total_posts": len(posts),
        "subreddits": ["r/stocks", "r/investing"],
        "posts": posts,
    }


# Register tools
tool_registry.register(search_news)
tool_registry.register(get_company_news)
tool_registry.register(get_reddit_sentiment)