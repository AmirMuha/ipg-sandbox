/**
 * Stacked outcome ratio track (the design's `.outcome-track`), plus its legend.
 * Server component: it reads no client state, and the segments are sized by
 * flex-grow ratios rather than measured DOM, so no measurement pass is needed.
 */
const SEGMENTS = [
  { key: "approve", className: "bg-accent", fa: "قبول", en: "Approve" },
  { key: "decline", className: "bg-danger", fa: "رد", en: "Decline" },
  { key: "timeout", className: "bg-warning", fa: "اتمام مهلت", en: "Timeout" },
  { key: "verify_fail", className: "bg-text-2", fa: "خطای تأیید", en: "Verify Fail" },
  { key: "pending_settle", className: "bg-border", fa: "در انتظار تسویه", en: "Pending Settle" },
  { key: "refund", className: "bg-accent-ink", fa: "بازگشت وجه", en: "Refund" },
] as const;

export function OutcomeDistribution({
  distribution,
  total,
  locale = "fa",
}: {
  distribution: Record<string, number>;
  total: number;
  locale?: string;
}) {
  const rows = SEGMENTS.map((seg) => ({
    ...seg,
    label: locale === "fa" ? seg.fa : seg.en,
    count: distribution[seg.key] ?? 0,
  })).filter((row) => row.count > 0);

  if (rows.length === 0) {
    return (
      <div
        className="outcome-track flex h-2.5 w-full overflow-hidden rounded-pill bg-surface-subtle"
        data-testid="outcome-distribution"
      />
    );
  }

  const pct = (n: number) => (total > 0 ? `${Math.round((n / total) * 100)}%` : "—");

  return (
    <div data-testid="outcome-distribution">
      <div className="outcome-track flex h-2.5 w-full overflow-hidden rounded-pill bg-surface-subtle">
        {rows.map((row) => (
          <span
            key={row.key}
            className={row.className}
            style={{ flex: `${row.count} 0 0%` }}
            title={`${row.label}: ${row.count}`}
          />
        ))}
      </div>

      <ul className="mt-2.5 flex flex-wrap items-center gap-x-4 gap-y-1.5">
        {rows.map((row) => (
          <li key={row.key} className="flex items-center gap-1.5 text-xs text-muted">
            <span className={`w-2 h-2 rounded-full shrink-0 ${row.className}`} aria-hidden="true" />
            <span>{row.label}</span>
            <span className="text-text-2 font-medium tabular-nums">{row.count}</span>
            <span className="tabular-nums opacity-70">{pct(row.count)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}