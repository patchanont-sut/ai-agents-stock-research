"""
MarketMind AI Dashboard — Evidence Library Builder
Converts the analysis result into a structured, deduplicated evidence library.
Entirely deterministic — no LLM calls.
"""
from __future__ import annotations
import html
import re
from typing import Optional

from .models import (
    AnalysisResult,
    EvidenceItem,
    Article,
)

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _clean_html_text(value: str, max_length: int | None = None) -> str:
    """Strip HTML tags, unescape entities, and collapse whitespace.

    Second layer of defense — Google News client already sanitizes,
    but this catches any remaining HTML from other sources.
    """
    if not value:
        return ""
    text = html.unescape(str(value))
    text = _TAG_RE.sub(" ", text)
    text = _WS_RE.sub(" ", text).strip()
    if max_length is not None:
        text = text[:max_length].strip()
    return text

_INVALID_SOURCE_VALUES = frozenset({"", "unknown", "unavailable", "n/a", "none"})


def _is_valid_source(value: str) -> bool:
    """Return False for placeholder/non-source values."""
    if not value:
        return False
    return value.strip().lower() not in _INVALID_SOURCE_VALUES


def _normalize_title(title: str) -> str:
    """Normalize a title for deduplication comparison."""
    return " ".join(title.lower().strip().split())


def _extract_key_points(text: str, max_points: int = 3) -> list[str]:
    """Extract short bullet points from text deterministically."""
    if not text:
        return []
    sentences = [s.strip() for s in text.replace("\n", ". ").split(".") if s.strip()]
    points = []
    for s in sentences[:max_points * 3]:
        if len(s) > 10 and len(s) < 200:
            points.append(s[:200])
        if len(points) >= max_points:
            break
    return points


def _article_to_evidence(
    article: Article,
    evidence_id: str,
    source_type: str,
) -> EvidenceItem:
    """Convert an Article into an EvidenceItem, sanitizing HTML."""
    clean_title = _clean_html_text(article.title) or "Untitled"
    clean_source = _clean_html_text(article.source) or "Unknown source"
    clean_snippet = _clean_html_text(article.snippet or "")
    clean_key_points = _extract_key_points(clean_snippet or clean_title)
    clean_key_points = [_clean_html_text(kp) for kp in clean_key_points]

    return EvidenceItem(
        id=evidence_id,
        source_type=source_type,
        title=clean_title,
        source=clean_source,
        url=article.url if article.url else None,
        published_at=article.published_at,
        snippet=clean_snippet,
        key_points=clean_key_points,
        sentiment_score=article.sentiment_score,
        reliability_notes=[],
    )


def build_evidence_library(result: AnalysisResult) -> list[EvidenceItem]:
    """
    Build a deterministic, deduplicated evidence library from the analysis result.

    Evidence IDs are sequential: E1, E2, E3...

    Sources:
    - research.news_articles → news items
    - research.reddit_posts → reddit items
    - research.company_profile → company_profile item
    - valuation → fundamentals item
    - sentiment → agent_output item
    - risk → agent_output item
    - cio_decision → agent_output item
    """
    evidence_items: list[EvidenceItem] = []
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    counter = 0

    def _next_id() -> str:
        nonlocal counter
        counter += 1
        return f"E{counter}"

    def _is_duplicate(url: Optional[str], title: str) -> bool:
        norm_title = _normalize_title(title)
        if url and url in seen_urls:
            return True
        if norm_title in seen_titles:
            return True
        return False

    def _register(url: Optional[str], title: str) -> None:
        norm_title = _normalize_title(title)
        if url:
            seen_urls.add(url)
        seen_titles.add(norm_title)

    research = result.research

    # ── News Articles ──
    if research:
        for article in research.news_articles or []:
            if _is_duplicate(article.url if article.url else None, article.title):
                continue
            if not _is_valid_source(article.source or ""):
                continue
            eid = _next_id()
            _register(article.url if article.url else None, article.title)
            evidence_items.append(_article_to_evidence(article, eid, "news"))

    # ── Reddit Posts ──
    if research:
        for post in research.reddit_posts or []:
            if _is_duplicate(post.url if post.url else None, post.title):
                continue
            if not _is_valid_source(post.source or ""):
                continue
            eid = _next_id()
            _register(post.url if post.url else None, post.title)
            evidence_items.append(_article_to_evidence(post, eid, "reddit"))

    # ── Company Profile ──
    if research and research.company_profile and len(research.company_profile.strip()) > 10:
        eid = _next_id()
        evidence_items.append(EvidenceItem(
            id=eid,
            source_type="company_profile",
            title=f"Company Profile: {result.symbol}",
            source="Company profile data",
            snippet=research.company_profile[:500],
            key_points=_extract_key_points(research.company_profile),
        ))

    # ── Valuation / Fundamentals ──
    if result.valuation:
        val = result.valuation
        parts = []
        if val.pe_ratio is not None:
            parts.append(f"P/E Ratio: {val.pe_ratio}")
        if val.sector_avg_pe is not None:
            parts.append(f"Sector Avg P/E: {val.sector_avg_pe}")
        if val.peg_ratio is not None:
            parts.append(f"PEG Ratio: {val.peg_ratio}")
        if val.price_to_book is not None:
            parts.append(f"Price/Book: {val.price_to_book}")
        if val.market_cap:
            parts.append(f"Market Cap: {val.market_cap}")
        if val.revenue_growth is not None:
            parts.append(f"Revenue Growth: {val.revenue_growth}%")
        if val.verdict:
            parts.append(f"Verdict: {val.verdict}")
        if parts:
            eid = _next_id()
            snippet = "; ".join(parts)
            evidence_items.append(EvidenceItem(
                id=eid,
                source_type="fundamentals",
                title=f"Valuation Data: {result.symbol}",
                source="Financial data providers",
                snippet=snippet,
                key_points=parts[:3],
            ))

    # ── Sentiment Summary ──
    if result.sentiment:
        sent = result.sentiment
        if sent.explanation or sent.overall_score != 0.0:
            eid = _next_id()
            evidence_items.append(EvidenceItem(
                id=eid,
                source_type="agent_output",
                title=f"Sentiment Analysis: {result.symbol}",
                source="Sentiment Agent",
                snippet=f"Score: {sent.overall_score} ({sent.label.value}). {sent.explanation[:300]}",
                key_points=_extract_key_points(sent.explanation),
                sentiment_score=sent.overall_score,
            ))

    # ── Risk Summary ──
    if result.risk:
        risk = result.risk
        if risk.summary:
            eid = _next_id()
            evidence_items.append(EvidenceItem(
                id=eid,
                source_type="agent_output",
                title=f"Risk Assessment: {result.symbol}",
                source="Risk Agent",
                snippet=f"Macro: {risk.macro_risk.value}, Company: {risk.company_risk.value}, Volatility: {risk.volatility_risk.value}. {risk.summary[:300]}",
                key_points=_extract_key_points(risk.summary),
            ))

    # ── CIO Decision ──
    if result.cio_decision:
        cio = result.cio_decision
        eid = _next_id()
        evidence_items.append(EvidenceItem(
            id=eid,
            source_type="agent_output",
            title=f"CIO Decision: {cio.action.value} on {result.symbol}",
            source="CIO Agent",
            snippet=f"Action: {cio.action.value}, Confidence: {cio.confidence}, Risk: {cio.risk_level.value}. {cio.reasoning[:300]}",
            key_points=cio.key_points[:3] if cio.key_points else _extract_key_points(cio.reasoning),
        ))

    return evidence_items