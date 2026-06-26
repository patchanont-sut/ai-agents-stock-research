import { l, t, Language } from '../i18n';
import type { AnalysisResult, AnalysisTrace } from '../types';
import { localizedValue } from './LanguageToggle';

interface ResearchWorkbenchProps {
  result: AnalysisResult;
  trace: AnalysisTrace | null;
  completedAgents: string[];
  lang: Language;
}

const AGENT_FLOW = [
  { id: 'research', label: 'traceAgentResearch' },
  { id: 'sentiment', label: 'traceAgentSentiment' },
  { id: 'valuation', label: 'traceAgentValuation' },
  { id: 'bull', label: 'traceAgentBullCase' },
  { id: 'bear', label: 'traceAgentBearCase' },
  { id: 'risk', label: 'traceAgentRisk' },
  { id: 'debate', label: 'traceAgentDebate' },
  { id: 'cio', label: 'traceAgentCIO' },
  { id: 'memo', label: 'traceAgentMemo' },
];

function formatPercent(value: number): string {
  return `${Math.round(Math.max(0, Math.min(1, value)) * 100)}%`;
}

function formatAgentStatus(status: 'pending' | 'running' | 'complete' | 'failed'): string {
  const keys = {
    pending: 'traceStatusPending',
    running: 'traceStatusRunning',
    complete: 'traceStatusComplete',
    failed: 'traceStatusFailed',
  };
  return t(keys[status]);
}

function inferAgentStatus(
  agentId: string,
  result: AnalysisResult,
  trace: AnalysisTrace | null,
  completedAgents: string[]
): 'pending' | 'running' | 'complete' | 'failed' {
  const traced = trace?.agents.find((entry) => entry.agent_name === agentId);
  if (traced) return traced.status;
  if (completedAgents.includes(agentId)) return 'complete';
  if (result.status === 'failed') return 'failed';

  const inferredComplete =
    (agentId === 'research' && !!result.research) ||
    (agentId === 'sentiment' && !!result.sentiment) ||
    (agentId === 'valuation' && !!result.valuation) ||
    (agentId === 'bull' && !!result.bull_case) ||
    (agentId === 'bear' && !!result.bear_case) ||
    (agentId === 'risk' && !!result.risk) ||
    (agentId === 'debate' && !!result.debate) ||
    (agentId === 'cio' && !!result.cio_decision) ||
    (agentId === 'memo' && !!result.investment_memo);

  return inferredComplete ? 'complete' : 'pending';
}

export function ResearchWorkbench({ result, trace, completedAgents, lang }: ResearchWorkbenchProps) {
  const reliability = result.evidence_quality?.overall_reliability_score ?? 0;
  const grounding = result.investment_memo?.grounding_report?.grounded_score ?? 0;
  const confidence = result.cio_decision?.confidence ?? 0;
  const evidenceCount =
    result.evidence_library?.length ?? result.evidence_quality?.evidence_item_count ?? 0;
  const sourceCount = result.evidence_quality?.source_count ?? 0;
  const citedClaims = result.investment_memo?.grounding_report?.cited_claim_count ?? 0;
  const claimCount = result.investment_memo?.grounding_report?.claim_count ?? 0;
  const coverage = claimCount > 0 ? citedClaims / claimCount : 0;

  const bullSignal = (l(result.bull_case?.evidence ?? [], result.bull_case?.evidence_th) as string[])[0];
  const bearSignal = (l(result.bear_case?.evidence ?? [], result.bear_case?.evidence_th) as string[])[0];
  const riskSignal =
    (l(result.risk?.company_factors ?? [], result.risk?.company_factors_th) as string[])[0] ||
    (l(result.risk?.macro_factors ?? [], result.risk?.macro_factors_th) as string[])[0];

  return (
    <section className="card workbench-panel" aria-label={t('workbenchTitle')}>
      <div className="workbench-header">
        <div>
          <div className="card-title workbench-title">{t('workbenchTitle')}</div>
          <p className="workbench-subtitle">{t('workbenchSubtitle')}</p>
        </div>
        <div className="workbench-status-chip">
          {localizedValue(result.cio_decision?.action ?? result.status.toUpperCase(), lang)}
        </div>
      </div>

      <div className="workbench-score-strip">
        <div className="metric-tile">
          <div className="metric-tile-label">{t('workbenchDecision')}</div>
          <div className="metric-tile-value">{formatPercent(confidence)}</div>
        </div>
        <div className="metric-tile">
          <div className="metric-tile-label">{t('reliabilityOverall')}</div>
          <div className="metric-tile-value">{formatPercent(reliability)}</div>
        </div>
        <div className="metric-tile">
          <div className="metric-tile-label">{t('groundingScore')}</div>
          <div className="metric-tile-value">{formatPercent(grounding)}</div>
        </div>
        <div className="metric-tile">
          <div className="metric-tile-label">{t('evalEvidenceCount')}</div>
          <div className="metric-tile-value">{evidenceCount}</div>
        </div>
      </div>

      <div className="workbench-grid">
        <div className="workbench-block">
          <div className="workbench-block-title">{t('workbenchSignals')}</div>
          <div className="workbench-signal-list">
            {bullSignal && (
              <div className="workbench-signal workbench-signal-bull">
                <span className="workbench-signal-label">{t('workbenchBullSignal')}</span>
                <p>{bullSignal}</p>
              </div>
            )}
            {bearSignal && (
              <div className="workbench-signal workbench-signal-bear">
                <span className="workbench-signal-label">{t('workbenchBearSignal')}</span>
                <p>{bearSignal}</p>
              </div>
            )}
            {riskSignal && (
              <div className="workbench-signal workbench-signal-risk">
                <span className="workbench-signal-label">{t('workbenchRiskSignal')}</span>
                <p>{riskSignal}</p>
              </div>
            )}
          </div>
        </div>

        <div className="workbench-block">
          <div className="workbench-block-title">{t('workbenchEvidence')}</div>
          <div className="workbench-coverage-meta">
            <span>{t('reliabilitySources')}: {sourceCount}</span>
            <span>{t('workbenchClaimsCited', { cited: String(citedClaims), total: String(claimCount) })}</span>
          </div>
          <div className="workbench-coverage-track" aria-hidden="true">
            <div className="workbench-coverage-fill" style={{ width: `${Math.round(coverage * 100)}%` }} />
          </div>
          <div className="workbench-coverage-foot">
            <span>{t('workbenchCoverage')}</span>
            <strong>{formatPercent(coverage)}</strong>
          </div>
        </div>
      </div>

      <div className="workbench-block">
        <div className="workbench-block-title">{t('workbenchPipeline')}</div>
        <div className="workbench-pipeline">
          {AGENT_FLOW.map((agent) => {
            const status = inferAgentStatus(agent.id, result, trace, completedAgents);
            const traceEntry = trace?.agents.find((entry) => entry.agent_name === agent.id);
            return (
              <div key={agent.id} className={`workbench-step workbench-step-${status}`}>
                <div className="workbench-step-name">{t(agent.label)}</div>
                <div className="workbench-step-status">{formatAgentStatus(status)}</div>
                {traceEntry && traceEntry.duration_ms > 0 && (
                  <div className="workbench-step-duration">{Math.round(traceEntry.duration_ms)}ms</div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

export default ResearchWorkbench;
