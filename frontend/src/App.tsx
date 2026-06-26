// MarketMind AI Dashboard — Main Application
import React, { useState, useCallback, useEffect } from 'react';
import { getLanguage, hasThaiText, setLanguage, Language, t } from './i18n';
import { useAnalysis } from './hooks/useAnalysis';
import { LanguageToggle } from './components/LanguageToggle';
import { LoadingSpinner } from './components/LoadingSpinner';
import { EmptyState } from './components/EmptyState';
import { ErrorDisplay } from './components/ErrorDisplay';
import { ErrorBoundary } from './components/ErrorBoundary';
import { BullBearPanel } from './components/BullBearPanel';
import { DebateViewer } from './components/DebateViewer';
import { NewsFeed } from './components/NewsFeed';
import { PipelineProgress } from './components/PipelineProgress';
import { SkeletonCard } from './components/SkeletonCard';
import { DecisionHero } from './components/DecisionHero';
import { MetricsPanel } from './components/MetricsPanel';
import { ExecutiveSummary } from './components/ExecutiveSummary';
import { SourceQualityPanel } from './components/SourceQualityPanel';
import { AgentTracePanel } from './components/AgentTracePanel';
import { ReliabilityPanel } from './components/ReliabilityPanel';
import { InvestmentMemoPanel } from './components/InvestmentMemoPanel';
import { EvidenceExplorer } from './components/EvidenceExplorer';
import { GroundingPanel } from './components/GroundingPanel';
import { EvaluationPanel } from './components/EvaluationPanel';
import { ComparisonPanel } from './components/ComparisonPanel';
import { LiveMonitor } from './components/LiveMonitor';
import { ResearchWorkbench } from './components/ResearchWorkbench';

type AppView = 'dashboard' | 'analysis' | 'watchlist' | 'reports' | 'compare';
type SavedAnalysis = {
  id: string;
  symbol: string;
  action: string;
  confidence: number | null;
};

const HISTORY_KEY = 'marketmind.history';
const WATCHLIST_KEY = 'marketmind.watchlist';
const DEFAULT_WATCHLIST = ['NVDA', 'QQQ', 'SPY', 'AMD'];
const SIDEBAR_NAV: Array<{ id: Exclude<AppView, 'compare'>; label: string }> = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'analysis', label: 'Analysis' },
  { id: 'watchlist', label: 'Watchlist' },
  { id: 'reports', label: 'Reports' },
];
const TOPBAR_TABS = SIDEBAR_NAV;
const WATCHLIST_ALIASES: Record<string, string> = {
  NASDAQ: 'QQQ',
  'S&P 500': 'SPY',
  SP500: 'SPY',
};

function readJson<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

function saveJson<T>(key: string, value: T) {
  localStorage.setItem(key, JSON.stringify(value));
}

function readWatchlist() {
  const saved = readJson<string[]>(WATCHLIST_KEY, DEFAULT_WATCHLIST);
  const next = [...new Set(saved.map((item) => WATCHLIST_ALIASES[item.toUpperCase()] ?? item.toUpperCase()))];
  saveJson(WATCHLIST_KEY, next);
  return next;
}

export default function App() {
  const [symbol, setSymbol] = useState('');
  const [lang, setLang] = useState<Language>(getLanguage());
  const [activeView, setActiveView] = useState<AppView>('dashboard');
  const [history, setHistory] = useState<SavedAnalysis[]>(() => readJson(HISTORY_KEY, []));
  const [watchlist, setWatchlist] = useState<string[]>(readWatchlist);
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
    const trimmed = symbol.trim().toUpperCase();
    if (trimmed) {
      setActiveView('analysis');
      window.scrollTo({ top: 0, behavior: 'smooth' });
      startAnalysis(trimmed, lang);
    }
  }, [lang, symbol, startAnalysis]);

  const handleTickerSelect = useCallback((ticker: string) => {
    setSymbol(ticker);
    setActiveView('analysis');
    window.scrollTo({ top: 0, behavior: 'smooth' });
    startAnalysis(ticker, lang);
  }, [lang, startAnalysis]);

  const handleLoadDemo = useCallback(async () => {
    setActiveView('analysis');
    window.scrollTo({ top: 0, behavior: 'smooth' });
    await loadDemo();
  }, [loadDemo]);

  const handleOpenCompare = useCallback(() => {
    setActiveView('compare');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  const handleViewChange = useCallback((view: AppView) => {
    setActiveView(view);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  const addToWatchlist = useCallback((ticker: string) => {
    const nextTicker = ticker.trim().toUpperCase();
    if (!nextTicker) return;
    setWatchlist((current) => {
      const next = [nextTicker, ...current.filter((item) => item !== nextTicker)].slice(0, 12);
      saveJson(WATCHLIST_KEY, next);
      return next;
    });
  }, []);

  const removeFromWatchlist = useCallback((ticker: string) => {
    setWatchlist((current) => {
      const next = current.filter((item) => item !== ticker);
      saveJson(WATCHLIST_KEY, next);
      return next;
    });
  }, []);

  useEffect(() => {
    if (!result || (result.status !== 'complete' && result.status !== 'partial')) return;
    setHistory((current) => {
      const item: SavedAnalysis = {
        id: result.id,
        symbol: result.symbol,
        action: result.cio_decision?.action ?? result.status.toUpperCase(),
        confidence: result.cio_decision?.confidence ?? null,
      };
      const next = [item, ...current.filter((entry) => entry.id !== result.id)].slice(0, 8);
      saveJson(HISTORY_KEY, next);
      return next;
    });
  }, [result]);

  const missingThaiFields = result ? countMissingThaiFields(result) : 0;
  const hasResult = isLoading || Boolean(result) || Boolean(error);
  const hasCompleteResult = Boolean(result) && !isLoading && !error;
  const showHeaderSearch = hasResult;
  const memoTitle = result?.investment_memo?.title ?? '';
  const isSyntheticResult = memoTitle.includes('(Synthetic)') || result?.id === 'test';

  return (
    <div className="dashboard-shell">
      <div className="bg-blob bg-blob-1" aria-hidden="true" />
      <div className="bg-blob bg-blob-2" aria-hidden="true" />

      <aside className="sidebar" aria-label="Main navigation">
        <a className="sidebar-brand" href="/" aria-label={`${t('appTitle')} home`}>
          <div className="sidebar-logo">M</div>
          <div className="sidebar-title">{t('appTitle')}</div>
          <div className="sidebar-subtitle">{t('appSubtitle')}</div>
        </a>

        <nav className="sidebar-nav" aria-label="Dashboard sections">
          {SIDEBAR_NAV.map((item) => (
            <button
              key={item.id}
              className={`sidebar-nav-item ${activeView === item.id ? 'active' : ''}`}
              type="button"
              onClick={() => handleViewChange(item.id)}
            >
              <span className="sidebar-nav-icon" aria-hidden="true">{item.label.slice(0, 1)}</span>
              <span>{item.label}</span>
            </button>
          ))}
          <button
            type="button"
            className={`sidebar-nav-item ${activeView === 'compare' ? 'active' : ''}`}
            onClick={handleOpenCompare}
          >
            <span className="sidebar-nav-icon" aria-hidden="true">C</span>
            <span>Compare</span>
          </button>
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-upgrade-card sidebar-status">
            <p>{t('homeEyebrow')}</p>
            <button className="btn-secondary" onClick={() => void handleLoadDemo()} disabled={isLoading}>
              {t('demoLoadBtn')}
            </button>
          </div>
        </div>
      </aside>

      <div className="main-content">
        <header className="topbar">
          <div className="sidebar-title topbar-title">{t('appTitle')}</div>

          <nav className="topbar-tabs" aria-label="Workspace views">
            {TOPBAR_TABS.map((item) => (
              <button
                key={item.id}
                className={`topbar-tab ${activeView === item.id ? 'active' : ''}`}
                type="button"
                onClick={() => handleViewChange(item.id)}
              >
                {item.label}
              </button>
            ))}
            <button
              className={`topbar-tab ${activeView === 'compare' ? 'active' : ''}`}
              type="button"
              onClick={handleOpenCompare}
            >
              Compare
            </button>
          </nav>

          <div className="topbar-actions">
            {activeView !== 'compare' && showHeaderSearch && (
              <form className="topbar-search" onSubmit={handleSubmit}>
                <input
                  type="text"
                  className="topbar-search-input"
                  placeholder={t('searchPlaceholder')}
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value)}
                  disabled={isLoading}
                  autoFocus
                />
                <button type="submit" className="topbar-search-btn" disabled={isLoading || !symbol.trim()}>
                  {isLoading ? t('analyzingBtn') : t('analyzeBtn')}
                </button>
              </form>
            )}

            <div className="app-mode-switch" role="tablist" aria-label="Analysis mode">
              <button
                className={`mode-btn ${activeView !== 'compare' ? 'active' : ''}`}
                onClick={() => handleViewChange('analysis')}
                type="button"
              >
                {t('singleMode')}
              </button>
              <button
                className={`mode-btn ${activeView === 'compare' ? 'active' : ''}`}
                onClick={handleOpenCompare}
                type="button"
              >
                {t('compareMode')}
              </button>
            </div>

            <LanguageToggle lang={lang} onChange={handleLanguageChange} />
          </div>
        </header>

        <main className="app-content">
          <ErrorBoundary>
          {activeView === 'compare' && (
            <ComparisonPanel lang={lang} />
          )}

          {activeView !== 'compare' && (
            <>
              {error && <ErrorDisplay message={error} onRetry={() => retry(symbol, lang)} />}

              {activeView === 'analysis' && isLoading && !error && (
                <div className="dashboard has-result">
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
                </div>
              )}

              {activeView === 'dashboard' && !isLoading && !error && (
                <EmptyState
                  symbol={symbol}
                  isLoading={isLoading}
                  onSymbolChange={setSymbol}
                  onSubmit={handleSubmit}
                  onTickerSelect={handleTickerSelect}
                  onLoadDemo={handleLoadDemo}
                  history={history}
                  watchlist={watchlist}
                  onAddToWatchlist={addToWatchlist}
                  onRemoveFromWatchlist={removeFromWatchlist}
                />
              )}

              {activeView === 'analysis' && !isLoading && !error && !result && (
                <EmptyState
                  symbol={symbol}
                  isLoading={isLoading}
                  onSymbolChange={setSymbol}
                  onSubmit={handleSubmit}
                  onTickerSelect={handleTickerSelect}
                  onLoadDemo={handleLoadDemo}
                  history={history}
                  watchlist={watchlist}
                  onAddToWatchlist={addToWatchlist}
                  onRemoveFromWatchlist={removeFromWatchlist}
                />
              )}

              {activeView === 'watchlist' && (
                <section className="dashboard has-result" aria-label="Watchlist management">
                  <div className="section-heading">
                    <span className="section-eyebrow">01</span>
                    <h2>Watchlist</h2>
                  </div>
                  <div className="home-sidebar">
                    <div className="home-sidebar-card">
                      <div className="home-sidebar-card-header">
                        <span>Tracked symbols</span>
                        <button className="card-action" onClick={() => void handleLoadDemo()} type="button">
                          Demo
                        </button>
                      </div>
                      {watchlist.map((ticker) => (
                        <div key={ticker} className="watchlist-item" onClick={() => handleTickerSelect(ticker)}>
                          <div className="watchlist-item-left">
                            <div className="watchlist-ticker-box">{ticker}</div>
                          </div>
                          <div className="watchlist-item-action">
                            <button
                              className="watchlist-remove"
                              onClick={(e) => {
                                e.stopPropagation();
                                removeFromWatchlist(ticker);
                              }}
                              aria-label={`Remove ${ticker}`}
                              title={`Remove ${ticker}`}
                              type="button"
                            >
                              ×
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                    <div className="home-sidebar-card">
                      <LiveMonitor watchlist={watchlist} onTickerSelect={handleTickerSelect} />
                    </div>
                  </div>
                </section>
              )}

              {activeView === 'reports' && (
                <section className="dashboard has-result" aria-label="Recent reports">
                  <div className="section-heading">
                    <span className="section-eyebrow">01</span>
                    <h2>Reports</h2>
                  </div>
                  <div className="home-sidebar-card">
                    <div className="home-sidebar-card-header">
                      <span>Recent Activity</span>
                      <button className="card-action" onClick={() => handleViewChange('analysis')} type="button">
                        New analysis
                      </button>
                    </div>
                    <div className="recent-list">
                      {history.length === 0 && <div className="local-empty">No saved runs yet</div>}
                      {history.map((item) => (
                        <button type="button" key={item.id} className="recent-item" onClick={() => handleTickerSelect(item.symbol)}>
                          <span>{item.symbol}</span>
                          <small>
                            {item.action}
                            {item.confidence !== null ? ` · ${Math.round(item.confidence * 100)}%` : ''}
                          </small>
                        </button>
                      ))}
                    </div>
                  </div>
                </section>
              )}

              {activeView === 'analysis' && result && (result.status === 'complete' || result.status === 'partial') && (
                <div className={`dashboard ${hasCompleteResult ? 'has-result' : ''}`}>
                  <div className="analysis-grid">
                    <div className="analysis-main">
                      <section className="brief-section brief-section-hero" aria-label={t('decisionHeroTitle')}>
                        <DecisionHero result={result} lang={lang} missingThaiFields={missingThaiFields} />
                        <ExecutiveSummary result={result} />
                        <ResearchWorkbench
                          result={result}
                          trace={trace}
                          completedAgents={completedAgents}
                          lang={lang}
                        />
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
                        {!isSyntheticResult && <EvaluationPanel analysisId={result.id} />}
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
                    </div>

                    <aside className="analysis-rail" aria-label="Market sidebar">
                      <div className="rail-card rail-card-quote">
                        <span className="rail-kicker">Active Brief</span>
                        <strong>{result.symbol}</strong>
                        <small>{result.cio_decision?.action ?? result.status}</small>
                      </div>
                      <div className="rail-card">
                        <div className="home-sidebar-card-header">
                          <span>Watchlist</span>
                          <button
                            className="card-action"
                            onClick={() => addToWatchlist(result.symbol)}
                            type="button"
                          >
                            Track
                          </button>
                        </div>
                        {watchlist.map((ticker) => (
                          <button key={ticker} className="rail-list-row" type="button" onClick={() => handleTickerSelect(ticker)}>
                            <span>{ticker}</span>
                            <small>Open</small>
                          </button>
                        ))}
                      </div>
                      <div className="rail-card">
                        <div className="home-sidebar-card-header">
                          <span>Recent Activity</span>
                          <button className="card-action" onClick={() => void handleLoadDemo()} type="button">
                            Demo
                          </button>
                        </div>
                        {history.length === 0 && <div className="local-empty">No saved runs yet</div>}
                        {history.map((item) => (
                          <button key={item.id} className="rail-list-row" type="button" onClick={() => handleTickerSelect(item.symbol)}>
                            <span>{item.symbol}</span>
                            <small>{item.action}{item.confidence !== null ? ` · ${Math.round(item.confidence * 100)}%` : ''}</small>
                          </button>
                        ))}
                      </div>
                      <div className="rail-card">
                        <LiveMonitor watchlist={watchlist} onTickerSelect={handleTickerSelect} />
                      </div>
                    </aside>
                  </div>
                </div>
              )}
            </>
          )}
          </ErrorBoundary>
        </main>
      </div>
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
