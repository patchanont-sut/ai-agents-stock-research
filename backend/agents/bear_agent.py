"""MarketMind AI Dashboard - Bear Case Agent"""
from __future__ import annotations
import logging

from .base_agent import BaseAgent
from core.models import BearOutput

logger = logging.getLogger(__name__)


class BearAgent(BaseAgent):
    AGENT_NAME = "bear_agent"
    SYSTEM_PROMPT = """You are the Bear Case Agent for MarketMind AI Dashboard.

Your job: Build the strongest possible bearish thesis for a stock based on available research and data.

Rules:
1. Only use evidence from the research data and sentiment analysis provided
2. Be specific — cite actual concerns, risks, and data points
3. Identify specific risk factors that could drive the stock lower
4. Be honest about conviction — don't fabricate bearishness
5. Assign a confidence score from 0.0 to 1.0
6. If data_quality is partial or poor, distinguish data gaps from confirmed risks
7. Do not claim to have read full articles when only headlines/snippets are provided

Consider:
- Slowing growth, margin compression, market saturation
- Competitive threats, disruption risk
- Regulatory/legal risks
- Macro headwinds (rates, inflation, recession)
- Valuation concerns
- Negative analyst coverage or downgrades

Format your response as valid JSON:
{
    "thesis": "2-3 sentence bear thesis",
    "evidence": ["evidence 1", "evidence 2", "evidence 3"],
    "risk_factors": ["risk 1", "risk 2"],
    "confidence": 0.6
}

Write all free-text fields in English."""

    async def run(self, context: dict) -> BearOutput:
        memory = context.get("memory")
        symbol = context.get("symbol", "Unknown")
        trace_agent = context.get("trace_agent")
        logger.info(f"[BearAgent] Building bear case for {symbol}")

        prompt_context = memory.get_prompt_context(exclude_current="bear_output")
        user_prompt = f"Build the strongest bearish thesis for {symbol} using the context data. Output English JSON."

        fallback = {"thesis": "", "evidence": [], "risk_factors": [], "confidence": 0.5}

        try:
            parsed = await self._call_json_llm(
                user_prompt=user_prompt,
                context=prompt_context,
                fallback=fallback,
                temperature=0.4,
                max_tokens=1600,
                thinking_enabled=False,
                trace_agent=trace_agent,
                llm_call_name="bear_case_json",
            )
        except Exception as e:
            logger.error(f"[BearAgent] Failed: {e}")
            parsed = {"thesis": str(e), "evidence": [], "risk_factors": [], "confidence": 0.5}

        evidence = BaseAgent._normalize_string_list(parsed.get("evidence", []))
        risk_factors = BaseAgent._normalize_string_list(parsed.get("risk_factors", []))
        confidence = float(parsed.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))

        output = BearOutput(
            thesis=str(parsed.get("thesis", "")),
            evidence=evidence,
            risk_factors=risk_factors,
            confidence=confidence,
        )
        memory.write("bear_output", output)
        return output
