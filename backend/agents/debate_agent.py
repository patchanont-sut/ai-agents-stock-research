"""MarketMind AI Dashboard - Debate Agent
Structured bull vs bear debate based on all previous agent outputs.
"""
from __future__ import annotations
import logging

from .base_agent import BaseAgent
from core.models import DebateOutput, DebateTurn

logger = logging.getLogger(__name__)


class DebateAgent(BaseAgent):
    AGENT_NAME = "debate_agent"
    SYSTEM_PROMPT = """You are the Debate Moderator for MarketMind AI Dashboard.

Your job: Facilitate a structured debate between the Bull and Bear cases.

Based on the bull thesis, bear thesis, risk assessment, sentiment, and valuation data,
create a 4-turn debate (2 bull, 2 bear) where each side presents their strongest argument
and responds to the other side.

The debate should:
- Turn 1: Bull presents the core bullish argument
- Turn 2: Bear counters the bull argument and presents bearish risks
- Turn 3: Bull responds to bear's concerns with counter-evidence
- Turn 4: Bear makes final rebuttal

After the debate, declare a winner: "bull", "bear", or "tie".

IMPORTANT: Use ONLY the evidence from the context. Do not fabricate data.

Format as JSON:
{
    "turns": [
        {"side": "bull", "content": "Bull argument 1..."},
        {"side": "bear", "content": "Bear counter-argument..."},
        {"side": "bull", "content": "Bull rebuttal..."},
        {"side": "bear", "content": "Bear final argument..."}
    ],
    "winning_side": "bull",
    "summary": "Brief explanation of why this side won the debate"
}

Write all free-text fields in English."""

    async def run(self, context: dict) -> DebateOutput:
        memory = context.get("memory")
        symbol = context.get("symbol", "Unknown")
        trace_agent = context.get("trace_agent")
        logger.info(f"[DebateAgent] Running debate for {symbol}")

        prompt_context = memory.get_prompt_context(exclude_current="debate_output")
        user_prompt = f"Moderate a structured bull vs bear debate about {symbol} stock. Output English JSON with 4 turns."

        fallback = {"turns": [], "winning_side": "tie", "summary": ""}

        try:
            parsed = await self._call_json_llm(
                user_prompt=user_prompt,
                context=prompt_context,
                fallback=fallback,
                max_tokens=2400,
                thinking_enabled=True,
                reasoning_effort="high",
                trace_agent=trace_agent,
                llm_call_name="debate_json",
            )
        except Exception as e:
            logger.error(f"[DebateAgent] Failed: {e}")
            parsed = {"turns": [], "winning_side": "tie", "summary": str(e)}

        turns = []
        for turn_data in parsed.get("turns", []):
            if not isinstance(turn_data, dict):
                continue
            turns.append(DebateTurn(
                side=str(turn_data.get("side", "bull")),
                content=str(turn_data.get("content", "")),
            ))

        winning_side = str(parsed.get("winning_side", "tie"))
        if winning_side not in ("bull", "bear", "tie"):
            winning_side = "tie"

        output = DebateOutput(
            turns=turns,
            winning_side=winning_side,
            summary=str(parsed.get("summary", "")),
        )
        memory.write("debate_output", output)
        return output
