// MarketMind AI Dashboard — Evidence Explorer
import React, { useState, useMemo } from 'react';
import { EvidenceItem } from '../types';
import { t } from '../i18n';

function cleanDisplayText(value?: string | null): string {
  return String(value || '')
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

interface Props {
  evidenceLibrary: EvidenceItem[] | null | undefined;
}

type FilterType = 'all' | 'news' | 'reddit' | 'company_profile' | 'fundamentals' | 'macro' | 'agent_output';

const FILTER_KEYS: { value: FilterType; i18nKey: string }[] = [
  { value: 'all', i18nKey: 'evidenceFilterAll' },
  { value: 'news', i18nKey: 'evidenceFilterNews' },
  { value: 'reddit', i18nKey: 'evidenceFilterReddit' },
  { value: 'company_profile', i18nKey: 'evidenceFilterCompany' },
  { value: 'fundamentals', i18nKey: 'evidenceFilterFundamentals' },
  { value: 'macro', i18nKey: 'evidenceFilterMacro' },
  { value: 'agent_output', i18nKey: 'evidenceFilterAgent' },
];

export function EvidenceExplorer({ evidenceLibrary }: Props) {
  const [filter, setFilter] = useState<FilterType>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const filtered = useMemo(() => {
    if (!evidenceLibrary) return [];
    let items = evidenceLibrary;
    if (filter !== 'all') {
      items = items.filter((ev) => ev.source_type === filter);
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      items = items.filter(
        (ev) =>
          ev.title.toLowerCase().includes(q) ||
          ev.snippet.toLowerCase().includes(q) ||
          ev.source.toLowerCase().includes(q) ||
          ev.id.toLowerCase().includes(q)
      );
    }
    return items;
  }, [evidenceLibrary, filter, searchQuery]);

  if (!evidenceLibrary || evidenceLibrary.length === 0) {
    return (
      <div className="card card-secondary evidence-explorer">
        <div className="card-title">
          <span className="icon">🔍</span> {t('evidenceExplorerTitle')}
        </div>
        <p className="evidence-explorer-empty">{t('noEvidenceAvailable')}</p>
      </div>
    );
  }

  return (
    <div className="card card-secondary evidence-explorer">
      <div className="card-title">
        <span className="icon">🔍</span> {t('evidenceExplorerTitle')}
        <span className="evidence-count-badge">{evidenceLibrary.length}</span>
      </div>

      <div className="evidence-filter-row">
          <input
            type="text"
            className="evidence-search-input"
            placeholder={t('evidenceSearchPlaceholder')}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <div className="evidence-filter-chips">
          {FILTER_KEYS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              className={`evidence-filter-chip ${filter === opt.value ? 'evidence-filter-chip-active' : ''}`}
              onClick={() => setFilter(opt.value)}
            >
              {t(opt.i18nKey)}
            </button>
          ))}
        </div>
      </div>

      <div className="evidence-cards">
        {filtered.map((ev) => (
          <div key={ev.id} className="evidence-card">
            <div className="evidence-card-header">
              <span className="evidence-card-id">{ev.id}</span>
              <span className={`evidence-card-type evidence-card-type-${ev.source_type}`}>
                {ev.source_type}
              </span>
            </div>
            <h4 className="evidence-card-title">{cleanDisplayText(ev.title)}</h4>
            <div className="evidence-card-source">{cleanDisplayText(ev.source)}</div>
            {ev.snippet && (
              <p className="evidence-card-snippet">{cleanDisplayText(ev.snippet)}</p>
            )}
            {ev.key_points.length > 0 && (
              <ul className="evidence-card-keypoints">
                {ev.key_points.map((kp, i) => (
                  <li key={i}>{cleanDisplayText(kp)}</li>
                ))}
              </ul>
            )}
            {ev.url && (
              <a
                href={ev.url}
                target="_blank"
                rel="noopener noreferrer"
                className="evidence-card-url"
              >
                <span>{t('evidenceOpenSource')}</span>
                <span aria-hidden="true">↗</span>
              </a>
            )}
            {ev.sentiment_score != null && (
              <div className="evidence-card-sentiment">
                Sentiment: {ev.sentiment_score.toFixed(2)}
              </div>
            )}
          </div>
        ))}
        {filtered.length === 0 && (
          <p className="evidence-explorer-no-results">{t('evidenceNoMatches')}</p>
        )}
      </div>
    </div>
  );
}
