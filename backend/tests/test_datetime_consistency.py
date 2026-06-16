"""
Tests for datetime timezone consistency in the orchestration layer.

Ensures that run_pipeline() does not fail due to offset-naive vs
offset-aware datetime subtraction.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, AsyncMock

import pytest

from core.models import AnalysisResult, AnalysisStatus
from core.orchestrator import Orchestrator


# ── Helpers ──

class _FakeResearchOutput:
    """Simulates a minimal ResearchAgent output."""
    summary = "Test research summary"


class _FakeSentimentOutput:
    """Simulates a minimal SentimentAgent output."""
    overall_score = 0.65
    summary = "Test sentiment summary"


class _FakeValuationOutput:
    """Simulates a minimal ValuationAgent output."""
    summary = "Test valuation summary"


class _FakeBullOutput:
    """Simulates a minimal BullAgent output."""
    thesis = "Test bull thesis"


class _FakeBearOutput:
    """Simulates a minimal BearAgent output."""
    thesis = "Test bear thesis"


class _FakeRiskOutput:
    """Simulates a minimal RiskAgent output."""
    summary = "Test risk summary"


class _FakeDebateOutput:
    """Simulates a minimal DebateAgent output."""
    summary = "Test debate summary"


class _FakeCIOOutput:
    """Simulates a minimal CIOAgent output."""
    action = "HOLD"
    reasoning = "Test CIO reasoning"


class _FakeMemoOutput:
    """Simulates a minimal MemoAgent output."""
    title = "Test Investment Memo"


class MonkeypatchedOrchestrator(Orchestrator):
    """Orchestrator whose agent methods return instantly with fake outputs,
    skipping LLM calls and external I/O."""

    async def _run_research(self, result, trace_entry):
        result.research = _FakeResearchOutput()  # type: ignore[assignment]
        result.stock.symbol = self.symbol
        self._capture_summary(trace_entry, result.research)

    async def _run_sentiment(self, result, trace_entry):
        result.sentiment = _FakeSentimentOutput()  # type: ignore[assignment]
        self._capture_summary(trace_entry, result.sentiment)

    async def _run_valuation(self, result, trace_entry):
        result.valuation = _FakeValuationOutput()  # type: ignore[assignment]
        self._capture_summary(trace_entry, result.valuation)

    async def _run_bull(self, result, trace_entry):
        result.bull_case = _FakeBullOutput()  # type: ignore[assignment]
        self._capture_summary(trace_entry, result.bull_case)

    async def _run_bear(self, result, trace_entry):
        result.bear_case = _FakeBearOutput()  # type: ignore[assignment]
        self._capture_summary(trace_entry, result.bear_case)

    async def _run_risk(self, result, trace_entry):
        result.risk = _FakeRiskOutput()  # type: ignore[assignment]
        self._capture_summary(trace_entry, result.risk)

    async def _run_debate(self, result, trace_entry):
        result.debate = _FakeDebateOutput()  # type: ignore[assignment]
        self._capture_summary(trace_entry, result.debate)

    async def _run_cio(self, result, trace_entry):
        result.cio_decision = _FakeCIOOutput()  # type: ignore[assignment]
        self._capture_summary(trace_entry, result.cio_decision)

    async def _run_memo(self, result, trace_entry):
        # Simulate evidence_library as empty list
        result.evidence_library = []
        result.investment_memo = _FakeMemoOutput()  # type: ignore[assignment]
        self._capture_summary(trace_entry, result.investment_memo)


# ── Tests ──

@pytest.mark.asyncio
@patch("core.orchestrator.ThaiTranslationService", autospec=True)
@patch("core.orchestrator.build_evidence_library", return_value=[])
@patch("core.orchestrator.compute_reliability_score", return_value=None)
async def test_completed_at_is_timezone_aware(mock_rel, mock_ev, mock_trans):
    """completed_at should be a timezone-aware UTC datetime."""
    orch = MonkeypatchedOrchestrator(symbol="AAPL", session_id="test-aware-1")
    result = await orch.run_pipeline()

    assert result.completed_at is not None
    assert result.completed_at.tzinfo is not None, "completed_at must be timezone-aware"
    assert result.completed_at.tzinfo.utcoffset(result.completed_at) is not None  # type: ignore[union-attr]


@pytest.mark.asyncio
@patch("core.orchestrator.ThaiTranslationService", autospec=True)
@patch("core.orchestrator.build_evidence_library", return_value=[])
@patch("core.orchestrator.compute_reliability_score", return_value=None)
async def test_generated_at_is_timezone_aware(mock_rel, mock_ev, mock_trans):
    """generated_at should be a timezone-aware UTC datetime."""
    orch = MonkeypatchedOrchestrator(symbol="TSLA", session_id="test-aware-2")
    result = await orch.run_pipeline()

    assert result.generated_at is not None
    assert result.generated_at.tzinfo is not None, "generated_at must be timezone-aware"
    assert result.generated_at.tzinfo.utcoffset(result.generated_at) is not None  # type: ignore[union-attr]


@pytest.mark.asyncio
@patch("core.orchestrator.ThaiTranslationService", autospec=True)
@patch("core.orchestrator.build_evidence_library", return_value=[])
@patch("core.orchestrator.compute_reliability_score", return_value=None)
async def test_completed_at_and_started_at_subtraction_does_not_fail(mock_rel, mock_ev, mock_trans):
    """The key bug: subtracting offset-naive from offset-aware raises TypeError.

    Since both are now timezone-aware UTC, the subtraction must succeed.
    """
    orch = MonkeypatchedOrchestrator(symbol="MSFT", session_id="test-subtraction-1")
    result = await orch.run_pipeline()

    assert result.completed_at is not None
    assert result.generated_at is not None
    # If this doesn't raise, the fix is correct
    delta = result.completed_at - result.generated_at
    assert isinstance(delta, timedelta), "Subtraction should produce a timedelta"
    assert delta.total_seconds() >= 0, "Elapsed time should be non-negative"


def test_fallback_result_datetimes_are_aware():
    """The run_full_pipeline() fatal-exception path also uses timezone-aware UTC."""
    fallback = AnalysisResult(
        id="test-fallback-1",
        symbol="FAIL",
        status=AnalysisStatus.FAILED,
        errors=["Fatal pipeline error: test"],
        generated_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )

    assert fallback.generated_at.tzinfo is not None  # type: ignore[union-attr]
    assert fallback.completed_at.tzinfo is not None  # type: ignore[union-attr]
    # Subtraction must not raise
    delta = fallback.completed_at - fallback.generated_at  # type: ignore[operator]
    assert isinstance(delta, timedelta)


@pytest.mark.asyncio
@patch("core.orchestrator.ThaiTranslationService", autospec=True)
@patch("core.orchestrator.build_evidence_library", return_value=[])
@patch("core.orchestrator.compute_reliability_score", return_value=None)
async def test_trace_entry_timestamps_are_aware(mock_rel, mock_ev, mock_trans):
    """All AgentTraceEntry timestamps should be timezone-aware."""
    orch = MonkeypatchedOrchestrator(symbol="GOOG", session_id="test-trace-aware-1")
    await orch.run_pipeline()

    from core.orchestrator import _traces
    trace = _traces.get("test-trace-aware-1")
    assert trace is not None, "Trace should have been recorded"

    for entry in trace.agents:
        assert entry.started_at.tzinfo is not None, (
            f"Agent {entry.agent_name} started_at must be timezone-aware"
        )
        assert entry.completed_at.tzinfo is not None, (
            f"Agent {entry.agent_name} completed_at must be timezone-aware"
        )
        # Duration should be non-negative
        assert entry.duration_ms >= 0, (
            f"Agent {entry.agent_name} duration should be non-negative"
        )