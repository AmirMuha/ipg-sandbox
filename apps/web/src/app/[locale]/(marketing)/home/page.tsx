import type { Metadata } from "next";
import { setRequestLocale } from "next-intl/server";
import { MarketingShell } from "../../../../components/marketing/MarketingShell";
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
    <article className="bg-surface border border-border rounded-lg p-6 transition-colors duration-base ease-standard hover:border-accent-border hover:shadow-raised">
      <div className="w-10 h-10 grid place-items-center rounded-md border border-border bg-accent-subtle text-accent mb-4">
        {icon}
      </div>
      <h3 className="font-display text-[17px] font-semibold mb-2">{title}</h3>
      <p className="text-sm text-muted leading-[1.7]">{children}</p>
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
      {/* Hero — export's 2-column grid, stacking under 900px */}
      <section className="w-full max-w-[1180px] mx-auto px-4 md:px-6 py-14 md:py-28 grid md:grid-cols-2 gap-8 md:gap-12 items-center">
        <div className="animate-in">
          <span className="inline-flex items-center gap-2 font-mono text-xs font-medium text-accent-ink">
            <svg
              width="13"
              height="13"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              aria-hidden="true"
            >
              <rect x="2" y="5" width="20" height="14" rx="2" />
              <line x1="2" y1="10" x2="22" y2="10" />
            </svg>
            دامین محلی · بدون ترافیک خارجی
          </span>
          <h1 className="font-display text-[30px] md:text-[64px] leading-none font-semibold my-4 text-balance">
            درگاه پرداخت را تا آخرین سناریو تست کنید
          </h1>
          <p className="text-xl text-text-2 leading-[1.62]">
            سندباکس درگاه، زرین‌پال، آیدی‌پی و به‌پرداخت ملت را با پاسخ‌های واقعی
            روی لوکال اجرا می‌کند. کارت بانکی لازم نیست، نماد اعتماد لازم نیست؛ فقط
            API خودتان را به لوکال وصل کنید.
          </p>
          <div className="flex flex-wrap items-center gap-4 mt-6">
            <a
              href={`/${locale}/login`}
              className="inline-flex items-center justify-center min-h-12 px-6 rounded-md bg-accent text-accent-on text-[17px] font-medium hover:bg-accent/92 active:bg-accent/86 transition-colors duration-fast ease-standard"
            >
              شروع رایگان
            </a>
            <a
              href={`/${locale}/providers`}
              className="inline-flex items-center justify-center min-h-12 px-6 rounded-md text-[17px] font-medium text-muted hover:bg-surface-subtle hover:text-text transition-colors duration-fast ease-standard"
            >
              درگاه‌های پشتیبانی‌شده
            </a>
          </div>
          <p className="flex items-center gap-2 mt-4 text-xs text-muted">
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="text-accent shrink-0"
              aria-hidden="true"
            >
              <polyline points="20 6 9 17 4 12" />
            </svg>
            تایید هویت، نماد اعتماد و کارت تستی برای شروع لازم نیست
          </p>
        </div>

        <Quickstart />
      </section>

      <section className="w-full max-w-[1180px] mx-auto px-4 md:px-6 py-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <FeatureCard
          title="شبیه‌سازی دقیق"
          icon={
            <svg
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
          با هدر <code className="font-mono">X-IPG-Scenario</code> سناریوی تایم‌اوت،
          رد شدن و شکست در مرحله تایید را در تست خودتان اجرا کنید.
        </FeatureCard>
      </section>

      <section className="w-full max-w-[1180px] mx-auto px-4 md:px-6 py-12 grid md:grid-cols-[2fr_1fr] gap-8 items-start">
        <div>
          <div className="max-w-[620px] mb-8">
            <span className="inline-flex items-center gap-2 font-mono text-xs font-medium text-accent-ink">
              درگاه‌های فعال
            </span>
            <h2 className="font-display text-xl md:text-[28px] font-semibold my-3">
              سه آداپتور، یک قرارداد
            </h2>
            <p className="text-sm text-muted">
              آدرس و امضای هر آداپتور با درگاه واقعی یکی است؛ فقط دامنه به لوکال تغییر
              می‌کند.
            </p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {GATEWAYS.map((g) => (
              <div
                key={g.id}
                className="bg-surface border border-border rounded-lg p-6 transition-colors duration-base ease-standard hover:border-accent-border hover:shadow-raised"
              >
                <h3 className="font-mono text-sm font-semibold" dir="ltr">
                  {g.id}
                </h3>
                <p className="text-sm text-muted mt-2">{g.detail}</p>
                <p className="mt-3">
                  <span className="inline-flex items-center gap-2 px-2 py-0.5 rounded-sm border border-success-border bg-success-bg text-success-ink font-mono text-xs font-medium">
                    <span className="w-1.5 h-1.5 rounded-full bg-current" />
                    پایدار
                  </span>
                </p>
              </div>
            ))}
          </div>
        </div>

        <aside className="bg-surface border border-border rounded-lg p-6 transition-colors duration-base ease-standard hover:border-accent-border hover:shadow-raised">
          <span className="inline-flex items-center gap-2 font-mono text-xs font-medium text-accent-ink">
            چرا لوکال
          </span>
          <h3 className="font-display text-[17px] font-semibold mt-3">ترافیک بیرونی صفر</h3>
          <p className="text-sm text-muted mt-2 leading-[1.7]">
            همه سناریوها روی{" "}
            <code className="font-mono" dir="ltr">
              localhost:8080
            </code>{" "}
            اجرا می‌شوند؛ تست شما به هیچ سرویس بیرونی وابسته نیست و در CI هم قابل
            تکرار است.
          </p>
          <a
            href={`/${locale}/console`}
            className="mt-4 inline-flex items-center justify-center w-full min-h-11 px-4 rounded-sm border border-border bg-surface text-text text-sm font-medium hover:bg-surface-subtle transition-colors duration-fast ease-standard"
          >
            باز کردن داشبورد تستی
          </a>
        </aside>
      </section>

      <section className="w-full max-w-[1180px] mx-auto px-4 md:px-6 py-12">
        <div className="border border-accent-border bg-accent-subtle rounded-lg p-8 flex flex-wrap items-center justify-between gap-6">
          <div>
            <h2 className="font-display text-xl font-semibold mb-2">
              همین حالا اولین تراکنش را شبیه‌سازی کنید
            </h2>
            <p className="text-sm text-muted">
              پلن توسعه‌دهنده رایگان است و سقف روزانه‌اش برای یک دوره کامل تست کافی
              است.
            </p>
          </div>
          <a
            href={`/${locale}/login`}
            className="inline-flex items-center justify-center min-h-12 px-6 rounded-md bg-accent text-accent-on text-[17px] font-medium hover:bg-accent/92 transition-colors duration-fast ease-standard"
          >
            ساخت حساب رایگان
          </a>
        </div>
      </section>
    </MarketingShell>
  );
}
