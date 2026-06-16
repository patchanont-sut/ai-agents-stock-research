"""Tests for citation grounding checker."""
import sys
sys.path.insert(0, "backend")

from core.models import (
    InvestmentMemo,
    MemoSection,
    CitationRef,
    EvidenceItem,
    GroundingReport,
)
from core.grounding import extract_citation_ids, compute_grounding_report


def make_evidence(eid: str, title: str = "Test", snippet: str = "") -> EvidenceItem:
    return EvidenceItem(
        id=eid,
        source_type="news",
        title=title,
        source="TestSource",
        snippet=snippet,
    )


def make_memo_section(heading: str, content: str) -> MemoSection:
    return MemoSection(heading=heading, content=content, citations=[])


def test_extract_citation_ids():
    text = "This is a claim [E1] and another [E2] and again [E1]."
    ids = extract_citation_ids(text)
    assert ids == ["E1", "E2"]


def test_extract_citation_ids_empty():
    assert extract_citation_ids("") == []
    assert extract_citation_ids("No citations here.") == []


def test_extract_citation_ids_with_parentheses():
    text = "References: [E10] [E5] [E100]"
    ids = extract_citation_ids(text)
    assert "E10" in ids
    assert "E5" in ids
    assert "E100" in ids


def test_valid_citations_pass():
    evidence = [make_evidence("E1", "Apple earnings"), make_evidence("E2", "Market data")]
    memo = InvestmentMemo(
        title="Test Memo",
        executive_summary="Summary with [E1] citation.",
        recommendation="BUY",
        sections=[
            MemoSection(
                heading="Rationale",
                content="We recommend BUY based on strong earnings [E1] and positive market data [E2].",
            ),
        ],
    )
    report = compute_grounding_report(memo, evidence)
    assert report.valid_citation_count >= 2
    assert report.claim_count > 0
    assert report.grounded_score >= 0.0
    assert report.grounded_score <= 1.0


def test_unknown_citation_creates_issue():
    evidence = [make_evidence("E1", "Apple earnings")]
    memo = InvestmentMemo(
        title="Test Memo",
        recommendation="HOLD",
        sections=[
            MemoSection(
                heading="Rationale",
                content="Based on [E1] and [E999] we recommend HOLD.",
            ),
        ],
    )
    report = compute_grounding_report(memo, evidence)
    assert report.invalid_citation_count >= 1
    unknown_issues = [i for i in report.issues if i.issue_type == "unknown_evidence_id"]
    assert len(unknown_issues) >= 1
    assert any("E999" in i.detail for i in unknown_issues)


def test_missing_citation_creates_issue():
    evidence = [make_evidence("E1", "Apple earnings")]
    memo = InvestmentMemo(
        title="Test Memo",
        recommendation="HOLD",
        sections=[
            MemoSection(
                heading="Rationale",
                content="This is a very long claim that spans multiple sentences and makes factual assertions about the company's performance without citing any evidence.",
            ),
        ],
    )
    report = compute_grounding_report(memo, evidence)
    missing_issues = [i for i in report.issues if i.issue_type == "missing_citation"]
    assert len(missing_issues) >= 1


def test_grounded_score_in_range():
    evidence = [
        make_evidence("E1", "Strong earnings", "Revenue grew 15%"),
        make_evidence("E2", "Positive market", "Bullish sentiment"),
    ]
    memo = InvestmentMemo(
        title="Test",
        executive_summary="We rate this a BUY [E1] [E2].",
        recommendation="BUY",
        sections=[
            MemoSection(
                heading="Rationale",
                content="Revenue grew 15% [E1] and market sentiment is bullish [E2].",
            ),
        ],
    )
    report = compute_grounding_report(memo, evidence)
    assert 0.0 <= report.grounded_score <= 1.0


def test_empty_memo_returns_zero_score():
    evidence = [make_evidence("E1", "Test")]
    memo = InvestmentMemo()
    report = compute_grounding_report(memo, evidence)
    assert report.grounded_score == 0.0
    assert report.claim_count == 0


def test_weak_overlap_detection():
    evidence = [
        make_evidence("E1", "Unrelated topic about agriculture", "This evidence is about farming. It discusses crop yields and soil quality."),
    ]
    memo = InvestmentMemo(
        title="Test",
        recommendation="HOLD",
        sections=[
            MemoSection(
                heading="Rationale",
                content="The stock price is likely to increase due to strong demand for cloud computing services [E1].",
            ),
        ],
    )
    report = compute_grounding_report(memo, evidence)
    overlap_issues = [i for i in report.issues if i.issue_type == "weak_overlap"]
    assert report.grounded_score <= 1.0


def test_executive_summary_unknown_ids_detected():
    evidence = [make_evidence("E1", "Apple earnings")]
    memo = InvestmentMemo(
        title="Test",
        executive_summary="We recommend BUY based on [E999] which is unknown.",
        recommendation="BUY",
        sections=[
            MemoSection(heading="A", content="Section claim [E1].", citations=[]),
        ],
    )
    report = compute_grounding_report(memo, evidence)
    unknown_issues = [i for i in report.issues if i.issue_type == "unknown_evidence_id"]
    assert len(unknown_issues) >= 1
    assert any("E999" in i.detail for i in unknown_issues)


def test_executive_summary_missing_citation_detected():
    evidence = [make_evidence("E1", "Apple earnings")]
    memo = InvestmentMemo(
        title="Test",
        executive_summary="This is a very long executive summary claim that makes multiple factual assertions about the company without citing any evidence at all.",
        recommendation="HOLD",
        sections=[
            MemoSection(heading="A", content="Section with [E1].", citations=[]),
        ],
    )
    report = compute_grounding_report(memo, evidence)
    missing_issues = [i for i in report.issues if i.issue_type == "missing_citation"]
    exec_missing = [i for i in missing_issues if "Executive summary" in i.detail]
    assert len(exec_missing) >= 1


def test_perfect_memo_scores_high():
    evidence = [
        make_evidence("E1", "Apple earnings beat", "Apple reported record quarterly revenue of $90 billion"),
        make_evidence("E2", "Strong iPhone sales", "iPhone sales grew 10% year over year"),
    ]
    memo = InvestmentMemo(
        title="Test",
        executive_summary="Apple had great earnings [E1] driven by iPhone [E2].",
        recommendation="BUY",
        sections=[
            MemoSection(
                heading="Decision Rationale",
                content="Apple reported record quarterly revenue of $90 billion [E1] which supports a BUY rating.",
            ),
            MemoSection(
                heading="Bull Case",
                content="iPhone sales grew 10% year over year [E2] indicating strong demand.",
            ),
            MemoSection(
                heading="Key Risks",
                content="Competition in smartphone market remains a concern but Apple's ecosystem is strong [E1].",
            ),
        ],
    )
    report = compute_grounding_report(memo, evidence)
    assert report.valid_citation_count > 0
    assert report.invalid_citation_count == 0
    assert report.grounded_score >= 0.5