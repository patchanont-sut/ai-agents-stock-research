"""
MarketMind AI Dashboard - FastAPI Application Entry Point
"""
from __future__ import annotations
import logging
import uuid
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from pathlib import Path
import json

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from config import settings, validate_config
from cache.cache_manager import cache
from core.models import (
    AnalyzeRequest,
    AnalyzeResponse,
    AnalysisResult,
    AnalysisStatus,
    MacroData,
    CompareRequest,
    CompareResult,
    CompareStockSummary,
    EvaluationMetrics,
)
from core.orchestrator import (
    get_analysis_progress,
    get_analysis_result,
    get_analysis_trace,
    run_full_pipeline,
    seed_analysis_result,
)
from core.translation_service import ThaiTranslationService
from core.comparison import rank_comparison, normalize_compare_symbols

# ── Logging Setup ──
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    logger.info("=" * 50)
    logger.info("MarketMind AI Dashboard — Starting up...")
    validate_config()
    
    # Import tools to register them
    from tools import macro_tools, market_tools, news_tools  # noqa: F401
    from core.tool_registry import tool_registry
    
    logger.info(f"Cache dir: {settings.CACHE_DIR}")
    logger.info(f"Cache entries loaded: {cache.size}")
    logger.info(f"Tools registered: {len(tool_registry)}")
    logger.info(f"CORS origins: {settings.CORS_ORIGINS}")
    logger.info("Server ready at http://{}:{}".format(settings.HOST, settings.PORT))
    logger.info("=" * 50)
    yield
    logger.info("MarketMind AI Dashboard — Shutting down...")
    from data.http_client import close_data_http_client
    await close_data_http_client()
    cache.prune_expired()


app = FastAPI(
    title="MarketMind AI Dashboard",
    description="Multi-Agent Stock News & Market Sentiment Analysis System",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health Check ──
@app.get("/api/health")
async def health_check():
    from core.tool_registry import tool_registry
    return {
        "status": "ok",
        "service": "MarketMind AI Dashboard",
        "version": "1.0.0",
    }


# ── Analysis Endpoints ──
@app.post("/api/analyze", response_model=AnalyzeResponse)
async def start_analysis(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """Start a new stock analysis. Fires background pipeline, returns analysis ID for polling."""
    symbol = request.symbol.upper().strip()
    analysis_id = str(uuid.uuid4())

    # Create pending analysis result
    pending = AnalysisResult(
        id=analysis_id,
        symbol=symbol,
        status=AnalysisStatus.PENDING,
    )
    pending.status = AnalysisStatus.RUNNING
    seed_analysis_result(pending)

    # Fire background task for the full agent pipeline
    language = request.language or "en"
    background_tasks.add_task(run_full_pipeline, symbol, analysis_id, language)

    return AnalyzeResponse(
        analysis_id=analysis_id,
        status=AnalysisStatus.RUNNING,
        message=f"Analysis started for {symbol}. Poll /api/analysis/{analysis_id}/status for progress.",
    )


@app.get("/api/analysis/{analysis_id}/status")
async def get_analysis_status(analysis_id: str):
    """Get the current status of an analysis with agent progress."""
    result = get_analysis_result(analysis_id)
    if result:
        return {
            "analysis_id": analysis_id,
            "status": result.status.value,
            "symbol": result.symbol,
            "completed_agents": get_analysis_progress(analysis_id),
        }

    raise HTTPException(status_code=404, detail="Analysis not found")


@app.get("/api/analysis/{analysis_id}/result")
async def get_analysis_result_endpoint(analysis_id: str):
    """Get the full analysis result."""
    result = get_analysis_result(analysis_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")

    if result.status in (AnalysisStatus.PENDING, AnalysisStatus.RUNNING):
        raise HTTPException(status_code=202, detail="Analysis still in progress")

    # The pipeline owns translation. Result fetch only validates coverage so
    # opening or toggling the UI never triggers another model call.
    translation_report = ThaiTranslationService().inspect_analysis(result)
    if translation_report.missing_required:
        result.status = AnalysisStatus.PARTIAL
        message = (
            "Thai translation incomplete: "
            + ", ".join(translation_report.missing_required[:8])
        )
        if message not in result.errors:
            result.errors.append(message)

    return result.model_dump(exclude_none=True)


# ── Data Endpoints (standalone) ──
@app.get("/api/price/{symbol}")
async def get_stock_price_endpoint(symbol: str):
    """Get current stock price (standalone)."""
    from data.finnhub_client import get_stock_quote
    from data.alpha_vantage_client import get_global_quote

    # Try Finnhub
    quote = await get_stock_quote(symbol.upper())
    if quote and quote.get("current_price"):
        return {
            "symbol": symbol.upper(),
            "price": quote["current_price"],
            "change": quote.get("change"),
            "change_percent": quote.get("change_percent"),
            "source": "Finnhub",
        }

    # Fallback to Alpha Vantage
    av = await get_global_quote(symbol.upper())
    if av:
        return {
            "symbol": symbol.upper(),
            "price": av.get("price"),
            "change": av.get("change"),
            "change_percent": av.get("change_percent"),
            "source": "Alpha Vantage",
        }

    return {"symbol": symbol.upper(), "price": None, "error": "Unable to fetch price"}


@app.get("/api/news/{symbol}")
async def get_news_endpoint(symbol: str, limit: int = 10):
    """Get recent news for a stock (standalone)."""
    from data.finnhub_client import get_company_news as finnhub_news
    from data.google_news_client import fetch_google_news

    articles = await finnhub_news(symbol.upper())
    if not articles:
        articles = await fetch_google_news(f"{symbol.upper()} stock", limit=limit)
        source = "Google News"
    else:
        source = "Finnhub"
        articles = articles[:limit]

    return {
        "symbol": symbol.upper(),
        "articles": articles,
        "source": source,
    }


@app.get("/api/macro")
async def get_macro_endpoint():
    """Get macro market data."""
    from data.finnhub_client import get_market_indices
    from data.alpha_vantage_client import get_treasury_yield, get_fed_funds_rate

    result = MacroData()
    
    indices = await get_market_indices()
    if indices:
        if "sp500" in indices:
            result.sp500_change = indices["sp500"].get("change_percent")
        if "nasdaq" in indices:
            result.nasdaq_change = indices["nasdaq"].get("change_percent")
        if "vix" in indices:
            result.vix = indices["vix"].get("price")

    treasury = await get_treasury_yield()
    if treasury:
        result.treasury_10y = treasury.get("yield")

    fed = await get_fed_funds_rate()
    if fed:
        result.fed_funds_rate = fed.get("rate")

    return result


@app.get("/api/analysis/{analysis_id}/trace")
async def get_analysis_trace_endpoint(analysis_id: str):
    """Get the agent trace for a running or completed analysis."""
    trace = get_analysis_trace(analysis_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found for this analysis")
    return trace.model_dump(exclude_none=True)


@app.get("/api/analysis/{analysis_id}/evidence")
async def get_evidence_endpoint(analysis_id: str):
    """Get the evidence library and investment memo for a completed analysis."""
    result = get_analysis_result(analysis_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")

    if result.status in (AnalysisStatus.PENDING, AnalysisStatus.RUNNING):
        raise HTTPException(status_code=202, detail="Analysis still in progress")

    return {
        "analysis_id": result.id,
        "symbol": result.symbol,
        "evidence_library": (
            [item.model_dump(exclude_none=True) for item in result.evidence_library]
            if result.evidence_library
            else []
        ),
        "investment_memo": (
            result.investment_memo.model_dump(exclude_none=True)
            if result.investment_memo
            else None
        ),
    }


@app.get("/api/search")
async def search_stocks_endpoint(q: str):
    """Search for stock symbols."""
    from data.finnhub_client import lookup_symbol
    results = await lookup_symbol(q)
    return {"query": q, "results": results}


# ── Comparison Endpoints ──

_comparison_store: dict[str, CompareResult] = {}
_comparison_progress: dict[str, dict[str, list[str]]] = {}



async def _build_stock_summary(result: AnalysisResult) -> CompareStockSummary:
    """Build a CompareStockSummary from a completed AnalysisResult."""
    bull_points: list[str] = []
    if result.bull_case:
        bull_points = [e for e in (result.bull_case.evidence or []) if e][:3]
    bear_points: list[str] = []
    if result.bear_case:
        bear_points = [e for e in (result.bear_case.evidence or []) if e][:3]
    key_risks: list[str] = []
    if result.risk:
        key_risks = (
            (result.risk.macro_factors or [])[:2]
            + (result.risk.company_factors or [])[:2]
        )

    return CompareStockSummary(
        symbol=result.symbol,
        company_name=result.stock.name if result.stock else "",
        cio_action=result.cio_decision.action.value if result.cio_decision else "",
        confidence=result.cio_decision.confidence if result.cio_decision else 0.0,
        risk_level=result.cio_decision.risk_level.value if result.cio_decision else "",
        sentiment_score=result.sentiment.overall_score if result.sentiment else 0.0,
        valuation_verdict=result.valuation.verdict if result.valuation else "",
        reliability_score=(
            result.evidence_quality.overall_reliability_score
            if result.evidence_quality
            else 0.0
        ),
        grounding_score=(
            result.investment_memo.grounding_report.grounded_score
            if result.investment_memo and result.investment_memo.grounding_report
            else 0.0
        ),
        top_bull_points=bull_points,
        top_bear_points=bear_points,
        key_risks=key_risks,
        errors=result.errors[:5] if result.errors else [],
    )


async def run_comparison_pipeline(symbols: list[str], compare_id: str, language: str = "en") -> None:
    """Run individual analyses for all symbols in parallel, then synthesize a comparison."""
    import asyncio

    logger.info(f"[Compare] Starting comparison {compare_id} for {symbols} (language={language})")

    compare_result = CompareResult(
        id=compare_id,
        symbols=symbols,
        status=AnalysisStatus.RUNNING,
        generated_at=datetime.now(timezone.utc),
    )
    _comparison_store[compare_id] = compare_result
    _comparison_progress[compare_id] = {}

    # Run each analysis in its own background task
    async def analyze_one(sym: str) -> tuple[str, AnalysisResult | None, str | None]:
        analysis_id = str(uuid.uuid4())
        _comparison_progress[compare_id][sym] = [analysis_id, "running"]
        try:
            await run_full_pipeline(sym, analysis_id, language)
            result = get_analysis_result(analysis_id)
            if result is None:
                return sym, None, "Analysis produced no result"
            if result.status in (AnalysisStatus.FAILED,):
                return sym, None, f"Analysis failed: {result.errors}"
            _comparison_progress[compare_id][sym] = [analysis_id, result.status.value]
            return sym, result, None
        except Exception as e:
            logger.error(f"[Compare] Analysis failed for {sym}: {e}")
            _comparison_progress[compare_id][sym] = [analysis_id, "failed"]
            return sym, None, str(e)

    tasks = [analyze_one(sym) for sym in symbols]
    results = await asyncio.gather(*tasks)

    summaries: list[CompareStockSummary] = []
    errors: list[str] = []

    for sym, result, err in results:
        if err:
            errors.append(f"{sym}: {err}")
            # Build partial summary from whatever we have
            if result is not None:
                summary = await _build_stock_summary(result)
                summaries.append(summary)
            else:
                summaries.append(CompareStockSummary(symbol=sym, errors=[err]))
        elif result is not None:
            summary = await _build_stock_summary(result)
            summaries.append(summary)
        else:
            errors.append(f"{sym}: No result returned")
            summaries.append(CompareStockSummary(symbol=sym, errors=["No result"]))

    compare_result.summaries = summaries

    # Build comparison table
    compare_result.comparison_table = [
        {
            "symbol": s.symbol,
            "company": s.company_name,
            "action": s.cio_action,
            "confidence": s.confidence,
            "risk": s.risk_level,
            "sentiment": s.sentiment_score,
            "valuation": s.valuation_verdict,
            "reliability": s.reliability_score,
            "grounding": s.grounding_score,
        }
        for s in summaries
    ]

    # Rank
    winner, rationale = rank_comparison(summaries)
    compare_result.winner_symbol = winner
    compare_result.ranking_rationale = rationale
    compare_result.errors = errors

    if errors and len(errors) < len(symbols):
        compare_result.status = AnalysisStatus.PARTIAL
    elif len(errors) == len(symbols):
        compare_result.status = AnalysisStatus.FAILED
    else:
        compare_result.status = AnalysisStatus.COMPLETE

    compare_result.completed_at = datetime.now(timezone.utc)
    _comparison_store[compare_id] = compare_result
    logger.info(
        f"[Compare] Comparison {compare_id} complete: {compare_result.status.value}, winner={winner}"
    )


@app.post("/api/compare")
async def start_comparison(request: CompareRequest, background_tasks: BackgroundTasks):
    """Start a multi-stock comparison. Runs analysis pipelines for each symbol in parallel."""
    try:
        symbols = normalize_compare_symbols(request.symbols)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    compare_id = str(uuid.uuid4())
    language = request.language or "en"

    # Init store
    _comparison_store[compare_id] = CompareResult(
        id=compare_id,
        symbols=symbols,
        status=AnalysisStatus.PENDING,
    )

    background_tasks.add_task(run_comparison_pipeline, symbols, compare_id, language)

    return {
        "compare_id": compare_id,
        "symbols": symbols,
        "status": "running",
        "message": f"Comparison started for {symbols}. Poll /api/compare/{compare_id}/status for progress.",
    }


@app.get("/api/compare/{compare_id}/status")
async def get_compare_status(compare_id: str):
    """Get comparison progress including per-symbol completion status."""
    compare_result = _comparison_store.get(compare_id)
    if not compare_result:
        raise HTTPException(status_code=404, detail="Comparison not found")

    return {
        "compare_id": compare_id,
        "status": compare_result.status.value,
        "symbols": compare_result.symbols,
        "completed_symbols": (
            [s.symbol for s in compare_result.summaries]
            if compare_result.status not in (AnalysisStatus.PENDING, AnalysisStatus.RUNNING)
            else []
        ),
        "symbol_progress": _comparison_progress.get(compare_id, {}),
    }


@app.get("/api/compare/{compare_id}/result")
async def get_compare_result(compare_id: str):
    """Get the final comparison result."""
    compare_result = _comparison_store.get(compare_id)
    if not compare_result:
        raise HTTPException(status_code=404, detail="Comparison not found")

    if compare_result.status in (AnalysisStatus.PENDING, AnalysisStatus.RUNNING):
        raise HTTPException(
            status_code=202,
            detail="Comparison still in progress. Poll /api/compare/{compare_id}/status first.",
        )

    return compare_result.model_dump(exclude_none=True)


# ── Evaluation Endpoints ──

@app.get("/api/evaluation/{analysis_id}", response_model=EvaluationMetrics)
async def get_evaluation(analysis_id: str):
    """Get AI quality evaluation metrics for a completed analysis."""
    from core.evaluation import evaluate_analysis

    result = get_analysis_result(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")

    if result.status in (AnalysisStatus.PENDING, AnalysisStatus.RUNNING):
        raise HTTPException(status_code=202, detail="Analysis still in progress")

    return evaluate_analysis(result)


@app.get("/api/evaluation/compare/{compare_id}")
async def get_comparison_evaluation(compare_id: str):
    """Get AI quality evaluation metrics for each stock in a comparison."""
    from core.evaluation import evaluate_comparison

    compare_result = _comparison_store.get(compare_id)
    if not compare_result:
        raise HTTPException(status_code=404, detail="Comparison not found")

    if compare_result.status in (AnalysisStatus.PENDING, AnalysisStatus.RUNNING):
        raise HTTPException(status_code=202, detail="Comparison still in progress")

    metrics = evaluate_comparison(compare_result)
    return {
        "compare_id": compare_id,
        "symbols": compare_result.symbols,
        "winner_symbol": compare_result.winner_symbol,
        "metrics": [m.model_dump(exclude_none=True) for m in metrics],
    }


# ── Memo Export Endpoint ──

def render_memo_markdown(result: AnalysisResult) -> str:
    memo = result.investment_memo
    if not memo:
        return ""

    lines: list[str] = [
        f"# {memo.title or f'Investment Research Memo: {result.symbol}'}",
        "",
        f"**Symbol:** {result.symbol}",
        f"**Recommendation:** {memo.recommendation or 'N/A'}",
        f"**Analysis ID:** {result.id}",
        f"**Generated:** {result.generated_at or 'N/A'}",
        "",
    ]

    if memo.executive_summary:
        lines += ["## Executive Summary", "", memo.executive_summary, ""]

    if memo.sections:
        lines += ["## Analysis Sections", ""]
        for section in memo.sections:
            lines += [f"### {section.heading}", "", section.content, ""]
            if section.citations:
                lines.append("**Citations:**")
                lines += [
                    f"- [{cite.evidence_id}] {cite.quote_or_summary}"
                    for cite in section.citations
                ]
                lines.append("")

    if memo.key_citations:
        lines += ["## Key Citations", ""]
        lines += [
            f"- **[{cite.evidence_id}]** {cite.quote_or_summary}"
            for cite in memo.key_citations
        ]
        lines.append("")

    if memo.grounding_report:
        gr = memo.grounding_report
        lines += [
            "## Grounding Report Summary",
            "",
            f"- **Grounding Score:** {gr.grounded_score}",
            f"- **Claims:** {gr.claim_count}",
            f"- **Cited Claims:** {gr.cited_claim_count}",
            f"- **Valid Citations:** {gr.valid_citation_count}",
            f"- **Invalid Citations:** {gr.invalid_citation_count}",
            "",
        ]

    if result.evidence_library:
        lines += ["## Evidence Appendix", ""]
        for item in result.evidence_library:
            lines += [
                f"### [{item.id}] {item.title}",
                f"- **Source:** {item.source}",
                f"- **Type:** {item.source_type}",
            ]
            if item.url:
                lines.append(f"- **URL:** {item.url}")
            if item.snippet:
                lines.append(f"- **Snippet:** {item.snippet}")
            lines += [f"  - {kp}" for kp in item.key_points]
            lines.append("")

    if result.errors:
        lines += ["## Errors / Warnings", ""]
        lines += [f"- {err}" for err in result.errors]
        lines.append("")

    lines += [
        "---",
        f"*Generated by MarketMind AI Dashboard on {datetime.now(timezone.utc).isoformat()}*",
    ]
    return "\n".join(lines)


@app.get("/api/analysis/{analysis_id}/memo.md")
async def get_memo_markdown(analysis_id: str):
    """Export the investment memo as a Markdown (.md) file."""
    from fastapi.responses import PlainTextResponse

    result = get_analysis_result(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")

    if result.status in (AnalysisStatus.PENDING, AnalysisStatus.RUNNING):
        raise HTTPException(status_code=202, detail="Analysis still in progress")

    memo = result.investment_memo
    if not memo:
        raise HTTPException(status_code=404, detail="No investment memo available for this analysis")

    return PlainTextResponse(
        content=render_memo_markdown(result),
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{result.symbol}_memo_{result.id[:8]}.md"',
        },
    )


# ── Demo / Offline Endpoint ──

@app.get("/api/demo/analysis")
async def get_demo_analysis():
    """Return a pre-built synthetic analysis result.

    This endpoint requires no API keys, no LLM calls, and no live
    financial data.  It is safe for portfolio demos and offline use.
    """
    synthetic_path = Path(__file__).resolve().parent.parent / "test_synthetic.json"

    try:
        raw = json.loads(synthetic_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise HTTPException(status_code=503, detail="Demo data unavailable")

    result_dict = raw.get("result")
    if not result_dict:
        raise HTTPException(status_code=503, detail="Demo result missing")

    try:
        demo_result = AnalysisResult.model_validate(result_dict)
    except Exception:
        raise HTTPException(status_code=503, detail="Demo result invalid")

    return demo_result.model_dump(exclude_none=True)


# ── Run directly ──
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=settings.PORT,
        reload=False,
        log_level=settings.LOG_LEVEL.lower(),
    )
