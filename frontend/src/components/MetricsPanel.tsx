// MarketMind AI Dashboard — Metrics Panel
// 3-column compact panel: Sentiment + Risk + Valuation
import { t, l } from '../i18n';
import { Language } from '../i18n';
import { AnalysisResult } from '../types';
import { localizedValue } from './LanguageToggle';

interface MetricsPanelProps {
  result: AnalysisResult;
  lang: Language;
}

export function MetricsPanel({ result, lang }: MetricsPanelProps) {
  return (
    <div className="metrics-panel">
      {/* Sentiment Column */}
      {result.sentiment && (
        <div className="metric-card">
          <div className="metric-card-header">
            <span className="metric-card-icon">🎯</span>
            <span className="metric-card-title">{t('metricSentiment')}</span>
          </div>
          <div className="metric-sentiment-body">
            <div className="metric-gauge">
              <div className="metric-gauge-bar">
                <div
                  className="metric-gauge-indicator"
                  style={{ left: `${((result.sentiment.overall_score + 1) / 2) * 100}%` }}
                />
              </div>
              <div className={`metric-gauge-score metric-score-${
                result.sentiment.overall_score > 0.2 ? 'positive' : result.sentiment.overall_score < -0.2 ? 'negative' : 'neutral'
              }`}>
                {result.sentiment.overall_score.toFixed(2)}
              </div>
              <div className="metric-gauge-label">
                {localizedValue(result.sentiment.label, lang)}
              </div>
            </div>
            <p className="metric-card-desc">
              {l(result.sentiment.explanation, result.sentiment.explanation_th)}
            </p>
          </div>
        </div>
      )}

      {/* Risk Column */}
      {result.risk && (
        <div className="metric-card">
          <div className="metric-card-header">
            <span className="metric-card-icon">🛡️</span>
            <span className="metric-card-title">{t('metricRisk')}</span>
          </div>
          <div className="metric-risk-body">
            <div className="metric-risk-chips">
              <div className={`metric-risk-chip risk-${result.risk.macro_risk}`}>
                <span className="metric-risk-chip-label">{t('macroRisk')}</span>
                <span className="metric-risk-chip-value">{localizedValue(result.risk.macro_risk, lang)}</span>
              </div>
              <div className={`metric-risk-chip risk-${result.risk.company_risk}`}>
                <span className="metric-risk-chip-label">{t('companyRisk')}</span>
                <span className="metric-risk-chip-value">{localizedValue(result.risk.company_risk, lang)}</span>
              </div>
              <div className={`metric-risk-chip risk-${result.risk.volatility_risk}`}>
                <span className="metric-risk-chip-label">{t('volatilityRisk')}</span>
                <span className="metric-risk-chip-value">{localizedValue(result.risk.volatility_risk, lang)}</span>
              </div>
            </div>
            <p className="metric-card-desc">
              {l(result.risk.summary, result.risk.summary_th)}
            </p>
          </div>
        </div>
      )}

      {/* Valuation Column */}
      {result.valuation && (
        <div className="metric-card">
          <div className="metric-card-header">
            <span className="metric-card-icon">💰</span>
            <span className="metric-card-title">{t('metricValuation')}</span>
          </div>
          <div className="metric-valuation-body">
            <div className="metric-valuation-grid">
              <div className="metric-valuation-item">
                <div className="metric-valuation-label">{t('peRatio')}</div>
                <div className="metric-valuation-value">
                  {result.valuation.pe_ratio?.toFixed(1) || t('na')}
                </div>
              </div>
              <div className="metric-valuation-item">
                <div className="metric-valuation-label">{t('sectorAvgPE')}</div>
                <div className="metric-valuation-value">
                  {result.valuation.sector_avg_pe?.toFixed(1) || t('na')}
                </div>
              </div>
              <div className="metric-valuation-item">
                <div className="metric-valuation-label">{t('pegRatio')}</div>
                <div className="metric-valuation-value">
                  {result.valuation.peg_ratio?.toFixed(2) || t('na')}
                </div>
              </div>
              <div className="metric-valuation-item">
                <div className="metric-valuation-label">{t('marketCap')}</div>
                <div className="metric-valuation-value">
                  {result.valuation.market_cap || t('na')}
                </div>
              </div>
            </div>
            {/* Verdict badge — uses English text for class, localized for display */}
            {(() => {
              const verdictEn = result.valuation.verdict || '';
              const isUnder = /\bunder/i.test(verdictEn);
              const isOver = /\bover/i.test(verdictEn);
              const verdictClass = isUnder ? 'metric-verdict-undervalued' : isOver ? 'metric-verdict-overvalued' : 'metric-verdict-fair';
              return (
                <div className={`metric-verdict ${verdictClass}`}>
                  {l(result.valuation.verdict, result.valuation.verdict_th)}
                </div>
              );
            })()}
            <p className="metric-card-desc">
              {l(result.valuation.explanation, result.valuation.explanation_th)}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}