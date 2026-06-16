// MarketMind AI Dashboard — Decision Hero
// Full-width hero banner: stock identity + CIO decision + key points + status badges
import { t, l } from '../i18n';
import { Language } from '../i18n';
import { AnalysisResult } from '../types';
import { localizedValue } from './LanguageToggle';

interface DecisionHeroProps {
  result: AnalysisResult;
  lang: Language;
  missingThaiFields: number;
}

export function DecisionHero({ result, lang, missingThaiFields }: DecisionHeroProps) {
  const cio = result.cio_decision;
  const stock = result.stock;
  const stockName = stock?.name || result.symbol;
  const stockPrice = stock?.price;
  const changePct = stock?.change_percent;

  if (!cio) {
    return (
      <div className="decision-hero decision-hero-missing">
        <div className="hero-stock-row">
          <h1 className="hero-stock-name">{stockName}</h1>
          <span className="hero-stock-symbol">{result.symbol}</span>
          {stockPrice != null && (
            <span className="hero-stock-price">
              ${stockPrice.toFixed(2)}
            </span>
          )}
        </div>
        <p className="hero-missing-text">{t('noKeyPoints')}</p>
      </div>
    );
  }

  const actionClass = `hero-action-${cio.action}`;
  const confidencePercent = Math.round(cio.confidence * 100);

  // Determine verdict class from ENGLISH verdict text to avoid Thai substring issues
  const valuationVerdictEn = result.valuation?.verdict || '';
  const isUndervalued = /\bunder/i.test(valuationVerdictEn);
  const isOvervalued = /\bover/i.test(valuationVerdictEn);

  return (
    <div className={`decision-hero ${actionClass}`}>
      {/* Row 1: Stock identity */}
      <div className="hero-stock-row">
        <h1 className="hero-stock-name">{stockName}</h1>
        <span className="hero-stock-symbol">{result.symbol}</span>
        {stockPrice != null && (
          <span className="hero-stock-price">
            ${stockPrice.toFixed(2)}
            {changePct != null && (
              <span className={`hero-change ${changePct >= 0 ? 'hero-change-up' : 'hero-change-down'}`}>
                {changePct >= 0 ? '▲' : '▼'} {Math.abs(changePct).toFixed(2)}%
              </span>
            )}
          </span>
        )}
      </div>

      {/* Row 2: CIO action as the visual anchor */}
      <div className={`hero-action-badge ${actionClass}`}>
        {localizedValue(cio.action, lang)}
      </div>

      {/* Row 3: Reasoning narrative */}
      <p className="hero-reasoning">
        {l(cio.reasoning, cio.reasoning_th)}
      </p>

      {/* Row 4: Chip row — confidence, risk, horizon, valuation verdict */}
      <div className="hero-chip-row">
        <span className="hero-chip hero-chip-confidence">
          {t('confidence')}: {confidencePercent}%
        </span>
        <span className={`hero-chip hero-chip-risk hero-chip-risk-${cio.risk_level}`}>
          {t('risk')}: {localizedValue(cio.risk_level, lang)}
        </span>
        <span className="hero-chip hero-chip-horizon">
          {cio.time_horizon}
        </span>
        {valuationVerdictEn && (
          <span className={`hero-chip hero-chip-valuation ${isUndervalued ? 'hero-chip-green' : isOvervalued ? 'hero-chip-red' : 'hero-chip-yellow'}`}>
            {l(result.valuation!.verdict, result.valuation!.verdict_th)}
          </span>
        )}
      </div>

      {/* Row 5: CIO key points */}
      {cio.key_points && cio.key_points.length > 0 && (
        <div className="hero-keypoints">
          <div className="hero-keypoints-label">{t('keyPoints')}</div>
          <div className="hero-keypoints-list">
            {l(cio.key_points, cio.key_points_th).map((point: string, i: number) => (
              <span key={i} className="hero-keypoint-pill">{point}</span>
            ))}
          </div>
        </div>
      )}

      {/* Row 6: Status bar — subtle indicators for stale/partial/missing-Thai */}
      {(result.stale || result.status === 'partial' || (lang === 'th' && missingThaiFields > 0)) && (
        <div className="hero-status-bar">
          {result.stale && (
            <span className="hero-status-badge hero-status-stale">{t('statusBarStale')}</span>
          )}
          {result.status === 'partial' && (
            <span className="hero-status-badge hero-status-partial">{t('statusBarPartial')}</span>
          )}
          {lang === 'th' && missingThaiFields > 0 && (
            <span className="hero-status-badge hero-status-missingthai">
              {t('statusBarMissingThai', { missing: String(missingThaiFields) })}
            </span>
          )}
        </div>
      )}
    </div>
  );
}