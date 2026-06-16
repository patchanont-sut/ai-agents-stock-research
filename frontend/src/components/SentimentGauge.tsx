// MarketMind AI Dashboard — Sentiment Gauge
import { t } from '../i18n';
import { Language } from '../i18n';
import { localizedValue } from './LanguageToggle';

export function SentimentGauge({ score, label, lang }: { score: number; label: string; lang: Language }) {
  const leftPercent = ((score + 1) / 2) * 100;
  const colorClass = score > 0.2 ? 'score-positive' : score < -0.2 ? 'score-negative' : 'score-neutral';
  return (
    <div className="card card-accent">
      <div className="card-title"><span className="icon">🎯</span> {t('sentimentTitle')}</div>
      <div className="sentiment-gauge">
        <div className="gauge-bar">
          <div className="gauge-indicator" style={{ left: `${leftPercent}%` }} />
        </div>
        <div className={`gauge-score ${colorClass}`}>{score.toFixed(2)}</div>
        <div className="gauge-label">{localizedValue(label, lang)}</div>
      </div>
    </div>
  );
}