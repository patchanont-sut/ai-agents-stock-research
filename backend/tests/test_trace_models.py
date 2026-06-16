"""Tests for trace model serialization and deserialization."""
import json
import sys
from datetime import datetime, timezone

sys.path.insert(0, "backend")

from core.trace import AnalysisTrace, AgentTraceEntry, ToolCallTrace
from core.tool_registry import ToolRegistry


def test_tool_call_trace_defaults():
    tc = ToolCallTrace()
    assert tc.tool_name == ""
    assert tc.arguments == {}
    assert tc.duration_ms == 0.0
    assert tc.success is False
    assert tc.error is None


def test_agent_trace_entry_defaults():
    entry = AgentTraceEntry()
    assert entry.agent_name == ""
    assert entry.status == "pending"
    assert entry.tool_calls == []
    assert entry.errors == []
    assert entry.short_summary == ""


def test_analysis_trace_defaults():
    trace = AnalysisTrace()
    assert trace.analysis_id == ""
    assert trace.agents == []


def test_tool_call_trace_serialization():
    now = datetime(2026, 6, 14, 10, 0, 0, tzinfo=timezone.utc)
    tc = ToolCallTrace(
        tool_name="search_news",
        arguments={"query": "AAPL stock", "limit": 5},
        started_at=now,
        completed_at=now,
        duration_ms=150.0,
        success=True,
        compact_result_preview="Found 5 articles",
    )
    data = tc.model_dump()
    assert data["tool_name"] == "search_news"
    assert data["arguments"]["query"] == "AAPL stock"
    assert data["success"] is True
    assert data["compact_result_preview"] == "Found 5 articles"


def test_agent_trace_entry_serialization():
    now = datetime(2026, 6, 14, 10, 0, 0, tzinfo=timezone.utc)
    entry = AgentTraceEntry(
        agent_name="research",
        status="complete",
        started_at=now,
        completed_at=now,
        duration_ms=1200.0,
        tool_calls=[
            ToolCallTrace(
                tool_name="fetch_news",
                arguments={"symbol": "AAPL"},
                started_at=now,
                completed_at=now,
                duration_ms=120.0,
                success=True,
            )
        ],
        short_summary="Summarized 10 news articles.",
    )
    data = entry.model_dump()
    assert data["agent_name"] == "research"
    assert data["status"] == "complete"
    assert len(data["tool_calls"]) == 1
    assert data["tool_calls"][0]["tool_name"] == "fetch_news"
    assert data["short_summary"] == "Summarized 10 news articles."


def test_analysis_trace_serialization():
    now = datetime(2026, 6, 14, 10, 0, 0, tzinfo=timezone.utc)
    trace = AnalysisTrace(
        analysis_id="abc-123",
        symbol="AAPL",
        started_at=now,
        completed_at=now,
        agents=[
            AgentTraceEntry(
                agent_name="research",
                status="complete",
                started_at=now,
                completed_at=now,
                duration_ms=1000.0,
                short_summary="Research complete.",
            ),
            AgentTraceEntry(
                agent_name="sentiment",
                status="failed",
                started_at=now,
                completed_at=now,
                duration_ms=500.0,
                errors=["API timeout"],
                short_summary="",
            ),
        ],
    )
    data = trace.model_dump()
    assert data["analysis_id"] == "abc-123"
    assert data["symbol"] == "AAPL"
    assert len(data["agents"]) == 2
    assert data["agents"][0]["status"] == "complete"
    assert data["agents"][1]["status"] == "failed"
    assert data["agents"][1]["errors"] == ["API timeout"]


def test_json_roundtrip():
    now = datetime(2026, 6, 14, 10, 0, 0, tzinfo=timezone.utc)
    trace = AnalysisTrace(
        analysis_id="test-id",
        symbol="TSLA",
        started_at=now,
        agents=[
            AgentTraceEntry(
                agent_name="cio",
                status="complete",
                started_at=now,
                completed_at=now,
                duration_ms=3000.0,
                short_summary="BUY: Strong conviction",
            )
        ],
    )
    json_str = json.dumps(trace.model_dump(), default=str)
    parsed = json.loads(json_str)
    assert parsed["analysis_id"] == "test-id"
    assert parsed["symbol"] == "TSLA"
    assert len(parsed["agents"]) == 1
    assert parsed["agents"][0]["short_summary"] == "BUY: Strong conviction"


# ── execute_tool_with_trace regression tests ──

async def _fake_success_tool(**kwargs):
    return {"data": "ok", "count": 5}


async def _fake_failure_tool(**kwargs):
    raise RuntimeError("simulated failure")


def test_execute_tool_with_trace_success():
    """execute_tool_with_trace appends a ToolCallTrace on success."""
    registry = ToolRegistry()
    # Manually register without using the decorator (simpler for tests)
    registry._tools["fake_success"] = _fake_success_tool

    trace_agent = AgentTraceEntry(agent_name="test_agent", status="running")
    assert len(trace_agent.tool_calls) == 0

    import asyncio
    result = asyncio.run(
        registry.execute_tool_with_trace(
            "fake_success",
            {"param1": "val1"},
            trace_agent=trace_agent,
        )
    )

    assert result["error"] is None
    assert result["result"] == {"data": "ok", "count": 5}
    assert len(trace_agent.tool_calls) == 1

    tc = trace_agent.tool_calls[0]
    assert tc.tool_name == "fake_success"
    assert tc.arguments == {"param1": "val1"}
    assert tc.success is True
    assert tc.error is None
    assert "data" in tc.compact_result_preview or "ok" in tc.compact_result_preview
    assert tc.duration_ms >= 0
    assert tc.started_at is not None
    assert tc.completed_at is not None


def test_execute_tool_with_trace_failure():
    """execute_tool_with_trace records failure correctly."""
    registry = ToolRegistry()
    registry._tools["fake_fail"] = _fake_failure_tool

    trace_agent = AgentTraceEntry(agent_name="test_agent", status="running")

    import asyncio
    result = asyncio.run(
        registry.execute_tool_with_trace(
            "fake_fail",
            {"x": 1},
            trace_agent=trace_agent,
        )
    )

    assert result["error"] is not None
    assert "simulated failure" in result["error"]
    assert result["result"] is None
    assert len(trace_agent.tool_calls) == 1

    tc = trace_agent.tool_calls[0]
    assert tc.tool_name == "fake_fail"
    assert tc.success is False
    assert "simulated failure" in (tc.error or "")
    assert tc.duration_ms >= 0


def test_execute_tool_with_trace_no_trace_agent():
    """execute_tool_with_trace works without a trace_agent (backward-compatible)."""
    registry = ToolRegistry()
    registry._tools["fake_success"] = _fake_success_tool

    import asyncio
    result = asyncio.run(
        registry.execute_tool_with_trace("fake_success", {}, trace_agent=None)
    )

    assert result["error"] is None
    assert result["result"] == {"data": "ok", "count": 5}
