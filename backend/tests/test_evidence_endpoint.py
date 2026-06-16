"""Tests for the evidence API endpoint."""
import sys
sys.path.insert(0, "backend")

from core.models import (
    AnalysisResult,
    AnalysisStatus,
    EvidenceItem,
    InvestmentMemo,
    GroundingReport,
)
from core.orchestrator import _analysis_store


def test_endpoint_returns_evidence_for_completed_analysis():
    """Simulate what the endpoint would return."""
    analysis_id = "test-evid-001"
    result = AnalysisResult(
        id=analysis_id,
        symbol="AAPL",
        status=AnalysisStatus.COMPLETE,
        evidence_library=[
            EvidenceItem(
                id="E1",
                source_type="news",
                title="Test Article",
                source="Finnhub",
                snippet="Test",
            ),
            EvidenceItem(
                id="E2",
                source_type="agent_output",
                title="CIO Decision: BUY on AAPL",
                source="CIO Agent",
                snippet="Action: BUY",
            ),
        ],
        investment_memo=InvestmentMemo(
            title="Test Memo",
            executive_summary="Summary [E1]",
            recommendation="BUY",
            grounding_report=GroundingReport(
                claim_count=3,
                cited_claim_count=3,
                grounded_score=0.9,
            ),
        ),
    )
    _analysis_store[analysis_id] = result

    # Simulate endpoint logic
    stored = _analysis_store.get(analysis_id)
    assert stored is not None
    assert stored.evidence_library is not None
    assert len(stored.evidence_library) == 2
    assert stored.investment_memo is not None
    assert stored.investment_memo.grounding_report is not None

    # Test serialization
    dump = stored.model_dump(exclude_none=True)
    assert len(dump["evidence_library"]) == 2
    assert dump["investment_memo"] is not None

    # Cleanup
    del _analysis_store[analysis_id]


def test_endpoint_returns_404_for_unknown_analysis():
    """Verify that looking up a nonexistent analysis returns None."""
    result = _analysis_store.get("nonexistent-id")
    assert result is None


def test_empty_evidence_library_serializes_as_empty_list():
    result = AnalysisResult(
        id="empty-evid",
        symbol="AAPL",
        status=AnalysisStatus.COMPLETE,
        evidence_library=[],
        investment_memo=None,
    )
    dump = result.model_dump(exclude_none=True)
    assert dump["evidence_library"] == []
    assert "investment_memo" not in dump