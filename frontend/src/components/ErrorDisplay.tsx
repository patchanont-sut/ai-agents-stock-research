// MarketMind AI Dashboard — Error Display
import { t } from '../i18n';

export function ErrorDisplay({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="error-state">
      <div className="error-icon">⚠️</div>
      <p>{t('errorPrefix')} {message}</p>
      <button className="retry-btn" onClick={onRetry}>{t('tryAgain')}</button>
    </div>
  );
}