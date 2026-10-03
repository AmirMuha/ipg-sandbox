import { formatRial } from "../lib/format";
import type { ProjectAnalyticsOverview } from "../lib/api";

/**
 * The design's `.stats-grid` — four `.stat-card`s.
 *
 * Every number comes from GET /analytics/overview, not from the transactions list: FR-004
 * exists because these cards used to sum whatever page the table happened to load, so a
 * project with 200 transactions reported the totals of the newest 50.
 */
export function StatCards({
  overview,
  locale,
}: {
  overview: ProjectAnalyticsOverview | null;
  locale: string;
}) {
  const total = overview?.total_transactions ?? 0;
  const successRate = overview?.success_rate_percent ?? 0;
  const settled = overview?.status_breakdown.settled ?? 0;
  const declined = (overview?.status_breakdown.declined ?? 0) + (overview?.status_breakdown.failed ?? 0);
  const funnel = overview?.funnel;

  return (
    <section className="grid grid-cols-[repeat(auto-fit,minmax(220px,1fr))] gap-4">
      <div className="stat-card bg-surface border border-border rounded-console p-4 flex flex-col gap-2 relative overflow-hidden">
        <div className="stat-card-title text-xs text-muted font-medium flex items-center justify-between">
          <span>{locale === "fa" ? "حجم کل تراکنش‌ها" : "Total Simulated Volume"}</span>
          <span className="text-[11px] text-muted">IRR</span>
        </div>
        <div className="stat-card-value text-xl font-bold tracking-display text-text tabular-nums">
          {formatRial(overview?.total_volume_rial ?? 0, locale)}
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
            {settled} {locale === "fa" ? "تایید" : "Approved"} · {declined}{" "}
            {locale === "fa" ? "رد شده" : "Declined"}
          </span>
        </div>
      </div>

      <div className="stat-card bg-surface border border-border rounded-console p-4 flex flex-col gap-2 relative overflow-hidden">
        <div className="stat-card-title text-xs text-muted font-medium flex items-center justify-between">
          <span>{locale === "fa" ? "قیف پرداخت" : "Payment Funnel"}</span>
          <span className="text-[11px] text-muted">
            {locale === "fa" ? "محلی" : "Local"}
          </span>
        </div>
        <div
          className="stat-card-value text-xl font-bold tracking-display text-text tabular-nums"
          data-testid="funnel-settled"
        >
          {funnel?.settled ?? 0}
        </div>
        <div className="stat-card-meta text-xs text-muted flex items-center gap-1.5">
          <span className="stat-pill success text-[11px] font-semibold px-1.5 py-px rounded bg-success-bg text-success-ink">
            {locale === "fa" ? "تسویه" : "Settled"}
          </span>
          <span dir="ltr">
            {funnel?.initiated ?? 0} → {funnel?.hosted ?? 0} → {funnel?.callback ?? 0} →{" "}
            {funnel?.settled ?? 0}
          </span>
        </div>
      </div>

      <div className="stat-card bg-surface border border-border rounded-console p-4 flex flex-col gap-2 relative overflow-hidden">
        <div className="stat-card-title text-xs text-muted font-medium flex items-center justify-between">
          <span>{locale === "fa" ? "ارسال کال‌بک" : "Callback Deliveries"}</span>
          <span className="status-dot w-[7px] h-[7px] rounded-full bg-success inline-block" />
        </div>
        <div className="stat-card-value text-xl font-bold tracking-display text-text tabular-nums">
          {overview?.webhooks.total_deliveries ?? "—"}
        </div>
        <div className="stat-card-meta text-xs text-muted flex items-center gap-1.5">
          {overview?.webhooks.failed ? (
            <span className="stat-pill error text-[11px] font-semibold px-1.5 py-px rounded bg-danger-bg text-danger-ink">
              {overview.webhooks.failed} {locale === "fa" ? "خطا" : "Failed"}
            </span>
          ) : null}
          <span>
            {overview?.gateways.active_total ?? 0}/{overview?.gateways.configured_total ?? 0}{" "}
            {locale === "fa" ? "درگاه فعال" : "gateways active"}
          </span>
        </div>
      </div>
    </section>
  );
}