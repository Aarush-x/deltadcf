import { adjustmentColor, formatPrice } from "../utils/format";

const DCF_ROWS = [
  { key: "stage_1_growth", label: "Stage 1 Gr" },
  { key: "stage_2_growth", label: "Stage 2 Gr" },
  { key: "discount_rate", label: "Discount Rate" },
];

export default function IntrinsicValue({ valuation, dcfParameters, currency }) {
  const price = valuation?.intrinsic_price_per_share ?? 0;
  const isNegative = price < 0;

  return (
    <section className="bg-background border-b border-border-terminal p-5">
      <header className="border-b border-border-terminal pb-2 mb-4">
        <span className="font-data-sm text-data-sm uppercase text-text-dim">
          INTRINSIC VALUE / SHARE
        </span>
      </header>

      <div className="flex flex-col items-center justify-center py-8 border border-border-terminal bg-background mb-6">
        <div className="flex items-baseline gap-2 mb-2">
          <span
            className={`font-data-lg text-5xl ${
              isNegative ? "text-critical" : "text-success"
            }`}
          >
            {formatPrice(price)}
          </span>
          {currency && (
            <span className="font-data-md text-xl text-text-dim uppercase">
              {currency}
            </span>
          )}
        </div>
        <span className="font-data-sm text-data-sm text-text-dim uppercase tracking-widest">
          {isNegative ? "NEGATIVE EQUITY VALUE" : "INTRINSIC VALUE"}
        </span>
      </div>

      <div className="w-full">
        <table className="w-full text-left font-data-md">
          <thead>
            <tr className="border-b border-border-terminal">
              <th className="py-2 text-text-dim font-normal uppercase text-xs">
                Parameter
              </th>
              <th className="py-2 text-text-dim font-normal uppercase text-xs text-right">
                Base
              </th>
              <th className="py-2 text-text-dim font-normal uppercase text-xs text-right">
                Adj
              </th>
              <th className="py-2 text-text-dim font-normal uppercase text-xs text-right">
                Final
              </th>
            </tr>
          </thead>
          <tbody>
            {DCF_ROWS.map(({ key, label }) => {
              const row = dcfParameters?.[key];
              if (!row) return null;
              return (
                <tr key={key} className="border-b border-border-terminal">
                  <td className="py-2 text-on-surface-variant">{label}</td>
                  <td className="py-2 text-right text-on-surface-variant">
                    {row.base}
                  </td>
                  <td
                    className={`py-2 text-right ${adjustmentColor(row.adjustment)}`}
                  >
                    {row.adjustment}
                  </td>
                  <td className="py-2 text-right text-on-surface font-bold">
                    {row.final}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
