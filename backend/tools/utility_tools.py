"""MarketMind AI Dashboard - Utility Tools"""
from __future__ import annotations
import logging

from core.tool_registry import tool, tool_registry

logger = logging.getLogger(__name__)


@tool(
    name="summarize_text",
    description="Summarize a long text into a concise summary. Useful for condensing news articles or reports.",
)
async def summarize_text(text: str, max_length: int = 300) -> dict:
    """
    Simple text summarization via truncation + key sentence extraction.
    For production, this would use an LLM call. Currently falls back to truncation.
    """
    if not text:
        return {"summary": "", "original_length": 0}

    # Basic extractive summarization: first N chars + ellipsis
    if len(text) <= max_length:
        summary = text
        truncated = False
    else:
        # Try to break at sentence boundary
        truncated = text[:max_length]
        last_period = truncated.rfind(".")
        last_space = truncated.rfind(" ")
        if last_period > max_length * 0.5:
            summary = truncated[:last_period + 1]
        elif last_space > 0:
            summary = truncated[:last_space] + "..."
        else:
            summary = truncated + "..."

    return {
        "summary": summary,
        "original_length": len(text),
        "summary_length": len(summary),
    }


@tool(
    name="store_memory",
    description="Store a value in the shared analysis memory. All agents can read this later.",
)
async def store_memory(key: str, value: str, session_id: str = "default") -> dict:
    """
    Store arbitrary key-value data in the shared memory for this analysis session.
    Other agents can retrieve it via retrieve_memory.
    """
    from core.memory import _session_stores

    store = _session_stores.get(session_id)
    if not store:
        return {"error": f"No memory session found for session_id='{session_id}'"}

    store.write(key, value)
    return {"stored": True, "key": key, "session_id": session_id}


@tool(
    name="retrieve_memory",
    description="Retrieve a value previously stored in the shared analysis memory by its key.",
)
async def retrieve_memory(key: str, session_id: str = "default") -> dict:
    """
    Retrieve a value from the shared analysis memory.
    Returns the value or None if not found.
    """
    from core.memory import _session_stores

    store = _session_stores.get(session_id)
    if not store:
        return {"error": f"No memory session found for session_id='{session_id}'", "value": None}

    value = store.read(key)
    return {
        "key": key,
        "value": value,
        "found": value is not None,
    }


# Register tools
tool_registry.register(summarize_text)
tool_registry.register(store_memory)
tool_registry.register(retrieve_memory)


# ── Register all tools at import time ──
def register_all_tools():
    """Import all tool modules to register them with the tool registry."""
    import backend.tools.news_tools
    import backend.tools.market_tools
    import backend.tools.macro_tools
    import backend.tools.utility_tools
    logger.info(f"All tools registered. Total: {len(tool_registry)} tools: {tool_registry.tool_names}")