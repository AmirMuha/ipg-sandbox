"use client";

import { useState } from "react";
import { upgradePlan } from "../../lib/api";

export function UpgradeButton({
  locale,
  label,
  primary,
}: {
  locale: string;
  label: string;
  primary: boolean;
}) {
  const [loading, setLoading] = useState(false);

  async function handleClick() {
    setLoading(true);
    try {
      const res = await upgradePlan("team");
      if (res.payment_url) {
        window.location.href = res.payment_url;
      }
    } catch {
      window.location.href = `/${locale}/login`;
    } finally {
      setLoading(false);
    }
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={loading}
      className={`mt-auto inline-flex items-center justify-center min-h-11 px-4 rounded-sm text-sm font-medium transition-colors duration-fast ease-standard disabled:opacity-50 ${
        primary
          ? "bg-accent text-accent-on hover:bg-accent/92"
          : "border border-border bg-surface text-text hover:bg-surface-subtle"
      }`}
    >
      {loading ? "در حال انتقال به درگاه..." : label}
    </button>
  );
}
