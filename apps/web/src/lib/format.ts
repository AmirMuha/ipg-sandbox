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
 * Status → badge markup lives in components/StatusBadge.tsx, as plain design
 * classes. It cannot live here as a Tailwind class string: Tailwind's content
 * scanner only sees literal utilities, so a badge assembled at runtime from a
 * status name would be purged from the stylesheet and render unstyled.
 */

