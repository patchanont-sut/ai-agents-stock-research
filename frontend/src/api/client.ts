// MarketMind AI Dashboard - API Client

const BASE_URL = '/api';

interface HealthResponse {
  status: string;
  service: string;
  version: string;
  translation_service_loaded: boolean;
  translation_service_file: string;
  backend_entrypoint_file: string;
  server_start_time: string;
  build_marker: string;
}

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
  startAnalysis: (symbol: string, forceRefresh = false, language: string = 'en') =>
    request<{ analysis_id: string; status: string; message: string }>('/analyze', {
      method: 'POST',
      body: JSON.stringify({ symbol, force_refresh: forceRefresh, language }),
    }),

  // Poll analysis status
  getStatus: (analysisId: string) =>
    request<{ analysis_id: string; status: string; symbol: string; completed_agents: string[] }>(
      `/analysis/${analysisId}/status`
    ),

  // Get full analysis result
  getAnalysisResult: (analysisId: string) =>
    request<import('../types').AnalysisResult>(`/analysis/${analysisId}/result`),

  // Get stock price standalone
  getPrice: (symbol: string) =>
    request<{ symbol: string; price: number | null }>(`/price/${symbol}`),

  // Get news standalone
  getNews: (symbol: string, limit = 10) =>
    request<{ symbol: string; articles: import('../types').Article[] }>(
      `/news/${symbol}?limit=${limit}`
    ),

  // Get macro data
  getMacro: () =>
    request<import('../types').MacroData>('/macro'),

  // Search stocks
  search: (query: string) =>
    request<{ query: string; results: any[] }>(`/search?q=${encodeURIComponent(query)}`),

  // Get agent trace
  getTrace: (analysisId: string) =>
    request<import('../types').AnalysisTrace>(`/analysis/${analysisId}/trace`),

  // Get evidence library and memo
  getEvidence: (analysisId: string) =>
    request<import('../types').EvidenceResponse>(`/analysis/${analysisId}/evidence`),

  // Health check
  health: () =>
    request<HealthResponse>('/health'),

  // ── Comparison Endpoints ──

  // Start a multi-stock comparison
  startCompare: (symbols: string[], language: string = 'en', forceRefresh = false) =>
    request<{ compare_id: string; symbols: string[]; status: string; message: string }>('/compare', {
      method: 'POST',
      body: JSON.stringify({ symbols, language, force_refresh: forceRefresh }),
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

  // Get AI quality evaluation for a comparison
  getCompareEvaluation: (compareId: string) =>
    request<import('../types').CompareEvaluationResponse>(`/evaluation/compare/${compareId}`),

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
