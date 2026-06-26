"""
MarketMind AI Dashboard - Agent Orchestrator
Manages the full analysis pipeline: runs all agents in order,
handles errors gracefully, and populates the AnalysisResult.
"""
from __future__ import annotations
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from .models import (
    AnalysisResult,
    AnalysisStatus,
)
from .memory import get_or_create_memory
from .translation_service import ThaiTranslationService
from .trace import (
    AnalysisTrace,
    AgentTraceEntry,
    ToolCallTrace,
)
from .reliability import compute_reliability_score
from .evidence import build_evidence_library
from .grounding import compute_grounding_report

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Runs the full multi-agent analysis pipeline for a given stock symbol.
    Each agent receives the shared memory and tool registry.
    """

    def __init__(self, symbol: str, session_id: str):
        self.symbol = symbol.upper().strip()
        self.session_id = session_id
        self.memory = get_or_create_memory(session_id, self.symbol)
        self._started_at = None
        self._trace = AnalysisTrace(
            analysis_id=session_id,
            symbol=self.symbol,
        )

    async def run_pipeline(self) -> AnalysisResult:
        """
        Execute the full agent pipeline including the new memo agent.
        Returns a complete AnalysisResult with all agent outputs.
        """
        self._started_at = datetime.now(timezone.utc)
        self._trace.started_at = self._started_at
        _traces[self.session_id] = self._trace

        result = AnalysisResult(
            id=self.session_id,
            symbol=self.symbol,
            status=AnalysisStatus.RUNNING,
            generated_at=self._started_at,
        )

        from agents.bear_agent import BearAgent
        from agents.bull_agent import BullAgent
        from agents.cio_agent import CIOAgent
        from agents.debate_agent import DebateAgent
        from agents.research_agent import ResearchAgent
        from agents.risk_agent import RiskAgent
        from agents.sentiment_agent import SentimentAgent
        from agents.valuation_agent import ValuationAgent

        agent_order = [
            ("research", ResearchAgent, "research"),
            ("sentiment", SentimentAgent, "sentiment"),
            ("valuation", ValuationAgent, "valuation"),
            ("bull", BullAgent, "bull_case"),
            ("bear", BearAgent, "bear_case"),
            ("risk", RiskAgent, "risk"),
            ("debate", DebateAgent, "debate"),
            ("cio", CIOAgent, "cio_decision"),
            ("memo", None, ""),
        ]

        has_partial_failure = False

        for agent_name, agent_cls, result_attr in agent_order:
            trace_entry = AgentTraceEntry(
                agent_name=agent_name,
                status="running",
                started_at=datetime.now(timezone.utc),
            )
            self._trace.agents.append(trace_entry)
            _traces[self.session_id] = self._trace

            try:
                if agent_name == "memo":
                    await self._run_memo(result, trace_entry)
                else:
                    await self._run_agent(agent_cls, result_attr, result, trace_entry)
                trace_entry.status = "complete"
                logger.info(f"[Orchestrator] ✓ {agent_name} completed for {self.symbol}")
            except Exception as e:
                logger.error(f"[Orchestrator] ✗ {agent_name} FAILED for {self.symbol}: {e}")
                result.errors.append(f"{agent_name} agent error: {str(e)}")
                trace_entry.status = "failed"
                trace_entry.errors.append(str(e))
                has_partial_failure = True
            finally:
                trace_entry.completed_at = datetime.now(timezone.utc)
                if trace_entry.started_at:
                    trace_entry.duration_ms = (
                        (trace_entry.completed_at - trace_entry.started_at).total_seconds()
                    ) * 1000
                _analysis_progress.setdefault(self.session_id, []).append(agent_name)
                _traces[self.session_id] = self._trace

        result.status = AnalysisStatus.PARTIAL if has_partial_failure else AnalysisStatus.COMPLETE

        # ── Compute reliability score after research is available ──
        if result.research:
            try:
                eq = compute_reliability_score(result.research, self._trace)
                result.evidence_quality = eq
            except Exception as e:
                logger.warning(f"[Orchestrator] Reliability scoring failed: {e}")

        try:
            translation_report = await ThaiTranslationService().translate_analysis(result)
            if translation_report.missing_required:
                result.status = AnalysisStatus.PARTIAL
                result.errors.append(
                    "Thai translation incomplete: "
                    + ", ".join(translation_report.missing_required[:8])
                )
            if translation_report.failed:
                result.errors.append(
                    "Thai translation warning: "
                    + ", ".join(translation_report.failed[:8])
                )
            logger.info(
                "[Orchestrator] Thai translation: %s/%s fields translated",
                translation_report.translated,
                translation_report.attempted,
            )
        except Exception as e:
            logger.error(f"[Orchestrator] Thai translation failed: {e}")
            result.status = AnalysisStatus.PARTIAL
            result.errors.append(
                "Thai translation failed: AI result is available in English, but Thai translation could not be generated"
            )

        result.completed_at = datetime.now(timezone.utc)

        elapsed = (result.completed_at - self._started_at).total_seconds()
        logger.info(
            f"[Orchestrator] Pipeline complete for {self.symbol} "
            f"({result.status.value}) in {elapsed:.1f}s"
        )

        return result

    async def _run_agent(
        self,
        agent_cls: type[Any],
        result_attr: str,
        result: AnalysisResult,
        trace_entry: AgentTraceEntry,
    ):
        agent = agent_cls()
        try:
            output = await agent.run({
                "memory": self.memory,
                "symbol": self.symbol,
                "session_id": self.session_id,
                "trace_agent": trace_entry,
            })
            setattr(result, result_attr, output)
            if result_attr == "research":
                result.stock.symbol = self.symbol
            self._capture_summary(trace_entry, output)
        finally:
            await agent.close()

    async def _run_memo(self, result: AnalysisResult, trace_entry: AgentTraceEntry):
        """Build evidence library and generate citation-grounded investment memo."""
        from agents.memo_agent import MemoAgent

        logger.info(f"[Orchestrator] Building evidence library for {self.symbol}")

        # Build evidence library
        try:
            evidence_library = build_evidence_library(result)
            result.evidence_library = evidence_library
            logger.info(f"[Orchestrator] Evidence library built: {len(evidence_library)} items")
        except Exception as e:
            logger.error(f"[Orchestrator] Evidence library build failed: {e}")
            result.errors.append(f"Evidence library build error: {str(e)}")
            evidence_library = []
            result.evidence_library = evidence_library

        # Run MemoAgent
        agent = MemoAgent()
        try:
            output = await agent.run({
                "memory": self.memory,
                "symbol": self.symbol,
                "session_id": self.session_id,
                "analysis_result": result,
                "evidence_library": evidence_library,
                "trace_agent": trace_entry,
            })
            if output is not None:
                # Compute grounding report
                try:
                    grounding = compute_grounding_report(output, evidence_library)
                    output.grounding_report = grounding
                    logger.info(
                        f"[Orchestrator] Grounding score: {grounding.grounded_score} "
                        f"({grounding.valid_citation_count} valid, "
                        f"{grounding.invalid_citation_count} invalid citations)"
                    )
                except Exception as e:
                    logger.error(f"[Orchestrator] Grounding check failed: {e}")
                    result.errors.append(f"Grounding check failed: {str(e)}")

                result.investment_memo = output
                self._capture_summary(trace_entry, output)
            else:
                raise RuntimeError("MemoAgent returned None")
        except Exception as e:
            logger.error(f"[Orchestrator] Memo generation failed: {e}")
            result.errors.append(f"Memo generation error: {str(e)}")
            # Attempt fallback memo
            try:
                fallback = agent._build_fallback_memo(
                    self.symbol, result, evidence_library or []
                )
                if fallback:
                    grounding = compute_grounding_report(fallback, evidence_library or [])
                    fallback.grounding_report = grounding
                    result.investment_memo = fallback
                    result.errors.append(
                        "Investment memo was generated via fallback (AI generation failed)."
                    )
                    trace_entry.short_summary = f"Memo (fallback): {fallback.title}"
            except Exception as fallback_err:
                logger.error(f"[Orchestrator] Fallback memo also failed: {fallback_err}")
                result.errors.append(f"Memo fallback also failed: {str(fallback_err)}")
        finally:
            await agent.close()

    @staticmethod
    def _capture_summary(trace_entry: AgentTraceEntry, output: object) -> None:
        """Capture a short human-readable summary from agent output."""
        try:
            if hasattr(output, "summary") and output.summary:
                trace_entry.short_summary = str(output.summary)[:200]
            elif hasattr(output, "thesis") and output.thesis:
                trace_entry.short_summary = str(output.thesis)[:200]
            elif hasattr(output, "action") and hasattr(output, "reasoning"):
                trace_entry.short_summary = f"{output.action}: {str(output.reasoning)[:150]}"
            elif hasattr(output, "explanation") and output.explanation:
                trace_entry.short_summary = str(output.explanation)[:200]
            elif hasattr(output, "overall_score"):
                trace_entry.short_summary = f"Sentiment score: {output.overall_score}"
            elif hasattr(output, "title") and output.title:
                trace_entry.short_summary = str(output.title)[:200]
        except Exception:
            pass


# ── Synchronous wrapper for background tasks ──

_analysis_store: dict[str, AnalysisResult] = {}
_analysis_progress: dict[str, list[str]] = {}
_traces: dict[str, AnalysisTrace] = {}


def seed_analysis_result(result: AnalysisResult) -> None:
    """Store pending/running analysis state before the background task finishes."""
    _analysis_store[result.id] = result


async def run_full_pipeline(symbol: str, session_id: str, language: str = "en") -> None:
    """
    Background task: run the full pipeline and store the result.
    This is called from the FastAPI endpoint.
    """
    logger.info(f"[Pipeline] Starting full analysis for {symbol} (id={session_id}, lang={language})")

    _analysis_progress[session_id] = []
    orchestrator = Orchestrator(symbol=symbol, session_id=session_id)
    try:
        result = await orchestrator.run_pipeline()
    except Exception as e:
        logger.error(f"[Pipeline] Fatal error for {symbol}: {e}")
        result = AnalysisResult(
            id=session_id,
            symbol=symbol,
            status=AnalysisStatus.FAILED,
            errors=[f"Fatal pipeline error: {str(e)}"],
            generated_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )

    # Finalize trace
    trace = _traces.get(session_id)
    if trace:
        trace.completed_at = datetime.now(timezone.utc)
        _traces[session_id] = trace

    _analysis_store[session_id] = result
    logger.info(f"[Pipeline] Result stored for {session_id}: {result.status.value}")


def get_analysis_result(session_id: str) -> Optional[AnalysisResult]:
    """Get a completed analysis result from the store."""
    return _analysis_store.get(session_id)


def get_analysis_progress(session_id: str) -> list[str]:
    """Get the list of completed agent names for an in-progress analysis."""
    return _analysis_progress.get(session_id, [])


def get_analysis_trace(session_id: str) -> Optional[AnalysisTrace]:
    """Get the trace for a running or completed analysis."""
    return _traces.get(session_id)
