"""MarketMind AI Dashboard - Bull Case Agent"""
from __future__ import annotations
import logging

from .base_agent import BaseAgent
from core.models import BullOutput

logger = logging.getLogger(__name__)


class BullAgent(BaseAgent):
    AGENT_NAME = "bull_agent"
    SYSTEM_PROMPT = """You are the Bull Case Agent for MarketMind AI Dashboard.

Your job: Build the strongest possible bullish thesis for a stock based on available research and data.

Rules:
1. Only use evidence from the research data and sentiment analysis provided
2. Be specific — cite actual news headlines, metrics, and data points
3. Identify key catalysts that could drive the stock higher
4. Be honest about conviction — don't fabricate bullishness
5. Assign a confidence score from 0.0 to 1.0
6. If data_quality is partial or poor, make the thesis more cautious and lower confidence when appropriate
7. Do not claim to have read full articles when only headlines/snippets are provided

Consider:
- Revenue growth, profit margins, market expansion
- New product launches, innovation
- Competitive advantages and moats
- Favorable macro conditions
- Positive analyst coverage
- Strong institutional or retail interest

Format your response as valid JSON:
{
    "thesis": "2-3 sentence bull thesis",
    "evidence": ["evidence 1", "evidence 2", "evidence 3"],
    "catalysts": ["catalyst 1", "catalyst 2"],
    "confidence": 0.7
}

Write all free-text fields in English."""

    async def run(self, context: dict) -> BullOutput:
        memory = context.get("memory")
        symbol = context.get("symbol", "Unknown")
        logger.info(f"[BullAgent] Building bull case for {symbol}")

        user_prompt = f"Build the strongest bullish thesis for {symbol} using the context data. Output English JSON."
        fallback = {"thesis": "", "evidence": [], "catalysts": [], "confidence": 0.5}
        parsed = await self._call_context_json_llm(
            context,
            exclude_current="bull_output",
            user_prompt=user_prompt,
            fallback=fallback,
            temperature=0.4,
            max_tokens=1600,
            llm_call_name="bull_case_json",
            thinking_enabled=False,
        )
        if parsed.get("_error"):
            parsed["thesis"] = parsed["_error"]

        evidence = BaseAgent._normalize_string_list(parsed.get("evidence", []))
        catalysts = BaseAgent._normalize_string_list(parsed.get("catalysts", []))
        confidence = float(parsed.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))

        output = BullOutput(
            thesis=str(parsed.get("thesis", "")),
            evidence=evidence,
            catalysts=catalysts,
            confidence=confidence,
        )
        memory.write("bull_output", output)
        return output
