"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import { getMe } from "../lib/api";

/**
 * Sub-bar tabs from ipg-sandbox-dashboard.html (.seg / .seg-btn).
 * Client-only: the active route needs usePathname, which a server component
 * can't read.
 */
export function NavLinks({ locale }: { locale: string }) {
  const t = useTranslations("nav");
  const pathname = usePathname();
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    let mounted = true;
    getMe()
      .then((data) => {
        if (mounted && data.user?.is_admin) {
          setIsAdmin(true);
        }
      })
      .catch(() => {});
    return () => {
      mounted = false;
    };
  }, []);

  const tabs = [
    { key: "transactions", href: `/${locale}/console`, label: t("transactions"), icon: "list" as const },
    { key: "webhooks", href: `/${locale}/webhooks`, label: t("webhooks"), icon: "bell" as const },
    { key: "gateways", href: `/${locale}/gateways`, label: t("gateways"), icon: "card" as const },
    { key: "sdk", href: `/${locale}/sdk`, label: t("sdk"), icon: "code" as const },
    { key: "settings", href: `/${locale}/settings`, label: t("settings"), icon: "gear" as const },
    ...(isAdmin
      ? [
          {
            key: "admin",
            href: `/${locale}/admin`,
            label: t("admin"),
            icon: "shield" as const,
          },
        ]
      : []),
  ];

  return (
    <nav
      className="seg flex items-center gap-1 p-0.5 rounded-sm bg-surface-subtle border border-border overflow-x-auto snap-x snap-mandatory"
      data-testid="tab-group"
    >
      {tabs.map((tab) => {
        const active = pathname === tab.href || pathname?.startsWith(`${tab.href}/`);
        return (
          <Link
            key={tab.href}
            href={tab.href}
            aria-current={active ? "page" : undefined}
            data-testid={`nav-${tab.key}`}
            className={`seg-btn shrink-0 snap-start inline-flex items-center gap-2 min-h-9 px-3.5 py-1.5 rounded-sm text-[13px] transition-colors duration-fast ease-standard ${
              active
                ? "bg-surface-elevated text-text font-semibold shadow-[0_1px_2px_rgba(32,25,20,0.08)]"
                : "text-muted font-medium hover:text-text"
            }`}
          >
            <TabIcon kind={tab.icon} />
            <span>{tab.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}

function TabIcon({ kind }: { kind: "list" | "bell" | "code" | "shield" | "card" | "gear" }) {
  const common = {
    width: 15,
    height: 15,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 2,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true,
  };
  if (kind === "bell")
    return (
      <svg {...common}>
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
        <path d="M13.73 21a2 2 0 0 1-3.46 0" />
      </svg>
    );
  if (kind === "code")
    return (
      <svg {...common}>
        <polyline points="16 18 22 12 16 6" />
        <polyline points="8 6 2 12 8 18" />
      </svg>
    );
  if (kind === "shield")
    return (
      <svg {...common}>
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      </svg>
    );
  if (kind === "card")
    return (
      <svg {...common}>
        <rect x="2" y="5" width="20" height="14" rx="2" />
        <line x1="2" y1="10" x2="22" y2="10" />
      </svg>
    );
  if (kind === "gear")
    return (
      <svg {...common}>
        <circle cx="12" cy="12" r="3" />
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
      </svg>
    );
  return (
    <svg {...common}>
      <line x1="8" y1="6" x2="21" y2="6" />
      <line x1="8" y1="12" x2="21" y2="12" />
      <line x1="8" y1="18" x2="21" y2="18" />
      <line x1="3" y1="6" x2="3.01" y2="6" />
      <line x1="3" y1="12" x2="3.01" y2="12" />
      <line x1="3" y1="18" x2="3.01" y2="18" />
    </svg>
  );
}
