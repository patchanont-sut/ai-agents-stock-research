"""
MarketMind AI Dashboard - Memo Agent
Generates a citation-grounded investment research memo from all agent outputs.
Cites evidence IDs from the evidence library using [E1], [E2] notation.
"""
from __future__ import annotations
import json
import logging

from .base_agent import BaseAgent
from core.models import (
    InvestmentMemo,
    MemoSection,
    CitationRef,
    EvidenceItem,
    AnalysisResult,
)

logger = logging.getLogger(__name__)


class MemoAgent(BaseAgent):
    AGENT_NAME = "memo"
    SYSTEM_PROMPT = """You are a senior investment research analyst at MarketMind AI.

Your job: Write a concise, citation-grounded investment research memo based on the
full multi-agent analysis and the structured evidence library provided below.

IMPORTANT RULES:
1. Every factual claim MUST cite evidence IDs in square brackets, like [E1], [E2].
2. ONLY cite evidence IDs that appear in the evidence library provided below.
3. NEVER invent sources, data points, or evidence IDs.
4. If evidence is weak or missing for a claim, say so explicitly — do not pretend certainty.
5. Use clear, professional language suitable for an institutional investor.
6. Each section must include at least one citation if relevant evidence exists.
7. The memo should be self-contained: a reader should understand the investment thesis
   without reading the underlying agent outputs.

Your output must be valid JSON matching the InvestmentMemo schema:
{
    "title": "Investment Research Memo: AAPL",
    "executive_summary": "A 3-5 sentence summary citing key evidence [E1]...",
    "recommendation": "BUY / HOLD / SELL with brief justification citing evidence",
    "sections": [
        {
            "heading": "Decision Rationale",
            "content": "Paragraph explaining why the recommendation makes sense [E1]...",
            "citations": [{"evidence_id": "E1", "quote_or_summary": "Summary of what E1 says"}]
        },
        {
            "heading": "Bull Case",
            "content": "Key bull arguments with citations [E2]...",
            "citations": [{"evidence_id": "E2", "quote_or_summary": "Summary of what E2 says"}]
        },
        {
            "heading": "Bear Case",
            "content": "Key bear arguments with citations [E3]...",
            "citations": [{"evidence_id": "E3", "quote_or_summary": "Summary of what E3 says"}]
        },
        {
            "heading": "Key Risks",
            "content": "Major risk factors with citations...",
            "citations": []
        },
        {
            "heading": "What Would Change the View",
            "content": "Scenarios that would flip the recommendation...",
            "citations": []
        }
    ],
    "key_citations": [
        {"evidence_id": "E1", "quote_or_summary": "The most important evidence for this memo"}
    ]
}"""

    async def run(self, context: dict) -> InvestmentMemo | None:
        memory = context.get("memory")
        symbol = context.get("symbol", "Unknown")
        analysis_result: AnalysisResult | None = context.get("analysis_result")
        evidence_library: list[EvidenceItem] = context.get("evidence_library", [])
        trace_agent = context.get("trace_agent")

        logger.info(f"[MemoAgent] Generating investment memo for {symbol}")

        if not evidence_library:
            logger.warning(f"[MemoAgent] No evidence library provided — generating fallback memo")
            return self._build_fallback_memo(symbol, analysis_result, evidence_library)

        # Build evidence context string for the LLM
        evidence_context = self._build_evidence_context(evidence_library)
        analysis_context = self._build_analysis_context(analysis_result)

        user_prompt = f"""Write an investment research memo for {symbol}.

EVIDENCE LIBRARY (cite these IDs only):
{evidence_context}

ANALYSIS SUMMARY:
{analysis_context}

INSTRUCTIONS:
1. Write a complete investment memo as JSON.
2. Every factual claim must cite evidence using [E1], [E2] format.
3. Use the exact section headings listed in the system prompt.
4. Be honest about uncertainty — if evidence is mixed, say so.
5. Include at least 3 key_citations that are most important to the thesis."""

        try:
            response = await self._call_llm_simple(
                user_prompt=user_prompt,
                context="",
                temperature=0.3,
                max_tokens=3500,
                thinking_enabled=False,
                response_format={"type": "json_object"},
                trace_agent=trace_agent,
                llm_call_name="memo_json",
            )
            memo = self._parse_memo_response(response, symbol)
            if memo:
                if trace_agent:
                    trace_agent.short_summary = (
                        f"Memo: {memo.title} ({len(memo.sections)} sections, "
                        f"{len(memo.key_citations)} key citations)"
                    )[:200]
                return memo
            else:
                raise ValueError("Failed to parse memo LLM response")
        except Exception as e:
            logger.error(f"[MemoAgent] LLM generation failed: {e}")
            return self._build_fallback_memo(symbol, analysis_result, evidence_library)

    def _build_evidence_context(self, evidence_library: list[EvidenceItem]) -> str:
        """Build a structured text summary of the evidence library for the LLM prompt."""
        lines = []
        for item in evidence_library:
            lines.append(f"[{item.id}] ({item.source_type}) {item.title}")
            lines.append(f"    Source: {item.source}")
            if item.snippet:
                lines.append(f"    Snippet: {item.snippet[:300]}")
            if item.key_points:
                for kp in item.key_points:
                    lines.append(f"    - {kp}")
            lines.append("")
        return "\n".join(lines)

    def _build_analysis_context(self, result: AnalysisResult | None) -> str:
        """Build a summary of the analysis result for the LLM."""
        if result is None:
            return "No analysis result available."

        parts = []
        parts.append(f"Symbol: {result.symbol}")

        if result.cio_decision:
            cio = result.cio_decision
            parts.append(f"CIO Decision: {cio.action.value} (confidence: {cio.confidence})")
            parts.append(f"CIO Reasoning: {cio.reasoning[:500]}")

        if result.bull_case:
            bull = result.bull_case
            parts.append(f"Bull Thesis: {bull.thesis[:300]}")
            if bull.evidence:
                parts.append(f"Bull Evidence: {'; '.join(bull.evidence[:5])}")

        if result.bear_case:
            bear = result.bear_case
            parts.append(f"Bear Thesis: {bear.thesis[:300]}")
            if bear.evidence:
                parts.append(f"Bear Evidence: {'; '.join(bear.evidence[:5])}")

        if result.risk:
            risk = result.risk
            parts.append(f"Risk: Macro={risk.macro_risk.value}, Company={risk.company_risk.value}, "
                         f"Volatility={risk.volatility_risk.value}")

        if result.sentiment:
            sent = result.sentiment
            parts.append(f"Sentiment: {sent.overall_score} ({sent.label.value})")

        if result.valuation:
            val = result.valuation
            if val.verdict:
                parts.append(f"Valuation Verdict: {val.verdict}")

        if result.debate:
            deb = result.debate
            if deb.winning_side:
                parts.append(f"Debate Winner: {deb.winning_side}")

        return "\n".join(parts)

    def _parse_memo_response(self, response: str, symbol: str) -> InvestmentMemo | None:
        """Parse the LLM JSON response into an InvestmentMemo."""
        try:
            data = BaseAgent._parse_json_response(
                response,
                fallback={},
                allow_list_first_dict=True,
            )
            if not data:
                return None

            sections = []
            for sec_data in data.get("sections", []):
                citations = []
                for cit_data in sec_data.get("citations", []):
                    citations.append(CitationRef(
                        evidence_id=cit_data.get("evidence_id", ""),
                        quote_or_summary=cit_data.get("quote_or_summary", ""),
                    ))
                sections.append(MemoSection(
                    heading=sec_data.get("heading", ""),
                    content=sec_data.get("content", ""),
                    citations=citations,
                ))

            key_citations = []
            for cit_data in data.get("key_citations", []):
                key_citations.append(CitationRef(
                    evidence_id=cit_data.get("evidence_id", ""),
                    quote_or_summary=cit_data.get("quote_or_summary", ""),
                ))

            memo = InvestmentMemo(
                title=data.get("title", f"Investment Research Memo: {symbol}"),
                executive_summary=data.get("executive_summary", ""),
                recommendation=data.get("recommendation", "HOLD"),
                sections=sections,
                key_citations=key_citations,
            )
            return memo
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error(f"[MemoAgent] Failed to parse memo JSON: {e}")
            return None

    def _build_fallback_memo(
        self,
        symbol: str,
        result: AnalysisResult | None,
        evidence_library: list[EvidenceItem],
    ) -> InvestmentMemo:
        """
        Build a deterministic fallback memo from CIO decision, bull/bear cases,
        risk, and evidence IDs. No LLM call needed.
        """
        logger.info(f"[MemoAgent] Building fallback memo for {symbol}")

        # Map evidence IDs by type for citation
        evidence_by_type: dict[str, list[str]] = {}
        for ev in evidence_library:
            evidence_by_type.setdefault(ev.source_type, []).append(ev.id)

        all_ids = [ev.id for ev in evidence_library]

        def _find_ids(*types: str) -> list[str]:
            ids = []
            for t in types:
                ids.extend(evidence_by_type.get(t, []))
            return ids if ids else all_ids[:3]

        def _cite(ids: list[str]) -> str:
            if not ids:
                return ""
            return " ".join(f"[{eid}]" for eid in ids[:3])

        cio_action = "HOLD"
        cio_reasoning = "Insufficient data to make a confident recommendation."
        if result and result.cio_decision:
            cio = result.cio_decision
            cio_action = cio.action.value
            cio_reasoning = cio.reasoning or cio_reasoning

        bull_thesis = "No bull thesis available."
        bull_ids = _find_ids("news", "agent_output")
        if result and result.bull_case:
            bull_thesis = result.bull_case.thesis or bull_thesis

        bear_thesis = "No bear thesis available."
        bear_ids = _find_ids("reddit", "agent_output")
        if result and result.bear_case:
            bear_thesis = result.bear_case.thesis or bear_thesis

        risk_summary = "Risk assessment not available."
        risk_ids = _find_ids("agent_output")
        if result and result.risk:
            risk_summary = result.risk.summary or risk_summary

        decision_ids = _find_ids("agent_output", "news", "fundamentals")

        sections = [
            MemoSection(
                heading="Decision Rationale",
                content=(
                    f"The CIO recommends {cio_action}. "
                    f"{cio_reasoning[:500]} {_cite(decision_ids)}"
                ),
                citations=[
                    CitationRef(
                        evidence_id=eid,
                        quote_or_summary="Key evidence supporting this decision.",
                    )
                    for eid in decision_ids[:3]
                ],
            ),
            MemoSection(
                heading="Bull Case",
                content=(
                    f"The bull thesis is: {bull_thesis[:500]} {_cite(bull_ids)}"
                ),
                citations=[
                    CitationRef(
                        evidence_id=eid,
                        quote_or_summary="Evidence supporting the bull case.",
                    )
                    for eid in bull_ids[:3]
                ],
            ),
            MemoSection(
                heading="Bear Case",
                content=(
                    f"The bear thesis is: {bear_thesis[:500]} {_cite(bear_ids)}"
                ),
                citations=[
                    CitationRef(
                        evidence_id=eid,
                        quote_or_summary="Evidence supporting the bear case.",
                    )
                    for eid in bear_ids[:3]
                ],
            ),
            MemoSection(
                heading="Key Risks",
                content=(
                    f"Key risks identified: {risk_summary[:500]} {_cite(risk_ids)}"
                ),
                citations=[
                    CitationRef(
                        evidence_id=eid,
                        quote_or_summary="Evidence about risk factors.",
                    )
                    for eid in risk_ids[:3]
                ],
            ),
            MemoSection(
                heading="What Would Change the View",
                content=(
                    "A significant change in fundamentals, macro conditions, "
                    "or company-specific news would alter this recommendation. "
                    f"{_cite(all_ids[:3])}"
                ),
                citations=[],
            ),
        ]

        key_citations = [
            CitationRef(
                evidence_id=eid,
                quote_or_summary=f"Key evidence {eid} from evidence library.",
            )
            for eid in all_ids[:5]
        ]

        return InvestmentMemo(
            title=f"Investment Research Memo: {symbol} (Fallback)",
            executive_summary=(
                f"The CIO recommends {cio_action} for {symbol} based on available evidence. "
                f"This is a fallback memo generated due to an issue with AI memo generation. "
                f"{_cite(all_ids[:3])}"
            ),
            recommendation=cio_action,
            sections=sections,
            key_citations=key_citations,
        )
