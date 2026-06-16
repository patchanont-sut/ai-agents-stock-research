// MarketMind AI Dashboard — News Feed
// Secondary section styling with alternating row stripes for scanability
import { t } from '../i18n';
import { AnalysisResult } from '../types';

export function NewsFeed({ result }: { result: AnalysisResult }) {
  const newsArticles = result.research?.news_articles || [];
  const redditPosts = result.research?.reddit_posts || [];
  const totalArticles = newsArticles.length + redditPosts.length;

  if (!totalArticles) return null;

  return (
    <div className="card card-secondary">
      <div className="card-title">
        <span className="icon">📰</span>
        {t('secondaryNews')}
        <span className="news-count">{totalArticles} {t('articles')}</span>
      </div>

      <div className="news-feed">
        {newsArticles.map((article) => (
          <div key={article.id} className="news-item">
            <div className="news-title">
              <a href={article.url} target="_blank" rel="noopener noreferrer">
                {article.title}
              </a>
            </div>
            <div className="news-meta">
              <span className="news-source">{article.source}</span>
              {article.sentiment_score != null && (
                <span
                  className={`news-sentiment sentiment-${
                    article.sentiment_score > 0.2
                      ? 'positive'
                      : article.sentiment_score < -0.2
                      ? 'negative'
                      : 'neutral'
                  }`}
                >
                  {article.sentiment_score > 0.2
                    ? '🟢'
                    : article.sentiment_score < -0.2
                    ? '🔴'
                    : '⚪'}{' '}
                  {article.sentiment_score.toFixed(2)}
                </span>
              )}
            </div>
          </div>
        ))}
        {redditPosts.map((post) => (
          <div key={post.id} className="news-item">
            <div className="news-title">
              <a href={post.url} target="_blank" rel="noopener noreferrer">
                {post.title}
              </a>
            </div>
            <div className="news-meta">
              <span className="news-source">{post.source}</span>
              {post.sentiment_score != null && (
                <span
                  className={`news-sentiment sentiment-${
                    post.sentiment_score > 0.2
                      ? 'positive'
                      : post.sentiment_score < -0.2
                      ? 'negative'
                      : 'neutral'
                  }`}
                >
                  {post.sentiment_score > 0.2
                    ? '🟢'
                    : post.sentiment_score < -0.2
                    ? '🔴'
                    : '⚪'}{' '}
                  {post.sentiment_score.toFixed(2)}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
