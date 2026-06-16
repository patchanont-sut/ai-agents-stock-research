// MarketMind AI Dashboard — Stock Comparison Panel
import React, { useState, useCallback, useEffect, useRef } from 'react';
import { t } from '../i18n';
import { api } from '../api/client';
import type { CompareResult, CompareStockSummary, CompareStatusResponse } from '../types';

interface Props {
  lang: string;
}

function SummaryCard({ summary, isWinner }: { summary: CompareStockSummary; isWinner: boolean }) {
  const actionClass = summary.cio_action === 'BUY' ? 'action-buy' : summary.cio_action === 'SELL' ? 'action-sell' : 'action-hold';
  return (
    <div className={`compare-summary-card ${isWinner ? 'winner' : ''}`}>
      {isWinner && <div className="winner-badge">{t('winnerCard')}</div>}
      <div className="compare-summary-header">
        <span className="compare-symbol">{summary.symbol}</span>
        {summary.company_name && <span className="compare-company">{summary.company_name}</span>}
      </div>
      <div className="compare-summary-action">
        <span className={`action-badge ${actionClass}`}>{summary.cio_action || t('compareNa')}</span>
        <span className="action-confidence">{summary.confidence > 0 ? `${(summary.confidence * 100).toFixed(0)}%` : ''}</span>
      </div>
      <div className="compare-metrics-row">
        <div className="compare-metric">
          <span className="compare-metric-label">{t('compareRiskLabel')}</span>
          <span className={`compare-metric-value risk-${summary.risk_level?.toLowerCase()}`}>{summary.risk_level || t('compareNa')}</span>
        </div>
        <div className="compare-metric">
          <span className="compare-metric-label">{t('compareSentimentLabel')}</span>
          <span className="compare-metric-value">{summary.sentiment_score != null ? summary.sentiment_score.toFixed(2) : t('compareNa')}</span>
        </div>
        <div className="compare-metric">
          <span className="compare-metric-label">{t('compareReliabilityLabel')}</span>
          <span className="compare-metric-value">{(summary.reliability_score * 100).toFixed(0)}%</span>
        </div>
        <div className="compare-metric">
          <span className="compare-metric-label">{t('compareGroundingLabel')}</span>
          <span className="compare-metric-value">{(summary.grounding_score * 100).toFixed(0)}%</span>
        </div>
      </div>
      {summary.valuation_verdict && (
        <div className="compare-valuation">
          <span className="compare-metric-label">{t('compareValuation')}</span>: {summary.valuation_verdict}
        </div>
      )}
      {summary.top_bull_points.length > 0 && (
        <div className="compare-points bull">
          <div className="compare-points-title">{t('compareBullPoints')}</div>
          <ul>
            {summary.top_bull_points.map((p, i) => <li key={i}>{p}</li>)}
          </ul>
        </div>
      )}
      {summary.top_bear_points.length > 0 && (
        <div className="compare-points bear">
          <div className="compare-points-title">{t('compareBearPoints')}</div>
          <ul>
            {summary.top_bear_points.map((p, i) => <li key={i}>{p}</li>)}
          </ul>
        </div>
      )}
      {summary.errors.length > 0 && (
        <div className="compare-errors">
          {summary.errors.map((e, i) => <div key={i} className="compare-error">{t('compareWarning')}: {e}</div>)}
        </div>
      )}
    </div>
  );
}

const POLL_INTERVAL_MS = 2000;
const MAX_POLL_ATTEMPTS = 150; // 5 minutes at 2s intervals

export function ComparisonPanel({ lang }: Props) {
  const [symbols, setSymbols] = useState<string[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [compareId, setCompareId] = useState<string | null>(null);
  const [result, setResult] = useState<CompareResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<'input' | 'loading' | 'result' | 'loading-timeout'>('input');
  const [symbolProgress, setSymbolProgress] = useState<Record<string, string[]>>({});
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const cleanupPoll = useCallback(() => {
    if (pollRef.current !== null) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  useEffect(() => {
    return cleanupPoll;
  }, [cleanupPoll]);

  // Parse comma-separated input into symbols
  const parsePasteInput = useCallback((raw: string): string[] => {
    const parts = raw.split(/,+/).map(s => s.trim().toUpperCase()).filter(Boolean);
    const uniq: string[] = [];
    for (const p of parts) {
      if (!uniq.includes(p)) uniq.push(p);
    }
    return uniq.slice(0, 4); // max 4
  }, []);

  const handleAddSymbol = useCallback(() => {
    const s = inputValue.trim().toUpperCase();
    if (!s) return;

    // Check for comma-separated paste
    if (s.includes(',')) {
      const parsed = parsePasteInput(s);
      if (parsed.length >= 1) {
        setSymbols(prev => {
          const merged = [...prev];
          for (const p of parsed) {
            if (!merged.includes(p) && merged.length < 4) {
              merged.push(p);
            }
          }
          return merged;
        });
        setInputValue('');
        return;
      }
    }

    if (!symbols.includes(s) && symbols.length < 4) {
      setSymbols([...symbols, s]);
      setInputValue('');
    }
  }, [inputValue, symbols, parsePasteInput]);

  const handleRemoveSymbol = useCallback((sym: string) => {
    setSymbols(symbols.filter(s => s !== sym));
  }, [symbols]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddSymbol();
    }
  }, [handleAddSymbol]);

  // Handle paste event on the input for comma-separated values
  const handlePaste = useCallback((e: React.ClipboardEvent<HTMLInputElement>) => {
    const pasted = e.clipboardData.getData('text');
    if (pasted && (pasted.includes(',') || pasted.includes('\n'))) {
      // Check if it looks like a comma/newline separated list
      const parsed = parsePasteInput(pasted);
      if (parsed.length >= 2) {
        e.preventDefault();
        setSymbols(prev => {
          const merged = [...prev];
          for (const p of parsed) {
            if (!merged.includes(p) && merged.length < 4) {
              merged.push(p);
            }
          }
          return merged;
        });
      }
    }
  }, [parsePasteInput]);

  const handleCheckAgain = useCallback(async () => {
    if (!compareId) return;
    setLoading(true);
    setError(null);
    setMode('loading');
    setSymbolProgress({});
    startPolling(compareId);
  }, [compareId]);

  const startPolling = useCallback((id: string) => {
    cleanupPoll();
    let attempts = 0;

    pollRef.current = setInterval(async () => {
      attempts++;
      try {
        const status: CompareStatusResponse = await api.getCompareStatus(id);
        setSymbolProgress(status.symbol_progress || {});

        const finalStatuses = new Set(['complete', 'partial', 'failed']);
        if (finalStatuses.has(status.status)) {
          cleanupPoll();
          try {
            const compResult = await api.getCompareResult(id);
            setResult(compResult);
            setMode('result');
            setLoading(false);
          } catch (e) {
            setError((e as Error).message);
            setMode('input');
            setLoading(false);
          }
          return;
        }

        if (attempts >= MAX_POLL_ATTEMPTS) {
          cleanupPoll();
          setError(t('compareTimeoutMessage'));
          setMode('loading-timeout');
          setLoading(false);
        }
      } catch (e) {
        const msg = (e as Error).message || '';
        if (msg.includes('404')) {
          cleanupPoll();
          setError(t('compareTimedOut') + ': ' + msg);
          setMode('input');
          setLoading(false);
        }
        if (attempts >= MAX_POLL_ATTEMPTS) {
          cleanupPoll();
          setError((e as Error).message);
          setMode('input');
          setLoading(false);
        }
      }
    }, POLL_INTERVAL_MS);
  }, [cleanupPoll]);

  const handleCompare = useCallback(async () => {
    if (symbols.length < 2) return;
    cleanupPoll();
    setLoading(true);
    setError(null);
    setMode('loading');
    setSymbolProgress({});
    try {
      const startRes = await api.startCompare(symbols, lang);
      const id = startRes.compare_id;
      setCompareId(id);
      startPolling(id);
    } catch (e) {
      setError((e as Error).message);
      setMode('input');
      setLoading(false);
    }
  }, [symbols, lang, startPolling, cleanupPoll]);

  const handleReset = useCallback(() => {
    cleanupPoll();
    setMode('input');
    setResult(null);
    setCompareId(null);
    setSymbolProgress({});
    setError(null);
  }, [cleanupPoll]);

  // Compute progress bar stats
  const doneCount = Object.entries(symbolProgress).filter(([, info]) => {
    const status = info.length > 1 ? info[1] : '';
    return status === 'complete' || status === 'partial';
  }).length;
  const totalCount = symbols.length;
  const progressPct = totalCount > 0 ? Math.round((doneCount / totalCount) * 100) : 0;

  if (mode === 'result' && result) {
    const hasWinner: boolean = !!(result.winner_symbol && result.winner_symbol !== '');

    return (
      <div className="compare-result-container animate-fade-in" role="region" aria-label={t('comparisonTable')}>
        <div className="compare-header-bar">
          <button className="btn-back" onClick={handleReset}>
            ← {t('compareNewComparison')}
          </button>
          <h2 className="compare-title">{t('comparisonTable')}</h2>
        </div>

        {/* Winner card — only if there is a valid winner */}
        {hasWinner ? (
          <div className="card compare-winner-card">
            <div className="card-title">🏆 {t('winnerCard')}: {result.winner_symbol}</div>
            <p className="compare-rationale">{result.ranking_rationale}</p>
          </div>
        ) : (
          <div className="compare-no-winner">
            <h3>{t('winnerCard')}</h3>
            <p>{t('compareNoWinner')}</p>
            {result.ranking_rationale && <p className="compare-rationale">{result.ranking_rationale}</p>}
          </div>
        )}

        {/* Comparison table */}
        {result.comparison_table.length > 0 && (
          <div className="card compare-table-card">
            <div className="card-title">{t('comparisonTable')}</div>
            <div className="compare-table-wrap">
              <table className="compare-table" aria-label={t('comparisonTable')}>
                <caption className="sr-only">{t('comparisonTable')} — {result.summaries.map(s => s.symbol).join(', ')}</caption>
                <thead>
                  <tr>
                    <th>{t('compareTableSymbol')}</th>
                    <th>{t('compareTableAction')}</th>
                    <th>{t('compareTableConfidence')}</th>
                    <th>{t('compareRiskLabel')}</th>
                    <th>{t('compareSentimentLabel')}</th>
                    <th>{t('compareReliabilityLabel')}</th>
                    <th>{t('compareGroundingLabel')}</th>
                  </tr>
                </thead>
                <tbody>
                  {result.summaries.map(s => (
                    <tr key={s.symbol} className={s.symbol === result.winner_symbol ? 'winner-row' : ''}>
                      <td><strong>{s.symbol}</strong></td>
                      <td><span className={`action-badge action-${s.cio_action?.toLowerCase() || 'hold'}`}>{s.cio_action || t('compareNa')}</span></td>
                      <td>{s.confidence > 0 ? `${(s.confidence * 100).toFixed(0)}%` : '-'}</td>
                      <td><span className={`risk-badge risk-${s.risk_level?.toLowerCase() || 'medium'}`}>{s.risk_level || t('compareNa')}</span></td>
                      <td>{s.sentiment_score != null ? s.sentiment_score.toFixed(2) : '-'}</td>
                      <td>{(s.reliability_score * 100).toFixed(0)}%</td>
                      <td>{(s.grounding_score * 100).toFixed(0)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Individual summary cards */}
        <div className="compare-summaries-grid">
          {result.summaries.map(s => (
            <SummaryCard key={s.symbol} summary={s} isWinner={hasWinner && s.symbol === result.winner_symbol} />
          ))}
        </div>

        {/* Errors */}
        {result.errors.length > 0 && (
          <div className="card card-warnings">
            <div className="card-title">{t('compareErrorsTitle')}</div>
            <ul className="warnings-list">
              {result.errors.map((e, i) => <li key={i}>{e}</li>)}
            </ul>
          </div>
        )}
      </div>
    );
  }

  if (mode === 'loading-timeout') {
    return (
      <div className="compare-input-container">
        <div className="card">
          <div className="card-title">{t('compareTimedOut')}</div>
          <p className="muted-text">{t('compareStillRunning')}</p>
          <button className="search-btn compare-start-btn" onClick={handleCheckAgain}>
            {t('compareCheckAgain')}
          </button>
          <button className="btn-back" onClick={handleReset} style={{ marginLeft: '0.5rem' }}>
            ← {t('compareNewComparison')}
          </button>
          {error && <p className="error-text">{error}</p>}
        </div>
      </div>
    );
  }

  return (
    <div className="compare-input-container animate-fade-in">
      <div className="card">
        <div className="card-title">{t('compareMode')}</div>
        <p className="muted-text compare-intro-desc">{t('compareEmptyDesc')}</p>
        <p className="compare-intro-hint">{t('compareEmptyHint')}</p>

        {/* Symbol chips */}
        <div className="symbol-chips">
          {symbols.map(sym => (
            <span key={sym} className="symbol-chip">
              {sym}
              <button
                onClick={() => handleRemoveSymbol(sym)}
                className="chip-remove"
                disabled={loading}
                aria-label={t('compareRemoveLabel', { symbol: sym })}
              >
                ×
              </button>
            </span>
          ))}
        </div>

        {/* Input */}
        <div className="symbol-input-row">
          <input
            type="text"
            className="search-input"
            placeholder="AAPL, MSFT..."
            value={inputValue}
            onChange={e => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            onPaste={handlePaste}
            disabled={loading || symbols.length >= 4}
            aria-label={t('comparePlaceholder')}
          />
          <button
            className="search-btn"
            onClick={handleAddSymbol}
            disabled={loading || !inputValue.trim() || symbols.length >= 4}
          >
            {t('compareAddBtn')}
          </button>
        </div>

        {/* Compare button */}
        <button
          className="search-btn compare-start-btn"
          onClick={handleCompare}
          disabled={loading || symbols.length < 2}
        >
          {loading ? t('comparingBtn') : t('compareBtn')}
        </button>

        {loading && totalCount > 0 && (
          <div className="compare-progress-bar-container" role="status" aria-live="polite">
            <div className="compare-progress-bar-track">
              <div
                className={`compare-progress-bar-fill ${doneCount === totalCount && totalCount > 0 ? 'complete' : ''}`}
                style={{ width: `${progressPct}%` }}
              />
            </div>
            <span className="compare-progress-bar-text">
              {t('compareProgressOf', { done: String(doneCount), total: String(totalCount) })}
            </span>
          </div>
        )}

        {error && <p className="error-text">{error}</p>}
      </div>

      {loading && (
        <div className="compare-loading" role="status" aria-live="polite">
          <div className="loading-spinner" />
          <p>{t('compareLoading')}</p>
          {Object.keys(symbolProgress).length > 0 && (
            <div className="compare-progress-detail">
              <p className="compare-progress-title">{t('compareProgressLabel')}:</p>
              <ul>
                {Object.entries(symbolProgress).map(([sym, info]) => {
                  const rawStatus = info.length > 1 ? info[1] : (info[0] ? 'running' : 'pending');
                  const statusKey = `compareStatus${rawStatus.charAt(0).toUpperCase() + rawStatus.slice(1)}`;
                  const statusLabel = t(statusKey) || rawStatus;
                  return (
                    <li key={sym}>
                      <strong>{sym}</strong>: {statusLabel}
                    </li>
                  );
                })}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default ComparisonPanel;