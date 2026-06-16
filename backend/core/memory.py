"""
MarketMind AI Dashboard - Shared Memory Store
Provides append-only context that agents share during an analysis session.
Every agent can read all previous agent outputs and write its own.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Optional


MAX_CONTEXT_LIST_ITEMS = 5
MAX_CONTEXT_STRING_LENGTH = 600


class MemoryStore:
    """
    Append-only key-value store for agent context sharing.
    Each analysis session gets its own MemoryStore instance.
    """

    def __init__(self, symbol: str):
        self.symbol = symbol
        self._store: dict[str, Any] = {
            "symbol": symbol,
            "pipeline_started": datetime.now().isoformat(),
        }
        self._history: list[dict] = []  # chronological log of writes

    def write(self, key: str, value: Any) -> None:
        """Store a value by key. Overwrites if key exists."""
        self._store[key] = value
        self._history.append({
            "key": key,
            "timestamp": datetime.now().isoformat(),
            "action": "write",
        })

    def read(self, key: str) -> Optional[Any]:
        """Retrieve a value by key. Returns None if not found."""
        return self._store.get(key)

    def read_all(self) -> dict[str, Any]:
        """Return all stored data."""
        return dict(self._store)

    def get_context_summary(self) -> str:
        """
        Generate a human-readable summary of all context so far.
        Useful as part of the system prompt for each agent.
        """
        lines = [f"Analysis for: {self.symbol}"]
        lines.append(f"Started: {self._store.get('pipeline_started', 'unknown')}")
        lines.append("─" * 40)

        # Order matters - show agents in pipeline order
        agent_keys = [
            "research_output", "sentiment_output", "valuation_output",
            "bull_output", "bear_output", "risk_output",
            "debate_output", "cio_output",
        ]

        key_labels = {
            "research_output": "Research Agent",
            "sentiment_output": "Sentiment Agent",
            "valuation_output": "Valuation Agent",
            "bull_output": "Bull Case Agent",
            "bear_output": "Bear Case Agent",
            "risk_output": "Risk Agent",
            "debate_output": "Debate Agent",
            "cio_output": "CIO Agent",
        }

        for key in agent_keys:
            if key in self._store:
                label = key_labels.get(key, key)
                lines.append(f"\n[{label}]:")
                value = self._store[key]
                if hasattr(value, "model_dump"):
                    import json
                    lines.append(json.dumps(value.model_dump(), indent=2, default=str))
                else:
                    lines.append(str(value))

        return "\n".join(lines)

    def get_prompt_context(self, exclude_current: Optional[str] = None) -> str:
        """
        Return minimal context for an agent's system prompt.
        exclude_current: key to exclude (the current agent's output not yet written).
        """
        lines = [f"You are analyzing stock: {self.symbol}"]
        lines.append("Previous agent findings:")

        agent_order = [
            ("research_output", "Research"),
            ("sentiment_output", "Sentiment"),
            ("valuation_output", "Valuation"),
            ("bull_output", "Bull Case"),
            ("bear_output", "Bear Case"),
            ("risk_output", "Risk"),
            ("debate_output", "Debate"),
        ]

        has_previous = False
        for key, label in agent_order:
            if key == exclude_current:
                continue
            value = self._store.get(key)
            if value is not None:
                has_previous = True
                if hasattr(value, "model_dump"):
                    data = self._compact_for_prompt(value.model_dump())
                    import json
                    lines.append(f"\n[{label}]: {json.dumps(data, indent=2, default=str)}")
                else:
                    lines.append(f"\n[{label}]: {str(value)[:MAX_CONTEXT_STRING_LENGTH]}")

        if not has_previous:
            lines.append("(No previous agent outputs yet)")

        return "\n".join(lines)

    def _compact_for_prompt(self, value: Any) -> Any:
        if isinstance(value, str):
            if len(value) > MAX_CONTEXT_STRING_LENGTH:
                return value[:MAX_CONTEXT_STRING_LENGTH] + "..."
            return value
        if isinstance(value, list):
            return [self._compact_for_prompt(item) for item in value[:MAX_CONTEXT_LIST_ITEMS]]
        if isinstance(value, dict):
            return {key: self._compact_for_prompt(item) for key, item in value.items()}
        return value

    def clear(self):
        """Reset memory (for session reuse)."""
        self._store = {"symbol": self.symbol}
        self._history = []

    def __repr__(self):
        return f"<MemoryStore({self.symbol}): {len(self._store)} keys>"


# ── Global store_/retrieve_ tool functions (will be registered as tools) ──

_session_stores: dict[str, MemoryStore] = {}


def get_or_create_memory(session_id: str, symbol: str) -> MemoryStore:
    """Get or create a MemoryStore for a session."""
    if session_id not in _session_stores:
        _session_stores[session_id] = MemoryStore(symbol)
    return _session_stores[session_id]


def cleanup_memory(session_id: str):
    """Remove a session's memory."""
    _session_stores.pop(session_id, None)
