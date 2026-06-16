// MarketMind AI Dashboard — Agent Trace Timeline Panel
import { AgentTraceEntry, AnalysisTrace } from '../types';
import { t } from '../i18n';

const AGENT_DISPLAY_NAME_KEYS: Record<string, string> = {
  research: 'traceAgentResearch',
  sentiment: 'traceAgentSentiment',
  valuation: 'traceAgentValuation',
  bull: 'traceAgentBullCase',
  bear: 'traceAgentBearCase',
  risk: 'traceAgentRisk',
  debate: 'traceAgentDebate',
  cio: 'traceAgentCIO',
  memo: 'traceAgentMemo',
};

function localizeStatus(status: string): string {
  const keyMap: Record<string, string> = {
    pending: 'traceStatusPending',
    running: 'traceStatusRunning',
    complete: 'traceStatusComplete',
    failed: 'traceStatusFailed',
  };
  return t(keyMap[status] || status);
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)}ms`;
  const sec = (ms / 1000).toFixed(1);
  return `${sec}s`;
}

function AgentStep({ entry }: { entry: AgentTraceEntry }) {
  const displayNameKey = AGENT_DISPLAY_NAME_KEYS[entry.agent_name];
  const displayName = displayNameKey ? t(displayNameKey) : entry.agent_name;
  const statusClass = `trace-step-${entry.status}`;
  const hasToolCalls = entry.tool_calls.length > 0;

  return (
    <div className={`trace-step ${statusClass}`}>
      <div className="trace-step-header">
        <span className="trace-step-dot" aria-label={entry.status} />
        <span className="trace-step-name">{displayName}</span>
        <span className="trace-step-status">{localizeStatus(entry.status)}</span>
        {entry.duration_ms > 0 && (
          <span className="trace-step-duration">{formatDuration(entry.duration_ms)}</span>
        )}
        {hasToolCalls && (
          <span className="trace-step-toolcount">
            {entry.tool_calls.length} {entry.tool_calls.length === 1 ? t('traceToolCalls').replace(/s$/i, '') : t('traceToolCalls')}
          </span>
        )}
      </div>

      {entry.short_summary && (
        <div className="trace-step-summary">{entry.short_summary}</div>
      )}

      {entry.errors.length > 0 && (
        <ul className="trace-step-errors">
          {entry.errors.map((err, i) => (
            <li key={i}>{err}</li>
          ))}
        </ul>
      )}

      {hasToolCalls && (
        <details className="trace-tool-details">
          <summary className="trace-tool-summary">
            {t('traceToolCalls')} ({entry.tool_calls.length})
          </summary>
          <div className="trace-tool-list">
            {entry.tool_calls.map((tc, i) => (
              <div key={i} className={`trace-tool-item ${tc.success ? 'tool-success' : 'tool-failed'}`}>
                <div className="trace-tool-header">
                  <span className="trace-tool-name">{tc.tool_name}</span>
                  <span className="trace-tool-duration">{formatDuration(tc.duration_ms)}</span>
                  <span className="trace-tool-status">{tc.success ? '✓' : '✗'}</span>
                </div>
                {tc.error && <div className="trace-tool-error">{tc.error}</div>}
                {tc.compact_result_preview && (
                  <div className="trace-tool-preview">{tc.compact_result_preview}</div>
                )}
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  );
}

export function AgentTracePanel({ trace }: { trace: AnalysisTrace | null }) {
  if (!trace) {
    return (
      <div className="card card-secondary trace-panel">
        <div className="card-title">
          <span className="icon">🔍</span> {t('traceTitle')}
        </div>
        <p className="trace-empty">{t('traceEmpty')}</p>
      </div>
    );
  }

  const agents = trace.agents;
  if (!agents || agents.length === 0) {
    return (
      <div className="card card-secondary trace-panel">
        <div className="card-title">
          <span className="icon">🔍</span> {t('traceTitle')}
        </div>
        <p className="trace-empty">{t('traceWaiting')}</p>
      </div>
    );
  }

  return (
    <div className="card card-secondary trace-panel">
      <div className="card-title">
        <span className="icon">🔍</span> {t('traceTitle')}
        <span className="trace-agent-count">
          {agents.filter(a => a.status === 'complete').length}/{agents.length}
        </span>
      </div>
      <div className="trace-timeline">
        {agents.map((entry, i) => (
          <AgentStep key={`${entry.agent_name}-${i}`} entry={entry} />
        ))}
      </div>
    </div>
  );
}