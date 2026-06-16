"""Tests for ValuationAgent JSON shape and peers normalization."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.valuation_agent import ValuationAgent


def test_parse_json_returns_dict_for_normal_object():
    agent = ValuationAgent()

    parsed = agent._coerce_parsed_json(
        agent._parse_json('{"pe_ratio": 25.5, "verdict": "Fairly valued"}')
    )

    assert parsed["pe_ratio"] == 25.5
    assert parsed["verdict"] == "Fairly valued"


def test_list_response_uses_first_dict():
    agent = ValuationAgent()

    parsed = agent._coerce_parsed_json(
        agent._parse_json('[{"verdict": "Fairly valued"}, {"verdict": "Overvalued"}]')
    )

    assert parsed["verdict"] == "Fairly valued"


def test_empty_list_response_falls_back():
    agent = ValuationAgent()

    parsed = agent._coerce_parsed_json(agent._parse_json("[]"))

    assert parsed["verdict"] == "Unknown"
    assert parsed["explanation"] == "Valuation response was not a JSON object."


def test_non_dict_json_response_falls_back():
    agent = ValuationAgent()

    string_parsed = agent._coerce_parsed_json(agent._parse_json('"hello"'))
    number_parsed = agent._coerce_parsed_json(agent._parse_json("123"))

    assert string_parsed["verdict"] == "Unknown"
    assert number_parsed["verdict"] == "Unknown"


def test_peers_normalization_handles_string_list_and_invalid_values():
    agent = ValuationAgent()

    assert agent._normalize_peers("MSFT") == ["MSFT"]
    assert agent._normalize_peers(["MSFT", 123, None, "  GOOGL  ", ""]) == [
        "MSFT",
        "123",
        "GOOGL",
    ]
    assert agent._normalize_peers({"symbol": "MSFT"}) == []
