import Link from "next/link";
import Image from "next/image";

interface SiteNavProps {
  locale: string;
  active: "home" | "providers" | "pricing" | "console";
  maxWidthClass?: string;
}

export function SiteNav({
  locale,
  active,
  maxWidthClass = "max-w-[1480px]",
}: SiteNavProps) {
  const isFa = locale === "fa";

  const links = [
    { key: "home", href: `/${locale}/home`, label: isFa ? "خانه" : "Home" },
    { key: "providers", href: `/${locale}/providers`, label: isFa ? "درگاه‌ها" : "Gateways" },
    { key: "pricing", href: `/${locale}/pricing`, label: isFa ? "تعرفه‌ها" : "Pricing" },
    {
      key: "console",
      href: `/${locale}/transactions`,
      label: isFa ? "داشبورد تستی" : "Test Console",
    },
  ] as const;

  return (
    <header className="sticky top-0 z-50 bg-surface/92 backdrop-blur-[12px] border-b border-border">
      <div className={`w-full ${maxWidthClass} mx-auto px-4 md:px-6 flex items-center justify-between gap-6 h-16`}>
        <Link
          href={`/${locale}/home`}
          className="inline-flex items-center gap-2.5 font-display text-[17px] font-semibold text-text"
        >
          <Image
            src="/logo.webp"
            alt="IPG Sandbox"
            width={32}
            height={32}
            className="w-8 h-8 rounded-sm object-contain shrink-0"
            priority
          />
          {isFa ? "سندباکس درگاه" : "IPG Sandbox"}
        </Link>

        <nav className="hidden md:flex items-center gap-6">
          {links.map((link) => (
            <Link
              key={link.key}
              href={link.href}
              className={`inline-flex items-center min-h-11 text-sm font-medium border-b-2 transition-colors duration-fast ease-standard ${
                active === link.key
                  ? "text-text border-accent font-semibold"
                  : "text-muted border-transparent hover:text-text"
              }`}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          {active === "console" ? (
            <Link
              href={`/${locale}/home`}
              className="inline-flex items-center justify-center min-h-9 px-3.5 rounded-sm border border-border bg-surface text-text text-xs font-medium hover:bg-surface-subtle transition-colors duration-fast ease-standard"
            >
              {isFa ? "بازگشت به سایت" : "Back to Site"}
            </Link>
          ) : (
            <>
              <Link
                href={`/${locale}/login`}
                className="hidden sm:inline-flex items-center justify-center min-h-11 px-4 rounded-sm text-sm font-medium text-muted hover:bg-surface-subtle hover:text-text transition-colors duration-fast ease-standard"
              >
                {isFa ? "ورود" : "Login"}
              </Link>
              <Link
                href={`/${locale}/login`}
                className="inline-flex items-center justify-center min-h-11 px-4 rounded-sm border border-border bg-surface text-text text-sm font-medium hover:bg-surface-subtle transition-colors duration-fast ease-standard"
              >
                {isFa ? "شروع رایگان" : "Start Free"}
              </Link>
            </>
          )}
        </div>
      </div>

      <nav className="md:hidden flex items-center gap-4 overflow-x-auto px-4 pb-2.5 text-sm">
        {links.map((link) => (
          <Link
            key={link.key}
            href={link.href}
            className={`shrink-0 font-medium ${
              active === link.key ? "text-accent-ink border-b-2 border-accent" : "text-muted"
            }`}
          >
            {link.label}
          </Link>
        ))}
      </nav>
    </header>
  );
}
