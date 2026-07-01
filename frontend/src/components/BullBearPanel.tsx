import { l, t } from '../i18n';
import { AnalysisResult } from '../types';

type WinnerSide = 'bull' | 'bear' | 'tie';

type CaseSideProps = {
  className: string;
  title: string;
  thesis: string;
  thesisTh?: string;
  primaryItems: string[];
  primaryItemsTh?: string[];
  primaryLabel: string;
  secondaryItems: string[];
  secondaryItemsTh?: string[];
  secondaryLabel: string;
  confidence: number;
  confidenceClassName: string;
  textClassName: string;
};

function winnerLabel(side: WinnerSide): string {
  if (side === 'bull') return 'Bull';
  if (side === 'bear') return 'Bear';
  return 'Tie';
}

function CaseSide({
  className,
  title,
  thesis,
  thesisTh,
  primaryItems,
  primaryItemsTh,
  primaryLabel,
  secondaryItems,
  secondaryItemsTh,
  secondaryLabel,
  confidence,
  confidenceClassName,
  textClassName,
}: CaseSideProps) {
  return (
    <div className={className}>
      <h3 className="bullbear-side-title">{title}</h3>

      <p className="bullbear-thesis">
        {l(thesis, thesisTh)}
      </p>

      {primaryItems.length > 0 && (
        <div className="bullbear-subsection">
          <div className="bullbear-subsection-label">{primaryLabel}</div>
          <ul className="argument-list">
            {l(primaryItems, primaryItemsTh).map((item: string, index: number) => (
              <li key={index}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      {secondaryItems.length > 0 && (
        <div className="bullbear-subsection">
          <div className="bullbear-subsection-label">{secondaryLabel}</div>
          <ul className="argument-list">
            {l(secondaryItems, secondaryItemsTh).map((item: string, index: number) => (
              <li key={index}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="confidence-bar">
        <div
          className={`confidence-fill ${confidenceClassName}`}
          style={{ width: `${confidence * 100}%` }}
        />
      </div>
      <div className={`${textClassName} confidence-text`}>
        {t('confidence')}: {(confidence * 100).toFixed(0)}%
      </div>
    </div>
  );
}

export function BullBearPanel({ result }: { result: AnalysisResult }) {
  const debate = result.debate;
  const winningSide = debate?.winning_side as WinnerSide | undefined;
  const bull = result.bull_case;
  const bear = result.bear_case;

  return (
    <div className="card card-accent">
      <div className="card-title">
        <span className="icon">⚔️</span>
        {t('bullBearTitle')}
        {winningSide && (
          <span
            className={`bullbear-winner-badge ${winningSide === 'tie' ? 'bullbear-winner-tie' : `bullbear-winner-${winningSide}`}`}
          >
            {winningSide === 'tie' ? '🤝' : '🏆'} {winningSide === 'tie' ? 'Tie' : `${t('winner')}: ${winnerLabel(winningSide)}`}
          </span>
        )}
      </div>

      <div className="split-panel">
        <CaseSide
          className="bull-side"
          title={`🐂 ${t('bullCase')}`}
          thesis={bull?.thesis || t('noBullThesis')}
          thesisTh={bull?.thesis_th || undefined}
          primaryItems={bull?.evidence || []}
          primaryItemsTh={bull?.evidence_th}
          primaryLabel={t('evidence')}
          secondaryItems={bull?.catalysts || []}
          secondaryItemsTh={bull?.catalysts_th}
          secondaryLabel={t('catalysts')}
          confidence={bull?.confidence || 0}
          confidenceClassName="confidence-bull"
          textClassName="text-sm text-green"
        />
        <CaseSide
          className="bear-side"
          title={`🐻 ${t('bearCase')}`}
          thesis={bear?.thesis || t('noBearThesis')}
          thesisTh={bear?.thesis_th || undefined}
          primaryItems={bear?.evidence || []}
          primaryItemsTh={bear?.evidence_th}
          primaryLabel={t('evidence')}
          secondaryItems={bear?.risk_factors || []}
          secondaryItemsTh={bear?.risk_factors_th}
          secondaryLabel={t('riskFactors')}
          confidence={bear?.confidence || 0}
          confidenceClassName="confidence-bear"
          textClassName="text-sm text-red"
        />
      </div>
    </div>
  );
}
