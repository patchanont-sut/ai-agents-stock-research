"""
MarketMind AI Dashboard - Pydantic Data Models
Defines all data structures for the analysis pipeline.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

_SYMBOL_ALIASES = {
    "NASDAQ": "QQQ",
    "S&P500": "SPY",
    "S&P 500": "SPY",
    "SP500": "SPY",
}


def canonicalize_symbol(symbol: str) -> str:
    stripped = " ".join(symbol.strip().upper().split())
    return _SYMBOL_ALIASES.get(stripped, stripped)


# ── Enums ──

class SentimentLabel(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class CIOAction(str, Enum):
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"


class RiskLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    PARTIAL = "partial"  # some agents failed, others succeeded


# ── News / Article ──

class Article(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    url: str
    source: str  # e.g. "Google News", "Finnhub", "Reddit"
    published_at: Optional[datetime] = None
    snippet: str = ""
    sentiment_score: Optional[float] = None  # -1 to +1, set by sentiment agent


# ── Agent Output Models ──

class ResearchOutput(BaseModel):
    news_articles: list[Article] = []
    reddit_posts: list[Article] = []
    company_profile: str = ""
    company_profile_th: str = ""
    summary: str = ""  # LLM-generated summary
    summary_th: str = ""
    data_quality: str = "unknown"  # "good", "partial", "poor", or "unknown"
    data_issues: list[str] = []
    news_count: int = 0
    reddit_count: int = 0
    sources: list[str] = []
    price_source: str = ""
    fundamentals_source: str = ""
    macro_source: str = ""
    fetched_at: Optional[datetime] = None


class SentimentOutput(BaseModel):
    overall_score: float = 0.0  # -1 to +1
    label: SentimentLabel = SentimentLabel.NEUTRAL
    article_scores: list[dict] = []  # {article_id, score, explanation}
    explanation: str = ""
    explanation_th: str = ""


class BullOutput(BaseModel):
    thesis: str = ""
    thesis_th: str = ""
    evidence: list[str] = []
    evidence_th: list[str] = []
    catalysts: list[str] = []
    catalysts_th: list[str] = []
    confidence: float = 0.0  # 0 to 1


class BearOutput(BaseModel):
    thesis: str = ""
    thesis_th: str = ""
    evidence: list[str] = []
    evidence_th: list[str] = []
    risk_factors: list[str] = []
    risk_factors_th: list[str] = []
    confidence: float = 0.0  # 0 to 1


class RiskOutput(BaseModel):
    macro_risk: RiskLevel = RiskLevel.MEDIUM
    company_risk: RiskLevel = RiskLevel.MEDIUM
    volatility_risk: RiskLevel = RiskLevel.MEDIUM
    macro_factors: list[str] = []
    macro_factors_th: list[str] = []
    company_factors: list[str] = []
    company_factors_th: list[str] = []
    summary: str = ""
    summary_th: str = ""


class ValuationOutput(BaseModel):
    pe_ratio: Optional[float] = None
    sector_avg_pe: Optional[float] = None
    peg_ratio: Optional[float] = None
    price_to_book: Optional[float] = None
    market_cap: Optional[str] = None
    revenue_growth: Optional[float] = None
    sector: str = ""
    peers: list[str] = []
    verdict: str = ""
    verdict_th: str = ""
    explanation: str = ""
    explanation_th: str = ""


class DebateTurn(BaseModel):
    side: str  # "bull" or "bear"
    content: str
    content_th: str = ""


class DebateOutput(BaseModel):
    turns: list[DebateTurn] = []
    winning_side: str = ""  # "bull", "bear", or "tie"
    summary: str = ""
    summary_th: str = ""


class CIOOutput(BaseModel):
    action: CIOAction = CIOAction.HOLD
    reasoning: str = ""
    reasoning_th: str = ""
    confidence: float = 0.0
    risk_level: RiskLevel = RiskLevel.MEDIUM
    key_points: list[str] = []
    key_points_th: list[str] = []
    time_horizon: str = "6-12 months"


# ── Evidence Quality ──

class EvidenceQuality(BaseModel):
    """Deterministic evidence quality and reliability scoring output."""
    source_count: int = 0
    evidence_item_count: int = 0
    news_count: int = 0
    reddit_count: int = 0
    data_quality: str = "unknown"
    source_diversity_score: float = 0.0
    freshness_score: float = 0.0
    completeness_score: float = 0.0
    overall_reliability_score: float = 0.0
    warnings: list[str] = Field(default_factory=list)


# ── Citation-Grounded Research Memo Models ──

class EvidenceItem(BaseModel):
    """A single piece of structured evidence in the evidence library."""
    id: str  # e.g. "E1", "E2"
    source_type: str  # "news", "reddit", "company_profile", "fundamentals", "macro", "agent_output"
    title: str
    source: str
    url: Optional[str] = None
    published_at: Optional[datetime] = None
    snippet: str = ""
    key_points: list[str] = Field(default_factory=list)
    sentiment_score: Optional[float] = None
    reliability_notes: list[str] = Field(default_factory=list)


class CitationRef(BaseModel):
    """A citation reference to an evidence item."""
    evidence_id: str
    quote_or_summary: str
    quote_or_summary_th: str = ""


class MemoSection(BaseModel):
    """A section within the investment memo."""
    heading: str
    heading_th: str = ""
    content: str
    content_th: str = ""
    citations: list[CitationRef] = Field(default_factory=list)


class GroundingIssue(BaseModel):
    """A specific grounding issue detected in the memo."""
    claim: str
    issue_type: str  # "missing_citation", "unknown_evidence_id", "weak_overlap"
    detail: str


class GroundingReport(BaseModel):
    """Report on how well the memo is grounded in evidence."""
    claim_count: int = 0
    cited_claim_count: int = 0
    valid_citation_count: int = 0
    invalid_citation_count: int = 0
    grounded_score: float = 0.0  # 0 to 1
    issues: list[GroundingIssue] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class InvestmentMemo(BaseModel):
    """Citation-grounded investment research memo."""
    title: str = ""
    title_th: str = ""
    executive_summary: str = ""
    executive_summary_th: str = ""
    recommendation: str = ""
    recommendation_th: str = ""
    sections: list[MemoSection] = Field(default_factory=list)
    key_citations: list[CitationRef] = Field(default_factory=list)
    grounding_report: Optional["GroundingReport"] = None


# ── Full Analysis Result ──

class StockInfo(BaseModel):
    symbol: str
    name: str = ""
    price: Optional[float] = None
    change_percent: Optional[float] = None
    currency: str = "USD"
    exchange: str = ""


class AnalysisResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    symbol: str
    status: AnalysisStatus = AnalysisStatus.PENDING
    stock: StockInfo = StockInfo(symbol="")
    research: Optional[ResearchOutput] = None
    sentiment: Optional[SentimentOutput] = None
    bull_case: Optional[BullOutput] = None
    bear_case: Optional[BearOutput] = None
    risk: Optional[RiskOutput] = None
    valuation: Optional[ValuationOutput] = None
    debate: Optional[DebateOutput] = None
    cio_decision: Optional[CIOOutput] = None
    cached: bool = False
    stale: bool = False
    errors: list[str] = []
    generated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    evidence_quality: Optional[EvidenceQuality] = None
    evidence_library: Optional[list[EvidenceItem]] = None
    investment_memo: Optional[InvestmentMemo] = None


# ── API Request / Response ──

class AnalyzeRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=12, description="Stock ticker symbol (e.g. AAPL)")
    language: str = Field(
        default="en",
        pattern=r"^(en|th)$",
        description="Response language: 'en' or 'th'",
    )

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, symbol: str) -> str:
        canonical = canonicalize_symbol(symbol)
        if len(canonical) > 12 or not canonical:
            raise ValueError("Symbol must be 1-12 characters.")
        allowed_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.-"
        if not canonical[0].isalpha() or any(ch not in allowed_chars for ch in canonical):
            raise ValueError(
                "Symbol may contain only letters, numbers, dots, and hyphens, and must start with a letter."
            )
        return canonical


class AnalyzeResponse(BaseModel):
    analysis_id: str
    status: AnalysisStatus
    message: str = ""


class MacroData(BaseModel):
    sp500_change: Optional[float] = None
    nasdaq_change: Optional[float] = None
    vix: Optional[float] = None
    treasury_10y: Optional[float] = None
    fed_funds_rate: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# ── Comparison Models ──

class CompareRequest(BaseModel):
    """Request to compare multiple stocks side-by-side."""
    symbols: list[str] = Field(..., min_length=2, max_length=4, description="Stock ticker symbols (2-4)")
    language: str = Field(
        default="en",
        pattern=r"^(en|th)$",
        description="Response language: 'en' or 'th'",
    )

    @field_validator("symbols")
    @classmethod
    def validate_symbols(cls, symbols: list[str]) -> list[str]:
        normalized: list[str] = []
        for symbol in symbols:
            if not isinstance(symbol, str):
                raise ValueError("Symbols must be strings.")
            canonical = canonicalize_symbol(symbol)
            if len(canonical) > 12 or not canonical:
                raise ValueError("Symbols must be 1-12 characters.")
            allowed_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.-"
            if not canonical[0].isalpha() or any(
                ch not in allowed_chars for ch in canonical
            ):
                raise ValueError(
                    "Symbols may contain only letters, numbers, dots, and hyphens, and must start with a letter."
                )
            normalized.append(canonical)
        return normalized


class CompareStockSummary(BaseModel):
    """Concise summary of a single stock within a comparison."""
    symbol: str
    company_name: str = ""
    cio_action: str = ""
    confidence: float = 0.0
    risk_level: str = ""
    sentiment_score: float = 0.0
    valuation_verdict: str = ""
    reliability_score: float = 0.0
    grounding_score: float = 0.0
    top_bull_points: list[str] = Field(default_factory=list)
    top_bear_points: list[str] = Field(default_factory=list)
    key_risks: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class CompareResult(BaseModel):
    """Final result of a multi-stock comparison."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    symbols: list[str] = Field(default_factory=list)
    status: AnalysisStatus = AnalysisStatus.PENDING
    generated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    summaries: list[CompareStockSummary] = Field(default_factory=list)
    winner_symbol: str = ""
    ranking_rationale: str = ""
    comparison_table: list[dict] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


# ── Evaluation Models ──

class EvaluationMetrics(BaseModel):
    """Structured AI quality metrics for a completed analysis."""
    analysis_id: str
    symbol: str
    citation_validity_rate: float = 0.0
    grounding_score: float = 0.0
    evidence_count: int = 0
    source_diversity_score: float = 0.0
    agent_completion_rate: float = 0.0
    memo_completeness: float = 0.0
    missing_required_fields: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    overall_quality_score: float = 0.0
