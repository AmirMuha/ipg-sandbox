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
        className="btn btn--secondary btn--block"
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
      className={`btn btn--block ${primary ? "btn--primary" : "btn--secondary"}`}
    >
      {loading ? "در حال انتقال به درگاه..." : label}
    </button>
  );
}
