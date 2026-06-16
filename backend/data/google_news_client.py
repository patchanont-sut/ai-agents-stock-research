"""MarketMind AI Dashboard - Google News RSS Client"""
from __future__ import annotations
import html
import logging
import re
import urllib.parse
from datetime import datetime
from typing import Optional

import feedparser

from config import settings
from cache.cache_manager import cache
from data.http_client import get_data_http_client

logger = logging.getLogger(__name__)

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")

def _clean_html_text(value: str, max_length: int | None = None) -> str:
    """Strip HTML tags, unescape entities, and collapse whitespace."""
    if not value:
        return ""
    text = html.unescape(str(value))
    text = _TAG_RE.sub(" ", text)
    text = _WS_RE.sub(" ", text).strip()
    if max_length is not None:
        text = text[:max_length].strip()
    return text


async def fetch_google_news(query: str, limit: int = 15) -> list[dict]:
    """Search Google News RSS for articles about a stock or topic."""
    cache_key = f"google_news:v2:{query.lower()}:{limit}"
    
    cached = cache.get(cache_key)
    if cached:
        logger.debug(f"Google News cache hit: {cache_key}")
        return cached if len(cached) <= limit else cached[:limit]

    encoded = urllib.parse.quote(f"{query} stock")
    rss_url = f"{settings.GOOGLE_NEWS_RSS_URL}?q={encoded}&hl=en-US&ceid=US:en"

    try:
        client = get_data_http_client()
        response = await client.get(rss_url, follow_redirects=True)
        response.raise_for_status()
        
        feed = feedparser.parse(response.text)
        articles = []
        for entry in feed.entries[:limit]:
            pub_date = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    pub_date = datetime(*entry.published_parsed[:6])
                except Exception:
                    pass

            raw_title = entry.get("title", "") or ""
            raw_source = (
                entry.get("source", {}).get("title", "Google News")
                if hasattr(entry, "source")
                else "Google News"
            )
            raw_summary = entry.get("summary", "") or ""

            articles.append({
                "title": _clean_html_text(raw_title),
                "url": entry.get("link", ""),
                "source": _clean_html_text(raw_source) or "Google News",
                "published_at": pub_date,
                "snippet": _clean_html_text(raw_summary, max_length=300),
            })

        cache.set(cache_key, articles, ttl_seconds=settings.CACHE_TTL_NEWS)
        logger.info(f"Google News: {len(articles)} articles for '{query}'")
        return articles
    except Exception as e:
        logger.error(f"Google News RSS failed for '{query}': {e}")
        stale, is_stale = cache.get_with_meta(cache_key)
        if is_stale and stale:
            logger.info(f"Using stale Google News cache for: {query}")
            return stale
        return []


async def fetch_company_news_google(symbol: str, limit: int = 15) -> list[dict]:
    """Convenience: fetch news using company name + symbol."""
    return await fetch_google_news(f"{symbol} stock", limit)
