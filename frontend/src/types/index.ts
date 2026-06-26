// MarketMind AI Dashboard - TypeScript Types

export type SentimentLabel = 'positive' | 'negative' | 'neutral';
export type CIOAction = 'BUY' | 'HOLD' | 'SELL';
export type RiskLevel = 'Low' | 'Medium' | 'High';
export type AnalysisStatus = 'pending' | 'running' | 'complete' | 'failed' | 'partial';

export interface Article {
  id: string;
  title: string;
  url: string;
  source: string;
  published_at: string | null;
  snippet: string;
  sentiment_score: number | null;
}

export interface StockInfo {
  symbol: string;
  name: string;
  price: number | null;
  change_percent: number | null;
  currency: string;
  exchange: string;
}

export interface ResearchOutput {
  news_articles: Article[];
  reddit_posts: Article[];
  company_profile: string;
  company_profile_th: string;
  summary: string;
  summary_th: string;
  data_quality?: 'good' | 'partial' | 'poor' | 'unknown' | string;
  data_issues?: string[];
  news_count?: number;
  reddit_count?: number;
  sources?: string[];
  price_source?: string;
  fundamentals_source?: string;
  macro_source?: string;
  fetched_at?: string | null;
}

export interface SentimentOutput {
  overall_score: number;
  label: SentimentLabel;
  article_scores: { article_id: string; score: number; explanation: string }[];
  explanation: string;
  explanation_th: string;
}

export interface BullOutput {
  thesis: string;
  thesis_th: string;
  evidence: string[];
  evidence_th: string[];
  catalysts: string[];
  catalysts_th: string[];
  confidence: number;
}

export interface BearOutput {
  thesis: string;
  thesis_th: string;
  evidence: string[];
  evidence_th: string[];
  risk_factors: string[];
  risk_factors_th: string[];
  confidence: number;
}

export interface RiskOutput {
  macro_risk: RiskLevel;
  company_risk: RiskLevel;
  volatility_risk: RiskLevel;
  macro_factors: string[];
  macro_factors_th: string[];
  company_factors: string[];
  company_factors_th: string[];
  summary: string;
  summary_th: string;
}

export interface ValuationOutput {
  pe_ratio: number | null;
  sector_avg_pe: number | null;
  peg_ratio: number | null;
  price_to_book: number | null;
  market_cap: string | null;
  revenue_growth: number | null;
  sector: string;
  peers: string[];
  verdict: string;
  verdict_th: string;
  explanation: string;
  explanation_th: string;
}

export interface DebateTurn {
  side: 'bull' | 'bear';
  content: string;
  content_th: string;
}

export interface DebateOutput {
  turns: DebateTurn[];
  winning_side: string;
  summary: string;
  summary_th: string;
}

export interface CIOOutput {
  action: CIOAction;
  reasoning: string;
  reasoning_th: string;
  confidence: number;
  risk_level: RiskLevel;
  key_points: string[];
  key_points_th: string[];
  time_horizon: string;
}

export interface EvidenceQuality {
  source_count: number;
  evidence_item_count: number;
  news_count: number;
  reddit_count: number;
  data_quality: string;
  source_diversity_score: number;
  freshness_score: number;
  completeness_score: number;
  overall_reliability_score: number;
  warnings: string[];
}

// ── Citation-Grounded Research Memo Types ──

export interface EvidenceItem {
  id: string;
  source_type: string;
  title: string;
  source: string;
  url: string | null;
  published_at: string | null;
  snippet: string;
  key_points: string[];
  sentiment_score: number | null;
  reliability_notes: string[];
}

export interface CitationRef {
  evidence_id: string;
  quote_or_summary: string;
  quote_or_summary_th?: string;
}

export interface MemoSection {
  heading: string;
  heading_th?: string;
  content: string;
  content_th?: string;
  citations: CitationRef[];
}

export interface GroundingIssue {
  claim: string;
  issue_type: string;
  detail: string;
}

export interface GroundingReport {
  claim_count: number;
  cited_claim_count: number;
  valid_citation_count: number;
  invalid_citation_count: number;
  grounded_score: number;
  issues: GroundingIssue[];
  warnings: string[];
}

export interface InvestmentMemo {
  title: string;
  title_th?: string;
  executive_summary: string;
  executive_summary_th?: string;
  recommendation: string;
  recommendation_th?: string;
  sections: MemoSection[];
  key_citations: CitationRef[];
  grounding_report?: GroundingReport | null;
}

// ── Trace Types ──

export interface ToolCallTrace {
  tool_name: string;
  arguments: Record<string, unknown>;
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number;
  success: boolean;
  error: string | null;
  compact_result_preview: string;
}

export interface AgentTraceEntry {
  agent_name: string;
  status: 'pending' | 'running' | 'complete' | 'failed';
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number;
  tool_calls: ToolCallTrace[];
  errors: string[];
  short_summary: string;
}

export interface AnalysisTrace {
  analysis_id: string;
  symbol: string;
  started_at: string | null;
  completed_at: string | null;
  agents: AgentTraceEntry[];
}

export interface AnalysisResult {
  id: string;
  symbol: string;
  status: AnalysisStatus;
  stock: StockInfo;
  research: ResearchOutput | null;
  sentiment: SentimentOutput | null;
  bull_case: BullOutput | null;
  bear_case: BearOutput | null;
  risk: RiskOutput | null;
  valuation: ValuationOutput | null;
  debate: DebateOutput | null;
  cio_decision: CIOOutput | null;
  cached: boolean;
  stale: boolean;
  errors: string[];
  generated_at: string | null;
  completed_at: string | null;
  evidence_quality?: EvidenceQuality | null;
  evidence_library?: EvidenceItem[] | null;
  investment_memo?: InvestmentMemo | null;
}

// ── Comparison & Evaluation Types ──

export interface CompareStockSummary {
  symbol: string;
  company_name: string;
  cio_action: string;
  confidence: number;
  risk_level: string;
  sentiment_score: number;
  valuation_verdict: string;
  reliability_score: number;
  grounding_score: number;
  top_bull_points: string[];
  top_bear_points: string[];
  key_risks: string[];
  errors: string[];
}

export interface CompareResult {
  id: string;
  symbols: string[];
  status: AnalysisStatus;
  generated_at: string | null;
  completed_at: string | null;
  summaries: CompareStockSummary[];
  winner_symbol: string;
  ranking_rationale: string;
  comparison_table: Record<string, unknown>[];
  errors: string[];
}

export interface CompareStatusResponse {
  compare_id: string;
  status: AnalysisStatus;
  symbols: string[];
  completed_symbols: string[];
  symbol_progress: Record<string, string[]>;
}

export interface EvaluationMetrics {
  analysis_id: string;
  symbol: string;
  citation_validity_rate: number;
  grounding_score: number;
  evidence_count: number;
  source_diversity_score: number;
  agent_completion_rate: number;
  memo_completeness: number;
  missing_required_fields: string[];
  warnings: string[];
  overall_quality_score: number;
}

