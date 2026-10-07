"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import { getMe } from "../lib/api";

/**
 * The console's primary nav — `.console-nav` from the design. Real routes, not
 * the export's in-page `data-screen` switching: each tab is a URL so
 * back/forward, reload and deep links keep working.
 *
 * Client-only: the active tab needs usePathname, which a server component
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
    <nav className="console-nav" aria-label={t("transactions")} data-testid="tab-group">
      {tabs.map((tab) => {
        const active = pathname === tab.href || pathname?.startsWith(`${tab.href}/`);
        return (
          <Link
            key={tab.href}
            href={tab.href}
            aria-current={active ? "page" : undefined}
            data-testid={`nav-${tab.key}`}
            className="console-nav__link"
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
  const common = { className: "ic", viewBox: "0 0 24 24", "aria-hidden": true } as const;

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
        <path d="M4 17l6-6-6-6M12 19h8" />
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
        <rect x="2" y="6" width="20" height="12" rx="2" />
        <path d="M2 10h20" />
      </svg>
    );
  if (kind === "gear")
    return (
      <svg {...common}>
        <circle cx="12" cy="12" r="3" />
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.6a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9c.14.63.68 1.09 1.32 1.09H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
      </svg>
    );
  return (
    <svg {...common}>
      <path d="M3 6h18M3 12h18M3 18h12" />
    </svg>
  );
}
