"""Tests for ValuationAgent peers normalization."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.valuation_agent import ValuationAgent


def test_peers_normalization_handles_string_list_and_invalid_values():
    agent = ValuationAgent()

    assert agent._normalize_peers("MSFT") == ["MSFT"]
    assert agent._normalize_peers(["MSFT", 123, None, "  GOOGL  ", ""]) == [
        "MSFT",
        "123",
        "GOOGL",
    ]
    assert agent._normalize_peers({"symbol": "MSFT"}) == []
