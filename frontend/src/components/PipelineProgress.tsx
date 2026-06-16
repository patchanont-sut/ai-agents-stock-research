// MarketMind AI Dashboard — Pipeline Progress Bar
// Shows the 8-agent pipeline stages with animated completion states
import { t } from '../i18n';

const AGENTS = [
  { key: 'research', label: 'Research' },
  { key: 'sentiment', label: 'Sentiment' },
  { key: 'valuation', label: 'Valuation' },
  { key: 'bull', label: 'Bull' },
  { key: 'bear', label: 'Bear' },
  { key: 'risk', label: 'Risk' },
  { key: 'debate', label: 'Debate' },
  { key: 'cio', label: 'CIO' },
] as const;

interface PipelineProgressProps {
  completedAgents: string[];
}

export function PipelineProgress({ completedAgents }: PipelineProgressProps) {
  return (
    <div className="pipeline-progress">
      {AGENTS.map((agent, i) => {
        const isCompleted = completedAgents.includes(agent.key);
        const isActive = !isCompleted && (i === 0 || completedAgents.includes(AGENTS[i - 1].key));
        const isPending = !isCompleted && !isActive;
        
        return (
          <div key={agent.key} className="pipeline-step-wrapper">
            <div className={`pipeline-step ${isCompleted ? 'completed' : isActive ? 'active' : 'pending'}`}>
              <div className="pipeline-dot">
                {isCompleted ? '✓' : isActive ? '●' : ''}
              </div>
              <div className="pipeline-label">{agent.label}</div>
            </div>
            {i < AGENTS.length - 1 && (
              <div className={`pipeline-connector ${isCompleted ? 'completed' : ''}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}