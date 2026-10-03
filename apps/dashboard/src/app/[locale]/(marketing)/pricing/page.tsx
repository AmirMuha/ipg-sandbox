import type { Metadata } from "next";
import { setRequestLocale } from "next-intl/server";
import { MarketingShell } from "../../../../components/marketing/MarketingShell";
import { Badge, PageHead } from "../../../../components/marketing/PageHead";

export const metadata: Metadata = {
  title: "تعرفه‌ها | سندباکس درگاه",
  description:
    "پلن رایگان توسعه‌دهنده و پلن تیم حرفه‌ای برای شبیه‌سازی درگاه‌های پرداخت ایرانی.",
};

const PLANS = [
  {
    id: "developer",
    name: "توسعه‌دهنده",
    badge: "رایگان",
    badgeTone: "neutral" as const,
    price: "۰",
    period: "تومان — همیشه",
    summary: "برای تست‌های اولیه، پروژه‌های شخصی و بررسی سریع یکپارچگی.",
    features: [
      "۱۰۰ درخواست در روز",
      "۲ درگاه پرداخت هم‌زمان",
      "نگهداری لاگ ۲۴ ساعته",
      "پشتیبانی در گیت‌هاب",
    ],
    cta: "ثبت‌نام رایگان",
    primary: false,
  },
  {
    id: "team",
    name: "تیم حرفه‌ای",
    badge: "پیشنهاد ما",
    badgeTone: "accent" as const,
    price: "۱۹۹,۰۰۰",
    period: "تومان / ماه",
    summary:
      "برای استارتاپ‌ها و تیم‌هایی که پرداخت را در مسیر بحرانی محصول دارند.",
    features: [
      "درخواست نامحدود",
      "همه درگاه‌های پشتیبانی‌شده",
      "تاریخچه ۳۰ روزه تراکنش‌ها",
      "وب‌هوک و کال‌بک سفارشی",
      "پشتیبانی تیکت و چت",
    ],
    cta: "شروع آزمایشی ۱۴ روزه",
    primary: true,
  },
] satisfies ReadonlyArray<{
  id: string;
  name: string;
  badge: string;
  badgeTone: "neutral" | "accent";
  price: string;
  period: string;
  summary: string;
  features: string[];
  cta: string;
  primary: boolean;
}>;

const NOTES: ReadonlyArray<readonly [string, string]> = [
  ["صورتحساب", "هر زمان خواستید پلن تیمی را غیرفعال کنید؛ داده‌های ۳۰ روز اخیر باقی می‌ماند."],
  ["دوره آزمایشی", "۱۴ روز کامل با همه درگاه‌ها و بدون محدودیت درخواست؛ نیازی به کارت بانکی نیست."],
  ["اجرای کاملاً محلی", "دایمن روی لوکال اجرا می‌شود؛ حتی در محیط بدون اینترنت هم تست شما تکرارپذیر است."],
];

function Check() {
  return (
    <svg
      width="15"
      height="15"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="text-accent shrink-0 mt-[3px]"
      aria-hidden="true"
    >
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}

export default async function PricingPage({
  params: { locale },
}: {
  params: { locale: string };
}) {
  setRequestLocale(locale);

  return (
    <MarketingShell locale={locale} active="pricing">
      <PageHead eyebrow="تعرفه‌ها" title="ساده و شفاف">
        بدون هزینه‌های پنهان و بدون قرارداد سالانه. پلن توسعه‌دهنده همیشه رایگان
        می‌ماند؛ پلن تیمی وقتی لازم شد فعال می‌شود.
      </PageHead>

      <section
        id="plans"
        className="w-full max-w-[1180px] mx-auto px-4 md:px-6 grid gap-4 sm:grid-cols-2 items-stretch"
      >
        {PLANS.map((plan) => (
          <article
            key={plan.id}
            className={`bg-surface border rounded-lg p-6 md:p-8 flex flex-col gap-4 transition-colors duration-base ease-standard hover:shadow-raised ${
              plan.primary
                ? "border-accent shadow-[0_0_0_1px_rgb(var(--accent))]"
                : "border-border hover:border-accent-border"
            }`}
          >
            <div className="flex items-center justify-between gap-3">
              <h2 className="font-display text-lg font-semibold">{plan.name}</h2>
              <Badge tone={plan.badgeTone}>{plan.badge}</Badge>
            </div>
            <div className="flex items-baseline gap-2">
              <b className="font-display text-[28px] md:text-[42px] font-semibold">
                {plan.price}
              </b>
              <span className="text-sm text-muted">{plan.period}</span>
            </div>
            <p className="text-sm text-muted">{plan.summary}</p>
            <ul className="grid gap-3 pt-4 border-t border-border list-none">
              {plan.features.map((f) => (
                <li
                  key={f}
                  className="flex items-start gap-3 text-sm text-text"
                >
                  <Check />
                  {f}
                </li>
              ))}
            </ul>
            <a
              href={`/${locale}/login`}
              className={`mt-auto inline-flex items-center justify-center min-h-11 px-4 rounded-sm text-sm font-medium transition-colors duration-fast ease-standard ${
                plan.primary
                  ? "bg-accent text-accent-on hover:bg-accent/92"
                  : "border border-border bg-surface text-text hover:bg-surface-subtle"
              }`}
            >
              {plan.cta}
            </a>
          </article>
        ))}
      </section>

      <section className="w-full max-w-[1180px] mx-auto px-4 md:px-6 py-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {NOTES.map(([title, body]) => (
          <div
            key={title}
            className="bg-surface border border-border rounded-lg p-6 transition-colors duration-base ease-standard hover:border-accent-border hover:shadow-raised"
          >
            <h3 className="text-sm font-semibold mb-2">{title}</h3>
            <p className="text-sm text-muted">{body}</p>
          </div>
        ))}
      </section>
    </MarketingShell>
  );
}
