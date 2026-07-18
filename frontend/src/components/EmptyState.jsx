export default function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-5 text-center">
      <p className="font-data-md text-data-md text-text-dim mb-2">
        Enter a ticker above to begin analysis.
      </p>
      <p className="font-body-md text-body-md text-text-dim/70">
        Supports S&amp;P 500 equities
      </p>
    </div>
  );
}
