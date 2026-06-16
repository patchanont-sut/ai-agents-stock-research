// MarketMind AI Dashboard — AI Quality Evaluation Panel
import React, { useEffect, useState } from 'react';
import { t } from '../i18n';
import { api } from '../api/client';
import type { EvaluationMetrics } from '../types';

interface Props {
  analysisId: string;
}

function StatCard({ label, value, format = 'percent' }: { label: string; value: number; format?: 'percent' | 'count' | 'score' }) {
  let display: string;
  if (format === 'percent') {
    display = `${(value * 100).toFixed(0)}%`;
  } else if (format === 'count') {
    display = String(value);
  } else {
    display = value.toFixed(2);
  }
  return (
    <div className="stat-card">
      <span className="stat-label">{label}</span>
      <span className={`stat-value ${format === 'percent' ? (value >= 0.7 ? 'good' : value >= 0.4 ? 'warn' : 'bad') : ''}`}>
        {display}
      </span>
    </div>
  );
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  const pct = Math.min(Math.max(value * 100, 0), 100);
  return (
    <div className="score-bar">
      <div className="score-bar-header">
        <span>{label}</span>
        <span>{(value * 100).toFixed(0)}%</span>
      </div>
      <div className="score-bar-track">
        <div
          className={`score-bar-fill ${value >= 0.7 ? 'good' : value >= 0.4 ? 'warn' : 'bad'}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export function EvaluationPanel({ analysisId }: Props) {
  const [metrics, setMetrics] = useState<EvaluationMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function fetchMetrics() {
      try {
        setLoading(true);
        setError(null);
        const result = await api.getEvaluation(analysisId);
        if (!cancelled) setMetrics(result);
      } catch (e) {
        if (!cancelled) setError((e as Error).message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    fetchMetrics();
    return () => { cancelled = true; };
  }, [analysisId]);

  if (loading) {
    return (
      <div className="card evaluation-panel">
        <div className="card-title">{t('evaluationTitle')}</div>
        <p className="muted-text">{t('evalLoadingMetrics')}</p>
      </div>
    );
  }

  if (error || !metrics) {
    return (
      <div className="card evaluation-panel">
        <div className="card-title">{t('evaluationTitle')}</div>
        <p className="muted-text">{error || t('evaluationNoData')}</p>
      </div>
    );
  }

  return (
    <div className="card evaluation-panel">
      <div className="card-title">{t('evaluationTitle')}</div>

      {/* Overall score */}
      <div className="eval-overall">
        <div className="eval-overall-circle">
          <svg viewBox="0 0 36 36" className="eval-circle">
            <path
              className="eval-circle-bg"
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            />
            <path
              className={`eval-circle-fill ${metrics.overall_quality_score >= 0.7 ? 'good' : metrics.overall_quality_score >= 0.4 ? 'warn' : 'bad'}`}
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              strokeDasharray={`${Math.round(metrics.overall_quality_score * 100)}, 100`}
            />
            <text x="18" y="20.35" className="eval-circle-text">
              {(metrics.overall_quality_score * 100).toFixed(0)}%
            </text>
          </svg>
          <span className="eval-overall-label">{t('evalOverall')}</span>
        </div>
      </div>

      {/* Detailed metric bars */}
      <div className="eval-bars">
        <ScoreBar label={t('evalCitationValidity')} value={metrics.citation_validity_rate} />
        <ScoreBar label={t('evalGrounding')} value={metrics.grounding_score} />
        <ScoreBar label={t('evalSourceDiversity')} value={metrics.source_diversity_score} />
        <ScoreBar label={t('evalAgentCompletion')} value={metrics.agent_completion_rate} />
        <ScoreBar label={t('evalMemoCompleteness')} value={metrics.memo_completeness} />
      </div>

      {/* Quick stats */}
      <div className="eval-stats-grid">
        <StatCard label={t('evalEvidenceCount')} value={metrics.evidence_count} format="count" />
        <StatCard label={t('evalCitationValidity')} value={metrics.citation_validity_rate} format="percent" />
        <StatCard label={t('evalMemoCompleteness')} value={metrics.memo_completeness} format="percent" />
      </div>

      {/* Missing fields */}
      {metrics.missing_required_fields.length > 0 && (
        <div className="eval-section">
          <div className="eval-section-title">{t('evalMissingFields')} ({metrics.missing_required_fields.length})</div>
          <div className="eval-tags">
            {metrics.missing_required_fields.map((field, i) => (
              <span key={i} className="eval-tag bad">{field}</span>
            ))}
          </div>
        </div>
      )}

      {/* Warnings */}
      {metrics.warnings.length > 0 && (
        <div className="eval-section">
          <div className="eval-section-title">{t('evalWarnings')}</div>
          <ul className="eval-warnings-list">
            {metrics.warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default EvaluationPanel;