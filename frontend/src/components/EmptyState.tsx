// MarketMind AI Dashboard — Home Empty State
import type React from 'react';
import { useState, useEffect, useRef, useMemo } from 'react';
import { t } from '../i18n';
import { LiveMonitor } from './LiveMonitor';

interface EmptyStateProps {
  symbol: string;
  isLoading: boolean;
  history: {
    id: string;
    symbol: string;
    action: string;
    confidence: number | null;
  }[];
  watchlist: string[];
  onSymbolChange: (symbol: string) => void;
  onSubmit: (event: React.FormEvent) => void;
  onTickerSelect: (ticker: string) => void;
  onModeChange: (mode: 'single' | 'compare') => void;
  onLoadDemo: () => Promise<void>;
  onAddToWatchlist: (ticker: string) => void;
  onRemoveFromWatchlist: (ticker: string) => void;
}

const SUGGESTED_TICKERS = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMD'];

const TICKER_LOOKUP: { symbol: string; name: string }[] = [
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

function filterTickers(query: string): { symbol: string; name: string }[] {
  if (!query.trim()) return [];
  const upper = query.trim().toUpperCase();
  return TICKER_LOOKUP.filter(
    (t) => t.symbol.startsWith(upper) || t.name.toUpperCase().includes(upper)
  ).slice(0, 6);
}

export function EmptyState({
  symbol,
  isLoading,
  history,
  watchlist,
  onSymbolChange,
  onSubmit,
  onTickerSelect,
  onModeChange,
  onLoadDemo,
  onAddToWatchlist,
  onRemoveFromWatchlist,
}: EmptyStateProps) {
  const [showSuggestions, setShowSuggestions] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  // Filtered suggestions
  const suggestions = useMemo(() => filterTickers(symbol), [symbol]);

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

  return (
    <section className="home-hero">
      <div className="home-copy">
        <h1 className="home-dashboard-title">{t('homeTitle')}</h1>
        <p className="home-dashboard-subtitle">{t('homeSubtitle')}</p>

        {/* Mode switch */}
        <div className="home-mode-row">
          {[
            { value: 'single' as const, icon: '◆', titleKey: 'singleMode', descriptionKey: 'singleModeDesc' },
            { value: 'compare' as const, icon: '◈', titleKey: 'compareMode', descriptionKey: 'compareModeDesc' },
          ].map((mode) => (
            <button key={mode.value} className="home-mode-pill" onClick={() => onModeChange(mode.value)}>
              <span className="home-mode-icon">{mode.icon}</span>
              <span className="home-mode-text">
                <strong>{t(mode.titleKey)}</strong>
                <small>{t(mode.descriptionKey)}</small>
              </span>
            </button>
          ))}
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
                  onSymbolChange(ticker);
                  setShowSuggestions(false);
                  inputRef.current?.focus();
                }}
                disabled={isLoading}
              >
                {ticker}
              </button>
            ))}
          </div>
        </form>

        <div className="local-lists">
          <section className="local-list">
            <div className="local-list-header">
              <strong>Watchlist</strong>
              <button
                type="button"
                onClick={() => onAddToWatchlist(symbol)}
                disabled={!symbol.trim()}
                aria-label="Add current symbol to watchlist"
                title="Add current symbol to watchlist"
              >
                Add to watchlist
              </button>
            </div>
            <div className="local-chip-row">
              {watchlist.map((ticker) => (
                <span className="local-chip" key={ticker}>
                  <button type="button" onClick={() => onTickerSelect(ticker)} disabled={isLoading}>
                    {ticker}
                  </button>
                  <button type="button" aria-label={`Remove ${ticker}`} onClick={() => onRemoveFromWatchlist(ticker)}>
                    ×
                  </button>
                </span>
              ))}
            </div>
          </section>

          <section className="local-list">
            <div className="local-list-header">
              <strong>Recent</strong>
              <button type="button" onClick={() => onLoadDemo()}>
                Demo
              </button>
            </div>
            <div className="recent-list">
              {history.length === 0 && <span className="local-empty">No saved runs yet</span>}
              {history.map((item) => (
                <button type="button" key={item.id} className="recent-item" onClick={() => onTickerSelect(item.symbol)}>
                  <span>{item.symbol}</span>
                  <small>
                    {item.action}
                    {item.confidence !== null ? ` · ${Math.round(item.confidence * 100)}%` : ''}
                  </small>
                </button>
              ))}
            </div>
          </section>
        </div>

        <LiveMonitor watchlist={watchlist} onTickerSelect={onTickerSelect} />
      </div>
    </section>
  );
}
