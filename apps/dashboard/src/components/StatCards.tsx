import { formatRial } from "../lib/format";
import type { Transaction } from "../lib/api";

/**
 * The design's `.stats-grid` — four `.stat-card`s. Values are computed from
 * the real transaction list rather than the mock's hardcoded numbers.
 */
export function StatCards({
  transactions,
  locale,
  deliveryTotal,
  deliveryFailed,
}: {
  transactions: Transaction[];
  locale: string;
  deliveryTotal?: number;
  deliveryFailed?: number;
}) {
  const volume = transactions.reduce((sum, t) => sum + (t.amount_rial ?? 0), 0);
  const approved = transactions.filter((t) =>
    ["settled", "approved"].includes(t.status)
  ).length;
  const declined = transactions.filter((t) =>
    ["declined", "failed"].includes(t.status)
  ).length;
  const total = transactions.length;
  const successRate = total ? (approved / total) * 100 : 0;

  return (
    <section className="grid grid-cols-[repeat(auto-fit,minmax(220px,1fr))] gap-4">
      <div className="stat-card bg-surface border border-border rounded-console p-4 flex flex-col gap-2 relative overflow-hidden">
        <div className="stat-card-title text-xs text-muted font-medium flex items-center justify-between">
          <span>{locale === "fa" ? "حجم کل تراکنش‌ها" : "Total Simulated Volume"}</span>
          <span className="text-[11px] text-muted">IRR</span>
        </div>
        <div className="stat-card-value text-xl font-bold tracking-display text-text tabular-nums">
          {formatRial(volume, locale)}
        </div>
        <div className="stat-card-meta text-xs text-muted flex items-center gap-1.5">
          <span className="stat-pill success text-[11px] font-semibold px-1.5 py-px rounded bg-success-bg text-success-ink">
            {locale === "fa" ? `${total} تراکنش` : `${total} records`}
          </span>
        </div>
      </div>

      <div className="stat-card bg-surface border border-border rounded-console p-4 flex flex-col gap-2 relative overflow-hidden">
        <div className="stat-card-title text-xs text-muted font-medium flex items-center justify-between">
          <span>{locale === "fa" ? "نرخ موفقیت کلی" : "Overall Success Rate"}</span>
          <span className="stat-pill success text-[11px] font-semibold px-1.5 py-px rounded bg-success-bg text-success-ink">
            {successRate.toFixed(1)}%
          </span>
        </div>
        <div className="stat-card-value text-xl font-bold tracking-display text-text tabular-nums">
          {successRate.toFixed(1)}%
        </div>
        <div className="stat-card-meta text-xs text-muted flex items-center gap-1.5">
          <span>
            {approved} {locale === "fa" ? "تایید" : "Approved"} · {declined}{" "}
            {locale === "fa" ? "رد شده" : "Declined"}
          </span>
        </div>
      </div>

      <div className="stat-card bg-surface border border-border rounded-console p-4 flex flex-col gap-2 relative overflow-hidden">
        <div className="stat-card-title text-xs text-muted font-medium flex items-center justify-between">
          <span>{locale === "fa" ? "وضعیت دروازه‌ها" : "Gateway Health"}</span>
          <span className="text-[11px] text-muted">
            {locale === "fa" ? "محلی" : "Local"}
          </span>
        </div>
        <div className="stat-card-value text-xl font-bold tracking-display text-text tabular-nums">
          {new Set(transactions.map((t) => t.adapter_id)).size}
        </div>
        <div className="stat-card-meta text-xs text-muted flex items-center gap-1.5">
          <span className="stat-pill success text-[11px] font-semibold px-1.5 py-px rounded bg-success-bg text-success-ink">
            {locale === "fa" ? "فعال" : "Online"}
          </span>
          <span>{locale === "fa" ? "بدون وابستگی خارجی" : "Zero external network"}</span>
        </div>
      </div>

      <div className="stat-card bg-surface border border-border rounded-console p-4 flex flex-col gap-2 relative overflow-hidden">
        <div className="stat-card-title text-xs text-muted font-medium flex items-center justify-between">
          <span>{locale === "fa" ? "ارسال کال‌بک" : "Callback Deliveries"}</span>
          <span className="status-dot w-[7px] h-[7px] rounded-full bg-success inline-block" />
        </div>
        <div className="stat-card-value text-xl font-bold tracking-display text-text tabular-nums">
          {deliveryTotal ?? "—"}
        </div>
        <div className="stat-card-meta text-xs text-muted flex items-center gap-1.5">
          {deliveryFailed ? (
            <span className="stat-pill error text-[11px] font-semibold px-1.5 py-px rounded bg-danger-bg text-danger-ink">
              {deliveryFailed} {locale === "fa" ? "خطا" : "Failed"}
            </span>
          ) : null}
        </div>
      </div>
    </section>
  );
}