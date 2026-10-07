import { formatCapacity, formatRial, formatToman } from "../lib/format";
import type { ProjectAnalyticsOverview } from "../lib/api";

/**
 * The design's `.stats` row — four `.stat` cards.
 *
 * Every number comes from GET /analytics/overview, not from the transactions list: FR-004
 * exists because these cards used to sum whatever page the table happened to load, so a
 * project with 200 transactions reported the totals of the newest 50.
 *
 * The design's cards carry a period-over-period delta the API has no concept of, so the
 * third line keeps reporting what it actually knows (the settlement funnel, the capacity
 * meter) rather than inventing a trend.
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

  return (
    <section className="stats" data-testid="stats-grid">
      <div className="stat">
        <span className="stat__num num">{formatRial(overview?.total_volume_rial ?? 0, locale)}</span>
        <span className="stat__cap">{isFa ? "حجم کل تراکنش‌ها" : "Total Volume"}</span>
        <span className="stat__delta muted">
          ≈ {formatToman(overview?.total_volume_rial ?? 0, locale)} {isFa ? "تومان" : "Toman"}
        </span>
      </div>

      <div className="stat">
        <span className="stat__num num">{(overview?.success_rate_percent ?? 0).toFixed(1)}%</span>
        <span className="stat__cap">{isFa ? "نرخ موفقیت" : "Success Rate"}</span>
        <span className="stat__delta">
          <span className="badge badge--settled">
            {formatRial(settled, locale)} {isFa ? "تسویه‌شده" : "settled"}
          </span>
        </span>
      </div>

      <div className="stat">
        <span className="stat__num num">
          {cap > 0 ? formatCapacity(total, cap, locale) : formatRial(total, locale)}
        </span>
        <span className="stat__cap">{isFa ? "ظرفیت نگهداری" : "History Capacity"}</span>
        {/* .meter — no design equivalent, kept and restyled: the fill is total/cap,
            clamped so an over-cap project never overflows the track. */}
        <div
          className="meter"
          role="meter"
          aria-valuenow={capPct}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={isFa ? "ظرفیت نگهداری تاریخچه" : "History capacity used"}
        >
          <div style={{ inlineSize: `${capPct}%` }} />
        </div>
        {/* Rendered unconditionally: this route prerenders with no engine reachable,
            so a null-guard here silently drops the funnel. */}
        <span className="stat__delta muted">
          <span dir="ltr">
            {funnel?.initiated ?? 0} → {funnel?.hosted ?? 0} → {funnel?.callback ?? 0} →{" "}
            <span data-testid="funnel-settled">{funnel?.settled ?? 0}</span>
          </span>
        </span>
      </div>

      <div className="stat">
        <span className="stat__num num">
          {formatRial(overview?.webhooks.delivered ?? 0, locale)}
        </span>
        <span className="stat__cap">{isFa ? "ارسال کال‌بک" : "Callback Deliveries"}</span>
        <span className="stat__delta muted">
          <span>
            {formatRial(overview?.webhooks.delivered ?? 0, locale)} /{" "}
            {formatRial(overview?.webhooks.total_deliveries ?? 0, locale)}{" "}
            {isFa ? "ارسال موفق" : "delivered"}
          </span>
          {overview?.webhooks.failed ? (
            <span className="badge badge--declined">
              {overview.webhooks.failed} {isFa ? "خطا" : "Failed"}
            </span>
          ) : null}
        </span>
      </div>
    </section>
  );
}
