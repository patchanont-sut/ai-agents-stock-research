// MarketMind AI Dashboard — Grounding Panel
import { GroundingReport } from '../types';
import { t } from '../i18n';

interface Props {
  groundingReport: GroundingReport | null | undefined;
}

function localizeIssueType(issueType: string): string {
  const keyMap: Record<string, string> = {
    missing_citation: 'groundingIssueMissingCitation',
    unknown_evidence_id: 'groundingIssueUnknownEvidenceId',
    weak_overlap: 'groundingIssueWeakOverlap',
  };
  return t(keyMap[issueType] || issueType);
}

function ScoreBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const colorClass =
    pct >= 70 ? 'reliability-bar-high' : pct >= 40 ? 'reliability-bar-mid' : 'reliability-bar-low';

  return (
    <div className="grounding-score-bar">
      <div className="grounding-score-bar-track">
        <div
          className={`grounding-score-bar-fill ${colorClass}`}
          style={{ width: `${Math.min(100, pct)}%` }}
        />
      </div>
      <span className="grounding-score-bar-value">{pct}%</span>
    </div>
  );
}

export function GroundingPanel({ groundingReport }: Props) {
  if (!groundingReport) {
    return (
      <div className="card card-secondary grounding-panel">
        <div className="card-title">
          <span className="icon">📎</span> {t('groundingPanelTitle')}
        </div>
        <p className="grounding-empty">{t('noGroundingAvailable')}</p>
      </div>
    );
  }

  const gr = groundingReport;

  return (
    <div className="card card-secondary grounding-panel">
      <div className="card-title">
        <span className="icon">📎</span> {t('groundingPanelTitle')}
      </div>

      <div className="grounding-overall">
        <div className="grounding-overall-label">{t('groundingScore')}</div>
        <ScoreBar value={gr.grounded_score} />
      </div>

      <div className="grounding-stats">
        <div className="grounding-stat">
          <span className="grounding-stat-label">{t('groundingClaimCount')}</span>
          <span className="grounding-stat-value">{gr.claim_count}</span>
        </div>
        <div className="grounding-stat">
          <span className="grounding-stat-label">{t('groundingCitedClaims')}</span>
          <span className="grounding-stat-value">{gr.cited_claim_count}</span>
        </div>
        <div className="grounding-stat">
          <span className="grounding-stat-label">{t('groundingValidCitations')}</span>
          <span className="grounding-stat-value grounding-stat-valid">{gr.valid_citation_count}</span>
        </div>
        <div className="grounding-stat">
          <span className="grounding-stat-label">{t('groundingInvalidCitations')}</span>
          <span className={`grounding-stat-value ${gr.invalid_citation_count > 0 ? 'grounding-stat-invalid' : ''}`}>
            {gr.invalid_citation_count}
          </span>
        </div>
      </div>

      {gr.issues.length > 0 && (
        <div className="grounding-issues">
          <h4 className="grounding-issues-heading">{t('groundingIssues')} ({gr.issues.length})</h4>
          <ul className="grounding-issues-list">
            {gr.issues.map((issue, i) => (
              <li key={i} className={`grounding-issue grounding-issue-${issue.issue_type}`}>
                <span className="grounding-issue-type">{localizeIssueType(issue.issue_type)}</span>
                <span className="grounding-issue-claim">{issue.claim}</span>
                {issue.detail && (
                  <span className="grounding-issue-detail">{issue.detail}</span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {gr.warnings.length > 0 && (
        <ul className="reliability-warnings">
          {gr.warnings.map((w, i) => (
            <li key={i}>{w}</li>
          ))}
        </ul>
      )}
    </div>
  );
}