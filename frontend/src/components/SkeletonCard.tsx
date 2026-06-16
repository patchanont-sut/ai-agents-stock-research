// MarketMind AI Dashboard — Skeleton Loading Card
// Shimmer placeholder shown while analysis is in progress

interface SkeletonCardProps {
  lines?: number;
  height?: string;
}

export function SkeletonCard({ lines = 4, height = '180px' }: SkeletonCardProps) {
  return (
    <div className="skeleton-card" style={{ minHeight: height }}>
      <div className="skeleton-line skeleton-title" />
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="skeleton-line"
          style={{ width: `${70 + Math.random() * 30}%` }}
        />
      ))}
    </div>
  );
}