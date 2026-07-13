import { AlertCircle } from "lucide-react";

export default function ErrorState({ message }) {
  return (
    <div className="flex items-center justify-center min-h-[60vh] p-5">
      <div className="bg-nested-bg border border-red-500/30 p-8 max-w-lg w-full text-center">
        <AlertCircle className="w-8 h-8 text-critical mx-auto mb-4" />
        <p className="font-data-md text-data-md text-on-surface mb-3">{message}</p>
        <p className="font-body-md text-body-md text-text-dim">
          Verify the ticker is valid (e.g. AAPL or ETERNAL.NS), then retry. If
          the problem persists, the upstream market-data service may be unavailable.
        </p>
      </div>
    </div>
  );
}
