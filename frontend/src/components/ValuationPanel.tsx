// MarketMind AI Dashboard — Valuation Panel
import { t, l } from '../i18n';
import { AnalysisResult } from '../types';

export function ValuationPanel({ result }: { result: AnalysisResult }) {
  const val = result.valuation;
  if (!val) return null;
  const verdictText = l(val.verdict, val.verdict_th);
  const verdictClass = verdictText.toLowerCase().includes('under') ? 'verdict-undervalued'
    : verdictText.toLowerCase().includes('over') ? 'verdict-overvalued' : 'verdict-fair';
  return (
    <div className="card card-accent">
      <div className="card-title"><span className="icon">💰</span> {t('valuationTitle')}</div>
      <div className="metrics-grid">
        <div className="metric-item">
          <div className="metric-label">{t('peRatio')}</div>
          <div className="metric-value">{val.pe_ratio?.toFixed(1) || t('na')}</div>
        </div>
        <div className="metric-item">
          <div className="metric-label">{t('sectorAvgPE')}</div>
          <div className="metric-value">{val.sector_avg_pe?.toFixed(1) || t('na')}</div>
        </div>
        <div className="metric-item">
          <div className="metric-label">{t('pegRatio')}</div>
          <div className="metric-value">{val.peg_ratio?.toFixed(2) || t('na')}</div>
        </div>
        <div className="metric-item">
          <div className="metric-label">{t('marketCap')}</div>
          <div className="metric-value">{val.market_cap || t('na')}</div>
        </div>
      </div>
      {verdictText && <div className={`verdict ${verdictClass}`}>{verdictText}</div>}
      {val.explanation && <p className="text-sm text-muted" style={{ marginTop: 12 }}>{l(val.explanation, val.explanation_th)}</p>}
    </div>
  );
}