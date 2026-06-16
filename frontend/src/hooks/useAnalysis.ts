// MarketMind AI Dashboard — Analysis Hook
import { useState, useCallback, useEffect, useRef } from 'react';
import { api } from '../api/client';
import { AnalysisResult, AnalysisStatus, AnalysisTrace } from '../types';
import { Language } from '../i18n';

interface UseAnalysisReturn {
  analysisId: string | null;
  result: AnalysisResult | null;
  status: AnalysisStatus | null;
  error: string | null;
  isLoading: boolean;
  completedAgents: string[];
  trace: AnalysisTrace | null;
  startAnalysis: (symbol: string, language?: Language) => Promise<void>;
  loadDemo: () => Promise<void>;
  retry: (symbol: string, language?: Language) => void;
}

const POLL_INTERVAL_MS = 2000; // 2 seconds
const MAX_POLL_COUNT = 300;     // 10 minutes max

export function useAnalysis(): UseAnalysisReturn {
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [status, setStatus] = useState<AnalysisStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [completedAgents, setCompletedAgents] = useState<string[]>([]);
  const [trace, setTrace] = useState<AnalysisTrace | null>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const pollCountRef = useRef(0);

  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
    pollCountRef.current = 0;
  }, []);

  const fetchTrace = useCallback(async (id: string) => {
    try {
      const traceData = await api.getTrace(id);
      setTrace(traceData);
    } catch {
      // Trace endpoint may not be available yet — ignore silently during polling
    }
  }, []);

  const pollAnalysis = useCallback((id: string) => {
    stopPolling();

    pollingRef.current = setInterval(async () => {
      pollCountRef.current++;

      if (pollCountRef.current > MAX_POLL_COUNT) {
        stopPolling();
        setError('Analysis timed out after 10 minutes. The backend may still be processing.');
        setIsLoading(false);
        return;
      }

      try {
        const statusResp = await api.getStatus(id);
        setStatus(statusResp.status as AnalysisStatus);
        if (statusResp.completed_agents) {
          setCompletedAgents(statusResp.completed_agents);
        }

        // Fetch trace progressively while analysis is running
        fetchTrace(id);

        if (statusResp.status === 'complete' || statusResp.status === 'partial' || statusResp.status === 'failed') {
          stopPolling();
          setIsLoading(false);

          if (statusResp.status === 'complete' || statusResp.status === 'partial') {
            try {
              const fullResult = await api.getAnalysisResult(id);
              setResult(fullResult);
              setError(null);
            } catch (e: any) {
              setError(`Failed to fetch analysis result: ${e.message}`);
            }
          } else if (statusResp.status === 'failed') {
            // Try to fetch error details from result and trace endpoints
            let errorDetail = 'Analysis failed. The backend encountered errors.';
            try {
              const failedResult = await api.getAnalysisResult(id);
              if (failedResult && (failedResult as any).errors?.length) {
                errorDetail = (failedResult as any).errors.join('; ');
              }
            } catch {
              // result endpoint may not be available for failed analyses
            }
            try {
              const failedTrace = await api.getTrace(id);
              if (failedTrace && (failedTrace as any).errors?.length) {
                const traceErrors = (failedTrace as any).errors.join('; ');
                if (errorDetail.includes('The backend encountered errors')) {
                  errorDetail = traceErrors;
                } else {
                  errorDetail += ' | Trace: ' + traceErrors;
                }
              }
            } catch {
              // trace endpoint may also fail — ignore
            }
            setError(errorDetail);
          }

          // Final trace fetch after completion
          fetchTrace(id);
        }
      } catch (e: any) {
        stopPolling();
        setIsLoading(false);
        setError(`Polling error: ${e.message}`);
      }
    }, POLL_INTERVAL_MS);
  }, [stopPolling, fetchTrace]);

  const startAnalysis = useCallback(async (symbol: string, language: Language = 'en') => {
    stopPolling();
    setError(null);
    setResult(null);
    setTrace(null);
    setStatus('pending');
    setIsLoading(true);
    setCompletedAgents([]);

    try {
      const response = await api.startAnalysis(symbol, language);
      setAnalysisId(response.analysis_id);
      setStatus(response.status as AnalysisStatus);

      // Start polling for results
      pollAnalysis(response.analysis_id);
    } catch (e: any) {
      setIsLoading(false);
      setError(`Failed to start analysis: ${e.message}`);
    }
  }, [pollAnalysis, stopPolling]);

  const retry = useCallback((symbol: string, language: Language = 'en') => {
    if (symbol) {
      startAnalysis(symbol, language);
    }
  }, [startAnalysis]);

  const loadDemo = useCallback(async () => {
    stopPolling();
    setError(null);
    setResult(null);
    setTrace(null);
    setCompletedAgents([]);
    setIsLoading(true);
    setStatus('running');

    try {
      const demoResult = await api.getDemoAnalysis();
      setResult(demoResult);
      setStatus(demoResult.status as AnalysisStatus);
    } catch (e: any) {
      setStatus('failed');
      setError(`Failed to load demo: ${e.message}`);
    } finally {
      setIsLoading(false);
    }
  }, [stopPolling]);

  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, [stopPolling]);

  return {
    analysisId,
    result,
    status,
    error,
    isLoading,
    completedAgents,
    trace,
    startAnalysis,
    loadDemo,
    retry,
  };
}