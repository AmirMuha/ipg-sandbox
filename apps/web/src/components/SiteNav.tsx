import Link from "next/link";
import { UserMenu } from "./UserMenu";

/**
 * Marketing header — `.mhead` from the design: a sticky, blurred bar with the
 * wordmark, the section links, and the account control.
 *
 * The export's language toggle and sun/moon theme toggle are not ported: the
 * locale is fixed and the app ships dark-only, so both would be dead controls.
 */
export function SiteNav({
  locale,
  active,
}: {
  locale: string;
  active: "home" | "providers" | "pricing" | "console";
}) {
  const isFa = locale === "fa";

  const links = [
    { key: "home", href: `/${locale}/home`, label: isFa ? "خانه" : "Home" },
    { key: "providers", href: `/${locale}/providers`, label: isFa ? "درگاه‌ها" : "Gateways" },
    { key: "pricing", href: `/${locale}/pricing`, label: isFa ? "تعرفه‌ها" : "Pricing" },
  ] as const;

  return (
    <header className="mhead">
      <div className="mhead__in wrap-m">
        <Link className="brand" href={`/${locale}/home`}>
          <span className="brand__mark" aria-hidden="true">
            IP
          </span>
          <span className="brand__text">
            <span className="brand__name">{isFa ? "سندباکس درگاه" : "IPG Sandbox"}</span>
            <span className="brand__sub">
              {isFa ? "شبیه‌ساز درگاه‌های پرداخت" : "Payment gateway simulator"}
            </span>
          </span>
        </Link>

        <nav className="mhead__links" aria-label={isFa ? "ناوبری اصلی" : "Main"}>
          {links.map((link) => (
            <Link
              key={link.key}
              href={link.href}
              aria-current={active === link.key ? "page" : undefined}
              className="mhead__link"
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <span className="mhead__spacer" />

        <div className="mhead__actions">
          <Link href={`/${locale}/console`} className="btn btn--secondary btn--sm">
            {isFa ? "داشبورد تستی" : "Test console"}
          </Link>
          <UserMenu locale={locale} active={active} />
        </div>
      </div>
    </header>
  );
}
