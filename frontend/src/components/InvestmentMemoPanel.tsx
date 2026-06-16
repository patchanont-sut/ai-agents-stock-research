// MarketMind AI Dashboard — Investment Memo Panel
import React, { useState, useCallback } from 'react';
import { InvestmentMemo, EvidenceItem, CitationRef } from '../types';
import { t, getLanguage } from '../i18n';
import { api } from '../api/client';

interface Props {
  memo: InvestmentMemo | null | undefined;
  evidenceLibrary: EvidenceItem[] | null | undefined;
  analysisId?: string;
}

function CitationChip({
  citation,
  evidenceMap,
}: {
  citation: CitationRef;
  evidenceMap: Map<string, EvidenceItem>;
}) {
  const [expanded, setExpanded] = useState(false);

  if (!citation || !citation.evidence_id) {
    return <span className="citation-chip citation-chip-unknown">[?]</span>;
  }

  const ev = evidenceMap.get(citation.evidence_id);
  const isUnknown = !ev;
  const isThai = getLanguage() === 'th';
  const quoteText = isThai && citation.quote_or_summary_th
    ? citation.quote_or_summary_th
    : citation.quote_or_summary;

  return (
    <span className="citation-chip-wrapper">
      <button
        className={`citation-chip ${isUnknown ? 'citation-chip-unknown' : ''}`}
        onClick={() => setExpanded(!expanded)}
        title={isUnknown ? 'Unknown evidence ID' : (ev?.title || '')}
      >
        [{citation.evidence_id}]
      </button>
      {expanded && (
        <div className="citation-detail">
          {isUnknown ? (
            <div className="citation-detail-warning">
              ⚠ Unknown evidence ID: {citation.evidence_id}
            </div>
          ) : (
            <>
              <div className="citation-detail-title">{ev!.title}</div>
              <div className="citation-detail-source">
                {ev!.source_type} &middot; {ev!.source}
              </div>
              {ev!.snippet && (
                <div className="citation-detail-snippet">{ev!.snippet}</div>
              )}
              {ev!.url && (
                <a
                  href={ev!.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="citation-detail-url"
                >
                  View source ↗
                </a>
              )}
              {quoteText && (
                <div className="citation-detail-quote">
                  &ldquo;{quoteText}&rdquo;
                </div>
              )}
            </>
          )}
        </div>
      )}
    </span>
  );
}

function renderContentWithCitations(
  content: string,
  evidenceMap: Map<string, EvidenceItem>,
  sectionCitations: CitationRef[],
) {
  const citations = Array.isArray(sectionCitations) ? sectionCitations : [];
  const citationMap = new Map<string, CitationRef>();
  for (const cit of citations) {
    citationMap.set(cit.evidence_id, cit);
  }

  const parts = content.split(/(\[E\d+\])/g);

  return parts.map((part, i) => {
    const match = part.match(/^\[(E\d+)\]$/);
    if (match) {
      const eid = match[1];
      const cit = citationMap.get(eid) || { evidence_id: eid, quote_or_summary: '' };
      return <CitationChip key={i} citation={cit} evidenceMap={evidenceMap} />;
    }
    return <span key={i}>{part}</span>;
  });
}

export function InvestmentMemoPanel({ memo, evidenceLibrary, analysisId }: Props) {
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  const handleExport = useCallback(async () => {
    if (!analysisId) return;
    setExporting(true);
    setExportError(null);
    try {
      const markdown = await api.downloadMemoMarkdown(analysisId);
      const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `memo_${analysisId.slice(0, 8)}.md`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e) {
      setExportError((e as Error).message || t('exportError'));
    } finally {
      setExporting(false);
    }
  }, [analysisId]);

  if (!memo) {
    return (
      <div className="card card-secondary memo-panel">
        <div className="card-title">
          <span className="icon">📝</span> {t('memoPanelTitle')}
        </div>
        <p className="memo-empty">{t('noMemoAvailable')}</p>
      </div>
    );
  }

  const isThai = getLanguage() === 'th';
  const evidenceMap = new Map<string, EvidenceItem>();
  if (evidenceLibrary) {
    for (const ev of evidenceLibrary) {
      evidenceMap.set(ev.id, ev);
    }
  }

  const sections = Array.isArray(memo.sections) ? memo.sections : [];
  const keyCitations = Array.isArray(memo.key_citations) ? memo.key_citations : [];

  const displayTitle = isThai
    ? (memo.title_th || memo.title)
    : memo.title;

  const displayRecommendation = isThai
    ? (memo.recommendation_th || memo.recommendation)
    : memo.recommendation;

  const displaySummary = isThai
    ? (memo.executive_summary_th || memo.executive_summary)
    : memo.executive_summary;

  return (
    <div className="card card-secondary memo-panel">
      <div className="card-title">
        <span className="icon">📝</span> {t('memoPanelTitle')}
        {displayRecommendation && (
          <span className="memo-recommendation-badge">{displayRecommendation}</span>
        )}
        {analysisId && (
          <button
            className="export-btn"
            onClick={handleExport}
            disabled={exporting}
          >
            {exporting ? t('exportingMemo') : t('exportMemo')}
          </button>
        )}
      </div>

      {exportError && <p className="error-text">{exportError}</p>}

      <h3 className="memo-title">{displayTitle}</h3>

      {displaySummary && (
        <div className="memo-section">
          <h4 className="memo-section-heading">{t('executiveSummary')}</h4>
          <p className="memo-section-content">
            {renderContentWithCitations(displaySummary, evidenceMap, keyCitations)}
          </p>
        </div>
      )}

      {sections.map((section, i) => {
        const sectionHeading = isThai
          ? (section.heading_th || section.heading)
          : section.heading;
        const sectionContent = isThai
          ? (section.content_th || section.content)
          : section.content;

        return (
          <div key={i} className="memo-section">
            <h4 className="memo-section-heading">{sectionHeading}</h4>
            <p className="memo-section-content">
              {renderContentWithCitations(
                sectionContent,
                evidenceMap,
                Array.isArray(section.citations) ? section.citations : [],
              )}
            </p>
          </div>
        );
      })}

      {keyCitations.length > 0 && (
        <div className="memo-key-citations">
          <h4 className="memo-section-heading">{t('keyCitations')}</h4>
          <ul className="memo-key-citations-list">
            {keyCitations.map((cit, i) => {
              const ev = evidenceMap.get(cit.evidence_id);
              const summaryText = isThai && cit.quote_or_summary_th
                ? cit.quote_or_summary_th
                : cit.quote_or_summary
                || (ev ? ev.title : 'Unknown evidence');

              return (
                <li key={i} className="memo-key-citation-item">
                  <span className={`citation-chip ${!ev ? 'citation-chip-unknown' : ''}`}>
                    [{cit.evidence_id}]
                  </span>
                  <span className="memo-key-citation-summary">
                    {summaryText}
                  </span>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}

export default InvestmentMemoPanel;