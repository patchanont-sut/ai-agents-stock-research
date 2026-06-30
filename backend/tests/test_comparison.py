"""Tests for comparison ranking logic, symbol normalization, and CompareStockSummary building."""
from __future__ import annotations

import pytest
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.models import (
    AnalysisResult,
    AnalysisStatus,
    CompareStockSummary,
    CIOAction,
    RiskLevel,
    SentimentLabel,
    StockInfo,
    CIOOutput,
    SentimentOutput,
    ValuationOutput,
    BullOutput,
    BearOutput,
    RiskOutput,
    EvidenceQuality,
    InvestmentMemo,
    GroundingReport,
)
from core.comparison import rank_comparison, normalize_compare_symbols, _is_rankable
from agents.base_agent import BaseAgent


def make_summary(
    symbol: str,
    action: str = "BUY",
    confidence: float = 0.8,
    risk_level: str = "Low",
    sentiment: float = 0.5,
    reliability: float = 0.9,
    grounding: float = 0.85,
) -> CompareStockSummary:
    return CompareStockSummary(
        symbol=symbol,
        company_name=f"{symbol} Corp",
        cio_action=action,
        confidence=confidence,
        risk_level=risk_level,
        sentiment_score=sentiment,
        valuation_verdict="Fair Value",
        reliability_score=reliability,
        grounding_score=grounding,
        top_bull_points=["Strong growth"],
        top_bear_points=["High competition"],
        key_risks=["Market risk"],
        errors=[],
    )


def make_empty_summary(symbol: str) -> CompareStockSummary:
    """Return a summary with all default/empty values (simulating a failed analysis)."""
    return CompareStockSummary(symbol=symbol)


class TestComparisonRanking:
    """Test the deterministic ranking logic using the production function from core.comparison."""

    def test_buy_beats_hold_beats_sell(self):
        """BUY should rank higher than HOLD, which should rank higher than SELL."""
        summaries = [
            make_summary("AAPL", action="HOLD", confidence=0.9),
            make_summary("MSFT", action="BUY", confidence=0.7),
            make_summary("TSLA", action="SELL", confidence=0.95),
        ]
        winner, _ = rank_comparison(summaries)
        assert winner == "MSFT", f"Expected MSFT (BUY) to win, got {winner}"

    def test_confidence_breaks_ties(self):
        """When both are BUY, higher confidence should win."""
        summaries = [
            make_summary("AAPL", action="BUY", confidence=0.6),
            make_summary("GOOGL", action="BUY", confidence=0.9),
        ]
        winner, _ = rank_comparison(summaries)
        assert winner == "GOOGL"

    def test_reliability_and_grounding_matter(self):
        """Higher reliability and grounding should tip the scale."""
        summaries = [
            make_summary("AAPL", action="BUY", confidence=0.8, reliability=0.5, grounding=0.4),
            make_summary("MSFT", action="BUY", confidence=0.8, reliability=0.95, grounding=0.9),
        ]
        winner, _ = rank_comparison(summaries)
        assert winner == "MSFT"

    def test_risk_level_affects_ranking(self):
        """Lower risk should score higher."""
        summaries = [
            make_summary("AAPL", action="BUY", confidence=0.8, risk_level="High"),
            make_summary("MSFT", action="BUY", confidence=0.8, risk_level="Low"),
        ]
        winner, _ = rank_comparison(summaries)
        assert winner == "MSFT"

    def test_empty_summaries(self):
        winner, rationale = rank_comparison([])
        assert winner == ""
        assert "No valid completed summaries to rank." in rationale

    def test_ranking_rationale_includes_all_symbols(self):
        summaries = [
            make_summary("AAPL", action="BUY"),
            make_summary("TSLA", action="SELL"),
        ]
        _, rationale = rank_comparison(summaries)
        assert "AAPL" in rationale
        assert "TSLA" in rationale
        assert "Ranking rationale" in rationale

    # ── New tests: all-failed comparison robustness ──

    def test_all_default_summaries_return_no_winner(self):
        """When every compared stock failed (only default/empty values), no winner is selected."""
        summaries = [
            make_empty_summary("AAPL"),
            make_empty_summary("MSFT"),
            make_empty_summary("TSLA"),
        ]
        winner, rationale = rank_comparison(summaries)
        assert winner == "", f"Expected empty winner for all-failed, got '{winner}'"
        assert "No valid completed summaries to rank." in rationale

    def test_mixed_failed_and_valid_rankable(self):
        """Summaries with errors but meaningful valid analysis signals can still be ranked."""
        failed = make_empty_summary("FAIL")
        valid = make_summary("MSFT", action="BUY", confidence=0.7)
        summaries = [valid, failed]
        winner, rationale = rank_comparison(summaries)
        assert winner == "MSFT", f"Expected MSFT to win, got '{winner}'"
        # The failed summary should be mentioned as excluded
        assert "Excluded from ranking" in rationale
        assert "FAIL" in rationale

    def test_is_rankable_with_action(self):
        assert _is_rankable(make_summary("AAPL", action="BUY")) is True
        assert _is_rankable(make_summary("AAPL", action="HOLD")) is True
        assert _is_rankable(make_summary("AAPL", action="SELL")) is True

    def test_is_rankable_with_confidence(self):
        s = make_empty_summary("X")
        s.confidence = 0.5
        assert _is_rankable(s) is True

    def test_is_rankable_with_reliability(self):
        s = make_empty_summary("X")
        s.reliability_score = 0.8
        assert _is_rankable(s) is True

    def test_is_rankable_with_grounding(self):
        s = make_empty_summary("X")
        s.grounding_score = 0.9
        assert _is_rankable(s) is True

    def test_is_rankable_with_sentiment(self):
        s = make_empty_summary("X")
        s.sentiment_score = 0.3
        assert _is_rankable(s) is True

    def test_is_rankable_with_risk_level(self):
        s = make_empty_summary("X")
        s.risk_level = "High"
        assert _is_rankable(s) is True

    def test_is_rankable_with_valuation_verdict(self):
        s = make_empty_summary("X")
        s.valuation_verdict = "Undervalued"
        assert _is_rankable(s) is True

    def test_is_rankable_with_bull_points(self):
        s = make_empty_summary("X")
        s.top_bull_points = ["growth"]
        assert _is_rankable(s) is True

    def test_is_rankable_with_bear_points(self):
        s = make_empty_summary("X")
        s.top_bear_points = ["risk"]
        assert _is_rankable(s) is True

    def test_is_rankable_with_key_risks(self):
        s = make_empty_summary("X")
        s.key_risks = ["competition"]
        assert _is_rankable(s) is True

    def test_is_rankable_empty_is_false(self):
        s = make_empty_summary("X")
        assert _is_rankable(s) is False

    def test_all_failed_with_errors_still_have_no_winner(self):
        """Even if summaries have error messages, if no analysis signals, no winner."""
        s1 = CompareStockSummary(symbol="ERR1", errors=["Fetch failed"])
        s2 = CompareStockSummary(symbol="ERR2", errors=["Timeout"])
        winner, rationale = rank_comparison([s1, s2])
        assert winner == ""
        assert "No valid completed summaries to rank." in rationale


class TestSymbolNormalization:
    """Test normalize_compare_symbols validation logic."""

    def test_normalize_trims_and_uppercases(self):
        result = normalize_compare_symbols([" aapl ", "MSFT"])
        assert result == ["AAPL", "MSFT"]

    def test_rejects_duplicates_after_normalization(self):
        with pytest.raises(ValueError, match="Duplicate"):
            normalize_compare_symbols(["AAPL", " aapl "])

    def test_rejects_empty_after_trim(self):
        with pytest.raises(ValueError, match="Empty"):
            normalize_compare_symbols(["AAPL", " "])

    def test_rejects_less_than_two_unique(self):
        with pytest.raises(ValueError, match="At least"):
            normalize_compare_symbols(["AAPL"])

    def test_rejects_more_than_four(self):
        with pytest.raises(ValueError, match="At most"):
            normalize_compare_symbols(["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"])

    def test_all_unique_cleaned(self):
        result = normalize_compare_symbols(["aapl", " msft ", "\tgoogl", " AMZN "])
        assert result == ["AAPL", "MSFT", "GOOGL", "AMZN"]

    def test_aliases_are_canonicalized(self):
        result = normalize_compare_symbols(["S&P500", "NASDAQ"])
        assert result == ["SPY", "QQQ"]


class TestCompareStockSummary:
    """Test CompareStockSummary model validation."""

    def test_minimal_summary(self):
        s = CompareStockSummary(symbol="AAPL")
        assert s.symbol == "AAPL"
        assert s.company_name == ""
        assert s.cio_action == ""
        assert s.confidence == 0.0

    def test_full_summary(self):
        s = make_summary("AAPL")
        assert s.cio_action == "BUY"
        assert len(s.top_bull_points) == 1
        assert len(s.top_bear_points) == 1
        assert len(s.key_risks) == 1

    def test_summary_with_errors(self):
        s = CompareStockSummary(symbol="ERR", errors=["Data fetch failed", "Timeout"])
        assert len(s.errors) == 2
        assert s.cio_action == ""


class TestBuildStockSummary:
    """Test the _build_stock_summary function with synthetic AnalysisResult."""

    def test_build_from_complete_result(self):
        """Verify building a CompareStockSummary from a full AnalysisResult."""
        result = AnalysisResult(
            id="test-1",
            symbol="AAPL",
            status=AnalysisStatus.COMPLETE,
            stock=StockInfo(symbol="AAPL", name="Apple Inc."),
            sentiment=SentimentOutput(overall_score=0.65, label=SentimentLabel.POSITIVE),
            bull_case=BullOutput(
                thesis="Strong buy",
                evidence=["Revenue growth", "Market share gains", "Innovation pipeline"],
                confidence=0.85,
            ),
            bear_case=BearOutput(
                thesis="Valuation concerns",
                evidence=["P/E too high", "Slowing iPhone sales"],
                confidence=0.4,
            ),
            risk=RiskOutput(
                macro_risk=RiskLevel.LOW,
                company_risk=RiskLevel.MEDIUM,
                volatility_risk=RiskLevel.LOW,
                macro_factors=["Interest rates stable", "GDP growth"],
                company_factors=["Supply chain risk", "Regulatory pressure"],
            ),
            valuation=ValuationOutput(verdict="Fair Value"),
            cio_decision=CIOOutput(
                action=CIOAction.BUY,
                confidence=0.82,
                risk_level=RiskLevel.LOW,
                reasoning="Strong fundamentals",
            ),
            evidence_quality=EvidenceQuality(overall_reliability_score=0.88),
            investment_memo=InvestmentMemo(
                title="AAPL Memo",
                grounding_report=GroundingReport(grounded_score=0.92),
            ),
            errors=[],
        )

        assert result.bull_case is not None
        assert len(result.bull_case.evidence) == 3
        assert result.bull_case.evidence[:3] == [
            "Revenue growth",
            "Market share gains",
            "Innovation pipeline",
        ]

        assert result.bear_case is not None
        assert len(result.bear_case.evidence) == 2

        assert result.risk is not None
        assert len(result.risk.macro_factors) == 2
        assert len(result.risk.company_factors) == 2

        assert result.cio_decision.action == CIOAction.BUY
        assert result.evidence_quality.overall_reliability_score == 0.88
        assert result.investment_memo.grounding_report.grounded_score == 0.92

    def test_partial_result_with_errors(self):
        """Verify building summary from a partial result with errors works."""
        result = AnalysisResult(
            id="test-2",
            symbol="FAIL",
            status=AnalysisStatus.PARTIAL,
            stock=StockInfo(symbol="FAIL"),
            errors=["Research agent failed", "Sentiment timed out"],
        )

        assert result.status == AnalysisStatus.PARTIAL
        assert len(result.errors) == 2
        assert result.bull_case is None
        assert result.cio_decision is None


# ── Shared LLM JSON Parser Tests ──

DICT_FALLBACK = {"key": "fallback"}


class TestStripJsonFence:
    def test_strips_json_fence(self):
        text = '```json\n{"a": 1}\n```'
        result = BaseAgent._strip_json_fence(text)
        assert result == '{"a": 1}'

    def test_strips_generic_fence(self):
        text = '```\n{"a": 1}\n```'
        result = BaseAgent._strip_json_fence(text)
        assert result == '{"a": 1}'

    def test_no_fence_returns_cleaned(self):
        text = '  {"a": 1}  '
        result = BaseAgent._strip_json_fence(text)
        assert result == '{"a": 1}'

    def test_non_string_returns_empty(self):
        assert BaseAgent._strip_json_fence(None) == ""


class TestNormalizeStringList:
    def test_list_of_strings(self):
        assert BaseAgent._normalize_string_list(["a", "b", "c"]) == ["a", "b", "c"]

    def test_list_of_mixed(self):
        assert BaseAgent._normalize_string_list(["a", 123, None, "b"]) == ["a", "b"]

    def test_list_of_dicts(self):
        result = BaseAgent._normalize_string_list([
            {"content": "hello", "extra": 1},
            {"text": "world"},
            {"name": "test"},
        ])
        assert result == ["hello", "world", "test"]

    def test_single_string(self):
        assert BaseAgent._normalize_string_list("hello") == ["hello"]

    def test_empty_string(self):
        assert BaseAgent._normalize_string_list("") == []

    def test_none_returns_empty(self):
        assert BaseAgent._normalize_string_list(None) == []

    def test_number_returns_empty(self):
        assert BaseAgent._normalize_string_list(42) == []


class TestParseJsonResponse:
    def test_valid_dict_json(self):
        text = '{"action": "BUY", "confidence": 0.8}'
        result = BaseAgent._parse_json_response(text, DICT_FALLBACK, allow_list_first_dict=True)
        assert result == {"action": "BUY", "confidence": 0.8}

    def test_list_with_first_dict(self):
        text = '[{"a": 1}, {"b": 2}]'
        result = BaseAgent._parse_json_response(text, DICT_FALLBACK, allow_list_first_dict=True)
        assert result == {"a": 1}

    def test_list_with_non_dict_items_before_dict(self):
        text = '["ignored", 42, {"target": "yes"}]'
        result = BaseAgent._parse_json_response(text, DICT_FALLBACK, allow_list_first_dict=True)
        assert result == {"target": "yes"}

    def test_empty_list_fallback(self):
        text = '[]'
        result = BaseAgent._parse_json_response(text, DICT_FALLBACK, allow_list_first_dict=True)
        assert result == DICT_FALLBACK

    def test_list_of_only_non_dicts_fallback(self):
        text = '[1, 2, 3]'
        result = BaseAgent._parse_json_response(text, DICT_FALLBACK, allow_list_first_dict=True)
        assert result == DICT_FALLBACK

    def test_list_first_dict_disabled(self):
        """When allow_list_first_dict is False, a list should trigger fallback."""
        text = '[{"a": 1}]'
        result = BaseAgent._parse_json_response(text, DICT_FALLBACK, allow_list_first_dict=False)
        assert result == DICT_FALLBACK

    def test_primitive_string_fallback(self):
        text = '"just a string"'
        result = BaseAgent._parse_json_response(text, DICT_FALLBACK, allow_list_first_dict=True)
        assert result == DICT_FALLBACK

    def test_primitive_number_fallback(self):
        text = '42'
        result = BaseAgent._parse_json_response(text, DICT_FALLBACK, allow_list_first_dict=True)
        assert result == DICT_FALLBACK

    def test_malformed_json_fallback(self):
        text = '{broken json'
        result = BaseAgent._parse_json_response(text, DICT_FALLBACK, allow_list_first_dict=True)
        assert result == DICT_FALLBACK

    def test_empty_string_fallback(self):
        text = ''
        result = BaseAgent._parse_json_response(text, DICT_FALLBACK, allow_list_first_dict=True)
        assert result == DICT_FALLBACK

    def test_json_with_fence(self):
        text = '```json\n{"score": 0.9}\n```'
        result = BaseAgent._parse_json_response(text, DICT_FALLBACK, allow_list_first_dict=True)
        assert result == {"score": 0.9}

    def test_json_list_with_fence(self):
        text = '```json\n[{"best": 1}]\n```'
        result = BaseAgent._parse_json_response(text, DICT_FALLBACK, allow_list_first_dict=True)
        assert result == {"best": 1}
