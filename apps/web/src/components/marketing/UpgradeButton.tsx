"use client";

import { useEffect, useState } from "react";
import { getSubscription, upgradePlan } from "../../lib/api";

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
  // null = still checking the current plan; keep the button disabled meanwhile so a team
  // user cannot slip a second payment past the API's409 while the check is in flight.
  const [activeTeam, setActiveTeam] = useState<boolean | null>(null);

  useEffect(() => {
    getSubscription()
      .then((sub) => setActiveTeam(sub.tier === "team" && sub.status === "active"))
      .catch(() => setActiveTeam(false));
  }, []);

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

  if (activeTeam) {
    return (
      <a
        href={`/${locale}/settings`}
        data-testid="upgrade-active-team"
        className="mt-auto inline-flex items-center justify-center min-h-11 px-4 rounded-sm text-sm font-medium transition-colors duration-fast ease-standard border border-border bg-surface-subtle text-muted cursor-default"
      >
        پلن تیم فعال است — مدیریت اشتراک
      </a>
    );
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={loading || activeTeam === null}
      data-testid="upgrade-button"
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
