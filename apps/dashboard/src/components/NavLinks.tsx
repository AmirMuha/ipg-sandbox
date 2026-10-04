"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTranslations } from "next-intl";

/**
 * Sub-bar tabs from ipg-sandbox-dashboard.html (.seg / .seg-btn).
 * Client-only: the active route needs usePathname, which a server component
 * can't read.
 *
 * The three segments point at /transactions, /webhooks and /settings. The third
 * is the adapters+SDK page but keeps its /settings URL — the route and its
 * `project-history-cap-input` / `project-webhook-retry-max-input` testids are
 * the console's settings surface under test.
 */
export function NavLinks({ locale }: { locale: string }) {
  const t = useTranslations("nav");
  const pathname = usePathname();

  const tabs = [
    { key: "transactions", href: `/${locale}/transactions`, label: t("transactions"), icon: "list" as const },
    { key: "webhooks", href: `/${locale}/webhooks`, label: t("webhooks"), icon: "bell" as const },
    {
      key: "settings",
      href: `/${locale}/settings`,
      label: locale === "fa" ? "درگاه‌ها و SDK" : "Adapters & SDK",
      icon: "code" as const,
    },
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

function TabIcon({ kind }: { kind: "list" | "bell" | "code" }) {
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