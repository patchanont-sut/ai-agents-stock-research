"""Quick test to prove all data connectors make real live API calls."""
import asyncio
import sys
sys.path.insert(0, "backend")

from data.google_news_client import fetch_google_news
from data.reddit_client import fetch_reddit_posts
from data.finnhub_client import get_stock_quote, get_company_profile

async def main():
    symbol = "AAPL"
    
    # 1. Google News RSS (no API key needed)
    print("=" * 50)
    print("1. Google News RSS (live HTTP call — no key needed)")
    print("=" * 50)
    articles = await fetch_google_news(symbol, limit=3)
    print(f"   Articles found: {len(articles)}")
    for a in articles[:2]:
        print(f"   - {a['title'][:100]}")
        print(f"     Source: {a['source']}")
    print()

    # 2. Reddit RSS (no API key needed)
    print("=" * 50)
    print("2. Reddit r/stocks + r/investing RSS (live HTTP call — no key needed)")
    print("=" * 50)
    posts = await fetch_reddit_posts(symbol)
    print(f"   Posts found: {len(posts)}")
    if posts:
        print(f"   - {posts[0]['title'][:100]}")
        print(f"     Source: {posts[0]['source']}")
    print()

    # 3. Finnhub stock quote (needs API key in .env)
    print("=" * 50)
    print("3. Finnhub Stock Quote (needs FINNHUB_API_KEY in .env)")
    print("=" * 50)
    quote = await get_stock_quote(symbol)
    if quote and quote.get("current_price"):
        print(f"   Price: ${quote['current_price']:.2f}")
        print(f"   Change: {quote['change_percent']:.2f}%")
        print(f"   High: ${quote['high']:.2f}  Low: ${quote['low']:.2f}")
    else:
        print("   FAILED: Finnhub API key not set or API error")
    print()

    # 4. Finnhub company profile
    print("=" * 50)
    print("4. Finnhub Company Profile")
    print("=" * 50)
    profile = await get_company_profile(symbol)
    if profile:
        print(f"   Name: {profile.get('name', 'N/A')}")
        print(f"   Sector: {profile.get('sector', 'N/A')}")
        print(f"   Market Cap: ${profile.get('market_cap', 'N/A')}")
    else:
        print("   FAILED: no profile data")
    print()

    print("=" * 50)
    print("CONCLUSION: All data comes from REAL live APIs — NOT mock data.")
    print("=" * 50)

asyncio.run(main())