"""Tests for memo and evidence Pydantic models."""
import sys
sys.path.insert(0, "backend")

from core.models import (
    AnalysisResult,
    InvestmentMemo,
    MemoSection,
    CitationRef,
    EvidenceItem,
    GroundingReport,
    GroundingIssue,
)


def test_investment_memo_serialization():
    memo = InvestmentMemo(
        title="Test Memo",
        executive_summary="Summary text",
        recommendation="BUY",
        sections=[
            MemoSection(
                heading="Rationale",
                content="Test content [E1]",
                citations=[CitationRef(evidence_id="E1", quote_or_summary="Test citation")],
            ),
        ],
        key_citations=[CitationRef(evidence_id="E1", quote_or_summary="Key")],
    )
    data = memo.model_dump()
    assert data["title"] == "Test Memo"
    assert data["recommendation"] == "BUY"
    assert len(data["sections"]) == 1
    assert data["sections"][0]["citations"][0]["evidence_id"] == "E1"


def test_investment_memo_deserialization():
    data = {
        "title": "Test",
        "executive_summary": "Summary",
        "recommendation": "HOLD",
        "sections": [],
        "key_citations": [],
    }
    memo = InvestmentMemo(**data)
    assert memo.title == "Test"
    assert memo.recommendation == "HOLD"


def test_analysis_result_accepts_memo_and_evidence():
    result = AnalysisResult(
        id="test-id",
        symbol="AAPL",
        evidence_library=[
            EvidenceItem(
                id="E1",
                source_type="news",
                title="Test Article",
                source="Finnhub",
                snippet="Test snippet",
            ),
        ],
        investment_memo=InvestmentMemo(
            title="Memo",
            executive_summary="Summary [E1]",
            recommendation="BUY",
        ),
    )
    data = result.model_dump()
    assert data["evidence_library"] is not None
    assert len(data["evidence_library"]) == 1
    assert data["investment_memo"]["title"] == "Memo"


def test_grounding_report_serialization():
    report = GroundingReport(
        claim_count=5,
        cited_claim_count=3,
        valid_citation_count=2,
        invalid_citation_count=1,
        grounded_score=0.6,
        issues=[
            GroundingIssue(
                claim="Test claim",
                issue_type="missing_citation",
                detail="No evidence cited",
            ),
        ],
        warnings=["Warning 1"],
    )
    data = report.model_dump()
    assert data["grounded_score"] == 0.6
    assert len(data["issues"]) == 1


def test_investment_memo_with_grounding():
    memo = InvestmentMemo(
        title="Memo",
        executive_summary="Summary",
        recommendation="BUY",
        grounding_report=GroundingReport(
            claim_count=3,
            cited_claim_count=3,
            grounded_score=0.9,
        ),
    )
    data = memo.model_dump()
    assert data["grounding_report"] is not None
    assert data["grounding_report"]["grounded_score"] == 0.9


def test_citation_ref_thai_fields():
    cit = CitationRef(
        evidence_id="E1",
        quote_or_summary="Test",
        quote_or_summary_th="ทดสอบ",
    )
    data = cit.model_dump()
    assert data["quote_or_summary_th"] == "ทดสอบ"


def test_memo_section_thai_fields():
    section = MemoSection(
        heading="Key Risks",
        heading_th="ความเสี่ยงสำคัญ",
        content="Risk content",
        content_th="เนื้อหาความเสี่ยง",
    )
    data = section.model_dump()
    assert data["heading_th"] == "ความเสี่ยงสำคัญ"
    assert data["content_th"] == "เนื้อหาความเสี่ยง"


def test_investment_memo_thai_fields():
    memo = InvestmentMemo(
        title="Test Memo",
        title_th="บันทึกทดสอบ",
        executive_summary="Summary",
        executive_summary_th="บทสรุป",
        recommendation="BUY",
        recommendation_th="ซื้อ",
        sections=[
            MemoSection(
                heading="Rationale",
                heading_th="เหตุผล",
                content="Content [E1]",
                content_th="เนื้อหา [E1]",
                citations=[CitationRef(
                    evidence_id="E1",
                    quote_or_summary="Test citation",
                    quote_or_summary_th="การอ้างอิงทดสอบ",
                )],
            ),
        ],
        key_citations=[CitationRef(
            evidence_id="E1",
            quote_or_summary="Key",
            quote_or_summary_th="สำคัญ",
        )],
    )
    data = memo.model_dump()
    assert data["title_th"] == "บันทึกทดสอบ"
    assert data["executive_summary_th"] == "บทสรุป"
    assert data["recommendation_th"] == "ซื้อ"
    assert data["sections"][0]["heading_th"] == "เหตุผล"
    assert data["sections"][0]["content_th"] == "เนื้อหา [E1]"
    assert data["sections"][0]["citations"][0]["quote_or_summary_th"] == "การอ้างอิงทดสอบ"
    assert data["key_citations"][0]["quote_or_summary_th"] == "สำคัญ"


def test_analysis_result_accepts_memo_thai_fields():
    result = AnalysisResult(
        id="test-id",
        symbol="AAPL",
        investment_memo=InvestmentMemo(
            title="Memo",
            title_th="บันทึก",
            executive_summary="Summary [E1]",
            executive_summary_th="บทสรุป [E1]",
            recommendation="BUY",
            recommendation_th="ซื้อ",
            key_citations=[CitationRef(
                evidence_id="E1",
                quote_or_summary="Test",
                quote_or_summary_th="ทดสอบ",
            )],
        ),
    )
    data = result.model_dump()
    assert data["investment_memo"]["title_th"] == "บันทึก"
    assert data["investment_memo"]["executive_summary_th"] == "บทสรุป [E1]"
    assert data["investment_memo"]["recommendation_th"] == "ซื้อ"
    assert data["investment_memo"]["key_citations"][0]["quote_or_summary_th"] == "ทดสอบ"


def test_memo_thai_fields_default_to_empty():
    """New Thai fields should default to empty string."""
    memo = InvestmentMemo(
        title="Memo",
        executive_summary="Summary",
        recommendation="BUY",
    )
    data = memo.model_dump()
    assert data["title_th"] == ""
    assert data["executive_summary_th"] == ""
    assert data["recommendation_th"] == ""

    section = MemoSection(heading="Test", content="Content")
    assert section.heading_th == ""
    assert section.content_th == ""

    cit = CitationRef(evidence_id="E1", quote_or_summary="Test")
    assert cit.quote_or_summary_th == ""
