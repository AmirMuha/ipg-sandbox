import type { Metadata } from "next";
import { setRequestLocale } from "next-intl/server";
import { MarketingShell } from "../../../../components/marketing/MarketingShell";
import { Badge } from "../../../../components/marketing/PageHead";
import { Quickstart } from "../../../../components/marketing/Quickstart";

export const metadata: Metadata = {
  title: "سندباکس درگاه | تست درگاه‌های پرداخت ایرانی",
  description:
    "شبیه‌سازی زرین‌پال، آیدی‌پی و به‌پرداخت ملت در محیط توسعه؛ بدون نیاز به کارت بانکی، نماد اعتماد یا تایید هویت.",
};

function FeatureCard({
  icon,
  title,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <article className="card">
      <span className="card__tag">{icon}</span>
      <h3>{title}</h3>
      <p>{children}</p>
    </article>
  );
}

const GATEWAYS = [
  { id: "zarinpal", detail: "pg/v4 · PaymentRequest و Verify" },
  { id: "idpay", detail: "v1.1 · پرداخت و کال‌بک وضعیت" },
  { id: "behpardakht", detail: "bpPayRequest · SOAP و REST" },
];

export default async function HomePage({
  params: { locale },
}: {
  params: { locale: string };
}) {
  setRequestLocale(locale);

  return (
    <MarketingShell locale={locale} active="home">
      {/* Hero — centred copy over the live quickstart surface */}
      <section className="hero">
        <span className="glow glow--hero" aria-hidden="true" />
        <div className="wrap-m">
          <div className="hero__copy">
            <span className="eyebrow">دامین محلی · بدون ترافیک خارجی</span>
            <h1>درگاه پرداخت را تا آخرین سناریو تست کنید</h1>
            <p className="hero__lead">
              سندباکس درگاه، زرین‌پال، آیدی‌پی و به‌پرداخت ملت را با پاسخ‌های واقعی
              روی لوکال اجرا می‌کند. کارت بانکی لازم نیست، نماد اعتماد لازم نیست؛ فقط
              API خودتان را به لوکال وصل کنید.
            </p>
            <div className="hero__cta">
              <a href={`/${locale}/login`} className="btn btn--primary">
                شروع رایگان
              </a>
              <a href={`/${locale}/providers`} className="btn btn--ghost">
                درگاه‌های پشتیبانی‌شده
              </a>
            </div>
            <div className="mt-6">
              <ul className="oplist">
                <li>
                  <svg
                    className="ic"
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden="true"
                  >
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  <span>تایید هویت، نماد اعتماد و کارت تستی برای شروع لازم نیست</span>
                </li>
              </ul>
            </div>
          </div>

          {/* The design's product surface: a framed panel under the hero copy. */}
          <div className="hero__panel">
            <div className="hero__panel-in hero__panel-in--single">
              <Quickstart />
            </div>
          </div>
        </div>
      </section>

      <section className="section wrap-m">
        <div className="cards">
          <FeatureCard
            title="شبیه‌سازی دقیق"
            icon={
              <svg
                className="ic"
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
              </svg>
            }
          >
            پاسخ‌ها و کدهای خطا دقیقاً مطابق مستندات هر درگاه برگردانده می‌شود؛ از -51
            زرین‌پال تا خطای ۴۱ به‌پرداخت.
          </FeatureCard>
          <FeatureCard
            title="بدون نیاز به احراز هویت"
            icon={
              <svg
                className="ic"
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <rect x="3" y="11" width="18" height="11" rx="2" />
                <path d="M7 11V7a5 5 0 0 1 10 0v4" />
              </svg>
            }
          >
            نه نماد اعتماد می‌خواهد، نه تایید هویت. پروژه را بسازید و همان لحظه اولین
            تراکنش آزمایشی را بزنید.
          </FeatureCard>
          <FeatureCard
            title="خطاهای شبکه و تایم‌اوت"
            icon={
              <svg
                className="ic"
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <polyline points="4 14 10 14 10 20" />
                <polyline points="20 10 14 10 14 4" />
                <line x1="14" y1="10" x2="21" y2="3" />
                <line x1="3" y1="21" x2="10" y2="14" />
              </svg>
            }
          >
            با هدر <code>X-IPG-Scenario</code> سناریوی تایم‌اوت، رد شدن و شکست در مرحله
            تایید را در تست خودتان اجرا کنید.
          </FeatureCard>
        </div>
      </section>

      <section className="section wrap-m">
        <div className="section__head">
          <span className="eyebrow">درگاه‌های فعال</span>
          <h2>سه آداپتور، یک قرارداد</h2>
          <p>
            آدرس و امضای هر آداپتور با درگاه واقعی یکی است؛ فقط دامنه به لوکال تغییر
            می‌کند.
          </p>
        </div>

        <div className="cards">
          {GATEWAYS.map((g) => (
            <article key={g.id} className="card">
              <span className="card__tag" dir="ltr">
                {g.id}
              </span>
              <p>{g.detail}</p>
              <p>
                <Badge tone="success" dot>
                  پایدار
                </Badge>
              </p>
            </article>
          ))}
        </div>

        <article className="card mt-6">
          <span className="eyebrow">چرا لوکال</span>
          <h3>ترافیک بیرونی صفر</h3>
          <p>
            همه سناریوها روی <code dir="ltr">localhost:8080</code> اجرا می‌شوند؛ تست
            شما به هیچ سرویس بیرونی وابسته نیست و در CI هم قابل تکرار است.
          </p>
          <a href={`/${locale}/console`} className="btn btn--secondary">
            باز کردن داشبورد تستی
          </a>
        </article>
      </section>

      <section className="section wrap-m section--tight">
        <div className="cta-band">
          <h2>همین حالا اولین تراکنش را شبیه‌سازی کنید</h2>
          <p>
            پلن توسعه‌دهنده رایگان است و سقف روزانه‌اش برای یک دوره کامل تست کافی است.
          </p>
          <div className="hero__cta">
            <a href={`/${locale}/login`} className="btn btn--primary">
              ساخت حساب رایگان
            </a>
          </div>
        </div>
      </section>
    </MarketingShell>
  );
}
