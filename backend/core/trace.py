"""
MarketMind AI Dashboard — Agent Trace Models
Records structured per-agent and per-tool traces for observability.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ToolCallTrace(BaseModel):
    """Trace entry for a single tool invocation by an agent."""
    tool_name: str = ""
    arguments: dict = Field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: float = 0.0
    success: bool = False
    error: Optional[str] = None
    compact_result_preview: str = ""


class LLMUsageTrace(BaseModel):
    """Token usage and estimated cost for a single LLM call."""
    call_name: str = ""
    model: str = ""
    thinking_enabled: bool = False
    reasoning_effort: Optional[str] = None
    prompt_tokens: int = 0
    prompt_cache_hit_tokens: int = 0
    prompt_cache_miss_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0


class AgentTraceEntry(BaseModel):
    """Trace entry for a single agent in the pipeline."""
    agent_name: str = ""
    status: str = "pending"  # pending | running | complete | failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: float = 0.0
    tool_calls: list[ToolCallTrace] = Field(default_factory=list)
    llm_usage: list[LLMUsageTrace] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    short_summary: str = ""


class AnalysisTrace(BaseModel):
    """Full trace for a single analysis session."""
    analysis_id: str = ""
    symbol: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    agents: list[AgentTraceEntry] = Field(default_factory=list)
