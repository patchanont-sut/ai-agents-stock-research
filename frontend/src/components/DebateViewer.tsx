// MarketMind AI Dashboard — Debate Viewer
// Secondary section styling with winning side badge at top
import { t, l } from '../i18n';
import { Language } from '../i18n';
import { AnalysisResult } from '../types';
import { localizedValue } from './LanguageToggle';

export function DebateViewer({ result, lang }: { result: AnalysisResult; lang: Language }) {
  const debate = result.debate;
  if (!debate || !debate.turns?.length) return null;

  return (
    <div className="card card-secondary card-accent">
      <div className="card-title">
        <span className="icon">🗣️</span>
        {t('secondaryDebate')}
        {debate.winning_side && debate.winning_side !== 'tie' && (
          <span className={`debate-winner-badge debate-winner-${debate.winning_side}`}>
            🏆 {t('winner')}: {localizedValue(debate.winning_side, lang)}
          </span>
        )}
        {debate.winning_side === 'tie' && (
          <span className="debate-winner-badge debate-winner-tie">
            🤝 {localizedValue('tie', lang)}
          </span>
        )}
      </div>

      <div className="debate-list">
        {debate.turns.map((turn, i) => (
          <div key={i} className={`debate-turn debate-turn-${turn.side}`}>
            <div
              className="debate-side-label"
              style={{ color: turn.side === 'bull' ? 'var(--accent-green)' : 'var(--accent-red)' }}
            >
              {turn.side === 'bull'
                ? `🐂 ${localizedValue('bull', lang)}`
                : `🐻 ${localizedValue('bear', lang)}`}
              <span className="debate-turn-num">#{i + 1}</span>
            </div>
            <div className="debate-content">{l(turn.content, turn.content_th)}</div>
          </div>
        ))}
      </div>

      {debate.summary && (
        <div className="debate-summary">
          <div className="debate-summary-label">📋 {t('riskSummary')}</div>
          <p>{l(debate.summary, debate.summary_th)}</p>
        </div>
      )}
    </div>
  );
}
