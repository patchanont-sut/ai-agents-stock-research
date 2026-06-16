"""Tests for evidence library builder."""
import sys
sys.path.insert(0, "backend")

from core.models import (
    AnalysisResult,
    ResearchOutput,
    Article,
    CIOOutput,
    CIOAction,
    SentimentOutput,
    SentimentLabel,
    BullOutput,
    BearOutput,
    RiskOutput,
    RiskLevel,
    ValuationOutput,
    EvidenceItem,
)
from core.evidence import build_evidence_library


def make_article(title: str, url: str = "", source: str = "Finnhub", snippet: str = "") -> Article:
    return Article(title=title, url=url, source=source, snippet=snippet)


def test_empty_result_produces_empty_library():
    result = AnalysisResult(symbol="TEST")
    lib = build_evidence_library(result)
    assert lib == []


def test_news_articles_become_evidence():
    result = AnalysisResult(
        symbol="AAPL",
        research=ResearchOutput(
            news_articles=[
                make_article("Apple releases new iPhone", "http://example.com/1", "Finnhub", "iPhone 16 announced"),
                make_article("Apple earnings beat", "http://example.com/2", "Google News", "Record revenue"),
            ]
        ),
    )
    lib = build_evidence_library(result)
    assert len(lib) >= 2
    news_items = [item for item in lib if item.source_type == "news"]
    assert len(news_items) == 2
    assert news_items[0].id == "E1"
    assert news_items[1].id == "E2"


def test_reddit_posts_become_evidence():
    result = AnalysisResult(
        symbol="AAPL",
        research=ResearchOutput(
            reddit_posts=[
                make_article("AAPL discussion", "http://reddit.com/1", "Reddit", "Bullish on AAPL"),
            ]
        ),
    )
    lib = build_evidence_library(result)
    reddit_items = [item for item in lib if item.source_type == "reddit"]
    assert len(reddit_items) == 1
    assert reddit_items[0].id == "E1"


def test_evidence_ids_are_deterministic():
    result = AnalysisResult(
        symbol="AAPL",
        research=ResearchOutput(
            news_articles=[
                make_article("Title A", "http://a.com", "Finnhub"),
                make_article("Title B", "http://b.com", "Google News"),
            ],
            reddit_posts=[
                make_article("Title C", "http://c.com", "Reddit"),
            ],
        ),
        cio_decision=CIOOutput(
            action=CIOAction.BUY,
            reasoning="Strong buy",
            key_points=["Point 1", "Point 2"],
        ),
    )
    lib1 = build_evidence_library(result)
    lib2 = build_evidence_library(result)
    assert [item.id for item in lib1] == [item.id for item in lib2]
    assert [item.source_type for item in lib1] == [item.source_type for item in lib2]


def test_duplicate_urls_are_deduplicated():
    result = AnalysisResult(
        symbol="AAPL",
        research=ResearchOutput(
            news_articles=[
                make_article("Apple news", "http://example.com/1", "Finnhub"),
                make_article("Same Apple news", "http://example.com/1", "Google News"),
            ],
        ),
    )
    lib = build_evidence_library(result)
    news_items = [item for item in lib if item.source_type == "news"]
    assert len(news_items) == 1


def test_duplicate_titles_are_deduplicated():
    result = AnalysisResult(
        symbol="AAPL",
        research=ResearchOutput(
            news_articles=[
                make_article("Apple Stock Soars", "http://a.com", "Finnhub"),
                make_article("Apple Stock Soars", "http://b.com", "Google News"),
            ],
        ),
    )
    lib = build_evidence_library(result)
    news_items = [item for item in lib if item.source_type == "news"]
    assert len(news_items) == 1


def test_empty_sources_are_ignored():
    result = AnalysisResult(
        symbol="AAPL",
        research=ResearchOutput(
            news_articles=[
                make_article("Good article", "http://example.com/1", "Finnhub"),
                make_article("Bad article", "http://example.com/2", ""),
                make_article("Unknown source", "http://example.com/3", "unknown"),
            ],
        ),
    )
    lib = build_evidence_library(result)
    news_items = [item for item in lib if item.source_type == "news"]
    assert len(news_items) == 1


def test_company_profile_becomes_evidence():
    result = AnalysisResult(
        symbol="AAPL",
        research=ResearchOutput(
            company_profile="Apple Inc. is a technology company headquartered in Cupertino, California.",
        ),
    )
    lib = build_evidence_library(result)
    profile_items = [item for item in lib if item.source_type == "company_profile"]
    assert len(profile_items) == 1


def test_short_company_profile_not_added():
    result = AnalysisResult(
        symbol="AAPL",
        research=ResearchOutput(
            company_profile="Short",
        ),
    )
    lib = build_evidence_library(result)
    profile_items = [item for item in lib if item.source_type == "company_profile"]
    assert len(profile_items) == 0


def test_valuation_becomes_evidence():
    result = AnalysisResult(
        symbol="AAPL",
        valuation=ValuationOutput(
            pe_ratio=28.5,
            market_cap="2.5T",
            verdict="Fairly valued",
        ),
    )
    lib = build_evidence_library(result)
    fund_items = [item for item in lib if item.source_type == "fundamentals"]
    assert len(fund_items) == 1
    assert "28.5" in fund_items[0].snippet


def test_cio_decision_becomes_evidence():
    result = AnalysisResult(
        symbol="AAPL",
        cio_decision=CIOOutput(
            action=CIOAction.BUY,
            reasoning="Strong buy case",
            key_points=["Great product", "Strong earnings"],
        ),
    )
    lib = build_evidence_library(result)
    cio_items = [item for item in lib if "CIO" in item.title]
    assert len(cio_items) == 1


def test_sentiment_becomes_evidence():
    result = AnalysisResult(
        symbol="AAPL",
        sentiment=SentimentOutput(
            overall_score=0.65,
            label=SentimentLabel.POSITIVE,
            explanation="Overall positive sentiment due to strong earnings.",
        ),
    )
    lib = build_evidence_library(result)
    sent_items = [item for item in lib if item.source_type == "agent_output" and "Sentiment" in item.title]
    assert len(sent_items) == 1


def test_risk_becomes_evidence():
    result = AnalysisResult(
        symbol="AAPL",
        risk=RiskOutput(
            macro_risk=RiskLevel.MEDIUM,
            company_risk=RiskLevel.LOW,
            volatility_risk=RiskLevel.MEDIUM,
            summary="Moderate risk overall.",
        ),
    )
    lib = build_evidence_library(result)
    risk_items = [item for item in lib if item.source_type == "agent_output" and "Risk" in item.title]
    assert len(risk_items) == 1