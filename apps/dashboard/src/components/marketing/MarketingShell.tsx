import Link from "next/link";
import { SiteNav } from "@/components/SiteNav";

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
      <SiteNav locale={locale} active={active} maxWidthClass="max-w-[1180px]" />

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
