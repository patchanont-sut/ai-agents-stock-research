"""Tests for reliability scoring."""
import sys
from datetime import datetime, timezone, timedelta

sys.path.insert(0, "backend")

from core.models import ResearchOutput, Article, EvidenceQuality
from core.reliability import compute_reliability_score


def make_article(title: str, source: str, hours_ago: int = 2) -> Article:
    """Helper: create an Article with a known published_at."""
    return Article(
        title=title,
        url=f"https://example.com/{title}",
        source=source,
        published_at=datetime.now(timezone.utc) - timedelta(hours=hours_ago),
        snippet="Test snippet",
    )


def test_reliability_no_research():
    eq = compute_reliability_score(None)
    assert eq.data_quality == "unknown"
    assert eq.overall_reliability_score == 0.0
    assert len(eq.warnings) >= 1


def test_reliability_with_data():
    research = ResearchOutput(
        news_articles=[
            make_article("News 1", "Finnhub"),
            make_article("News 2", "Google News"),
            make_article("News 3", "Finnhub"),
            make_article("Old news", "Finnhub", hours_ago=100),
        ],
        reddit_posts=[
            make_article("Reddit post", "Reddit"),
        ],
        company_profile="Apple Inc. designs and manufactures consumer electronics.",
        data_quality="good",
        price_source="Finnhub",
        fundamentals_source="Finnhub/Alpha Vantage",
        macro_source="Finnhub",
        news_count=4,
        reddit_count=1,
    )
    eq = compute_reliability_score(research)
    assert eq.evidence_item_count == 5
    assert eq.news_count == 4
    assert eq.reddit_count == 1
    assert eq.source_count >= 3
    assert 0 <= eq.source_diversity_score <= 1
    assert 0 <= eq.freshness_score <= 1
    assert 0 <= eq.completeness_score <= 1
    assert 0 <= eq.overall_reliability_score <= 1
    assert eq.data_quality == "good"


def test_reliability_zero_data():
    research = ResearchOutput(
        news_articles=[],
        reddit_posts=[],
        company_profile="",
        data_quality="poor",
        price_source="",
        fundamentals_source="",
        macro_source="",
    )
    eq = compute_reliability_score(research)
    assert eq.evidence_item_count == 0
    assert eq.source_count == 0
    assert eq.source_diversity_score == 0.0
    assert eq.completeness_score == 0.0
    assert eq.overall_reliability_score < 0.3


def test_reliability_scores_in_range():
    research = ResearchOutput(
        news_articles=[make_article("N", "Finnhub")],
        company_profile="Some company.",
        data_quality="partial",
        price_source="Finnhub",
    )
    eq = compute_reliability_score(research)
    assert 0 <= eq.source_diversity_score <= 1
    assert 0 <= eq.freshness_score <= 1
    assert 0 <= eq.completeness_score <= 1
    assert 0 <= eq.overall_reliability_score <= 1


def test_freshness_scoring():
    research_recent = ResearchOutput(
        news_articles=[
            make_article("Recent 1", "Finnhub", hours_ago=1),
            make_article("Recent 2", "Finnhub", hours_ago=5),
        ],
        company_profile="Test",
        data_quality="good",
    )
    eq_recent = compute_reliability_score(research_recent)

    research_old = ResearchOutput(
        news_articles=[
            make_article("Old 1", "Finnhub", hours_ago=100),
            make_article("Old 2", "Finnhub", hours_ago=200),
        ],
        company_profile="Test",
        data_quality="good",
    )
    eq_old = compute_reliability_score(research_old)
    assert eq_recent.freshness_score > eq_old.freshness_score


def test_evidence_quality_pydantic():
    """EvidenceQuality is a Pydantic model — test serialization."""
    eq = compute_reliability_score(None)
    d = eq.model_dump()
    assert "source_count" in d
    assert "evidence_item_count" in d
    assert "overall_reliability_score" in d
    assert "warnings" in d
    assert isinstance(d["warnings"], list)

    # Roundtrip
    eq2 = EvidenceQuality(**d)
    assert eq2.overall_reliability_score == eq.overall_reliability_score
    assert eq2.warnings == eq.warnings


def test_placeholder_sources_not_counted():
    """Placeholder values (unavailable, none, unknown, empty) are not counted as sources."""
    research = ResearchOutput(
        news_articles=[
            make_article("News 1", "Finnhub"),
            make_article("News 2", ""),          # empty — not a source
            make_article("News 3", "unknown"),    # placeholder — not a source
        ],
        reddit_posts=[
            make_article("Post 1", "none"),       # placeholder — not a source
        ],
        company_profile="A company description here.",
        data_quality="partial",
        price_source="unavailable",               # placeholder — not a source
        fundamentals_source="n/a",                # placeholder — not a source
        macro_source="null",                      # placeholder — not a source
        news_count=3,
        reddit_count=1,
    )
    eq = compute_reliability_score(research)
    # Only "Finnhub" should be counted
    assert eq.source_count == 1
    assert eq.source_diversity_score == 1 / 5  # 1 / max_expected_sources


def test_completeness_ignores_placeholders():
    """Completeness checks treat none/unknown/n/a/empty/unavailable as not available."""
    placeholders = ["", "none", "unknown", "n/a", "unavailable", "null"]
    for placeholder in placeholders:
        research = ResearchOutput(
            news_articles=[
                make_article("N1", "Finnhub"),
                make_article("N2", "Finnhub"),
                make_article("N3", "Finnhub"),
            ],
            company_profile="A company description.",
            data_quality="good",
            price_source=placeholder,
            fundamentals_source=placeholder,
            macro_source=placeholder,
            news_count=3,
        )
        eq = compute_reliability_score(research)
        # Only news_count>=3 (1 point) and company_profile (1 point) should count
        assert eq.completeness_score == 2 / 5, (
            f"placeholder={placeholder!r}: expected completeness 0.4, got {eq.completeness_score}"
        )


def test_completeness_counts_real_sources():
    """Valid source values count toward completeness."""
    research = ResearchOutput(
        news_articles=[
            make_article("N1", "Finnhub"),
            make_article("N2", "Finnhub"),
            make_article("N3", "Finnhub"),
        ],
        company_profile="A company description.",
        data_quality="good",
        price_source="Finnhub",
        fundamentals_source="Alpha Vantage",
        macro_source="Finnhub",
        news_count=3,
    )
    eq = compute_reliability_score(research)
    # All 5 checks should pass: price, fundamentals, macro, news>=3, company_profile
    assert eq.completeness_score == 5 / 5


def test_real_sources_still_counted():
    """Real source values are still counted alongside placeholders being ignored."""
    research = ResearchOutput(
        news_articles=[
            make_article("News 1", "Finnhub"),
            make_article("News 2", "Google News"),
            make_article("News 3", "  UnAvAiLaBlE  "),  # case-insensitive + whitespace — ignored
        ],
        reddit_posts=[
            make_article("Post 1", "Reddit"),
        ],
        company_profile="A company description.",
        data_quality="good",
        price_source="Finnhub",                          # duplicate — already counted
        fundamentals_source="Alpha Vantage",             # new real source
        macro_source="Finnhub",                          # duplicate
        news_count=3,
        reddit_count=1,
    )
    eq = compute_reliability_score(research)
    # Finnhub, Google News, Reddit, Alpha Vantage = 4 real sources
    assert eq.source_count == 4
    assert eq.source_diversity_score == 4 / 5
