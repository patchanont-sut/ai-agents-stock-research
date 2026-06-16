// MarketMind AI Dashboard — Evidence Quality & Reliability Panel
import { EvidenceQuality } from '../types';
import { t } from '../i18n';

function ScoreBar({ label, value, maxValue = 1 }: { label: string; value: number; maxValue?: number }) {
  const pct = Math.round((value / maxValue) * 100);
  const colorClass =
    pct >= 70 ? 'reliability-bar-high' : pct >= 40 ? 'reliability-bar-mid' : 'reliability-bar-low';

  return (
    <div className="reliability-metric">
      <div className="reliability-metric-header">
        <span className="reliability-metric-label">{label}</span>
        <span className="reliability-metric-value">{pct}%</span>
      </div>
      <div className="reliability-bar-track">
        <div
          className={`reliability-bar-fill ${colorClass}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export function ReliabilityPanel({ evidenceQuality }: { evidenceQuality?: EvidenceQuality | null }) {
  if (!evidenceQuality) {
    return (
      <div className="card card-secondary reliability-panel">
        <div className="card-title">
          <span className="icon">🛡️</span> {t('reliabilityTitle')}
        </div>
        <p className="reliability-empty">{t('reliabilityEmpty')}</p>
      </div>
    );
  }

  const eq = evidenceQuality;

  return (
    <div className="card card-secondary reliability-panel">
      <div className="card-title">
        <span className="icon">🛡️</span> {t('reliabilityTitle')}
        <span className="reliability-overall-badge">
          {Math.round(eq.overall_reliability_score * 100)}%
        </span>
      </div>

      <div className="reliability-scores">
        <ScoreBar label={t('reliabilityOverall')} value={eq.overall_reliability_score} />
        <ScoreBar label={t('reliabilityDiversity')} value={eq.source_diversity_score} />
        <ScoreBar label={t('reliabilityFreshness')} value={eq.freshness_score} />
        <ScoreBar label={t('reliabilityCompleteness')} value={eq.completeness_score} />
      </div>

      <div className="reliability-stats">
        <div className="reliability-stat">
          <span className="reliability-stat-label">{t('reliabilitySources')}</span>
          <span className="reliability-stat-value">{eq.source_count}</span>
        </div>
        <div className="reliability-stat">
          <span className="reliability-stat-label">{t('reliabilityItems')}</span>
          <span className="reliability-stat-value">{eq.evidence_item_count}</span>
        </div>
        <div className="reliability-stat">
          <span className="reliability-stat-label">{t('reliabilityQuality')}</span>
          <span className={`reliability-stat-value reliability-quality-${eq.data_quality}`}>
            {eq.data_quality}
          </span>
        </div>
      </div>

      {eq.warnings.length > 0 && (
        <ul className="reliability-warnings">
          {eq.warnings.map((w, i) => (
            <li key={i}>{w}</li>
          ))}
        </ul>
      )}
    </div>
  );
}