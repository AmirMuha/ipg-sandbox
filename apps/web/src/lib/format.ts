/**
 * Formatting utilities for IPG Sandbox dashboard.
 */

export function formatRial(amount: number, locale = "fa"): string {
  return new Intl.NumberFormat(locale === "fa" ? "fa-IR" : "en-US", {
    style: "decimal",
  }).format(amount);
}

export function formatToman(amountRial: number, locale = "fa"): string {
  const toman = Math.floor(amountRial / 10);
  return new Intl.NumberFormat(locale === "fa" ? "fa-IR" : "en-US", {
    style: "decimal",
  }).format(toman);
}

export function formatCapacity(count: number, cap: number, locale = "fa"): string {
  const f = (n: number) => new Intl.NumberFormat(locale === "fa" ? "fa-IR" : "en-US").format(n);
  return `${f(count)} / ${f(cap)}`;
}

export function formatDate(dateStr: string, locale = "fa"): string {
  try {
    const d = new Date(dateStr);
    return new Intl.DateTimeFormat(locale === "fa" ? "fa-IR" : "en-US", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(d);
  } catch {
    return dateStr;
  }
}

/**
 * Badges use the `*-ink` / `*-bg` / `*-border` tiers, not the bare semantic
 * hues: on the cream canvas --success is 3.84:1 and --warning 2.91:1, which
 * both FAIL WCAG AA for the 12px badge text. The ink tiers are mixed toward
 * black and clear 4.5:1.
 */
export function getStatusColor(status: string): string {
  switch (status) {
    case "settled":
    case "approved":
    case "delivered":
      return "text-success-ink bg-success-bg border-success-border";
    case "declined":
    case "failed":
      return "text-danger-ink bg-danger-bg border-danger-border";
    case "pending":
    case "initiated":
      return "text-warning-ink bg-warning-bg border-warning-border";
    case "refunded":
      return "text-accent-ink bg-accent-subtle border-accent/30";
    default:
      return "text-muted bg-surface-2 border-border";
  }
}
