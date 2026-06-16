// MarketMind AI Dashboard — Home Empty State
import type React from 'react';
import { useState, useEffect, useRef, useMemo } from 'react';
import { t } from '../i18n';

interface EmptyStateProps {
  symbol: string;
  isLoading: boolean;
  appMode: 'single' | 'compare';
  onSymbolChange: (symbol: string) => void;
  onSubmit: (event: React.FormEvent) => void;
  onTickerSelect: (ticker: string) => void;
  onModeChange: (mode: 'single' | 'compare') => void;
  onLoadDemo: () => Promise<void>;
}

const SUGGESTED_TICKERS = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMD'];

interface TickerInfo {
  symbol: string;
  name: string;
}

const TICKER_LOOKUP: TickerInfo[] = [
  { symbol: 'AAPL', name: 'Apple Inc.' },
  { symbol: 'MSFT', name: 'Microsoft Corp.' },
  { symbol: 'NVDA', name: 'NVIDIA Corp.' },
  { symbol: 'TSLA', name: 'Tesla Inc.' },
  { symbol: 'AMD', name: 'Advanced Micro Devices' },
  { symbol: 'GOOGL', name: 'Alphabet Inc.' },
  { symbol: 'AMZN', name: 'Amazon.com Inc.' },
  { symbol: 'META', name: 'Meta Platforms Inc.' },
  { symbol: 'NFLX', name: 'Netflix Inc.' },
  { symbol: 'JPM', name: 'JPMorgan Chase & Co.' },
  { symbol: 'V', name: 'Visa Inc.' },
  { symbol: 'WMT', name: 'Walmart Inc.' },
  { symbol: 'JNJ', name: 'Johnson & Johnson' },
  { symbol: 'MA', name: 'Mastercard Inc.' },
  { symbol: 'PG', name: 'Procter & Gamble' },
  { symbol: 'BAC', name: 'Bank of America' },
  { symbol: 'DIS', name: 'The Walt Disney Co.' },
  { symbol: 'ADBE', name: 'Adobe Inc.' },
  { symbol: 'CRM', name: 'Salesforce Inc.' },
  { symbol: 'INTC', name: 'Intel Corp.' },
];

const ROTATING_TICKERS = ['AAPL', 'TSLA', 'NVDA', 'MSFT', 'GOOGL'];
const ROTATION_INTERVAL = 3500;

function filterTickers(query: string): TickerInfo[] {
  if (!query.trim()) return [];
  const upper = query.trim().toUpperCase();
  return TICKER_LOOKUP.filter(
    (t) => t.symbol.startsWith(upper) || t.name.toUpperCase().includes(upper)
  ).slice(0, 6);
}

export function EmptyState({ symbol, isLoading, appMode, onSymbolChange, onSubmit, onTickerSelect, onModeChange, onLoadDemo }: EmptyStateProps) {
  const [rotatingIndex, setRotatingIndex] = useState(0);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  // Filtered suggestions
  const suggestions = useMemo(() => filterTickers(symbol), [symbol]);

  // Rotating ticker in preview
  useEffect(() => {
    const timer = setInterval(() => {
      setRotatingIndex((prev) => (prev + 1) % ROTATING_TICKERS.length);
    }, ROTATION_INTERVAL);
    return () => clearInterval(timer);
  }, []);

  // Animated pipeline steps
  useEffect(() => {
    const stepTimer = setInterval(() => {
      setActiveStep((prev) => (prev + 1) % 4);
    }, 2200);
    return () => clearInterval(stepTimer);
  }, []);

  // Close suggestions on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(e.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(e.target as Node)
      ) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const rotatingSymbol = ROTATING_TICKERS[rotatingIndex];
  const rotatingName = TICKER_LOOKUP.find((t) => t.symbol === rotatingSymbol)?.name || rotatingSymbol;

  return (
    <section className="home-hero">
      <div className="home-copy">
        <div className="home-eyebrow">{t('homeEyebrow')}</div>
        <h1>{t('homeTitle')}</h1>
        <p className="home-subtitle">{t('homeSubtitle')}</p>

        {/* Mode switch */}
        <div className="home-mode-row">
          <button className="home-mode-pill" onClick={() => onModeChange('single')}>
            <span className="home-mode-icon">◆</span>
            <span className="home-mode-text">
              <strong>{t('singleMode')}</strong>
              <small>{t('singleModeDesc')}</small>
            </span>
          </button>
          <button className="home-mode-pill" onClick={() => onModeChange('compare')}>
            <span className="home-mode-icon">◈</span>
            <span className="home-mode-text">
              <strong>{t('compareMode')}</strong>
              <small>{t('compareModeDesc')}</small>
            </span>
          </button>
        </div>

        {/* Search card */}
        <form className="home-search-card" onSubmit={onSubmit}>
          <label className="home-search-label" htmlFor="home-symbol">
            {t('homeSearchLabel')}
          </label>
          <div className="home-search-row">
            <div className="home-search-input-wrapper">
              <input
                id="home-symbol"
                ref={inputRef}
                type="text"
                className="home-search-input"
                placeholder={t('searchPlaceholder')}
                value={symbol}
                onChange={(event) => {
                  onSymbolChange(event.target.value);
                  setShowSuggestions(true);
                }}
                onFocus={() => setShowSuggestions(true)}
                onKeyDown={(e) => {
                  if (e.key === 'Escape') setShowSuggestions(false);
                }}
                disabled={isLoading}
                autoFocus
              />
              <span className="home-search-hint" aria-hidden="true">↵</span>

              {showSuggestions && suggestions.length > 0 && (
                <div className="ticker-suggestions" ref={suggestionsRef}>
                  {suggestions.map((t) => (
                    <button
                      key={t.symbol}
                      type="button"
                      className="ticker-suggestion-item"
                      onClick={() => {
                        onTickerSelect(t.symbol);
                        setShowSuggestions(false);
                      }}
                    >
                      <span className="ticker-suggestion-symbol">{t.symbol}</span>
                      <span className="ticker-suggestion-name">{t.name}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
            <button
              className={`home-search-button ${!symbol.trim() ? 'home-search-button-pulse' : ''}`}
              type="submit"
              disabled={isLoading || !symbol.trim()}
            >
              {isLoading ? t('analyzingBtn') : t('analyzeBtn')}
            </button>
          </div>
          <div className="ticker-chip-row" aria-label={t('homeTickerLabel')}>
            {SUGGESTED_TICKERS.map((ticker) => (
              <button
                key={ticker}
                className="ticker-chip"
                type="button"
                onClick={() => {
                  onTickerSelect(ticker);
                  setShowSuggestions(false);
                }}
                disabled={isLoading}
              >
                {ticker}
              </button>
            ))}
          </div>
        </form>

        <button
          type="button"
          className="home-search-button home-demo-button"
          onClick={() => onLoadDemo()}
        >
          {t('demoLoadBtn')}
        </button>

        {/* Features */}
        <div className="home-feature-grid">
          <span>{t('homeFeatureDecision')}</span>
          <span>{t('homeFeatureDebate')}</span>
          <span>{t('homeFeatureSources')}</span>
        </div>
      </div>

      {/* Preview card */}
      <div className="home-preview-card" aria-hidden="true">
        <div className="preview-header">
          <span className="preview-symbol">
            <span className="preview-symbol-rotating">{rotatingSymbol}</span>
            <span className="preview-symbol-name">{rotatingName}</span>
          </span>
          <span className="preview-status">{t('homePreviewStatus')}</span>
        </div>
        <div className="preview-shell">
          <div className="preview-section preview-section-primary">
            <span className="preview-kicker">{t('homePreviewAction')}</span>
            <div className="preview-timeline">
              <div className={`preview-step ${activeStep >= 0 ? 'preview-step-active' : ''}`}>
                <span>01</span>
                <strong>{t('homePreviewStepResearch')}</strong>
              </div>
              <div className={`preview-step ${activeStep >= 1 ? 'preview-step-active' : ''}`}>
                <span>02</span>
                <strong>{t('homePreviewStepDebate')}</strong>
              </div>
              <div className={`preview-step ${activeStep >= 2 ? 'preview-step-active' : ''}`}>
                <span>03</span>
                <strong>{t('homePreviewStepBrief')}</strong>
              </div>
            </div>
          </div>

          <div className="preview-section">
            <span className="preview-kicker">{t('homePreviewEvidence')}</span>
            <div className="preview-pill-row">
              <span className="preview-pill">{t('homePreviewMetricDecision')}</span>
              <span className="preview-pill">{t('homePreviewMetricRisk')}</span>
              <span className="preview-pill">{t('homeFeatureDebate')}</span>
              <span className="preview-pill">{t('homeFeatureSources')}</span>
            </div>
          </div>

          <div className="preview-section">
            <span className="preview-kicker">{t('homePreviewAppendix')}</span>
            <div className="preview-list">
              <div className="preview-list-row">
                <span>{t('secondaryDebate')}</span>
                <div className="preview-line" />
              </div>
              <div className="preview-list-row">
                <span>{t('newsTitle')}</span>
                <div className="preview-line" />
              </div>
              <div className="preview-list-row">
                <span>{t('sourceQualityTitle')}</span>
                <div className="preview-line preview-line-short" />
              </div>
            </div>
          </div>
        </div>
        <div className="preview-reason">{t('homePreviewReason')}</div>
      </div>
    </section>
  );
}