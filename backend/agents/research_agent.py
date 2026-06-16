"""MarketMind AI Dashboard - Research Agent (Fast: pre-fetch + single LLM call)"""
from __future__ import annotations
import json
import logging
import asyncio
from datetime import datetime, timezone

from .base_agent import BaseAgent
from core.models import ResearchOutput, Article
from core.trace import AgentTraceEntry, ToolCallTrace

logger = logging.getLogger(__name__)


def _article_timestamp(article: dict) -> float:
    published = article.get("published_at")
    if isinstance(published, datetime):
        return published.timestamp()
    if isinstance(published, str):
        try:
            return datetime.fromisoformat(published.replace("Z", "+00:00")).timestamp()
        except Exception:
            return 0
    return 0


def _rank_and_dedupe_articles(articles: list[dict], symbol: str, limit: int = 15) -> list[dict]:
    seen: set[str] = set()
    ranked: list[tuple[tuple[int, int, float], dict]] = []
    symbol_lower = symbol.lower()

    for article in articles:
        title = (article.get("title") or "").strip()
        url = (article.get("url") or "").strip()
        if not title and not url:
            continue

        key = (url or title).lower()
        if key in seen:
            continue
        seen.add(key)

        source_score = 1 if article.get("source") else 0
        relevance_score = 1 if symbol_lower in title.lower() or symbol_lower in (article.get("snippet") or "").lower() else 0
        ranked.append(((relevance_score, source_score, _article_timestamp(article)), article))

    ranked.sort(key=lambda item: item[0], reverse=True)
    return [article for _, article in ranked[:limit]]


def _build_data_quality(data: dict) -> tuple[str, list[str], dict]:
    issues: list[str] = []
    news_count = len(data.get("news_articles", []))
    reddit_count = len(data.get("reddit_posts", []))
    price = data.get("price", {})
    company = data.get("company", {})
    financials = data.get("financials", {})
    macro = data.get("macro", {})

    if news_count < 3:
        issues.append("limited news coverage")
    if reddit_count == 0:
        issues.append("reddit unavailable or no relevant posts")
    if not price.get("price"):
        issues.append("price unavailable")
    if not financials.get("pe_ratio") and not company.get("pe_ratio"):
        issues.append("fundamentals missing")
    if not macro:
        issues.append("macro data unavailable")

    critical_present = bool(price.get("price")) and bool(news_count)
    if critical_present and not issues:
        quality = "good"
    elif critical_present or news_count >= 3:
        quality = "partial"
    else:
        quality = "poor"

    metadata = {
        "news_count": news_count,
        "reddit_count": reddit_count,
        "sources": sorted({
            *(article.get("source", "") for article in data.get("news_articles", [])),
            *(post.get("source", "") for post in data.get("reddit_posts", [])),
        } - {""}),
        "price_source": price.get("source", "") or "unavailable",
        "fundamentals_source": "Finnhub/Alpha Vantage" if financials else "unavailable",
        "macro_source": "Finnhub" if macro else "unavailable",
    }
    return quality, issues, metadata


async def _record_fetch(
    label: str,
    coro,
    trace_agent: AgentTraceEntry | None,
    **kwargs,
):
    """Execute a coroutine and record the result as a ToolCallTrace."""
    started_at = datetime.now(timezone.utc)
    try:
        result = await coro
        success = True
        error_msg = None
        # Compact preview
        if isinstance(result, list):
            preview = f"{len(result)} items fetched"
        elif isinstance(result, dict):
            keys_list = list(result.keys())[:5]
            preview = f"keys: {keys_list}"
        elif result is not None:
            preview = str(result)[:200]
        else:
            preview = "null"
    except Exception as e:
        result = None
        success = False
        error_msg = str(e)
        preview = f"error: {error_msg[:150]}"
    completed_at = datetime.now(timezone.utc)
    duration_ms = ((completed_at - started_at).total_seconds()) * 1000

    if trace_agent is not None:
        trace_agent.tool_calls.append(ToolCallTrace(
            tool_name=label,
            arguments=kwargs,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
            success=success,
            error=error_msg,
            compact_result_preview=preview,
        ))
    return result


# ── Pre-fetch all data directly (avoids slow LLM tool-calling loop) ──

async def _fetch_all_data(symbol: str, trace_agent: AgentTraceEntry | None = None) -> dict:
    """Fetch all data sources concurrently. Returns a dict for the LLM to summarize."""
    from data.google_news_client import fetch_google_news
    from data.reddit_client import fetch_reddit_posts
    from data.finnhub_client import get_stock_quote, get_company_profile as finnhub_profile, get_company_basic_financials
    from data.alpha_vantage_client import get_company_overview
    from data.finnhub_client import get_market_indices

    results = {"symbol": symbol}

    # Fire all requests concurrently, each with tracing
    google_news, reddit, quote, finnhub_prof, financials, overview, indices = await asyncio.gather(
        _record_fetch("fetch_google_news", fetch_google_news(f"{symbol} stock", 15), trace_agent, symbol=symbol, limit=15),
        _record_fetch("fetch_reddit_posts", fetch_reddit_posts(symbol), trace_agent, symbol=symbol),
        _record_fetch("get_stock_quote", get_stock_quote(symbol), trace_agent, symbol=symbol),
        _record_fetch("get_company_profile", finnhub_profile(symbol), trace_agent, symbol=symbol),
        _record_fetch("get_company_basic_financials", get_company_basic_financials(symbol), trace_agent, symbol=symbol),
        _record_fetch("get_company_overview", get_company_overview(symbol), trace_agent, symbol=symbol),
        _record_fetch("get_market_indices", get_market_indices(), trace_agent),
    )

    results["news_articles"] = _rank_and_dedupe_articles(google_news or [], symbol, limit=15)
    results["reddit_posts"] = reddit or []

    # Merge price data
    price_info = {"price": None, "change_pct": None, "source": "none"}
    if quote and quote.get("current_price"):
        price_info["price"] = quote["current_price"]
        price_info["change_pct"] = quote.get("change_percent")
        price_info["source"] = "Finnhub"
    results["price"] = price_info

    # Company info
    company = {"name": symbol, "sector": "", "market_cap": None, "description": ""}
    if finnhub_prof:
        company["name"] = finnhub_prof.get("name", symbol)
        company["sector"] = finnhub_prof.get("sector", "")
        company["market_cap"] = finnhub_prof.get("market_cap")
    if overview:
        company["name"] = company["name"] or overview.get("name", symbol)
        company["sector"] = company["sector"] or overview.get("sector", "")
        company["description"] = overview.get("description", "")[:300]
        company["pe_ratio"] = overview.get("pe_ratio")
    results["company"] = company

    # Financials
    fin = {"pe_ratio": None, "eps": None, "beta": None, "market_cap": None}
    if financials:
        fin.update({k: v for k, v in financials.items() if v is not None})
    if overview and not fin.get("pe_ratio"):
        fin["pe_ratio"] = overview.get("pe_ratio")
    results["financials"] = fin

    # Macro
    results["macro"] = indices if indices else {}
    results["fetched_at"] = datetime.now(timezone.utc)

    data_quality, data_issues, metadata = _build_data_quality(results)
    results["data_quality"] = data_quality
    results["data_issues"] = data_issues
    results["metadata"] = metadata

    return results


class ResearchAgent(BaseAgent):
    AGENT_NAME = "research_agent"
    SYSTEM_PROMPT = """You are the Research Agent for MarketMind AI Dashboard. You receive pre-fetched data and summarize it.

Given the data below about a stock, produce a JSON summary:
{
    "company_summary": "2-3 sentence description of what the company does",
    "key_themes": ["theme1", "theme2", "theme3"],
    "news_highlights": ["notable headline 1", "notable headline 2"],
    "reddit_sentiment_summary": "Brief 1-sentence summary of what retail investors are saying",
    "data_quality": "good|partial|poor"
}

Rules:
- Be factual, only use the provided data
- You only have headlines/snippets and structured API data; do not claim to have read full articles
- If data is missing, note it honestly
- If data_quality is partial or poor, keep conclusions appropriately cautious
- Keep everything beginner-friendly
- Write all free-text fields in English."""

    async def run(self, context: dict) -> ResearchOutput:
        memory = context.get("memory")
        symbol = context.get("symbol", "Unknown")
        trace_agent = context.get("trace_agent")

        logger.info(f"[ResearchAgent] Fetching data for {symbol}...")

        try:
            # Pre-fetch all data directly (fast, concurrent HTTP calls) with tracing
            data = await _fetch_all_data(symbol, trace_agent=trace_agent)
            logger.info(f"[ResearchAgent] Data fetched: {len(data.get('news_articles',[]))} news, {len(data.get('reddit_posts',[]))} Reddit posts")
        except Exception as e:
            logger.error(f"[ResearchAgent] Data fetch failed: {e}")
            data = {"news_articles": [], "reddit_posts": [], "symbol": symbol}

        # Build context for LLM summarization
        news_text = "\n".join([
            f"- [{a.get('source','?')}] {a.get('title','')}" 
            for a in data.get("news_articles", [])[:10]
        ]) or "(no news available)"

        reddit_text = "\n".join([
            f"- [{p.get('source','?')}] {p.get('title','')}"
            for p in data.get("reddit_posts", [])[:10]
        ]) or "(no Reddit posts)"

        price = data.get("price", {})
        company = data.get("company", {})
        fin = data.get("financials", {})
        metadata = data.get("metadata", {})
        data_quality = data.get("data_quality", "unknown")
        data_issues = data.get("data_issues", [])

        context_for_llm = f"""Data for {symbol}:

COMPANY: {json.dumps(company, default=str)}
PRICE: {json.dumps(price, default=str)}
KEY METRICS: {json.dumps(fin, default=str)}
DATA QUALITY: {data_quality}
DATA ISSUES: {json.dumps(data_issues, default=str)}
DATA SOURCES: {json.dumps(metadata, default=str)}

RECENT NEWS ({len(data.get('news_articles',[]))} articles):
{news_text}

REDDIT POSTS ({len(data.get('reddit_posts',[]))} posts):
{reddit_text}
"""

        try:
            # Single LLM call for summarization
            parsed = await self._call_json_llm(
                user_prompt=f"Summarize this research data for {symbol} stock. Return ONLY valid English JSON.",
                context=context_for_llm,
                fallback={
                    "company_summary": f"Research for {symbol} — see data below.",
                    "data_quality": "partial",
                },
                temperature=0.3,
                max_tokens=1100,
                thinking_enabled=False,
                trace_agent=trace_agent,
                llm_call_name="research_summary_json",
            )
            logger.info(f"[ResearchAgent] LLM summary complete for {symbol}")
        except Exception as e:
            logger.error(f"[ResearchAgent] LLM summarization failed: {e}")
            parsed = {"company_summary": f"Research for {symbol} — see data below.", "data_quality": "partial"}

        # Build Article objects for the frontend news feed
        news_articles = []
        for a in data.get("news_articles", [])[:15]:
            pub_date = a.get("published_at")
            if isinstance(pub_date, datetime):
                pass  # keep as datetime
            elif isinstance(pub_date, str):
                try:
                    pub_date = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                except Exception:
                    pub_date = None
            
            news_articles.append(Article(
                title=a.get("title", ""),
                url=a.get("url", ""),
                source=a.get("source", ""),
                published_at=pub_date,
                snippet=a.get("snippet", ""),
            ))

        reddit_posts = []
        for p in data.get("reddit_posts", [])[:15]:
            pub_date = p.get("published_at")
            if isinstance(pub_date, datetime):
                pass
            elif isinstance(pub_date, str):
                try:
                    pub_date = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                except Exception:
                    pub_date = None
            
            reddit_posts.append(Article(
                title=p.get("title", ""),
                url=p.get("url", ""),
                source=p.get("source", ""),
                published_at=pub_date,
                snippet=p.get("snippet", ""),
            ))

        output = ResearchOutput(
            news_articles=news_articles,
            reddit_posts=reddit_posts,
            company_profile=parsed.get("company_summary", ""),
            summary=parsed.get("company_summary", ""),
            data_quality=data.get("data_quality", "unknown"),
            data_issues=data.get("data_issues", []),
            news_count=len(news_articles),
            reddit_count=len(reddit_posts),
            sources=data.get("metadata", {}).get("sources", []),
            price_source=data.get("metadata", {}).get("price_source", ""),
            fundamentals_source=data.get("metadata", {}).get("fundamentals_source", ""),
            macro_source=data.get("metadata", {}).get("macro_source", ""),
            fetched_at=data.get("fetched_at"),
        )

        memory.write("research_output", output)
        logger.info(f"[ResearchAgent] Done for {symbol}")
        return output

    def _parse_json(self, text: str) -> dict:
        return BaseAgent._parse_json_response(
            text,
            fallback={"company_summary": text[:500] if isinstance(text, str) else ""},
            allow_list_first_dict=True,
        )
