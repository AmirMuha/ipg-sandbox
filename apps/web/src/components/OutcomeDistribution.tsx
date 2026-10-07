/**
 * Stacked outcome ratio track (the design's `.chart`), plus its legend.
 * Server component: it reads no client state, and the segments are sized by
 * flex-grow ratios rather than measured DOM, so no measurement pass is needed.
 *
 * The export keys its track on transaction STATUS (settled/pending/declined/
 * expired/failed). This one is keyed on scenario OUTCOME, which is what
 * /analytics/overview actually returns — hence the scenario-named segment
 * classes in console.css. Same palette, different vocabulary.
 */
const SEGMENTS = [
  { key: "approve", fa: "قبول", en: "Approve" },
  { key: "decline", fa: "رد", en: "Decline" },
  { key: "timeout", fa: "اتمام مهلت", en: "Timeout" },
  { key: "verify_fail", fa: "خطای تأیید", en: "Verify Fail" },
  { key: "pending_settle", fa: "در انتظار تسویه", en: "Pending Settle" },
  { key: "refund", fa: "بازگشت وجه", en: "Refund" },
] as const;

/** `verify_fail` → `verify-fail`, so the key is a legal CSS class fragment.
 *  The `--x` suffix carries colour; `.chart__seg` adds the track geometry. */
const segColor = (key: string) => `chart__seg--${key.replace(/_/g, "-")}`;

export function OutcomeDistribution({
  distribution,
  total,
  locale = "fa",
}: {
  distribution: Record<string, number>;
  total: number;
  locale?: string;
}) {
  const isFa = locale === "fa";
  const rows = SEGMENTS.map((seg) => ({
    ...seg,
    label: locale === "fa" ? seg.fa : seg.en,
    count: distribution[seg.key] ?? 0,
  })).filter((row) => row.count > 0);

  const pct = (n: number) => (total > 0 ? `${Math.round((n / total) * 100)}%` : "—");

  return (
    <div className="card" data-testid="outcome-distribution">
      <div className="card__head">
        <h2 className="card__title">{isFa ? "توزیع نتایج" : "Outcome Distribution"}</h2>
        <span className="badge badge--failed">
          {total} {isFa ? "تراکنش" : "transactions"}
        </span>
      </div>
      <div className="card__body">
        <div className="chart">
          <div
            className="chart__bar"
            role="img"
            aria-label={rows.map((r) => `${r.label} ${r.count}`).join(", ")}
          >
            {rows.map((row) => (
              <span
                key={row.key}
                className={`chart__seg ${segColor(row.key)}`}
                style={{ flex: `${row.count} 0 0%` }}
                title={`${row.label}: ${row.count}`}
              />
            ))}
          </div>

          <div className="chart__legend">
            {rows.map((row) => (
              <span key={row.key} className="chart__key">
                <span className={`chart__swatch ${segColor(row.key)}`} aria-hidden="true" />
                <span>{row.label}</span>
                <span className="chart__count">
                  {row.count} · {pct(row.count)}
                </span>
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
