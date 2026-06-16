// MarketMind AI Dashboard — Main Application
import React, { useState, useCallback, useEffect } from 'react';
import { getLanguage, hasThaiText, setLanguage, Language, t } from './i18n';
import { useAnalysis } from './hooks/useAnalysis';
import {
  LanguageToggle,
  LoadingSpinner,
  EmptyState,
  ErrorDisplay,
  ErrorBoundary,
  BullBearPanel,
  DebateViewer,
  NewsFeed,
  PipelineProgress,
  SkeletonCard,
  DecisionHero,
  MetricsPanel,
  ExecutiveSummary,
  SourceQualityPanel,
  AgentTracePanel,
  ReliabilityPanel,
  InvestmentMemoPanel,
  EvidenceExplorer,
  GroundingPanel,
  EvaluationPanel,
  ComparisonPanel,
} from './components';

type AppMode = 'single' | 'compare';

export default function App() {
  const [symbol, setSymbol] = useState('');
  const [lang, setLang] = useState<Language>(getLanguage());
  const [appMode, setAppMode] = useState<AppMode>('single');
  const { result, error, isLoading, completedAgents, trace, startAnalysis, loadDemo, retry } = useAnalysis();

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  const handleLanguageChange = useCallback((next: Language) => {
    setLanguage(next);
    setLang(next);
  }, []);

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    if (appMode !== 'single') return;
    const trimmed = symbol.trim().toUpperCase();
    if (trimmed) {
      window.scrollTo({ top: 0, behavior: 'smooth' });
      startAnalysis(trimmed, lang);
    }
  }, [lang, symbol, startAnalysis, appMode]);

  const handleTickerSelect = useCallback((ticker: string) => {
    setSymbol(ticker);
    window.scrollTo({ top: 0, behavior: 'smooth' });
    startAnalysis(ticker, lang);
  }, [lang, startAnalysis]);

  const missingThaiFields = result ? countMissingThaiFields(result) : 0;
  const hasResult = isLoading || Boolean(result) || Boolean(error);
  const hasCompleteResult = Boolean(result) && !isLoading && !error;
  const showHeaderSearch = hasResult;
  const showHeaderModeSwitch = hasResult;

  // Scroll-triggered visibility for section headings and cards
  useEffect(() => {
    if (!hasCompleteResult) return;
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
          }
        });
      },
      { threshold: 0.1, rootMargin: '0px 0px -30px 0px' }
    );
    const elements = document.querySelectorAll('.section-heading, .card');
    elements.forEach((el) => observer.observe(el));
    const timeout = setTimeout(() => {
      elements.forEach((el) => el.classList.add('visible'));
    }, 800);
    return () => {
      observer.disconnect();
      clearTimeout(timeout);
    };
  }, [hasCompleteResult]);

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-content app-container">
          <a href="/" className="logo" aria-label="MarketMind AI home">
            <span className="logo-mark">M</span>
            <span className="logo-copy">
              <span className="logo-title">{t('appTitle')}</span>
              <span className="logo-subtitle">{t('appSubtitle')}</span>
            </span>
          </a>
          <LanguageToggle lang={lang} onChange={handleLanguageChange} />

          {/* Mode switch — hidden on homescreen, shown when analysis active */}
          {showHeaderModeSwitch && (
            <div className="mode-switch">
              <button
                className={`mode-btn ${appMode === 'single' ? 'active' : ''}`}
                onClick={() => setAppMode('single')}
              >
                {t('singleMode')}
              </button>
              <button
                className={`mode-btn ${appMode === 'compare' ? 'active' : ''}`}
                onClick={() => setAppMode('compare')}
              >
                {t('compareMode')}
              </button>
            </div>
          )}

          {appMode === 'single' && showHeaderSearch && (
            <form className="search-container" onSubmit={handleSubmit}>
              <input
                type="text"
                className="search-input"
                placeholder={t('searchPlaceholder')}
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                disabled={isLoading}
                autoFocus
              />
              <button type="submit" className="search-btn" disabled={isLoading || !symbol.trim()}>
                {isLoading ? t('analyzingBtn') : t('analyzeBtn')}
              </button>
            </form>
          )}
        </div>
      </header>

      {/* Dashboard Content */}
      <main className={`dashboard ${hasCompleteResult ? 'has-result' : ''}`}>
        <ErrorBoundary>
        {/* Compare Mode */}
        {appMode === 'compare' && (
          <ComparisonPanel lang={lang} />
        )}

        {/* Single Analysis Mode */}
        {appMode === 'single' && (
          <>
            {error && <ErrorDisplay message={error} onRetry={() => retry(symbol, lang)} />}

            {/* Loading state */}
            {isLoading && !error && (
              <>
                <LoadingSpinner message={t('loadingMessage', { symbol })} />
                <PipelineProgress completedAgents={completedAgents} />
                <div className="brief-loading-stack">
                  <SkeletonCard lines={5} height="300px" />
                  <SkeletonCard lines={4} height="180px" />
                  <div className="dashboard-row dashboard-row-2">
                    <SkeletonCard height="210px" />
                    <SkeletonCard height="210px" />
                  </div>
                </div>
              </>
            )}

            {!isLoading && !error && !result && (
              <EmptyState
                symbol={symbol}
                isLoading={isLoading}
                onSymbolChange={setSymbol}
                onSubmit={handleSubmit}
                onTickerSelect={handleTickerSelect}
                onModeChange={setAppMode}
                onLoadDemo={loadDemo}
              />
            )}

            {result && (result.status === 'complete' || result.status === 'partial') && (
              <>
                <section className="brief-section brief-section-hero" aria-label={t('decisionHeroTitle')}>
                  <DecisionHero result={result} lang={lang} missingThaiFields={missingThaiFields} />
                  <ExecutiveSummary result={result} />
                </section>

                <section className="brief-section brief-section-evidence" aria-labelledby="evidence-heading">
                  <div className="section-heading">
                    <span className="section-eyebrow">02</span>
                    <h2 id="evidence-heading">{t('evidenceSection')}</h2>
                  </div>
                  <MetricsPanel result={result} lang={lang} />
                  <BullBearPanel result={result} />
                </section>

                <section className="brief-section brief-section-appendix" aria-labelledby="appendix-heading">
                  <div className="section-heading section-heading-muted">
                    <span className="section-eyebrow">03</span>
                    <h2 id="appendix-heading">{t('appendixSection')}</h2>
                  </div>
                  <DebateViewer result={result} lang={lang} />
                  <SourceQualityPanel result={result} />
                  <ReliabilityPanel evidenceQuality={result.evidence_quality} />
                  <EvaluationPanel analysisId={result.id} />
                  <InvestmentMemoPanel
                    memo={result.investment_memo}
                    evidenceLibrary={result.evidence_library}
                    analysisId={result.id}
                  />
                  <GroundingPanel groundingReport={result.investment_memo?.grounding_report} />
                  <EvidenceExplorer evidenceLibrary={result.evidence_library} />
                  <AgentTracePanel trace={trace} />
                  <NewsFeed result={result} />

                  {result.errors.length > 0 && (
                    <div className="card card-warnings">
                      <div className="card-title">{t('warningsTitle')}</div>
                      <ul className="warnings-list">
                        {result.errors.map((err, i) => (
                          <li key={i}>{err}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </section>
              </>
            )}
          </>
        )}
        </ErrorBoundary>
      </main>
    </div>
  );
}

function countMissingThaiFields(result: ReturnType<typeof useAnalysis>['result']): number {
  if (!result) return 0;
  let missing = 0;

  const checkText = (en?: string, th?: string) => {
    if (en && !hasThaiText(th)) missing += 1;
  };
  const checkList = (en?: string[], th?: string[]) => {
    if (!en?.length) return;
    if (!th || th.length !== en.length || en.some((item, index) => item && !hasThaiText(th[index]))) {
      missing += 1;
    }
  };

  checkText(result.research?.company_profile, result.research?.company_profile_th);
  checkText(result.research?.summary, result.research?.summary_th);
  checkText(result.sentiment?.explanation, result.sentiment?.explanation_th);
  checkText(result.bull_case?.thesis, result.bull_case?.thesis_th);
  checkList(result.bull_case?.evidence, result.bull_case?.evidence_th);
  checkList(result.bull_case?.catalysts, result.bull_case?.catalysts_th);
  checkText(result.bear_case?.thesis, result.bear_case?.thesis_th);
  checkList(result.bear_case?.evidence, result.bear_case?.evidence_th);
  checkList(result.bear_case?.risk_factors, result.bear_case?.risk_factors_th);
  checkList(result.risk?.macro_factors, result.risk?.macro_factors_th);
  checkList(result.risk?.company_factors, result.risk?.company_factors_th);
  checkText(result.risk?.summary, result.risk?.summary_th);
  checkText(result.valuation?.verdict, result.valuation?.verdict_th);
  checkText(result.valuation?.explanation, result.valuation?.explanation_th);
  checkText(result.debate?.summary, result.debate?.summary_th);
  result.debate?.turns.forEach((turn) => checkText(turn.content, turn.content_th));
  checkText(result.cio_decision?.reasoning, result.cio_decision?.reasoning_th);
  checkList(result.cio_decision?.key_points, result.cio_decision?.key_points_th);

  const memo = result.investment_memo;
  if (memo) {
    checkText(memo.title, memo.title_th);
    checkText(memo.executive_summary, memo.executive_summary_th);
    if (memo.sections) {
      for (const section of memo.sections) {
        checkText(section.content, section.content_th);
      }
    }
    if (memo.key_citations) {
      for (const kc of memo.key_citations) {
        checkText(kc.quote_or_summary, kc.quote_or_summary_th);
      }
    }
  }

  return missing;
}
