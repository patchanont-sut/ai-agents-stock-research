"""
MarketMind AI Dashboard — Evidence Quality & Reliability Scoring
Deterministic scoring — no LLM calls.  Uses existing research output
and source metadata to produce structured quality metrics.
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Optional

from .models import ResearchOutput, Article, EvidenceQuality
from .trace import AnalysisTrace


_INVALID_SOURCE_VALUES = frozenset({"", "unavailable", "none", "null", "n/a", "unknown"})


def _is_valid_source(value: str) -> bool:
    """Return False for placeholder/non-source values."""
    if not value:
        return False
    return value.strip().lower() not in _INVALID_SOURCE_VALUES


def _data_quality_numeric(quality: str) -> float:
    """Map data_quality string to a numeric 0-1 value for scoring."""
    mapping = {
        "good": 1.0,
        "partial": 0.6,
        "poor": 0.3,
        "unknown": 0.4,
    }
    return mapping.get(quality, 0.4)


def compute_reliability_score(
    research: Optional[ResearchOutput],
    trace: Optional[AnalysisTrace] = None,
) -> EvidenceQuality:
    """
    Compute evidence quality and reliability score from research output.
    Entirely deterministic — no LLM calls.
    """
    warnings: list[str] = []

    if research is None:
        return EvidenceQuality(
            data_quality="unknown",
            warnings=["No research data available — reliability cannot be assessed."],
        )

    news_articles: list[Article] = research.news_articles or []
    reddit_posts: list[Article] = research.reddit_posts or []
    news_count = len(news_articles)
    reddit_count = len(reddit_posts)
    evidence_item_count = news_count + reddit_count

    # ── Source counting ──
    def _add_source(s: str) -> None:
        if _is_valid_source(s):
            all_sources.add(s)

    all_sources: set[str] = set()
    for article in news_articles:
        _add_source(article.source or "")
    for post in reddit_posts:
        _add_source(post.source or "")
    _add_source(research.price_source or "")
    _add_source(research.fundamentals_source or "")
    _add_source(research.macro_source or "")
    source_count = len(all_sources)

    # ── Source diversity score ──
    max_expected_sources = 5
    source_diversity_score = min(1.0, source_count / max_expected_sources)

    # ── Freshness score ──
    now = datetime.now(timezone.utc)
    freshness_cutoff = now - timedelta(hours=48)
    freshness_measurable = False
    recent_count = 0
    total_dated = 0

    for article in news_articles:
        pub = article.published_at
        if pub is not None:
            total_dated += 1
            freshness_measurable = True
            if pub >= freshness_cutoff:
                recent_count += 1

    for post in reddit_posts:
        pub = post.published_at
        if pub is not None:
            total_dated += 1
            freshness_measurable = True
            if pub >= freshness_cutoff:
                recent_count += 1

    if freshness_measurable and total_dated > 0:
        freshness_score = recent_count / total_dated
    else:
        freshness_score = 0.5
        warnings.append(
            "Freshness cannot be confidently measured — "
            "article publication dates are unavailable. Using neutral estimate."
        )

    # ── Completeness score ──
    checks_passed = 0
    checks_total = 5

    if _is_valid_source(research.price_source or ""):
        checks_passed += 1
    if _is_valid_source(research.fundamentals_source or ""):
        checks_passed += 1
    if _is_valid_source(research.macro_source or ""):
        checks_passed += 1
    if news_count >= 3:
        checks_passed += 1
    if research.company_profile and len(research.company_profile.strip()) > 10:
        checks_passed += 1

    completeness_score = checks_passed / checks_total

    # ── Overall reliability ──
    dq_val = _data_quality_numeric(research.data_quality or "unknown")
    overall = (
        source_diversity_score * 0.25
        + freshness_score * 0.25
        + completeness_score * 0.25
        + dq_val * 0.25
    )
    overall = round(min(1.0, max(0.0, overall)), 4)

    # ── Additional warnings ──
    if source_diversity_score < 0.4:
        warnings.append(
            f"Low source diversity ({source_count} unique sources detected). "
            "Analysis may reflect a narrow information set."
        )
    if freshness_score < 0.4 and freshness_measurable:
        warnings.append(
            "Most articles are older than 48 hours. "
            "Freshness is low — current market conditions may not be reflected."
        )
    if completeness_score < 0.4:
        warnings.append(
            "Data completeness is low — key data sources are missing. "
            "Confidence in the analysis should be reduced."
        )

    return EvidenceQuality(
        source_count=source_count,
        evidence_item_count=evidence_item_count,
        news_count=news_count,
        reddit_count=reddit_count,
        data_quality=research.data_quality or "unknown",
        source_diversity_score=source_diversity_score,
        freshness_score=freshness_score,
        completeness_score=completeness_score,
        overall_reliability_score=overall,
        warnings=warnings,
    )