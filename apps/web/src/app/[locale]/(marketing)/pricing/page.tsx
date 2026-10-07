import type { Metadata } from "next";
import { setRequestLocale } from "next-intl/server";
import { MarketingShell } from "../../../../components/marketing/MarketingShell";
import { Badge, PageHead } from "../../../../components/marketing/PageHead";
import { UpgradeButton } from "../../../../components/marketing/UpgradeButton";

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
    <svg className="ic" viewBox="0 0 24 24" aria-hidden="true">
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

      <section id="plans" className="wrap-m">
        <div className="tiers">
          {PLANS.map((plan) => (
            <article
              key={plan.id}
              className={`tier${plan.primary ? " tier--featured" : ""}`}
            >
              <div>
                <Badge tone={plan.badgeTone}>{plan.badge}</Badge>
                <h2 className="tier__name mt4">{plan.name}</h2>
                <div className="tier__price">
                  <span className="tier__amount">{plan.price}</span>
                  <span className="tier__per">{plan.period}</span>
                </div>
              </div>
              <p>{plan.summary}</p>
              <ul className="tier__list">
                {plan.features.map((f) => (
                  <li key={f}>
                    <Check />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
              {plan.primary ? (
                <UpgradeButton locale={locale} label={plan.cta} primary={plan.primary} />
              ) : (
                <a href={`/${locale}/login`} className="btn btn--secondary btn--block">
                  {plan.cta}
                </a>
              )}
            </article>
          ))}
        </div>
      </section>

      <section className="section--tight wrap-m">
        <div className="cards">
          {NOTES.map(([title, body]) => (
            <article key={title} className="card">
              <h3>{title}</h3>
              <p>{body}</p>
            </article>
          ))}
        </div>
      </section>
    </MarketingShell>
  );
}
