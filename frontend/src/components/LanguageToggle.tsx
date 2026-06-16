// MarketMind AI Dashboard — Language Toggle
import { Language } from '../i18n';

export function localizedValue(value: string | undefined, lang: Language): string {
  if (!value || lang !== 'th') return value || '';

  const labels: Record<string, string> = {
    positive: 'เชิงบวก',
    negative: 'เชิงลบ',
    neutral: 'เป็นกลาง',
    BUY: 'ซื้อ',
    HOLD: 'ถือ',
    SELL: 'ขาย',
    Low: 'ต่ำ',
    Medium: 'ปานกลาง',
    High: 'สูง',
    bull: 'ฝั่ง Bull',
    bear: 'ฝั่ง Bear',
    tie: 'เสมอ',
  };

  return labels[value] || value;
}

export function LanguageToggle({ lang, onChange }: { lang: Language; onChange: (lang: Language) => void }) {
  const toggle = () => {
    const next: Language = lang === 'en' ? 'th' : 'en';
    onChange(next);
  };

  return (
    <button
      className="lang-toggle"
      onClick={toggle}
      title={lang === 'en' ? 'Switch to Thai' : 'Switch to English'}
    >
      {lang === 'en' ? 'EN' : 'TH'}
    </button>
  );
}