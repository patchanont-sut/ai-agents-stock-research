// MarketMind AI Dashboard — Executive Summary
// Structured brief: The Call, Why It Makes Sense, What Could Change the View.
// Synthesizes existing backend fields only — no invented analysis.
import { t, l } from '../i18n';
import { AnalysisResult } from '../types';

interface ExecutiveSummaryProps {
  result: AnalysisResult;
}

export function ExecutiveSummary({ result }: ExecutiveSummaryProps) {
  const cio = result.cio_decision;
  const bull = result.bull_case;
  const bear = result.bear_case;
  const risk = result.risk;
  const valuation = result.valuation;

  // Nothing to synthesize
  if (!cio && !bull && !bear && !risk && !valuation) {
    return (
      <section className="executive-summary">
        <p className="exec-not-available">{t('execNotAvailable')}</p>
      </section>
    );
  }

  // Risk level label (English key for i18n interpolation)
  const riskLevelLabel = cio?.risk_level || risk?.company_risk || 'Medium';

  return (
    <section className="executive-summary">
      {/* Subsection 1: The Call */}
      <h3 className="exec-subsection-title">{t('execTheCall')}</h3>
      {cio && (
        <p className="exec-paragraph">
          {l(cio.reasoning, cio.reasoning_th)}
        </p>
      )}
      {!cio && risk && (
        <p className="exec-paragraph">
          {l(risk.summary, risk.summary_th)}
        </p>
      )}

      {/* Subsection 2: Why It Makes Sense */}
      <h3 className="exec-subsection-title">{t('execWhy')}</h3>
      <div className="exec-confidence-row">
        {bull && (
          <span className="exec-confidence exec-confidence-bull">
            {t('execBullConfidence', { pct: String(Math.round((bull.confidence || 0) * 100)) })}
          </span>
        )}
        {bear && (
          <span className="exec-confidence exec-confidence-bear">
            {t('execBearConfidence', { pct: String(Math.round((bear.confidence || 0) * 100)) })}
          </span>
        )}
        {riskLevelLabel && (
          <span className="exec-confidence exec-confidence-risk">
            {t('execRiskLevel', { level: riskLevelLabel })}
          </span>
        )}
      </div>
      {bull?.thesis && (
        <p className="exec-paragraph exec-paragraph-subtle">
          <strong>{t('execBullSide')}: </strong>
          {l(bull.thesis, bull.thesis_th)}
        </p>
      )}

      {/* Subsection 3: What Could Change the View */}
      <h3 className="exec-subsection-title">{t('execWhatCouldChange')}</h3>
      {bear?.thesis && (
        <p className="exec-paragraph exec-paragraph-subtle">
          <strong>{t('execBearSide')}: </strong>
          {l(bear.thesis, bear.thesis_th)}
        </p>
      )}
      {!bear?.thesis && risk?.summary && (
        <p className="exec-paragraph exec-paragraph-subtle">
          {l(risk.summary, risk.summary_th)}
        </p>
      )}
    </section>
  );
}