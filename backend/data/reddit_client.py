"""MarketMind AI Dashboard - Reddit RSS Client (no API key required)"""
from __future__ import annotations
import asyncio
import logging
import urllib.parse
from datetime import datetime

import feedparser

from config import settings
from cache.cache_manager import cache
from data.http_client import get_data_http_client

logger = logging.getLogger(__name__)


async def fetch_reddit_posts(symbol: str, subreddits: list[str] = None) -> list[dict]:
    """Search Reddit r/stocks and r/investing via RSS for posts about a stock symbol."""
    if subreddits is None:
        subreddits = ["stocks", "investing"]

    async def fetch_subreddit(subreddit: str) -> list[dict]:
        cache_key = f"reddit:{subreddit}:{symbol.lower()}"
        cached = cache.get(cache_key)
        if cached:
            logger.debug(f"Reddit cache hit: {cache_key}")
            return cached

        query = urllib.parse.quote(symbol.upper())
        rss_url = settings.REDDIT_RSS_TEMPLATE.format(subreddit=subreddit, query=query)

        try:
            client = get_data_http_client()
            response = await client.get(
                rss_url,
                headers={"User-Agent": "MarketMind-AI/1.0"},
                follow_redirects=True,
            )
            response.raise_for_status()

            feed = feedparser.parse(response.text)
            posts = []
            for entry in feed.entries[:settings.REDDIT_POST_LIMIT]:
                pub_date = None
                try:
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6])
                except Exception:
                    pass

                snippet = ""
                if hasattr(entry, "summary"):
                    # Strip HTML tags for a clean snippet
                    from re import sub
                    raw = entry.get("summary", "")
                    snippet = sub(r"<[^>]+>", "", raw)[:300]

                posts.append({
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "source": f"Reddit r/{subreddit}",
                    "published_at": pub_date,
                    "snippet": snippet,
                })

            cache.set(cache_key, posts, ttl_seconds=settings.CACHE_TTL_NEWS)
            logger.info(f"Reddit r/{subreddit}: {len(posts)} posts for '{symbol}'")
            return posts

        except Exception as e:
            logger.error(f"Reddit RSS r/{subreddit} failed for '{symbol}': {e}")
            stale, is_stale = cache.get_with_meta(cache_key)
            if is_stale and stale:
                return stale
            return []

    results = await asyncio.gather(*(fetch_subreddit(subreddit) for subreddit in subreddits))
    return [post for posts in results for post in posts]
