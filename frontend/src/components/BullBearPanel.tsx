// MarketMind AI Dashboard — Bull vs Bear Panel
// Polished: catalysts display, winner badge, improved typography
import { t, l, Language } from '../i18n';
import { AnalysisResult } from '../types';

export function BullBearPanel({ result }: { result: AnalysisResult }) {
  const bull = result.bull_case;
  const bear = result.bear_case;
  const debate = result.debate;

  const winnerLabel = (side: string): string => {
    if (side === 'bull') return 'Bull';
    if (side === 'bear') return 'Bear';
    if (side === 'tie') return 'Tie';
    return side;
  };

  return (
    <div className="card card-accent">
      <div className="card-title">
        <span className="icon">⚔️</span>
        {t('bullBearTitle')}
        {debate?.winning_side && debate.winning_side !== 'tie' && (
          <span className={`bullbear-winner-badge bullbear-winner-${debate.winning_side}`}>
            🏆 {t('winner')}: {winnerLabel(debate.winning_side)}
          </span>
        )}
        {debate?.winning_side === 'tie' && (
          <span className="bullbear-winner-badge bullbear-winner-tie">
            🤝 Tie
          </span>
        )}
      </div>

      <div className="split-panel">
        {/* Bull Side */}
        <div className="bull-side">
          <h3 className="bullbear-side-title">🐂 {t('bullCase')}</h3>

          <p className="bullbear-thesis">
            {l(bull?.thesis || t('noBullThesis'), bull?.thesis_th || undefined)}
          </p>

          {bull?.evidence && bull.evidence.length > 0 && (
            <div className="bullbear-subsection">
              <div className="bullbear-subsection-label">{t('evidence')}</div>
              <ul className="argument-list">
                {l(bull.evidence, bull.evidence_th).map((e: string, i: number) => (
                  <li key={i}>{e}</li>
                ))}
              </ul>
            </div>
          )}

          {bull?.catalysts && bull.catalysts.length > 0 && (
            <div className="bullbear-subsection">
              <div className="bullbear-subsection-label">{t('catalysts')}</div>
              <ul className="argument-list">
                {l(bull.catalysts, bull.catalysts_th).map((c: string, i: number) => (
                  <li key={i}>{c}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="confidence-bar">
            <div
              className="confidence-fill confidence-bull"
              style={{ width: `${(bull?.confidence || 0) * 100}%` }}
            />
          </div>
          <div className="text-sm text-green confidence-text">
            {t('confidence')}: {((bull?.confidence || 0) * 100).toFixed(0)}%
          </div>
        </div>

        {/* Bear Side */}
        <div className="bear-side">
          <h3 className="bullbear-side-title">🐻 {t('bearCase')}</h3>

          <p className="bullbear-thesis">
            {l(bear?.thesis || t('noBearThesis'), bear?.thesis_th || undefined)}
          </p>

          {bear?.evidence && bear.evidence.length > 0 && (
            <div className="bullbear-subsection">
              <div className="bullbear-subsection-label">{t('evidence')}</div>
              <ul className="argument-list">
                {l(bear.evidence, bear.evidence_th).map((e: string, i: number) => (
                  <li key={i}>{e}</li>
                ))}
              </ul>
            </div>
          )}

          {bear?.risk_factors && bear.risk_factors.length > 0 && (
            <div className="bullbear-subsection">
              <div className="bullbear-subsection-label">{t('riskFactors')}</div>
              <ul className="argument-list">
                {l(bear.risk_factors, bear.risk_factors_th).map((r: string, i: number) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="confidence-bar">
            <div
              className="confidence-fill confidence-bear"
              style={{ width: `${(bear?.confidence || 0) * 100}%` }}
            />
          </div>
          <div className="text-sm text-red confidence-text">
            {t('confidence')}: {((bear?.confidence || 0) * 100).toFixed(0)}%
          </div>
        </div>
      </div>
    </div>
  );
}