# MarketMind AI Dashboard

**Multi-Agent Stock Analysis System** — an AI-powered investment research tool that simulates a team of specialized agents to analyze stocks, debate outcomes, and produce structured, transparent investment briefs.

Built as a portfolio project demonstrating production-grade AI agent orchestration, LLM function calling, observability, and bilingual (EN/TH) support.

---

## Architecture

```
User ──► React Frontend ──► FastAPI Backend
                                │
                    ┌───────────┼───────────┐
                    │   Orchestrator + Trace │
                    └───────────┼───────────┘
                                │
         ┌──────────────────────┼──────────────────────┐
         │          8 AI Agents + Memo Agent            │
         │  Research → Sentiment → Valuation → Bull →  │
         │  Bear → Risk → Debate → CIO → Memo          │
         └──────────────────────┼──────────────────────┘
                                │
                    ┌───────────┼───────────┐
                    │  DeepSeek LLM + Tools  │
                    │  Finnhub | Alpha Vantage│
                    │  Google News | Reddit   │
                    └─────────────────────────┘
```

## AI Agent Pipeline

The system runs 9 agents in sequence:

| # | Agent | Role | Output |
|---|-------|------|--------|
| 1 | **Research** | Fetches news, Reddit posts, price data, company profile, macro data | `ResearchOutput` |
| 2 | **Sentiment** | Analyzes news sentiment per article (-1 to +1) | `SentimentOutput` |
| 3 | **Valuation** | Evaluates P/E, PEG, P/B, market cap, sector comparison | `ValuationOutput` |
| 4 | **Bull** | Constructs bullish thesis with evidence and catalysts | `BullOutput` |
| 5 | **Bear** | Constructs bearish thesis with evidence and risk factors | `BearOutput` |
| 6 | **Risk** | Assesses macro, company, and volatility risk | `RiskOutput` |
| 7 | **Debate** | Runs structured bull-vs-bear debate (multi-turn) | `DebateOutput` |
| 8 | **CIO Decision** | Synthesizes all prior outputs into BUY/HOLD/SELL | `CIOOutput` |
| 9 | **Memo** | Generates citation-grounded investment research memo | `InvestmentMemo` |

## Grounded Research Memo

The Memo Agent introduces a new portfolio-grade feature that makes AI analysis more trustworthy:

### Evidence Library
After the CIO agent completes, the system builds a **structured evidence library** from all available data sources:
- News articles and Reddit posts (deduplicated by URL/title)
- Company profile data
- Valuation and fundamentals data
- Sentiment analysis, risk assessment, and CIO decision summaries

Each evidence item is assigned a deterministic, sequential ID (`E1`, `E2`, `E3`...) and stored with metadata including source type, title, snippet, key points, and URLs.

### Citation-Backed Memo
The Memo Agent generates a professional investment research memo that cites specific evidence IDs using `[E1]`, `[E2]` bracket notation. The memo includes:
- **Executive Summary** with citations
- **Decision Rationale** explaining the recommendation
- **Bull Case** and **Bear Case** with cited evidence
- **Key Risks** with supporting citations
- **What Would Change the View** scenarios

### Grounding Report
A deterministic grounding checker validates every citation in the memo:
- Detects citation patterns like `[E1]`, `[E2]`
- Verifies each cited evidence ID exists in the evidence library
- Flags missing citations, unknown evidence IDs, and weak token overlap
- Produces a **grounded score** (0–1) measuring how well the memo is supported by evidence

### Evidence Explorer UI
The frontend includes an **Evidence Explorer** panel with searchable/filterable evidence cards. Users can browse all evidence items by type (news, reddit, company profile, fundamentals, agent output) and inspect citations inline.

### Why This Matters for AI Engineering
- **RAG-style evidence construction**: Structured retrieval from mixed data sources
- **Citation grounding**: Every claim traced back to specific evidence
- **Hallucination risk reduction**: Deterministic validation of LLM-generated citations
- **Human-readable evidence explorer**: Non-technical users can verify AI claims
- **Deterministic grounding evaluation**: No LLM needed for validation

## Data Sources

| Source | What It Provides |
|--------|-----------------|
| **Finnhub** | Stock quotes, company profile, market indices, company news |
| **Alpha Vantage** | Company overview, Treasury yield, Fed funds rate |
| **Google News RSS** | News article headlines and snippets |
| **Reddit RSS** | Retail investor sentiment from trading subreddits |

## Explainability & Observability

### Agent Trace System
Every analysis produces a **structured trace** recording:
- Per-agent: name, status (pending → running → complete/failed), timestamps, duration
- Per-tool-call: tool name, arguments, timing, success/failure, compact result preview
- Errors and short human-readable summaries

### Evidence Reliability Scoring
Deterministic scoring (no LLM) that computes:
- **Source Diversity** (0–1)
- **Data Freshness** (0–1)
- **Completeness** (0–1)
- **Overall Reliability** (0–1): weighted average

### Evaluation Script
```bash
python scripts/evaluate_outputs.py --file result.json
python scripts/evaluate_outputs.py --api http://localhost:8001 --analysis-id <id>
```

## Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm

### Environment Variables
Copy `.env.example` to `.env` and configure your API keys (DeepSeek, Finnhub, Alpha Vantage).

### Install Dependencies

**Backend:**
```bash
pip install -r backend/requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

## Running

### Backend
```bash
python backend/main.py
```
Starts at `http://localhost:8001`.

### Frontend
```bash
cd frontend
npm run dev
```
Starts at `http://localhost:5173`.

### Tests
```bash
python -m pytest backend/tests/ -v
```

### Evaluation
```bash
python scripts/evaluate_outputs.py --file test_synthetic.json
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/analyze` | Start a new analysis |
| `GET` | `/api/analysis/{id}/status` | Poll analysis progress |
| `GET` | `/api/analysis/{id}/result` | Get full analysis result |
| `GET` | `/api/analysis/{id}/trace` | Get agent execution trace |
| `GET` | `/api/analysis/{id}/evidence` | Get evidence library and investment memo |
| `GET` | `/api/analysis/{id}/memo.md` | Export investment memo as Markdown |
| `GET` | `/api/evaluation/{analysis_id}` | Get AI quality evaluation metrics |
| `POST` | `/api/compare` | Start multi-stock comparison (2-4 symbols) |
| `GET` | `/api/compare/{id}/status` | Poll comparison progress |
| `GET` | `/api/compare/{id}/result` | Get comparison result with winner |
| `GET` | `/api/evaluation/compare/{compare_id}` | Get evaluation metrics for comparison |
| `GET` | `/api/price/{symbol}` | Get current stock price |
| `GET` | `/api/news/{symbol}` | Get recent news articles |
| `GET` | `/api/macro` | Get macro market data |
| `GET` | `/api/search?q=` | Search for stock symbols |

---

## Portfolio Upgrade: Comparative Research & AI Evaluation

This section documents the major portfolio upgrade that transforms MarketMind from a single-stock analysis tool into a **comparative research platform with AI quality evaluation**.

### 1. Stock Comparison Workflow

Compare 2-4 stocks side-by-side with AI-generated analysis for each.

**How it works:**
- Enter 2-4 ticker symbols in the "Compare Stocks" mode
- The backend runs the full 9-agent pipeline for each symbol **in parallel**
- A deterministic ranking algorithm synthesizes the winner based on:
  - CIO action (BUY > HOLD > SELL)
  - Confidence score
  - Evidence reliability score
  - Citation grounding score
  - Risk level
  - Sentiment score
- Partial results are returned if some symbols fail (graceful degradation)

### 2. AI Quality Evaluation Dashboard

Deterministic evaluation metrics that demonstrate AI Engineering rigor — **no LLM calls needed for evaluation**.

**Metrics computed:**
- **Citation Validity Rate** — % of memo citations that reference valid evidence
- **Grounding Score** — how well memo claims are backed by evidence
- **Evidence Count** — total evidence items in the library
- **Source Diversity** — variety of evidence source types (news, Reddit, fundamentals, etc.)
- **Agent Completion Rate** — % of 9 agents that completed successfully
- **Memo Completeness** — structural completeness of the investment memo
- **Missing Required Fields** — specific fields that failed validation
- **Overall Quality Score** — weighted composite

### 3. Markdown Memo Export

Export any investment memo as a downloadable `.md` file with title, recommendation, executive summary, analysis sections, citations, grounding report, and evidence appendix.

### Why These Matter for AI Engineering

| Feature | AI Engineering Signal |
|---------|----------------------|
| **Parallel comparison** | Async orchestration, concurrent pipeline execution, graceful error handling |
| **Deterministic ranking** | Algorithmic synthesis without extra LLM calls — cost-efficient and testable |
| **Evaluation metrics** | Quality measurement systems, not just generation systems |
| **Memo export** | End-to-end data pipeline: research → analysis → memo → portable format |
| **Partial results** | Production-grade error handling — never fail completely when some data is available |
| **No new LLM calls** | All new features are deterministic — fast, free, and testable |

## Internationalization

Supports **English** and **Thai**. Language toggle in header switches all UI text.

## Portfolio Talking Points

- **Multi-Agent Orchestration**: 9 specialized agents with shared memory and graceful error handling
- **LLM Function Calling**: Agents invoke data retrieval tools via DeepSeek API
- **RAG-Style Evidence Construction**: Structured evidence library from mixed data sources
- **Citation Grounding**: Memo claims traced to specific evidence with deterministic validation
- **Hallucination Risk Reduction**: Unknown citations flagged; fallback memo when AI generation fails
- **Observability & Transparency**: Structured trace system with per-agent timing and tool calls
- **Deterministic Quality Scoring**: Evidence reliability and grounding computed without LLM
- **Bilingual Production Pattern**: Translation service with English fallback
- **Evaluation Framework**: Standalone CLI with structural checks and CI-friendly exit codes
- **Type-Safe Frontend**: React + TypeScript matching backend Pydantic models
- **API-First Design**: Clean REST API with status polling and progressive trace endpoint

---

Built with DeepSeek, FastAPI, React, and TypeScript. Not financial advice.