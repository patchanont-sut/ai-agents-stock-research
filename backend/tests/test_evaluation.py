"""Tests for evaluation checks using synthetic AnalysisResult dicts."""
import sys
import re

sys.path.insert(0, "backend")


def _run_checks(data: dict) -> list[dict]:
    """Run all checks manually and return results list."""
    results: list[dict] = []

    def record(name: str, passed: bool | None, detail: str = ""):
        results.append({"name": name, "passed": passed, "detail": detail})

    record("CIO decision exists", bool(data.get("cio_decision")))
    cio = data.get("cio_decision") or {}
    action = cio.get("action", "")
    record("CIO action is valid", action in ("BUY", "HOLD", "SELL") if cio else None)
    conf = cio.get("confidence")
    record("CIO confidence in [0, 1]",
           isinstance(conf, (int, float)) and 0 <= conf <= 1 if conf is not None else None)

    bull = data.get("bull_case") or {}
    record("Bull case thesis present", bool(bull.get("thesis")))
    record("Bull case evidence present", bool(bull.get("evidence")))

    bear = data.get("bear_case") or {}
    record("Bear case thesis present", bool(bear.get("thesis")))
    record("Bear case evidence present", bool(bear.get("evidence")))

    risk = data.get("risk") or {}
    record("Risk summary exists", bool(risk.get("summary")))

    research = data.get("research") or {}
    news_count = research.get("news_count", 0) or len(research.get("news_articles", []))
    has_data_issue = bool(research.get("data_issues"))
    record("Research has >=1 source or data issue", news_count >= 1 or has_data_issue)

    eq = data.get("evidence_quality")
    if eq:
        score = eq.get("overall_reliability_score")
        record("Evidence quality score in [0, 1]",
               isinstance(score, (int, float)) and 0 <= score <= 1)
    else:
        record("Evidence quality score exists", False)

    errors = data.get("errors", [])
    has_fatal = "Fatal pipeline error" in str(errors)
    record("No fatal pipeline errors", not has_fatal)

    # ── Evidence Library Checks ──
    evidence_lib = data.get("evidence_library")
    has_research_data = bool(research.get("news_articles") or research.get("reddit_posts"))
    if evidence_lib is not None:
        min_expected = 3 if has_research_data else 1
        record("Evidence library has sufficient items", len(evidence_lib) >= min_expected)
        ids = [item.get("id") for item in evidence_lib if item.get("id")]
        record("Evidence IDs are unique", len(ids) == len(set(ids)))

    # ── Investment Memo Checks ──
    if "investment_memo" in data:
        memo = data.get("investment_memo")
        if memo is not None:
            record("Investment memo exists", True)
            sections = memo.get("sections", [])
            record("Memo has at least 3 sections", len(sections) >= 3)
            all_content = memo.get("executive_summary", "")
            for sec in sections:
                all_content += " " + sec.get("content", "")
            citation_matches = re.findall(r"\[E\d+\]", all_content)
            record("Memo contains valid citation patterns", len(citation_matches) > 0)
            grounding = memo.get("grounding_report")
            if grounding is not None:
                gscore = grounding.get("grounded_score")
                record("Grounding report exists", True)
                record("Grounded score in [0, 1]",
                       isinstance(gscore, (int, float)) and 0 <= gscore <= 1)
                if evidence_lib:
                    ev_ids = {item.get("id") for item in evidence_lib}
                    cited_ids = set(re.findall(r"E\d+", all_content))
                    # Also collect from structured CitationRef objects
                    for sec in sections:
                        for cit in sec.get("citations", []):
                            eid = cit.get("evidence_id", "")
                            if eid:
                                cited_ids.add(eid)
                    for kc in memo.get("key_citations", []):
                        eid = kc.get("evidence_id", "")
                        if eid:
                            cited_ids.add(eid)
                    unknown = cited_ids - ev_ids
                    record("No unknown evidence IDs in memo citations", len(unknown) == 0)
        else:
            record("Investment memo exists", False)

    return results


def make_valid_result() -> dict:
    return {
        "symbol": "AAPL",
        "status": "complete",
        "cio_decision": {"action": "BUY", "confidence": 0.85, "reasoning": "Strong buy",
                         "reasoning_th": ""},
        "bull_case": {"thesis": "AAPL will grow", "evidence": ["Strong earnings"]},
        "bear_case": {"thesis": "AAPL may decline", "evidence": ["Market saturation"]},
        "risk": {"summary": "Moderate risk overall"},
        "research": {"news_articles": [{"title": "Test"}], "news_count": 3, "data_issues": []},
        "evidence_quality": {"overall_reliability_score": 0.75, "source_count": 4, "warnings": []},
        "errors": [],
        "language": "en",
    }


def test_all_checks_pass_for_valid_result():
    data = make_valid_result()
    results = _run_checks(data)
    failed = [r for r in results if r["passed"] is False]
    assert len(failed) == 0, f"Unexpected failures: {failed}"


def test_missing_cio_fails():
    data = make_valid_result()
    del data["cio_decision"]
    results = _run_checks(data)
    cio_exists = next(r for r in results if r["name"] == "CIO decision exists")
    assert cio_exists["passed"] is False


def test_invalid_cio_action_fails():
    data = make_valid_result()
    data["cio_decision"]["action"] = "MAYBE"
    results = _run_checks(data)
    cio_action = next(r for r in results if r["name"] == "CIO action is valid")
    assert cio_action["passed"] is False


def test_confidence_out_of_range_fails():
    data = make_valid_result()
    data["cio_decision"]["confidence"] = 1.5
    results = _run_checks(data)
    conf_check = next(r for r in results if r["name"] == "CIO confidence in [0, 1]")
    assert conf_check["passed"] is False
    data["cio_decision"]["confidence"] = -0.5
    results = _run_checks(data)
    conf_check = next(r for r in results if r["name"] == "CIO confidence in [0, 1]")
    assert conf_check["passed"] is False


def test_missing_bull_bear_fails():
    data = make_valid_result()
    del data["bull_case"]
    del data["bear_case"]
    results = _run_checks(data)
    bull_thesis = next(r for r in results if r["name"] == "Bull case thesis present")
    bear_thesis = next(r for r in results if r["name"] == "Bear case thesis present")
    assert bull_thesis["passed"] is False
    assert bear_thesis["passed"] is False


def test_missing_evidence_quality_fails():
    data = make_valid_result()
    del data["evidence_quality"]
    results = _run_checks(data)
    eq_exists = next(r for r in results if r["name"] == "Evidence quality score exists")
    assert eq_exists["passed"] is False


def test_fatal_error_fails():
    data = make_valid_result()
    data["errors"] = ["Fatal pipeline error: all agents failed"]
    results = _run_checks(data)
    no_fatal = next(r for r in results if r["name"] == "No fatal pipeline errors")
    assert no_fatal["passed"] is False


def test_evidence_fewer_than_3_fails_when_research_exists():
    data = make_valid_result()
    data["evidence_library"] = [
        {"id": "E1", "source_type": "news", "title": "T1", "source": "S", "snippet": ""},
        {"id": "E2", "source_type": "agent_output", "title": "T2", "source": "S", "snippet": ""},
    ]
    results = _run_checks(data)
    check = next(r for r in results if r["name"] == "Evidence library has sufficient items")
    assert check["passed"] is False


def test_unknown_ids_in_section_citations_detected():
    data = make_valid_result()
    data["evidence_library"] = [
        {"id": "E1", "source_type": "news", "title": "T", "source": "S", "snippet": ""},
        {"id": "E2", "source_type": "news", "title": "T", "source": "S", "snippet": ""},
        {"id": "E3", "source_type": "news", "title": "T", "source": "S", "snippet": ""},
    ]
    data["investment_memo"] = {
        "title": "Memo",
        "executive_summary": "Summary [E1].",
        "recommendation": "BUY",
        "sections": [
            {"heading": "A", "content": "Claim with [E1] which is valid.", "citations": [
                {"evidence_id": "E999", "quote_or_summary": "Bad citation"}
            ]},
            {"heading": "B", "content": "Another claim.", "citations": []},
            {"heading": "C", "content": "Third claim.", "citations": []},
        ],
        "key_citations": [],
        "grounding_report": {"grounded_score": 0.5},
    }
    results = _run_checks(data)
    unknown_check = next(r for r in results if r["name"] == "No unknown evidence IDs in memo citations")
    assert unknown_check["passed"] is False


def test_unknown_ids_in_key_citations_detected():
    data = make_valid_result()
    data["evidence_library"] = [
        {"id": "E1", "source_type": "news", "title": "T", "source": "S", "snippet": ""},
        {"id": "E2", "source_type": "news", "title": "T", "source": "S", "snippet": ""},
        {"id": "E3", "source_type": "news", "title": "T", "source": "S", "snippet": ""},
    ]
    data["investment_memo"] = {
        "title": "Memo",
        "executive_summary": "Summary [E1].",
        "recommendation": "BUY",
        "sections": [
            {"heading": "A", "content": "Claim [E1].", "citations": []},
            {"heading": "B", "content": "Claim.", "citations": []},
            {"heading": "C", "content": "Claim.", "citations": []},
        ],
        "key_citations": [
            {"evidence_id": "E888", "quote_or_summary": "Unknown evidence"},
        ],
        "grounding_report": {"grounded_score": 0.5},
    }
    results = _run_checks(data)
    unknown_check = next(r for r in results if r["name"] == "No unknown evidence IDs in memo citations")
    assert unknown_check["passed"] is False


def test_synthetic_with_memo_and_evidence():
    data = make_valid_result()
    data["evidence_library"] = [
        {"id": "E1", "source_type": "news", "title": "Test Article", "source": "Finnhub", "snippet": "Test"},
        {"id": "E2", "source_type": "agent_output", "title": "CIO Decision", "source": "CIO", "snippet": "BUY"},
        {"id": "E3", "source_type": "news", "title": "Another Article", "source": "Google", "snippet": "News"},
    ]
    data["investment_memo"] = {
        "title": "Test Memo",
        "executive_summary": "We recommend BUY [E1] based on analysis [E2].",
        "recommendation": "BUY",
        "sections": [
            {"heading": "Rationale", "content": "Based on evidence [E1] we are bullish.", "citations": []},
            {"heading": "Bull Case", "content": "Strong fundamentals [E2] support growth.", "citations": []},
            {"heading": "Bear Case", "content": "Risks exist [E3] but manageable.", "citations": []},
            {"heading": "Key Risks", "content": "Market risk remains [E1].", "citations": []},
        ],
        "key_citations": [],
        "grounding_report": {
            "claim_count": 5, "cited_claim_count": 4, "valid_citation_count": 3,
            "invalid_citation_count": 0, "grounded_score": 0.85, "issues": [], "warnings": [],
        },
    }
    results = _run_checks(data)
    memo_exists = next(r for r in results if r["name"] == "Investment memo exists")
    assert memo_exists["passed"] is True
    grounding_exists = next(r for r in results if r["name"] == "Grounding report exists")
    assert grounding_exists["passed"] is True


def test_synthetic_with_bad_citation():
    data = make_valid_result()
    data["evidence_library"] = [
        {"id": "E1", "source_type": "news", "title": "Test", "source": "Finnhub", "snippet": "T"},
        {"id": "E2", "source_type": "news", "title": "T", "source": "S", "snippet": ""},
        {"id": "E3", "source_type": "news", "title": "T", "source": "S", "snippet": ""},
    ]
    data["investment_memo"] = {
        "title": "Bad Memo",
        "executive_summary": "Summary [E999].",
        "recommendation": "HOLD",
        "sections": [
            {"heading": "X", "content": "Claim with bad citation [E999].", "citations": []},
            {"heading": "Y", "content": "Another claim.", "citations": []},
            {"heading": "Z", "content": "Third claim.", "citations": []},
        ],
        "key_citations": [],
        "grounding_report": {"grounded_score": 0.1},
    }
    results = _run_checks(data)
    unknown_check = next(r for r in results if r["name"] == "No unknown evidence IDs in memo citations")
    assert unknown_check["passed"] is False


def test_news_count_zero_without_data_issue_fails():
    data = make_valid_result()
    data["research"]["news_articles"] = []
    data["research"]["news_count"] = 0
    data["research"]["data_issues"] = []
    results = _run_checks(data)
    source_check = next(r for r in results if r["name"] == "Research has >=1 source or data issue")
    assert source_check["passed"] is False
    data["research"]["data_issues"] = ["No news available"]
    results = _run_checks(data)
    source_check = next(r for r in results if r["name"] == "Research has >=1 source or data issue")
    assert source_check["passed"] is True


def test_evidence_quality_score_range_edge_cases():
    data = make_valid_result()
    data["evidence_quality"]["overall_reliability_score"] = 0.0
    results = _run_checks(data)
    eq_check = next(r for r in results if r["name"] == "Evidence quality score in [0, 1]")
    assert eq_check["passed"] is True
    data["evidence_quality"]["overall_reliability_score"] = 1.0
    results = _run_checks(data)
    eq_check = next(r for r in results if r["name"] == "Evidence quality score in [0, 1]")
    assert eq_check["passed"] is True
    data["evidence_quality"]["overall_reliability_score"] = 1.01
    results = _run_checks(data)
    eq_check = next(r for r in results if r["name"] == "Evidence quality score in [0, 1]")
    assert eq_check["passed"] is False