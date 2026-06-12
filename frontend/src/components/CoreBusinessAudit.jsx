import { useState } from "react";
import { auditStatusColor, auditStatusLabel } from "../utils/format";

function AuditRow({ item }) {
  const [expanded, setExpanded] = useState(false);
  const id = String(item.id).padStart(2, "0");

  return (
    <div className="border border-border-terminal bg-background">
      <button
        aria-expanded={expanded}
        className="collapsible-trigger w-full flex items-center justify-between p-3 hover:bg-[#111111] transition-colors focus:outline-none text-left"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3">
          <span className="font-data-sm text-on-surface-variant w-6">{id}</span>
          <span className="font-data-md text-on-surface font-medium">{item.title}</span>
        </div>
        <div
          className={`flex items-center gap-1.5 ${auditStatusColor(item.status)}`}
        >
          <span className="font-data-sm uppercase tracking-wider">
            {auditStatusLabel(item.status)}
          </span>
        </div>
      </button>
      <div className="collapsible-content border-t border-border-terminal bg-nested-bg">
        <div className="p-3 text-on-surface-variant font-body-md text-sm">
          {item.description}
        </div>
      </div>
    </div>
  );
}

export default function CoreBusinessAudit({ items = [] }) {
  return (
    <section className="bg-background p-5 flex-1">
      <header className="border-b border-border-terminal pb-2 mb-4">
        <span className="font-data-sm text-data-sm uppercase text-text-dim">
          CORE BUSINESS AUDIT
        </span>
      </header>
      <div className="space-y-2">
        {items.length === 0 ? (
          <p className="font-body-md text-body-md text-text-dim">
            No qualitative audit available.
          </p>
        ) : (
          items.map((item) => <AuditRow key={item.id} item={item} />)
        )}
      </div>
    </section>
  );
}
