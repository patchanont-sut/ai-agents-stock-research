"""Focused tests for Flash-only DeepSeek payloads and usage tracing."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.base_agent import BaseAgent
from config import settings
from core.trace import AgentTraceEntry, LLMUsageTrace


class DummyAgent(BaseAgent):
    AGENT_NAME = "dummy_agent"

    async def run(self, context: dict):
        return None


class FakeResponse:
    def __init__(self, data: dict):
        self._data = data

    def raise_for_status(self):
        return None

    def json(self):
        return self._data


class FakeClient:
    def __init__(self, data: dict):
        self.data = data
        self.payloads: list[dict] = []

    async def post(self, _url: str, headers: dict, json: dict, timeout: float):
        self.payloads.append(json)
        return FakeResponse(self.data)


def _agent_with_client(data: dict):
    client = FakeClient(data)
    agent = DummyAgent(client=client)
    return agent, client


@pytest.fixture(autouse=True)
def _deepseek_settings(monkeypatch):
    monkeypatch.setattr(settings, "DEEPSEEK_MODEL", "deepseek-v4-flash")
    monkeypatch.setattr(settings, "DEEPSEEK_DEFAULT_THINKING", "disabled")
    monkeypatch.setattr(settings, "DEEPSEEK_REASONING_EFFORT", "high")
    monkeypatch.setattr(settings, "DEEPSEEK_ENABLE_JSON_MODE", True)
    monkeypatch.setattr(settings, "DEEPSEEK_ENABLE_USAGE_TRACE", True)


@pytest.mark.asyncio
async def test_no_think_payload_has_top_level_thinking_disabled():
    agent, client = _agent_with_client(
        {"choices": [{"message": {"content": "ok"}}], "usage": {}}
    )

    await agent._call_llm_simple(
        "hello",
        thinking_enabled=False,
        temperature=0.25,
    )

    payload = client.payloads[0]
    assert payload["model"] == "deepseek-v4-flash"
    assert payload["thinking"] == {"type": "disabled"}
    assert payload["temperature"] == 0.25
    assert "reasoning_effort" not in payload
    assert "extra_body" not in payload


@pytest.mark.asyncio
async def test_think_payload_has_reasoning_effort_and_omits_temperature():
    agent, client = _agent_with_client(
        {"choices": [{"message": {"content": "ok"}}], "usage": {}}
    )

    await agent._call_llm_simple(
        "hello",
        thinking_enabled=True,
        reasoning_effort="high",
        temperature=0.1,
    )

    payload = client.payloads[0]
    assert payload["thinking"] == {"type": "enabled"}
    assert payload["reasoning_effort"] == "high"
    assert "temperature" not in payload
    assert "extra_body" not in payload


@pytest.mark.asyncio
async def test_json_mode_adds_response_format():
    agent, client = _agent_with_client(
        {"choices": [{"message": {"content": '{"answer": true}'}}], "usage": {}}
    )

    parsed = await agent._call_json_llm(
        "json",
        context="",
        fallback={},
        thinking_enabled=False,
    )

    assert parsed == {"answer": True}
    assert client.payloads[0]["response_format"] == {"type": "json_object"}


@pytest.mark.asyncio
async def test_usage_trace_full_cache_fields_calculates_flash_cost():
    agent, _client = _agent_with_client(
        {
            "choices": [{"message": {"content": "ok"}}],
            "usage": {
                "prompt_tokens": 1000,
                "prompt_cache_hit_tokens": 250,
                "prompt_cache_miss_tokens": 750,
                "completion_tokens": 500,
                "total_tokens": 1500,
                "completion_tokens_details": {"reasoning_tokens": 125},
            },
        }
    )
    trace_agent = AgentTraceEntry(agent_name="dummy_agent")

    await agent._call_llm_simple(
        "hello",
        thinking_enabled=True,
        trace_agent=trace_agent,
        llm_call_name="test_call",
    )

    usage = trace_agent.llm_usage[0]
    expected_cost = (250 / 1_000_000 * 0.0028) + (750 / 1_000_000 * 0.14) + (
        500 / 1_000_000 * 0.28
    )
    assert usage.call_name == "test_call"
    assert usage.model == "deepseek-v4-flash"
    assert usage.thinking_enabled is True
    assert usage.reasoning_effort == "high"
    assert usage.prompt_cache_hit_tokens == 250
    assert usage.prompt_cache_miss_tokens == 750
    assert usage.reasoning_tokens == 125
    assert usage.estimated_cost_usd == pytest.approx(expected_cost)


@pytest.mark.asyncio
async def test_usage_trace_missing_cache_fields_treats_prompt_as_cache_miss():
    agent, _client = _agent_with_client(
        {
            "choices": [{"message": {"content": "ok"}}],
            "usage": {
                "prompt_tokens": 1000,
                "completion_tokens": 250,
                "total_tokens": 1250,
            },
        }
    )
    trace_agent = AgentTraceEntry(agent_name="dummy_agent")

    await agent._call_llm_simple(
        "hello",
        thinking_enabled=False,
        trace_agent=trace_agent,
        llm_call_name="cache_fallback",
    )

    usage = trace_agent.llm_usage[0]
    expected_cost = (1000 / 1_000_000 * 0.14) + (250 / 1_000_000 * 0.28)
    assert usage.prompt_cache_hit_tokens == 0
    assert usage.prompt_cache_miss_tokens == 1000
    assert usage.estimated_cost_usd == pytest.approx(expected_cost)


@pytest.mark.asyncio
async def test_missing_usage_does_not_crash_or_append_trace():
    agent, _client = _agent_with_client({"choices": [{"message": {"content": "ok"}}]})
    trace_agent = AgentTraceEntry(agent_name="dummy_agent")

    await agent._call_llm_simple(
        "hello",
        trace_agent=trace_agent,
        llm_call_name="missing_usage",
    )

    assert trace_agent.llm_usage == []


def test_trace_model_serialization_is_backward_compatible():
    entry = AgentTraceEntry(agent_name="dummy_agent")
    assert entry.llm_usage == []

    entry.llm_usage.append(
        LLMUsageTrace(
            call_name="call",
            model="deepseek-v4-flash",
            thinking_enabled=False,
            reasoning_effort=None,
            prompt_tokens=10,
            prompt_cache_hit_tokens=0,
            prompt_cache_miss_tokens=10,
            completion_tokens=5,
            reasoning_tokens=0,
            total_tokens=15,
            estimated_cost_usd=0.0000028,
        )
    )

    dumped = entry.model_dump()
    assert dumped["llm_usage"][0]["model"] == "deepseek-v4-flash"


def test_agent_source_routing_is_flash_think_or_no_think_only():
    root = Path(__file__).resolve().parents[1]

    no_think_files = [
        "agents/research_agent.py",
        "agents/sentiment_agent.py",
        "agents/valuation_agent.py",
        "agents/risk_agent.py",
        "agents/bull_agent.py",
        "agents/bear_agent.py",
        "agents/memo_agent.py",
    ]
    for relative_path in no_think_files:
        text = (root / relative_path).read_text(encoding="utf-8")
        assert "thinking_enabled=False" in text

    for relative_path in ["agents/debate_agent.py", "agents/cio_agent.py"]:
        text = (root / relative_path).read_text(encoding="utf-8")
        assert "thinking_enabled=True" in text
        assert 'reasoning_effort="high"' in text

    translation_text = (root / "core/translation_service.py").read_text(encoding="utf-8")
    assert '"thinking": {"type": "disabled"}' in translation_text


def test_python_code_does_not_introduce_forbidden_model_aliases_or_sdk_body():
    root = Path(__file__).resolve().parents[1]
    forbidden_terms = [
        "deepseek-v4-" + "pro",
        "deepseek-" + "chat",
        "deepseek-" + "reasoner",
        "DEEPSEEK_MODEL_" + "PRO",
        "extra" + "_body",
    ]

    for path in root.rglob("*.py"):
        if "tests" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for term in forbidden_terms:
            assert term not in text, f"{term} found in {path.relative_to(root)}"
