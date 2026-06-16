// MarketMind AI Dashboard — Source quality and data transparency panel
import { t } from '../i18n';
import { AnalysisResult } from '../types';

export function SourceQualityPanel({ result }: { result: AnalysisResult }) {
  const research = result.research;
  if (!research) return null;

  const quality = ['good', 'partial', 'poor'].includes(research.data_quality || '')
    ? research.data_quality!
    : 'unknown';
  const issues = research.data_issues || [];
  const sources = research.sources || [];
  const fetchedAt = research.fetched_at
    ? new Date(research.fetched_at).toLocaleString()
    : t('sourceUnknown');

  return (
    <div className="card card-secondary source-quality-panel">
      <div className="card-title">
        <span className="icon">🧾</span> {t('sourceQualityTitle')}
        <span className={`source-quality-badge source-quality-${quality}`}>
          {t(`sourceQuality_${quality}`)}
        </span>
      </div>

      <div className="source-quality-grid">
        <SourceMetric label={t('sourceNewsCount')} value={String(research.news_count ?? research.news_articles.length)} />
        <SourceMetric label={t('sourceRedditCount')} value={String(research.reddit_count ?? research.reddit_posts.length)} />
        <SourceMetric label={t('sourcePrice')} value={research.price_source || t('sourceUnknown')} />
        <SourceMetric label={t('sourceFundamentals')} value={research.fundamentals_source || t('sourceUnknown')} />
        <SourceMetric label={t('sourceMacro')} value={research.macro_source || t('sourceUnknown')} />
        <SourceMetric label={t('sourceFetchedAt')} value={fetchedAt} />
      </div>

      {sources.length > 0 && (
        <div className="source-chip-row" aria-label={t('sourceList')}>
          {sources.slice(0, 8).map((source) => (
            <span key={source} className="source-chip">{source}</span>
          ))}
        </div>
      )}

      {issues.length > 0 && (
        <ul className="source-issues">
          {issues.map((issue) => (
            <li key={issue}>{issue}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

function SourceMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="source-metric">
      <span className="source-metric-label">{label}</span>
      <span className="source-metric-value">{value}</span>
    </div>
  );
}
