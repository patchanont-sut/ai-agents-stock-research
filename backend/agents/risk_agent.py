"""MarketMind AI Dashboard - Risk Assessment Agent"""
from __future__ import annotations
import logging

from .base_agent import BaseAgent
from core.models import RiskOutput, RiskLevel

logger = logging.getLogger(__name__)


class RiskAgent(BaseAgent):
    AGENT_NAME = "risk_agent"
    SYSTEM_PROMPT = """You are the Risk Assessment Agent for MarketMind AI Dashboard.

Your job: Evaluate the risk profile of a stock across three dimensions:
1. Macro Risk - interest rates, inflation, recession risk, geopolitical events
2. Company Risk - competitive threats, regulatory issues, management, financial health
3. Volatility Risk - price swings, sector volatility, beta, market conditions

Rate each as: Low, Medium, or High.
Provide specific factors for each category and an overall summary.

Format your response as valid JSON:
{
    "macro_risk": "Medium",
    "company_risk": "Low",
    "volatility_risk": "Medium",
    "macro_factors": ["factor 1", "factor 2"],
    "company_factors": ["factor 1", "factor 2"],
    "summary": "2-3 sentence overall risk assessment"
}

Write all free-text fields in English."""

    async def run(self, context: dict) -> RiskOutput:
        memory = context.get("memory")
        symbol = context.get("symbol", "Unknown")
        logger.info(f"[RiskAgent] Assessing risk for {symbol}")

        user_prompt = f"Assess the risk profile for {symbol} across macro, company, and volatility dimensions. Output English JSON."
        fallback = {"macro_risk": "Medium", "company_risk": "Medium", "volatility_risk": "Medium",
                     "macro_factors": [], "company_factors": [], "summary": ""}
        parsed = await self._call_context_json_llm(
            context,
            exclude_current="risk_output",
            user_prompt=user_prompt,
            fallback=fallback,
            temperature=0.3,
            max_tokens=1200,
            llm_call_name="risk_json",
            thinking_enabled=False,
        )
        if parsed.get("_error"):
            parsed["summary"] = parsed["_error"]

        def to_risk_level(s: str) -> RiskLevel:
            s = s.lower()
            if "high" in s:
                return RiskLevel.HIGH
            elif "low" in s:
                return RiskLevel.LOW
            return RiskLevel.MEDIUM

        macro_factors = BaseAgent._normalize_string_list(parsed.get("macro_factors", []))
        company_factors = BaseAgent._normalize_string_list(parsed.get("company_factors", []))

        output = RiskOutput(
            macro_risk=to_risk_level(parsed.get("macro_risk", "Medium")),
            company_risk=to_risk_level(parsed.get("company_risk", "Medium")),
            volatility_risk=to_risk_level(parsed.get("volatility_risk", "Medium")),
            macro_factors=macro_factors,
            company_factors=company_factors,
            summary=str(parsed.get("summary", "")),
        )
        memory.write("risk_output", output)
        return output
