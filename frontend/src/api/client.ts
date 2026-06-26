// MarketMind AI Dashboard - API Client

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${url}`, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`HTTP ${response.status}: ${errorBody}`);
  }

  return response.json();
}

export const api = {
  // Start a new analysis
  startAnalysis: (symbol: string, language: string = 'en') =>
    request<{ analysis_id: string; status: string; message: string }>('/analyze', {
      method: 'POST',
      body: JSON.stringify({ symbol, language }),
    }),

  // Poll analysis status
  getStatus: (analysisId: string) =>
    request<{ analysis_id: string; status: string; symbol: string; completed_agents: string[] }>(
      `/analysis/${analysisId}/status`
    ),

  // Get full analysis result
  getAnalysisResult: (analysisId: string) =>
    request<import('../types').AnalysisResult>(`/analysis/${analysisId}/result`),

  // Get agent trace
  getTrace: (analysisId: string) =>
    request<import('../types').AnalysisTrace>(`/analysis/${analysisId}/trace`),

  // Demo: load synthetic analysis result (no API keys needed)
  getDemoAnalysis: () =>
    request<import('../types').AnalysisResult>('/demo/analysis'),

  // ── Live Monitor Endpoints ──

  // Get current stock price
  getPrice: (symbol: string) =>
    request<{
      symbol: string;
      price: number | null;
      change: number | null;
      change_percent: number | null;
      source?: string;
      error?: string;
    }>(`/price/${symbol}`),

  // Get recent news articles for a stock
  getNews: (symbol: string, limit: number = 5) =>
    request<{
      symbol: string;
      articles: {
        title: string;
        url: string;
        source?: string;
        datetime?: string;
      }[];
      source?: string;
    }>(`/news/${symbol}?limit=${limit}`),

  // ── Comparison Endpoints ──

  // Start a multi-stock comparison
  startCompare: (symbols: string[], language: string = 'en') =>
    request<{ compare_id: string; symbols: string[]; status: string; message: string }>('/compare', {
      method: 'POST',
      body: JSON.stringify({ symbols, language }),
    }),

  // Get comparison status
  getCompareStatus: (compareId: string) =>
    request<import('../types').CompareStatusResponse>(`/compare/${compareId}/status`),

  // Get comparison result
  getCompareResult: (compareId: string) =>
    request<import('../types').CompareResult>(`/compare/${compareId}/result`),

  // ── Evaluation Endpoints ──

  // Get AI quality evaluation for a single analysis
  getEvaluation: (analysisId: string) =>
    request<import('../types').EvaluationMetrics>(`/evaluation/${analysisId}`),

  // ── Memo Export ──

  // Download memo as Markdown (returns text, not JSON)
  downloadMemoMarkdown: async (analysisId: string): Promise<string> => {
    const response = await fetch(`${BASE_URL}/analysis/${analysisId}/memo.md`);
    if (!response.ok) {
      const errorBody = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorBody}`);
    }
    return response.text();
  },
};
