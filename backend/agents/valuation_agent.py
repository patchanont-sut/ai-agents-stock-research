"""MarketMind AI Dashboard - Valuation Agent"""
from __future__ import annotations
import json
import logging
from .base_agent import BaseAgent
from core.models import ValuationOutput

logger = logging.getLogger(__name__)


class ValuationAgent(BaseAgent):
    AGENT_NAME = "valuation_agent"
    SYSTEM_PROMPT = """You are the Valuation Agent for MarketMind AI Dashboard. You explain valuation in simple terms.

Your job: Analyze company fundamentals and valuation metrics. Use the research and financial data provided.

Explain in simple terms:
- What is P/E ratio and what does this company's P/E mean?
- How does it compare to sector average?
- What is PEG ratio and what does it tell us?
- Is the stock fairly valued, undervalued, or overvalued?
- Consider growth rates, margins, competitive position

IMPORTANT: Explain everything in beginner-friendly language. No jargon without explanation.

Format as JSON:
{
    "pe_ratio": 25.5,
    "sector_avg_pe": 22.0,
    "peg_ratio": 1.8,
    "price_to_book": 12.0,
    "market_cap": "2.8 Trillion",
    "revenue_growth": 5.2,
    "sector": "Technology",
    "peers": ["MSFT", "GOOGL", "AMZN"],
    "verdict": "Fairly valued",
    "explanation": "Simple 2-3 sentence explanation a beginner can understand"
}

Write all free-text fields in English."""

    async def run(self, context: dict) -> ValuationOutput:
        memory = context.get("memory")
        symbol = context.get("symbol", "Unknown")
        trace_agent = context.get("trace_agent")
        logger.info(f"[ValuationAgent] Analyzing valuation for {symbol}")

        prompt_context = memory.get_prompt_context(exclude_current="valuation_output")
        user_prompt = f"Explain the valuation of {symbol} in simple terms for a beginner investor. Return ONLY valid English JSON."

        try:
            parsed = await self._call_json_llm(
                user_prompt=user_prompt,
                context=prompt_context,
                fallback={"verdict": "Unknown", "explanation": ""},
                temperature=0.3,
                max_tokens=1200,
                thinking_enabled=False,
                trace_agent=trace_agent,
                llm_call_name="valuation_json",
            )
        except Exception as e:
            logger.error(f"[ValuationAgent] Failed: {e}")
            parsed = {"verdict": "Unknown", "explanation": str(e)}

        output = ValuationOutput(
            pe_ratio=parsed.get("pe_ratio"),
            sector_avg_pe=parsed.get("sector_avg_pe"),
            peg_ratio=parsed.get("peg_ratio"),
            price_to_book=parsed.get("price_to_book"),
            market_cap=str(parsed.get("market_cap", "")) if parsed.get("market_cap") else None,
            revenue_growth=parsed.get("revenue_growth"),
            sector=parsed.get("sector", ""),
            peers=self._normalize_peers(parsed.get("peers", [])),
            verdict=parsed.get("verdict", ""),
            explanation=parsed.get("explanation", ""),
        )
        memory.write("valuation_output", output)
        return output

    def _parse_json(self, text: str) -> object:
        try:
            return json.loads(BaseAgent._strip_json_fence(text))
        except (json.JSONDecodeError, TypeError, ValueError):
            return {"verdict": "Unknown", "explanation": text[:400] if isinstance(text, str) else ""}

    def _coerce_parsed_json(self, parsed: object) -> dict:
        """Return a valuation dict even when the model emits an unexpected JSON shape."""
        if isinstance(parsed, dict):
            return parsed

        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, dict):
                    return item

        return {
            "verdict": "Unknown",
            "explanation": "Valuation response was not a JSON object.",
        }

    def _normalize_peers(self, peers: object) -> list[str]:
        """Keep peers as a safe list of non-empty strings."""
        if isinstance(peers, str):
            stripped = peers.strip()
            return [stripped] if stripped else []

        if isinstance(peers, list):
            normalized: list[str] = []
            for peer in peers:
                if peer is None:
                    continue
                text = str(peer).strip()
                if text:
                    normalized.append(text)
            return normalized

        return []
