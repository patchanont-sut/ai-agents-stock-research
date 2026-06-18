// MarketMind AI Dashboard — Live Monitor for Watchlist
import { useState, useEffect, useRef, useCallback } from 'react';
import { api } from '../api/client';

type PulseItem = {
  symbol: string;
  price: number | null;
  changePercent: number | null;
  latestHeadline: string | null;
  hasNewNews: boolean;
  hasBigMove: boolean;
  error: string | null;
  checkedAt: string;
};

interface LiveMonitorProps {
  watchlist: string[];
  onTickerSelect: (ticker: string) => void;
}

const POLL_INTERVAL = 60_000;
const MOVE_THRESHOLD = 1.5;

export function LiveMonitor({ watchlist, onTickerSelect }: LiveMonitorProps) {
  const [active, setActive] = useState(false);
  const [items, setItems] = useState<Map<string, PulseItem>>(new Map());
  const prevMapRef = useRef<Map<string, { price: number | null; seenUrls: Set<string> }>>(new Map());

  const poll = useCallback(async () => {
    if (watchlist.length === 0) return;
    const results = await Promise.all(
      watchlist.map(async (symbol) => {
        const [priceRes, newsRes] = await Promise.allSettled([
          api.getPrice(symbol),
          api.getNews(symbol),
        ]);

        const errMessages: string[] = [];
        let price: number | null = null;
        let changePercent: number | null = null;

        if (priceRes.status === 'fulfilled') {
          price = priceRes.value.price ?? null;
          changePercent = priceRes.value.change_percent ?? null;
        } else {
          errMessages.push('Price fetch failed');
        }

        let latestHeadline: string | null = null;
        let latestUrl: string | null = null;
        const articles = newsRes.status === 'fulfilled' ? newsRes.value.articles : [];

        if (articles.length > 0) {
          latestHeadline = articles[0].title;
          latestUrl = articles[0].url;
        }

        const prev = prevMapRef.current.get(symbol);
        const prevPrice = prev?.price ?? null;
        const seenUrls = prev?.seenUrls ?? new Set<string>();

        let hasBigMove = false;
        if (price !== null && prevPrice !== null && prevPrice !== 0) {
          const pctChange = Math.abs((price - prevPrice) / prevPrice * 100);
          hasBigMove = pctChange >= MOVE_THRESHOLD;
        }

        const hasNewNews = prev !== undefined && latestUrl !== null && !seenUrls.has(latestUrl);

        const newSeen = new Set(seenUrls);
        if (latestUrl) newSeen.add(latestUrl);
        prevMapRef.current.set(symbol, { price, seenUrls: newSeen });

        return {
          symbol,
          price,
          changePercent,
          latestHeadline,
          hasNewNews,
          hasBigMove,
          error: errMessages.length > 0 ? errMessages.join('; ') : null,
          checkedAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
      })
    );

    setItems((prev) => {
      const next = new Map(prev);
      for (const item of results) {
        next.set(item.symbol, item);
      }
      return next;
    });
  }, [watchlist]);

  useEffect(() => {
    if (!active || watchlist.length === 0) return;
    poll();
    const id = setInterval(poll, POLL_INTERVAL);
    return () => clearInterval(id);
  }, [active, watchlist, poll]);

  if (watchlist.length === 0) {
    return (
      <div className="live-monitor">
        <div className="local-list-header">
          <strong>Live Monitor</strong>
        </div>
        <div className="live-monitor-empty">Add tickers to watchlist first.</div>
      </div>
    );
  }

  return (
    <div className="live-monitor">
      <div className="local-list-header">
        <strong>Live Monitor</strong>
        <button type="button" onClick={() => setActive((value) => !value)}>
          {active ? 'Stop' : 'Start monitor'}
        </button>
      </div>

      {active && (
        <div className="live-monitor-grid">
          {watchlist.map((symbol) => {
            const item = items.get(symbol);
            const hasPrice = item?.price !== null && item?.price !== undefined;
            return (
              <div key={symbol} className="live-monitor-row">
                <button
                  type="button"
                  className="live-monitor-main"
                  onClick={() => onTickerSelect(symbol)}
                >
                  <span className="live-monitor-symbol">{symbol}</span>
                  <span className="live-monitor-headline" title={item?.latestHeadline ?? ''}>
                    {item?.error || item?.latestHeadline || 'Checking...'}
                  </span>
                </button>

                <div className="live-monitor-meta">
                  {hasPrice && (
                    <span className="live-monitor-quote">
                      <span className="live-monitor-price">${item.price.toFixed(2)}</span>
                      {item.changePercent !== null && (
                        <span className={`live-monitor-change ${item.changePercent >= 0 ? 'change-up' : 'change-down'}`}>
                          {item.changePercent >= 0 ? '+' : ''}{item.changePercent.toFixed(2)}%
                        </span>
                      )}
                    </span>
                  )}
                  {item?.hasNewNews && <span className="live-badge news-badge">New</span>}
                  {item?.hasBigMove && <span className="live-badge move-badge">Move</span>}
                  {item?.checkedAt && <span className="live-monitor-time">{item.checkedAt}</span>}
                  <button
                    type="button"
                    className="live-monitor-analyze"
                    onClick={() => onTickerSelect(symbol)}
                  >
                    Analyze
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
