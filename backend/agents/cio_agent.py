"""MarketMind AI Dashboard - Chief Investment Officer (CIO) Agent
Final decision agent that synthesizes all analysis into BUY / HOLD / SELL.
"""
from __future__ import annotations
import logging

from .base_agent import BaseAgent
from core.models import CIOOutput, CIOAction, RiskLevel

logger = logging.getLogger(__name__)


class CIOAgent(BaseAgent):
    AGENT_NAME = "cio_agent"
    SYSTEM_PROMPT = """You are the Chief Investment Officer (CIO) for MarketMind AI Dashboard.

Your job: Review ALL previous agent analyses and make a final investment recommendation.

You have access to:
- Research Agent: company info, news, macro data
- Sentiment Agent: overall sentiment score and explanation
- Valuation Agent: P/E, growth, sector comparison
- Bull Case Agent: strongest buy thesis with evidence
- Bear Case Agent: strongest sell thesis with risk factors
- Risk Agent: macro, company, and volatility risk levels
- Debate Agent: structured bull vs bear debate results

Your final output must be:
- BUY, HOLD, or SELL
- A clear, simple reasoning (3-5 sentences a beginner can understand)
- Confidence level (0.0 to 1.0)
- Overall risk level (Low, Medium, High)
- Key points (3-5 bullet points summarizing your rationale)
- Time horizon for the recommendation

IMPORTANT RULES:
1. Be decisive but honest — if evidence is mixed, say HOLD
2. Explain your decision in beginner-friendly language
3. Acknowledge both sides before making your call
4. Never recommend BUY just because sentiment is positive — weigh all factors
5. Consider the investor's perspective: is this a good entry point?
6. If research data_quality is partial or poor, say so and avoid overstating confidence
7. Do not claim to have read full articles when only headlines/snippets are provided

Format as JSON:
{
    "action": "BUY",
    "reasoning": "Clear 3-5 sentence explanation for a beginner investor...",
    "confidence": 0.68,
    "risk_level": "Medium",
    "key_points": ["Point 1", "Point 2", "Point 3", "Point 4"],
    "time_horizon": "6-12 months"
}

Write all free-text fields in English."""

    async def run(self, context: dict) -> CIOOutput:
        memory = context.get("memory")
        symbol = context.get("symbol", "Unknown")
        trace_agent = context.get("trace_agent")
        logger.info(f"[CIOAgent] Making final decision for {symbol}")

        prompt_context = memory.get_prompt_context(exclude_current="cio_output")
        user_prompt = f"""Review all analysis for {symbol} and make your final investment recommendation.
Synthesize the research, sentiment, valuation, bull/bear cases, risk, and debate.
Output your BUY/HOLD/SELL decision as English JSON."""

        fallback = {"action": "HOLD", "reasoning": "", "confidence": 0.3,
                     "risk_level": "Medium", "key_points": [],
                     "time_horizon": "6-12 months"}

        try:
            parsed = await self._call_json_llm(
                user_prompt=user_prompt,
                context=prompt_context,
                fallback=fallback,
                max_tokens=1800,
                thinking_enabled=True,
                reasoning_effort="high",
                trace_agent=trace_agent,
                llm_call_name="cio_decision_json",
            )
        except Exception as e:
            logger.error(f"[CIOAgent] Failed: {e}")
            parsed = {"action": "HOLD", "reasoning": f"Error making decision: {e}",
                       "confidence": 0.3, "risk_level": "Medium",
                       "key_points": [], "time_horizon": "6-12 months"}

        # Parse action
        action_str = str(parsed.get("action", "HOLD")).upper()
        try:
            action = CIOAction(action_str)
        except ValueError:
            action = CIOAction.HOLD

        # Parse risk level
        risk_str = str(parsed.get("risk_level", "Medium")).lower()
        if "high" in risk_str:
            risk = RiskLevel.HIGH
        elif "low" in risk_str:
            risk = RiskLevel.LOW
        else:
            risk = RiskLevel.MEDIUM

        confidence = float(parsed.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))

        key_points = BaseAgent._normalize_string_list(parsed.get("key_points", []))

        output = CIOOutput(
            action=action,
            reasoning=str(parsed.get("reasoning", "")),
            confidence=confidence,
            risk_level=risk,
            key_points=key_points,
            time_horizon=str(parsed.get("time_horizon", "6-12 months")),
        )
        memory.write("cio_output", output)
        logger.info(f"[CIOAgent] Decision: {action.value} (confidence: {output.confidence})")
        return output
