export function formatExchangeLabel(ticker) {
  return `US: ${ticker}`;
}

export function formatPrice(value) {
  const formatted = Math.abs(value).toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return value < 0 ? `-${formatted}` : formatted;
}

export function adjustmentColor(adjustment) {
  if (!adjustment || adjustment === "+0.0%") return "text-on-surface-variant";
  return adjustment.startsWith("-") ? "text-critical" : "text-success";
}

export function auditStatusColor(status) {
  const normalized = (status || "").toUpperCase();
  if (normalized === "PASS") return "text-success";
  if (normalized === "MONITOR") return "text-warning";
  return "text-critical";
}

export function auditStatusLabel(status) {
  const normalized = (status || "").toUpperCase();
  if (normalized === "PASS") return "PASS";
  if (normalized === "MONITOR") return "MONITOR";
  return "FAIL";
}

export function severityColor(severity) {
  const normalized = (severity || "").toLowerCase();
  if (normalized === "pass") return "text-success";
  if (normalized === "caution") return "text-warning";
  return "text-critical";
}

export function severityLabel(severity) {
  const normalized = (severity || "").toLowerCase();
  if (normalized === "pass") return "PASS";
  if (normalized === "caution") return "CAUTION";
  return "RED FLAG";
}
