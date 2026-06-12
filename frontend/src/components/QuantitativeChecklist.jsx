export default function QuantitativeChecklist({ items = [] }) {
  return (
    <section className="bg-background border-b border-border-terminal p-5">
      <header className="flex justify-between items-center border-b border-border-terminal pb-2 mb-4">
        <span className="font-data-sm text-data-sm uppercase text-text-dim">
          QUANTITATIVE CHECKLIST
        </span>
      </header>
      <div className="flex flex-col">
        {items.map((item) => (
          <div
            key={item.metric}
            className="flex items-center justify-between py-3 border-b border-border-terminal"
          >
            <span className="font-data-md text-on-surface-variant">{item.metric}</span>
            <div className="flex items-center gap-4">
              <span className="font-data-md text-on-surface">{item.value}</span>
              <div
                className={`flex items-center gap-1.5 ${
                  item.status === "PASS" ? "text-success" : "text-critical"
                }`}
              >
                <span className="font-data-sm uppercase tracking-wider">
                  {item.status}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
