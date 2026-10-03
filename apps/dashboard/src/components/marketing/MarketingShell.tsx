import Link from "next/link";

/**
 * Marketing frame, ported from the design export's `.header` / `.footer`.
 *
 * Copy is Persian-only and `dir="rtl"` is forced regardless of the active
 * locale, so `/en/home` renders the export faithfully instead of flipping a
 * right-to-left page to LTR and reordering every layout rule.
 */
export function MarketingShell({
  children,
  locale,
  active,
}: {
  children: React.ReactNode;
  locale: string;
  active: "home" | "providers" | "pricing";
}) {
  const links = [
    { key: "home", href: `/${locale}/home`, label: "خانه" },
    { key: "providers", href: `/${locale}/providers`, label: "درگاه‌ها" },
    { key: "pricing", href: `/${locale}/pricing`, label: "تعرفه‌ها" },
    {
      key: "console",
      href: `/${locale}/transactions`,
      label: "داشبورد تستی",
    },
  ] as const;

  return (
    <div dir="rtl" className="min-h-screen flex flex-col">
      <header className="sticky top-0 z-50 bg-surface/92 backdrop-blur-[12px] border-b border-border">
        <div className="w-full max-w-[1180px] mx-auto px-4 md:px-6 flex items-center justify-between gap-6 h-16">
          <Link
            href={`/${locale}/home`}
            className="inline-flex items-center gap-2 font-display text-[17px] font-semibold"
          >
            <span className="w-7 h-7 grid place-items-center rounded-sm bg-accent text-accent-on shrink-0">
              <svg
                width="15"
                height="15"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <rect x="2" y="5" width="20" height="14" rx="2" />
                <line x1="2" y1="10" x2="22" y2="10" />
                <line x1="6" y1="15" x2="6.01" y2="15" />
                <line x1="10" y1="15" x2="12" y2="15" />
              </svg>
            </span>
            سندباکس درگاه
          </Link>

          {/* The export hides .nav-links under 860px with no replacement, which
              strands the pricing/providers pages on a phone. A wrapping nav
              keeps them reachable instead of silently dropping two routes. */}
          <nav className="hidden md:flex items-center gap-6">
            {links.map((link) => (
              <Link
                key={link.key}
                href={link.href}
                className={`inline-flex items-center min-h-11 text-sm font-medium border-b-2 transition-colors duration-fast ease-standard ${
                  active === link.key
                    ? "text-text border-accent"
                    : "text-muted border-transparent hover:text-text"
                }`}
              >
                {link.label}
              </Link>
            ))}
          </nav>

          <div className="flex items-center gap-2">
            <Link
              href={`/${locale}/login`}
              className="hidden sm:inline-flex items-center justify-center min-h-11 px-4 rounded-sm text-sm font-medium text-muted hover:bg-surface-subtle hover:text-text transition-colors duration-fast ease-standard"
            >
              ورود
            </Link>
            <Link
              href={`/${locale}/login`}
              className="inline-flex items-center justify-center min-h-11 px-4 rounded-sm border border-border bg-surface text-text text-sm font-medium hover:bg-surface-subtle transition-colors duration-fast ease-standard"
            >
              شروع رایگان
            </Link>
          </div>
        </div>

        <nav className="md:hidden flex items-center gap-4 overflow-x-auto px-4 pb-3 text-sm">
          {links.map((link) => (
            <Link
              key={link.key}
              href={link.href}
              className={`shrink-0 font-medium ${
                active === link.key ? "text-accent-ink" : "text-muted"
              }`}
            >
              {link.label}
            </Link>
          ))}
        </nav>
      </header>

      <main className="flex-1">{children}</main>

      <footer className="border-t border-border py-8 text-sm text-muted">
        <div className="w-full max-w-[1180px] mx-auto px-4 md:px-6 flex flex-wrap items-center justify-between gap-4">
          <span>سندباکس درگاه — شبیه‌ساز درگاه‌های پرداخت ایرانی</span>
          <nav className="flex flex-wrap gap-6" aria-label="پیوندهای پایانی">
            {links.map((link) => (
              <Link key={link.key} href={link.href} className="hover:text-text">
                {link.label}
              </Link>
            ))}
            <Link href={`/${locale}/login`} className="hover:text-text">
              ورود
            </Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}
