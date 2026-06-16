// MarketMind AI Dashboard — Loading Spinner
import { t } from '../i18n';

export function LoadingSpinner({ message }: { message: string }) {
  return (
    <div className="loading-container">
      <div className="spinner" />
      <p className="loading-text">{message}</p>
      <p className="loading-subtext">{t('loadingSubtext')}</p>
    </div>
  );
}