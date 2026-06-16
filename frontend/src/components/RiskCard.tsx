// MarketMind AI Dashboard — Risk Assessment Card
import { t, l } from '../i18n';
import { Language } from '../i18n';
import { AnalysisResult } from '../types';
import { localizedValue } from './LanguageToggle';

export function RiskCard({ result, lang }: { result: AnalysisResult; lang: Language }) {
  const risk = result.risk;
  if (!risk) return null;
  return (
    <div className="card card-accent">
      <div className="card-title"><span className="icon">🛡️</span> {t('riskTitle')}</div>
      <div className="risk-indicators">
        <div className="risk-indicator">
          <div className="risk-label">{t('macroRisk')}</div>
          <div className={`risk-value risk-${risk.macro_risk}`}>{localizedValue(risk.macro_risk, lang)}</div>
        </div>
        <div className="risk-indicator">
          <div className="risk-label">{t('companyRisk')}</div>
          <div className={`risk-value risk-${risk.company_risk}`}>{localizedValue(risk.company_risk, lang)}</div>
        </div>
        <div className="risk-indicator">
          <div className="risk-label">{t('volatilityRisk')}</div>
          <div className={`risk-value risk-${risk.volatility_risk}`}>{localizedValue(risk.volatility_risk, lang)}</div>
        </div>
      </div>
      <p className="text-sm text-muted">{l(risk.summary, risk.summary_th)}</p>
    </div>
  );
}