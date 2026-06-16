"""Tests for HTML sanitization in Google News client and evidence layer."""
import sys
sys.path.insert(0, "backend")

from data.google_news_client import _clean_html_text

from core.evidence import (
    _clean_html_text as evidence_clean_html_text,
    build_evidence_library,
)
from core.models import (
    AnalysisResult,
    ResearchOutput,
    Article,
)


# ── Helpers ──

def _ent(name: str) -> str:
    """Build an HTML entity like & at runtime to avoid editor auto-conversion."""
    return chr(38) + name


# ── Google News cleaner ──

def test_clean_html_text_strips_tags():
    raw = '<a href="https://x.com">Apple stock rises</a>' + _ent("nbsp;") + '<font color="#6f6f6f">MarketBeat</font>'
    clean = _clean_html_text(raw)
    assert "<a" not in clean
    assert "<font" not in clean
    assert _ent("nbsp;") not in clean
    assert "href=" not in clean
    assert "Apple stock rises" in clean
    assert "MarketBeat" in clean


def test_clean_html_text_unescapes_entities():
    raw = "Apple " + _ent("amp;") + " Microsoft " + _ent("gt;") + " Google"
    clean = _clean_html_text(raw)
    # After unescaping, & becomes & and > becomes >
    assert _ent("amp;") not in clean
    assert _ent("gt;") not in clean
    assert "&" in clean
    assert ">" in clean
    assert clean == "Apple & Microsoft > Google"


def test_clean_html_text_collapses_whitespace():
    clean = _clean_html_text("  Apple   stock  \n  rises  ")
    assert clean == "Apple stock rises"


def test_clean_html_text_max_length():
    clean = _clean_html_text("Apple stock rises significantly today", max_length=15)
    assert len(clean) <= 15
    assert clean == "Apple stock ris"


def test_clean_html_text_empty():
    assert _clean_html_text("") == ""
    assert _clean_html_text(None) == ""  # type: ignore[arg-type]


# ── Evidence layer sanitizer ──

def test_evidence_clean_html_text_strips_tags():
    raw = '<b>Bold title</b>' + _ent("nbsp;") + '<i>italic</i>'
    clean = evidence_clean_html_text(raw)
    assert "<b>" not in clean
    assert "<i>" not in clean
    assert _ent("nbsp;") not in clean
    assert "Bold title" in clean
    assert "italic" in clean


# ── build_evidence_library strips HTML from Articles ──

def test_build_evidence_strips_html_from_snippet():
    """EvidenceItem.snippet and key_points must not contain HTML fragments."""
    result = AnalysisResult(
        symbol="AAPL",
        research=ResearchOutput(
            news_articles=[
                Article(
                    title='<a href="https://x.com">Apple beats earnings</a>',
                    url="http://example.com/1",
                    source='<font color="#6f6f6f">MarketBeat</font>',
                    snippet='Apple <b>beats</b> Q1 estimates ' + _ent("nbsp;") + ' by 20%',
                ),
            ],
        ),
    )
    lib = build_evidence_library(result)
    news_items = [item for item in lib if item.source_type == "news"]
    assert len(news_items) >= 1

    item = news_items[0]
    # Title must be clean
    assert "<a" not in item.title
    assert "href=" not in item.title
    assert ">" not in item.title
    assert "<" not in item.title
    # Source must be clean
    assert "<font" not in item.source
    # Snippet must be clean
    assert "<b>" not in item.snippet
    assert _ent("nbsp;") not in item.snippet
    # Key points must be clean
    for kp in item.key_points:
        assert "<" not in kp, f"Key point contains HTML: {kp}"
        assert ">" not in kp, f"Key point contains HTML: {kp}"
        assert _ent("nbsp;") not in kp, f"Key point contains HTML entity: {kp}"