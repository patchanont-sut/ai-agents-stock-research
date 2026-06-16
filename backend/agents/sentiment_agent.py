"""MarketMind AI Dashboard - Sentiment Agent
Analyzes sentiment of news articles and Reddit posts.
Scores from -1 (very negative) to +1 (very positive).
"""
from __future__ import annotations
import json
import logging

from .base_agent import BaseAgent
from core.models import SentimentOutput, SentimentLabel

logger = logging.getLogger(__name__)


class SentimentAgent(BaseAgent):
    AGENT_NAME = "sentiment_agent"
    SYSTEM_PROMPT = """You are the Sentiment Analysis Agent for MarketMind AI Dashboard.

Your job: Analyze the sentiment of news articles, Reddit posts, and macro data for a stock.

Given the research data from the Research Agent, analyze:
1. Overall news sentiment (positive/negative/neutral)
2. Reddit retail investor sentiment
3. Give an overall sentiment score from -1.0 (extremely bearish) to +1.0 (extremely bullish)
4. Explain your reasoning

Guidelines for scoring:
- -1.0 to -0.5: Strongly negative (bad news, downgrades, scandals, macro headwinds)
- -0.5 to -0.2: Moderately negative (concerns, risks, competition)
- -0.2 to +0.2: Neutral/Mixed
- +0.2 to +0.5: Moderately positive (good earnings, growth, positive coverage)
- +0.5 to +1.0: Strongly positive (exceptional results, major catalysts, strong momentum)

Always consider:
- Source credibility (financial press vs social media)
- Recency of news
- Volume of coverage
- Contrast between professional media and retail sentiment

Format your response as valid JSON:
{
    "overall_score": 0.35,
    "label": "positive",
    "explanation": "2-3 sentence explanation of the sentiment",
    "key_drivers": ["driver 1", "driver 2"]
}

Write all free-text fields in English."""

    async def run(self, context: dict) -> SentimentOutput:
        memory = context.get("memory")
        symbol = context.get("symbol", "Unknown")
        trace_agent = context.get("trace_agent")

        logger.info(f"[SentimentAgent] Analyzing sentiment for {symbol}")

        research_context = memory.get_prompt_context(exclude_current="sentiment_output")

        user_prompt = f"""Analyze the sentiment for {symbol} based on the research data provided in context.
Consider news articles, Reddit posts, and macro conditions.
Output English JSON."""

        try:
            parsed = await self._call_json_llm(
                user_prompt=user_prompt,
                context=research_context,
                fallback={"overall_score": 0.0, "label": "neutral", "explanation": ""},
                temperature=0.3,
                max_tokens=900,
                thinking_enabled=False,
                trace_agent=trace_agent,
                llm_call_name="sentiment_json",
            )
        except Exception as e:
            logger.error(f"[SentimentAgent] Failed: {e}")
            parsed = {"overall_score": 0.0, "label": "neutral", "explanation": f"Error: {e}"}

        score = float(parsed.get("overall_score", 0))
        score = max(-1.0, min(1.0, score))

        label_str = parsed.get("label", "neutral").lower()
        try:
            label = SentimentLabel(label_str)
        except ValueError:
            label = SentimentLabel.NEUTRAL

        output = SentimentOutput(
            overall_score=score,
            label=label,
            explanation=parsed.get("explanation", ""),
            article_scores=[],
        )

        memory.write("sentiment_output", output)
        logger.info(f"[SentimentAgent] Score: {score} ({label.value})")
        return output
