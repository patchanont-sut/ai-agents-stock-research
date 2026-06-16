"""
MarketMind AI Dashboard — Citation Grounding Checker
Deterministically checks whether memo claims are grounded in the evidence library.
No LLM calls — purely rule-based pattern matching and token overlap.
"""
from __future__ import annotations
import re
from typing import Optional

from .models import (
    EvidenceItem,
    InvestmentMemo,
    GroundingReport,
    GroundingIssue,
)

# Pattern to detect citation IDs like [E1], [E2], [E123]
_CITATION_PATTERN = re.compile(r"\[(E\d+)\]")


def extract_citation_ids(text: str) -> list[str]:
    """Extract all unique citation IDs like [E1], [E2] from text."""
    if not text:
        return []
    matches = _CITATION_PATTERN.findall(text)
    # Return unique in order of first appearance
    seen: set[str] = set()
    result: list[str] = []
    for m in matches:
        if m not in seen:
            seen.add(m)
            result.append(m)
    return result


def _tokenize(text: str) -> set[str]:
    """Simple tokenizer: lowercase, split on non-alphanumeric, filter short tokens."""
    if not text:
        return set()
    tokens = re.findall(r"[a-z0-9]{3,}", text.lower())
    return set(tokens)


def _token_overlap(text_a: str, text_b: str) -> float:
    """
    Calculate Jaccard-like token overlap between two texts.
    Returns 0.0 to 1.0.
    """
    tokens_a = _tokenize(text_a)
    tokens_b = _tokenize(text_b)
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union) if union else 0.0


def _split_claims(text: str) -> list[str]:
    """Split text into claim-like sentences."""
    if not text:
        return []
    # Split on sentence boundaries
    raw = re.split(r"[.!?]+", text)
    claims = []
    for s in raw:
        s = s.strip()
        # Only count as a "meaningful claim" if it has enough content
        if len(s) >= 20:
            claims.append(s)
    return claims


def _analyze_claims(
    text: str,
    source_label: str,
    evidence_ids: set[str],
    evidence_by_id: dict[str, EvidenceItem],
    total_claims: int,
    cited_claims: int,
    valid_citations: set[str],
    invalid_citations: set[str],
    issues: list[GroundingIssue],
) -> tuple[int, int, set[str], set[str], list[GroundingIssue]]:
    """
    Analyze claims from a text block (section content or executive summary).
    Returns updated counters.
    """
    claims = _split_claims(text)
    for claim in claims:
        total_claims += 1
        claim_citations = extract_citation_ids(claim)

        # Check if claim has any citation
        if not claim_citations:
            if len(claim) >= 30:
                issues.append(GroundingIssue(
                    claim=claim[:200],
                    issue_type="missing_citation",
                    detail=f"{source_label} claim does not cite any evidence.",
                ))
            continue

        cited_claims += 1

        # Check if any citation is unknown
        has_valid = False
        for cid in claim_citations:
            if cid not in evidence_ids:
                issues.append(GroundingIssue(
                    claim=claim[:200],
                    issue_type="unknown_evidence_id",
                    detail=f"Citation {cid} not found in evidence library.",
                ))
            else:
                has_valid = True

        # Check weak overlap for valid citations
        if has_valid:
            for cid in claim_citations:
                if cid in evidence_ids:
                    valid_citations.add(cid)
                    ev = evidence_by_id[cid]
                    ev_text = (
                        (ev.title or "")
                        + " "
                        + (ev.snippet or "")
                        + " "
                        + " ".join(ev.key_points or [])
                    )
                    overlap = _token_overlap(claim, ev_text)
                    if overlap < 0.05:
                        issues.append(GroundingIssue(
                            claim=claim[:200],
                            issue_type="weak_overlap",
                            detail=(
                                f"Citation {cid} has low token overlap ({overlap:.3f}) "
                                f"with evidence '{ev.title[:80]}'."
                            ),
                        ))
                else:
                    invalid_citations.add(cid)

    return total_claims, cited_claims, valid_citations, invalid_citations, issues


def compute_grounding_report(
    memo: InvestmentMemo,
    evidence_library: list[EvidenceItem],
) -> GroundingReport:
    """
    Compute a grounding report that checks how well the memo is grounded
    in the provided evidence library.

    Rules:
    - Detect citation patterns like [E1], [E2]
    - A citation is valid only if the evidence ID exists in evidence_library
    - Split section content and executive summary into claim sentences
    - A claim is cited if it contains at least one valid citation ID
    - Flag missing citations, unknown IDs, and weak token overlap
    """
    if memo is None:
        return GroundingReport(
            claim_count=0,
            cited_claim_count=0,
            valid_citation_count=0,
            invalid_citation_count=0,
            grounded_score=0.0,
            issues=[],
            warnings=["No memo provided for grounding check."],
        )

    evidence_ids = {item.id for item in evidence_library}
    evidence_by_id = {item.id: item for item in evidence_library}

    issues: list[GroundingIssue] = []
    warnings: list[str] = []
    total_claims = 0
    cited_claims = 0
    valid_citations: set[str] = set()
    invalid_citations: set[str] = set()

    # ── Analyze claims in each section ──
    for section in memo.sections:
        total_claims, cited_claims, valid_citations, invalid_citations, issues = _analyze_claims(
            section.content,
            "Section",
            evidence_ids,
            evidence_by_id,
            total_claims,
            cited_claims,
            valid_citations,
            invalid_citations,
            issues,
        )

    # ── Analyze claims in executive summary with same rigorous logic ──
    if memo.executive_summary:
        total_claims, cited_claims, valid_citations, invalid_citations, issues = _analyze_claims(
            memo.executive_summary,
            "Executive summary",
            evidence_ids,
            evidence_by_id,
            total_claims,
            cited_claims,
            valid_citations,
            invalid_citations,
            issues,
        )

    # ── Count everything ──
    valid_citation_count = len(valid_citations)
    invalid_citation_count = len(invalid_citations)

    # ── Compute grounded_score ──
    if total_claims == 0:
        grounded_score = 0.0
        warnings.append("No claims found in memo to evaluate.")
    elif invalid_citation_count > 0 and valid_citation_count == 0:
        grounded_score = 0.0
        warnings.append("All citations reference unknown evidence IDs.")
    else:
        total_citations = valid_citation_count + invalid_citation_count
        citation_ratio = valid_citation_count / total_citations if total_citations > 0 else 1.0

        coverage_ratio = cited_claims / total_claims if total_claims > 0 else 0.0

        issue_penalty = min(0.5, len(issues) * 0.05)

        grounded_score = (
            citation_ratio * 0.4
            + coverage_ratio * 0.6
            - issue_penalty
        )
        grounded_score = round(max(0.0, min(1.0, grounded_score)), 4)

    # ── Build warnings ──
    if invalid_citation_count > 0:
        warnings.append(
            f"{invalid_citation_count} citation(s) reference unknown evidence IDs: "
            f"{', '.join(sorted(invalid_citations))}."
        )
    missing_citation_count = sum(
        1 for i in issues if i.issue_type == "missing_citation"
    )
    if missing_citation_count > 0:
        warnings.append(
            f"{missing_citation_count} claim(s) lack evidence citations."
        )

    return GroundingReport(
        claim_count=total_claims,
        cited_claim_count=cited_claims,
        valid_citation_count=valid_citation_count,
        invalid_citation_count=invalid_citation_count,
        grounded_score=grounded_score,
        issues=issues,
        warnings=warnings,
    )