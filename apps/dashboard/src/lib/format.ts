/**
 * Formatting utilities for IPG Sandbox dashboard.
 */

export function formatRial(amount: number, locale = "fa"): string {
  return new Intl.NumberFormat(locale === "fa" ? "fa-IR" : "en-US", {
    style: "decimal",
  }).format(amount);
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

export function getStatusColor(status: string): string {
  switch (status) {
    case "settled":
    case "approved":
    case "delivered":
      return "text-success bg-success/10 border-success/30";
    case "declined":
    case "failed":
      return "text-danger bg-danger/10 border-danger/30";
    case "pending":
    case "initiated":
      return "text-warning bg-warning/10 border-warning/30";
    case "refunded":
      return "text-accent bg-accent/10 border-accent/30";
    default:
      return "text-muted bg-surface-2 border-border";
  }
}
