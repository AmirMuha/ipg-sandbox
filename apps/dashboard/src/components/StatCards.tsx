import { formatCapacity, formatRial, formatToman } from "../lib/format";
import type { ProjectAnalyticsOverview } from "../lib/api";

/**
 * The design's `.stats-grid` — four `.stat-card`s.
 *
 * Every number comes from GET /analytics/overview, not from the transactions list: FR-004
 * exists because these cards used to sum whatever page the table happened to load, so a
 * project with 200 transactions reported the totals of the newest 50.
 *
 * Text uses the *-ink tiers on small labels — see the contrast note in lib/format.ts —
 * never the bare --success/--warning hues, which fail AA on the cream canvas.
 */
export function StatCards({
  overview,
  historyCap,
  locale,
}: {
  overview: ProjectAnalyticsOverview | null;
  historyCap?: number;
  locale: string;
}) {
  const isFa = locale === "fa";
  const total = overview?.total_transactions ?? 0;
  const settled = overview?.status_breakdown.settled ?? 0;
  const funnel = overview?.funnel;
  const cap = historyCap ?? 0;
  const capPct = cap > 0 ? Math.min(100, Math.round((total / cap) * 100)) : 0;

  const card = "stat-card bg-surface border border-border rounded-console p-4 flex flex-col gap-2 relative overflow-hidden";
  const title = "stat-card-title text-xs text-muted font-medium flex items-center justify-between gap-2";
  const value = "stat-card-value text-xl font-bold tracking-display text-text tabular-nums";
  const meta = "stat-card-meta text-xs text-muted flex items-center gap-1.5 flex-wrap";

  return (
    <section className="stats-grid grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
      <div className={card}>
        <div className={title}>
          <span>{isFa ? "حجم کل تراکنش‌ها" : "Total Volume"}</span>
          <span className="text-[11px]">IRR</span>
        </div>
        <div className={value}>{formatRial(overview?.total_volume_rial ?? 0, locale)}</div>
        <div className={meta}>
          <span>
            ≈ {formatToman(overview?.total_volume_rial ?? 0, locale)}{" "}
            {isFa ? "تومان" : "Toman"}
          </span>
        </div>
      </div>

      <div className={card}>
        <div className={title}>
          <span>{isFa ? "نرخ موفقیت" : "Success Rate"}</span>
          <span className="stat-pill success text-[11px] font-semibold px-1.5 py-px rounded bg-success-bg text-success-ink">
            {(overview?.success_rate_percent ?? 0).toFixed(1)}%
          </span>
        </div>
        <div className={value}>{(overview?.success_rate_percent ?? 0).toFixed(1)}%</div>
        <div className={meta}>
          <span>
            {formatRial(settled, locale)} {isFa ? "تراکنش تسویه‌شده" : "settled transactions"}
          </span>
        </div>
      </div>

      <div className={card}>
        <div className={title}>
          <span>{isFa ? "ظرفیت نگهداری" : "History Capacity"}</span>
          <span className="text-[11px]">{capPct}%</span>
        </div>
        <div className={value}>
          {cap > 0 ? formatCapacity(total, cap, locale) : formatRial(total, locale)}
        </div>
        {/* .meter — fill width is total/cap, clamped so an over-cap project never
            overflows the track. */}
        <div
          className="meter h-1.5 w-full rounded-pill bg-surface-subtle overflow-hidden"
          role="meter"
          aria-valuenow={capPct}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={isFa ? "ظرفیت نگهداری تاریخچه" : "History capacity used"}
        >
          <div className="h-full rounded-pill bg-accent" style={{ width: `${capPct}%` }} />
        </div>
        {/* Rendered unconditionally: this route prerenders at build time with no
            engine reachable, so a null-guard here silently drops the funnel. */}
        <div className={meta}>
          <span dir="ltr">
            {funnel?.initiated ?? 0} → {funnel?.hosted ?? 0} → {funnel?.callback ?? 0} →{" "}
            <span data-testid="funnel-settled">{funnel?.settled ?? 0}</span>
          </span>
        </div>
      </div>

      <div className={card}>
        <div className={title}>
          <span>{isFa ? "ارسال کال‌بک" : "Callback Deliveries"}</span>
          <span className="status-dot" aria-hidden="true" />
        </div>
        <div className={value}>
          {formatRial(overview?.webhooks.delivered ?? 0, locale)}
        </div>
        <div className={meta}>
          <span>
            {formatRial(overview?.webhooks.delivered ?? 0, locale)} /{" "}
            {formatRial(overview?.webhooks.total_deliveries ?? 0, locale)}{" "}
            {isFa ? "ارسال موفق" : "delivered"}
          </span>
          {overview?.webhooks.failed ? (
            <span className="stat-pill error text-[11px] font-semibold px-1.5 py-px rounded bg-danger-bg text-danger-ink">
              {overview.webhooks.failed} {isFa ? "خطا" : "Failed"}
            </span>
          ) : null}
        </div>
      </div>
    </section>
  );
}