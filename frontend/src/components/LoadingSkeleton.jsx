function SkeletonCard({ rows = 4 }) {
  return (
    <div className="bg-nested-bg border border-border-terminal p-5">
      <div className="h-3 w-32 shimmer-row animate-shimmer mb-6" />
      <div className="space-y-3">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="h-4 w-full shimmer-row animate-shimmer" />
        ))}
      </div>
    </div>
  );
}

export default function LoadingSkeleton({ ticker }) {
  return (
    <div className="bg-background">
      <div className="h-0.5 w-full bg-border-terminal overflow-hidden">
        <div className="h-full bg-action-blue animate-scan-progress" />
      </div>

      <p className="font-data-md text-data-md text-text-dim text-center py-4 tracking-wider">
        ANALYZING {ticker}...
      </p>

      <div className="grid grid-cols-1 md:grid-cols-[1.5fr_1fr] border-b border-border-terminal">
        <div className="border-r border-border-terminal flex flex-col gap-0">
          <SkeletonCard rows={5} />
          <SkeletonCard rows={4} />
        </div>
        <div className="flex flex-col gap-0">
          <SkeletonCard rows={6} />
          <SkeletonCard rows={3} />
        </div>
      </div>
    </div>
  );
}
