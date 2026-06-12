import Navbar from "./Navbar";
import QuantitativeChecklist from "./QuantitativeChecklist";
import CoreBusinessAudit from "./CoreBusinessAudit";
import IntrinsicValue from "./IntrinsicValue";
import ManagementIntegrity from "./ManagementIntegrity";
import LoadingSkeleton from "./LoadingSkeleton";
import ErrorState from "./ErrorState";
import EmptyState from "./EmptyState";
import { formatExchangeLabel } from "../utils/format";

export default function AnalysisPage({
  ticker,
  tickerInput,
  onTickerInputChange,
  onSubmit,
  onLogoClick,
  data,
  isLoading,
  isError,
  error,
  isDark,
  onToggleTheme,
}) {
  const showEmpty = !ticker && !isLoading;
  const showError = isError && !isLoading;
  const showData = data && !isLoading && !isError;

  return (
    <div className="min-h-screen bg-background">
      <Navbar
        tickerInput={tickerInput}
        onTickerInputChange={onTickerInputChange}
        onSubmit={onSubmit}
        onLogoClick={onLogoClick}
        isDark={isDark}
        onToggleTheme={onToggleTheme}
      />

      <main className="pt-14 min-h-screen">
        {ticker && (
          <div className="p-5 border-b border-border-terminal flex items-end justify-between bg-background">
            <div>
              <div className="flex items-center gap-3 mb-1">
                <h1 className="font-data-lg text-2xl tracking-tight text-on-surface">
                  {ticker}
                </h1>
                <span className="font-data-md text-data-md text-on-surface-variant">
                  {formatExchangeLabel(ticker)}
                </span>
              </div>
            </div>
          </div>
        )}

        {showEmpty && <EmptyState />}
        {isLoading && <LoadingSkeleton ticker={ticker} />}
        {showError && <ErrorState message={error?.message || "Analysis failed"} />}

        {showData && (
          <div className="grid grid-cols-1 md:grid-cols-[1.5fr_1fr] border-b border-border-terminal bg-background">
            <div className="border-r border-border-terminal flex flex-col">
              <QuantitativeChecklist items={data.quantitative_checklist} />
              <CoreBusinessAudit
                items={data.ai_researcher_report?.core_business_audit}
              />
            </div>
            <div className="flex flex-col">
              <IntrinsicValue
                valuation={data.valuation}
                dcfParameters={data.dcf_parameters}
                currency={data.currency}
              />
              <ManagementIntegrity
                items={data.ai_researcher_report?.management_integrity}
              />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
