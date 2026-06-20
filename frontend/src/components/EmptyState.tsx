// MarketMind AI Dashboard — Home Empty State (Redesigned Dashboard Launch)
import type React from 'react';
import { useState, useRef } from 'react';
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
  onLoadDemo: () => Promise<void>;
  onAddToWatchlist: (ticker: string) => void;
  onRemoveFromWatchlist: (ticker: string) => void;
}

const SUGGESTED_TICKERS = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMD'];

export function EmptyState({
  symbol,
  isLoading,
  history,
  watchlist,
  onSymbolChange,
  onSubmit,
  onTickerSelect,
  onLoadDemo,
  onAddToWatchlist,
  onRemoveFromWatchlist,
}: EmptyStateProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div className="home-dashboard">
      <div className="home-hero-area">
        <div className="home-badge-row">
          <span className="badge badge-accent">{t('homeEyebrow')}</span>
        </div>

        <h1 className="home-hero-headline">
          {t('homeTitle')}
        </h1>
        <p className="home-hero-subtitle">
          {t('homeSubtitle')}
        </p>

        <div className="home-control-card">
          <form onSubmit={onSubmit}>
            <div className="home-search-row">
              <div className="home-search-input-wrapper">
                <input
                  id="home-symbol"
                  ref={inputRef}
                  type="text"
                  className="home-search-input"
                  placeholder={t('searchPlaceholder')}
                  value={symbol}
                  onChange={(event) => onSymbolChange(event.target.value)}
                  disabled={isLoading}
                  autoFocus
                />
                <span className="home-search-hint" aria-hidden="true">↵</span>
              </div>
              <button
                className="home-analyze-btn"
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
                    inputRef.current?.focus();
                  }}
                  disabled={isLoading}
                >
                  {ticker}
                </button>
              ))}
            </div>
          </form>
        </div>
      </div>

      <div className="home-sidebar">
        <div className="home-sidebar-card">
          <div className="home-sidebar-card-header">
            <span>Watchlist</span>
            <button
              className="card-action"
              onClick={() => onAddToWatchlist(symbol)}
              disabled={!symbol.trim()}
              aria-label="Add current symbol to watchlist"
              title="Add current symbol to watchlist"
            >
              + Add
            </button>
          </div>
          <div>
            {watchlist.map((ticker) => (
              <div key={ticker} className="watchlist-item" onClick={() => onTickerSelect(ticker)}>
                <div className="watchlist-item-left">
                  <div className="watchlist-ticker-box">{ticker}</div>
                </div>
                <div className="watchlist-item-action">
                  <button
                    className="watchlist-remove"
                    onClick={(e) => {
                      e.stopPropagation();
                      onRemoveFromWatchlist(ticker);
                    }}
                    aria-label={`Remove ${ticker}`}
                    title={`Remove ${ticker}`}
                  >
                    ×
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="home-sidebar-card">
          <div className="home-sidebar-card-header">
            <span>Recent Activity</span>
            <button className="card-action" onClick={() => onLoadDemo()}>
              Demo
            </button>
          </div>
          <div className="recent-list">
            {history.length === 0 && <div className="local-empty">No saved runs yet</div>}
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
        </div>

        <div className="home-sidebar-card">
          <LiveMonitor watchlist={watchlist} onTickerSelect={onTickerSelect} />
        </div>
      </div>
    </div>
  );
}
