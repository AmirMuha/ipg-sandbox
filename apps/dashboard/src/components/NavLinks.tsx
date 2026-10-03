"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

/**
 * Sub-bar tabs from ipg-sandbox-dashboard.html (.sub-bar / .tab-link).
 * Client-only: the active route needs usePathname, which a server component
 * can't read.
 */
export function NavLinks({
  links,
}: {
  links: { href: string; label: string; testId: string; icon: "list" | "bell" | "code" | "chart" }[];
}) {
  const pathname = usePathname();

  return (
    <nav className="tab-group flex items-center" data-testid="tab-group">
      {links.map((l) => {
        const active = pathname === l.href;
        return (
          <Link
            key={l.href}
            href={l.href}
            aria-current={active ? "page" : undefined}
            className={`tab-link flex items-center gap-2 px-3.5 py-2 text-[13px] text-muted border-b-2 border-transparent hover:text-text transition-colors duration-fast ease-standard ${
              active
                ? "!text-text !bg-accent-subtle !border-accent font-medium"
                : ""
            }`}
            data-testid={l.testId}
          >
            <TabIcon kind={l.icon} />
            <span>{l.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}

function TabIcon({ kind }: { kind: "list" | "bell" | "code" | "chart" }) {
  const common = {
    width: 15,
    height: 15,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 2,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
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
  if (kind === "chart")
    return (
      <svg {...common}>
        <line x1="18" y1="20" x2="18" y2="10" />
        <line x1="12" y1="20" x2="12" y2="4" />
        <line x1="6" y1="20" x2="6" y2="14" />
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