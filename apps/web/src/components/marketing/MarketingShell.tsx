import Link from "next/link";
import { SiteNav } from "@/components/SiteNav";

/**
 * Marketing frame — `.mkt` from the design: the sticky `.mhead`, a page body,
 * and `.mfoot`.
 *
 * `className="mkt"` is load-bearing, not decorative: the design's marketing-only
 * geometry and its reshaped `.btn` / `.card` are scoped under it in
 * styles/marketing.css, so the sheet cannot leak into the console.
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
    { key: "console", href: `/${locale}/console`, label: "داشبورد تستی" },
  ] as const;

  return (
    <div dir="rtl" className="mkt">
      <SiteNav locale={locale} active={active} />

      <main>{children}</main>

      <footer className="mfoot">
        <div className="wrap-m">
          <div className="mfoot__bottom">
            <span>سندباکس درگاه — شبیه‌ساز درگاه‌های پرداخت ایرانی</span>
            <nav className="flex flex-wrap gap-6" aria-label="پیوندهای پایانی">
              {links.map((link) => (
                <Link key={link.key} href={link.href}>
                  {link.label}
                </Link>
              ))}
              <Link href={`/${locale}/login`}>ورود</Link>
            </nav>
          </div>
        </div>
      </footer>
    </div>
  );
}
