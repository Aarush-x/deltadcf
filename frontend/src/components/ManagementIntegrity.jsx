import { severityColor, severityLabel } from "../utils/format";

export default function ManagementIntegrity({ items = [] }) {
  return (
    <section className="bg-background p-5 flex-1">
      <header className="border-b border-border-terminal pb-2 mb-4 flex items-center gap-2">
        <span className="font-data-sm text-data-sm uppercase text-text-dim">
          INTEGRITY ALERTS
        </span>
      </header>
      <div className="space-y-4">
        {items.length === 0 ? (
          <p className="font-body-md text-body-md text-text-dim">
            No integrity alerts reported.
          </p>
        ) : (
          items.map((item, i) => (
            <div
              key={`${item.title}-${i}`}
              className="border border-border-terminal bg-nested-bg flex flex-col gap-2 p-3"
            >
              <div className="flex items-center mb-1">
                <span
                  className={`font-data-sm font-bold uppercase ${severityColor(item.severity)}`}
                >
                  {severityLabel(item.severity)}
                </span>
              </div>
              <p className="font-body-md text-on-surface-variant text-sm mt-1">
                {item.description}
              </p>
            </div>
          ))
        )}
      </div>
    </section>
  );
}
