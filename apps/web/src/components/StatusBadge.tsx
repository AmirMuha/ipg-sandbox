import type { ReactNode } from "react";

/**
 * Status badge, from the design's `.badge--*` family.
 *
 * The design's rule is that a badge never encodes state by colour alone, so
 * every variant carries an icon as well. Shape does work too: settled/pending
 * are pills, declined/expired are rounded rects, failed is dashed and neutral,
 * refunded is unfilled.
 *
 * The class string is built from plain CSS class names, not Tailwind
 * utilities. That is deliberate: Tailwind's content scanner cannot see classes
 * assembled at runtime, so a status badge built from Tailwind colour tokens
 * would be purged the moment the token names changed. The previous
 * `getStatusColor()` in lib/format.ts had exactly that exposure.
 */

/** Engine status → design badge variant. `delivered` is the webhook spelling. */
const VARIANT: Record<string, string> = {
  settled: "settled",
  approved: "settled",
  delivered: "settled",
  pending: "pending",
  initiated: "pending",
  declined: "declined",
  failed: "declined",
  expired: "expired",
  refunded: "refunded",
};

const ICON: Record<string, ReactNode> = {
  settled: <path d="M20 6L9 17l-5-5" />,
  pending: (
    <>
      <circle cx="12" cy="12" r="10" />
      <path d="M12 6v6l4 2" />
    </>
  ),
  declined: <path d="M18 6L6 18M6 6l12 12" />,
  expired: (
    <>
      <circle cx="12" cy="12" r="10" />
      <path d="M12 8v4M12 16h.01" />
    </>
  ),
  refunded: (
    <>
      <path d="M3 7v6h6" />
      <path d="M3.5 13a9 9 0 1 0 2.1-6.4L3 9" />
    </>
  ),
};

/** The `badge badge--x` class pair, for callers that style their own element. */
export function badgeClass(status: string): string {
  return `badge badge--${VARIANT[status] ?? "failed"}`;
}

export function StatusBadge({
  status,
  children,
  ...rest
}: {
  status: string;
  children: ReactNode;
} & React.HTMLAttributes<HTMLSpanElement>) {
  const variant = VARIANT[status] ?? "failed";
  return (
    <span className={`badge badge--${variant}`} {...rest}>
      <svg className="ic" viewBox="0 0 24 24" aria-hidden="true">
        {ICON[variant]}
      </svg>
      <span>{children}</span>
    </span>
  );
}
