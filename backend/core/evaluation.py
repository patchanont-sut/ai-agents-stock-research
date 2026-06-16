"""
MarketMind AI Dashboard - AI Quality Evaluation Metrics
Deterministic evaluation functions that assess output quality
of a completed analysis without requiring LLM calls.
"""
from __future__ import annotations
import logging
from typing import Optional

from .models import (
    AnalysisResult,
    AnalysisStatus,
    EvidenceItem,
    EvaluationMetrics,
    CompareResult,
    GroundingReport,
    InvestmentMemo,
)

logger = logging.getLogger(__name__)

# ── Known required field sets for completeness checks ──

REQUIRED_RESEARCH_FIELDS = [
    "company_profile",
    "summary",
    "news_articles",
    "data_quality",
]
REQUIRED_SENTIMENT_FIELDS = ["overall_score", "label"]
REQUIRED_BULL_FIELDS = ["thesis", "evidence", "confidence"]
REQUIRED_BEAR_FIELDS = ["thesis", "evidence", "confidence"]
REQUIRED_RISK_FIELDS = ["macro_risk", "company_risk", "summary"]
REQUIRED_VALUATION_FIELDS = ["verdict"]
REQUIRED_DEBATE_FIELDS = ["winning_side", "summary", "turns"]
REQUIRED_CIO_FIELDS = ["action", "reasoning", "confidence", "risk_level"]


def _check_field_set(result_obj, required: list[str]) -> list[str]:
    """Return list of missing required fields for a given output object."""
    if result_obj is None:
        return required
    missing = []
    for field_name in required:
        value = getattr(result_obj, field_name, None)
        if value is None or (isinstance(value, (str, list)) and not value):
            missing.append(field_name)
    return missing


def _compute_citation_validity_rate(memo: Optional[InvestmentMemo]) -> float:
    """Ratio of valid citations to total citations."""
    if memo is None:
        return 0.0
    grounding: Optional[GroundingReport] = memo.grounding_report
    if grounding is None:
        return 0.0
    total = grounding.valid_citation_count + grounding.invalid_citation_count
    if total == 0:
        return 0.0
    return round(grounding.valid_citation_count / total, 4)


def _compute_source_diversity(evidence_library: Optional[list[EvidenceItem]]) -> float:
    """Measure diversity of source types in evidence."""
    if not evidence_library:
        return 0.0
    source_types = set(item.source_type for item in evidence_library)
    # Possible source types: news, reddit, company_profile, fundamentals, macro, agent_output
    max_types = 6.0
    return round(min(len(source_types) / max_types, 1.0), 4)


def _compute_memo_completeness(memo: Optional[InvestmentMemo]) -> float:
    """Score how complete the memo is (has title, summary, recommendation, sections, citations)."""
    if memo is None:
        return 0.0
    checks = [
        bool(memo.title),
        bool(memo.executive_summary),
        bool(memo.recommendation),
        bool(memo.sections and len(memo.sections) > 0),
        bool(memo.key_citations and len(memo.key_citations) > 0),
        bool(memo.grounding_report is not None),
    ]
    passed = sum(1 for c in checks if c)
    return round(passed / len(checks), 4)


def evaluate_analysis(result: AnalysisResult) -> EvaluationMetrics:
    """
    Compute structured AI quality metrics for a completed analysis.
    Pure deterministic function, no LLM calls.
    """
    missing_fields: list[str] = []

    # Collect missing required fields from each agent output
    missing_fields.extend(
        [f"research.{f}" for f in _check_field_set(result.research, REQUIRED_RESEARCH_FIELDS)]
    )
    missing_fields.extend(
        [f"sentiment.{f}" for f in _check_field_set(result.sentiment, REQUIRED_SENTIMENT_FIELDS)]
    )
    missing_fields.extend(
        [f"bull_case.{f}" for f in _check_field_set(result.bull_case, REQUIRED_BULL_FIELDS)]
    )
    missing_fields.extend(
        [f"bear_case.{f}" for f in _check_field_set(result.bear_case, REQUIRED_BEAR_FIELDS)]
    )
    missing_fields.extend(
        [f"risk.{f}" for f in _check_field_set(result.risk, REQUIRED_RISK_FIELDS)]
    )
    missing_fields.extend(
        [f"valuation.{f}" for f in _check_field_set(result.valuation, REQUIRED_VALUATION_FIELDS)]
    )
    missing_fields.extend(
        [f"debate.{f}" for f in _check_field_set(result.debate, REQUIRED_DEBATE_FIELDS)]
    )
    missing_fields.extend(
        [f"cio_decision.{f}" for f in _check_field_set(result.cio_decision, REQUIRED_CIO_FIELDS)]
    )

    # Agent completion rate: 9 agents total
    total_agents = 9
    completed_agents = sum(
        [
            result.research is not None,
            result.sentiment is not None,
            result.valuation is not None,
            result.bull_case is not None,
            result.bear_case is not None,
            result.risk is not None,
            result.debate is not None,
            result.cio_decision is not None,
            result.investment_memo is not None,
        ]
    )
    agent_completion_rate = round(completed_agents / total_agents, 4)

    # Citation validity rate from grounding report
    citation_validity_rate = _compute_citation_validity_rate(result.investment_memo)

    # Grounding score from memo
    grounding_score = 0.0
    if result.investment_memo and result.investment_memo.grounding_report:
        grounding_score = result.investment_memo.grounding_report.grounded_score

    # Evidence count
    evidence_count = len(result.evidence_library) if result.evidence_library else 0

    # Source diversity
    source_diversity_score = _compute_source_diversity(result.evidence_library)

    # Memo completeness
    memo_completeness = _compute_memo_completeness(result.investment_memo)

    # Warnings
    warnings: list[str] = []
    if result.status in (AnalysisStatus.FAILED, AnalysisStatus.PARTIAL):
        warnings.append(f"Analysis status is {result.status.value}")
    if result.errors:
        warnings.extend(result.errors[:5])  # cap at 5
    if evidence_count == 0:
        warnings.append("No evidence items found")
    if agent_completion_rate < 1.0:
        warnings.append(f"Only {completed_agents}/{total_agents} agents completed")

    # Overall quality score: weighted composite
    overall = round(
        (
            citation_validity_rate * 0.2
            + grounding_score * 0.2
            + min(evidence_count / 15.0, 1.0) * 0.15  # normalize to 15 items
            + source_diversity_score * 0.15
            + agent_completion_rate * 0.15
            + memo_completeness * 0.15
        ),
        4,
    )

    return EvaluationMetrics(
        analysis_id=result.id,
        symbol=result.symbol,
        citation_validity_rate=citation_validity_rate,
        grounding_score=grounding_score,
        evidence_count=evidence_count,
        source_diversity_score=source_diversity_score,
        agent_completion_rate=agent_completion_rate,
        memo_completeness=memo_completeness,
        missing_required_fields=missing_fields,
        warnings=warnings,
        overall_quality_score=overall,
    )


def evaluate_comparison(compare_result: CompareResult) -> list[EvaluationMetrics]:
    """
    For a comparison result, produce evaluation metrics per summary.
    This is lighter-weight since we don't have full AnalysisResult objects;
    it focuses on comparison-specific quality signals.
    """
    metrics_list: list[EvaluationMetrics] = []
    for summary in compare_result.summaries:
        missing: list[str] = []
        if not summary.cio_action:
            missing.append("cio_action")
        if not summary.risk_level:
            missing.append("risk_level")
        if not summary.valuation_verdict:
            missing.append("valuation_verdict")
        if not summary.top_bull_points:
            missing.append("top_bull_points")
        if not summary.top_bear_points:
            missing.append("top_bear_points")

        evidence_count = len(summary.top_bull_points) + len(summary.top_bear_points) + len(summary.key_risks)
        completion_checks = [
            bool(summary.cio_action),
            bool(summary.risk_level),
            bool(summary.top_bull_points),
            bool(summary.top_bear_points),
            summary.confidence > 0,
            summary.reliability_score > 0,
        ]
        agent_completion_rate = round(sum(1 for c in completion_checks if c) / len(completion_checks), 4)
        overall = round(
            (summary.reliability_score * 0.3 + summary.grounding_score * 0.3 + agent_completion_rate * 0.4),
            4,
        )

        metrics_list.append(
            EvaluationMetrics(
                analysis_id=summary.symbol,
                symbol=summary.symbol,
                citation_validity_rate=summary.grounding_score,
                grounding_score=summary.grounding_score,
                evidence_count=evidence_count,
                source_diversity_score=0.0,
                agent_completion_rate=agent_completion_rate,
                memo_completeness=0.0,
                missing_required_fields=missing,
                warnings=summary.errors[:5] if summary.errors else [],
                overall_quality_score=overall,
            )
        )
    return metrics_list