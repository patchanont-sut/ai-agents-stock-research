"""Tests for the GET /api/analysis/{id}/trace endpoint."""
import sys

sys.path.insert(0, "backend")

from datetime import datetime, timezone

from fastapi.testclient import TestClient
from core.trace import AnalysisTrace, AgentTraceEntry, ToolCallTrace
import core.orchestrator as orchestrator_module


def _seed_trace(analysis_id: str | None = None) -> tuple[str, AnalysisTrace]:
    """Seed the in-memory trace store with a valid trace."""
    aid = analysis_id or "test-trace-001"
    now = datetime.now(timezone.utc)
    trace = AnalysisTrace(
        analysis_id=aid,
        symbol="AAPL",
        started_at=now,
        agents=[
            AgentTraceEntry(
                agent_name="research",
                status="complete",
                started_at=now,
                completed_at=now,
                duration_ms=1200.0,
                short_summary="Research done.",
                tool_calls=[
                    ToolCallTrace(
                        tool_name="fetch_google_news",
                        arguments={"symbol": "AAPL", "limit": 15},
                        started_at=now,
                        completed_at=now,
                        duration_ms=200.0,
                        success=True,
                        compact_result_preview="15 items fetched",
                    ),
                ],
            ),
            AgentTraceEntry(
                agent_name="cio",
                status="complete",
                started_at=now,
                completed_at=now,
                duration_ms=800.0,
                short_summary="BUY: Strong conviction",
            ),
        ],
    )
    orchestrator_module._traces[aid] = trace
    return aid, trace


def test_trace_endpoint_returns_data():
    """GET /api/analysis/{id}/trace returns expected shape when trace exists."""
    from main import app

    client = TestClient(app)
    aid, _ = _seed_trace("test-e2e-001")

    resp = client.get(f"/api/analysis/{aid}/trace")
    assert resp.status_code == 200, f"Got {resp.status_code}: {resp.text}"
    data = resp.json()

    assert data["analysis_id"] == aid
    assert data["symbol"] == "AAPL"
    assert "agents" in data
    assert isinstance(data["agents"], list)
    assert len(data["agents"]) == 2

    research = data["agents"][0]
    assert research["agent_name"] == "research"
    assert research["status"] == "complete"
    assert "tool_calls" in research
    assert isinstance(research["tool_calls"], list)
    assert len(research["tool_calls"]) == 1
    assert research["tool_calls"][0]["tool_name"] == "fetch_google_news"


def test_trace_endpoint_404():
    """GET /api/analysis/{id}/trace returns 404 when trace does not exist."""
    from main import app

    client = TestClient(app)
    resp = client.get("/api/analysis/nonexistent-id/trace")
    assert resp.status_code == 404


def test_trace_nested_tool_calls_shape():
    """Verify the returned trace includes nested tool_calls with all expected fields."""
    from main import app

    client = TestClient(app)
    aid, _ = _seed_trace("test-shape-001")

    resp = client.get(f"/api/analysis/{aid}/trace")
    data = resp.json()

    research = data["agents"][0]
    tc = research["tool_calls"][0]
    # Note: "error" may be excluded by exclude_none=True serialization when None
    required_fields = [
        "tool_name", "arguments", "started_at", "completed_at",
        "duration_ms", "success", "compact_result_preview",
    ]
    for field in required_fields:
        assert field in tc, f"Field '{field}' missing from tool_calls[0]"
    assert tc["success"] is True
    # error is None so it's excluded by exclude_none
    assert tc.get("error") is None
    assert tc["compact_result_preview"] == "15 items fetched"
    assert tc["duration_ms"] == 200.0
