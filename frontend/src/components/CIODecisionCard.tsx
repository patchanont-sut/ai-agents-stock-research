// MarketMind AI Dashboard — CIO Decision Card
import { t, l } from '../i18n';
import { Language } from '../i18n';
import { AnalysisResult } from '../types';
import { localizedValue } from './LanguageToggle';

export function CIODecisionCard({ result, lang }: { result: AnalysisResult; lang: Language }) {
  const cio = result.cio_decision;
  if (!cio) return null;
  const actionClass = `cio-action-${cio.action}`;
  return (
    <div className={`cio-card ${actionClass}`}>
      <div className="card-title" style={{ justifyContent: 'center' }}>🧠 {t('cioTitle')}</div>
      <div className={`cio-action ${actionClass}`}>{localizedValue(cio.action, lang)}</div>
      <p style={{ color: 'var(--text-secondary)', marginBottom: 8 }}>{l(cio.reasoning, cio.reasoning_th)}</p>
      <div style={{ display: 'flex', justifyContent: 'center', gap: 16, fontSize: '0.85rem' }}>
        <span>{t('confidence')}: <strong>{(cio.confidence * 100).toFixed(0)}%</strong></span>
        <span>{t('risk')}: <strong>{localizedValue(cio.risk_level, lang)}</strong></span>
        <span>{t('horizon')}: <strong>{cio.time_horizon}</strong></span>
      </div>
    </div>
  );
}