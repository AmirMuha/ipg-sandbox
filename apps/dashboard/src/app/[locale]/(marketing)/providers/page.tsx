import type { Metadata } from "next";
import { setRequestLocale } from "next-intl/server";
import { MarketingShell } from "../../../../components/marketing/MarketingShell";
import { Badge, PageHead } from "../../../../components/marketing/PageHead";

export const metadata: Metadata = {
  title: "درگاه‌های پشتیبانی‌شده | سندباکس درگاه",
  description:
    "مشخصات فنی و مسیرهای ارتباطی ۱۳ درگاه پرداخت فعال شاپرک و پرداخت‌یار در سندباکس درگاه.",
};

type SpecRow = readonly [string, string] | readonly [string, string, true];

const GATEWAYS: ReadonlyArray<{
  id: string;
  monogram: string;
  name: string;
  latin: string;
  status: "success" | "warn";
  statusLabel: string;
  summary: string;
  spec: readonly SpecRow[];
  doc: { href: string; size: string };
  live: boolean;
}> = [
  {
    id: "zarinpal",
    monogram: "zp",
    name: "زرین‌پال",
    latin: "zarinpal · REST",
    status: "success",
    statusLabel: "پایدار",
    summary: "پرداخت‌یار زرین‌پال با پشتیبانی از درخواست پرداخت، تایید و استعلام و بازگشت وجه.",
    spec: [
      ["پروتکل", "REST JSON"],
      ["مسیر", "/zarinpal/request/payment", true],
      ["سناریوها", "تایید، رد، تایم‌اوت، شکست تایید، استرداد"],
    ],
    doc: { href: "/docs/zarinpal-api-reference.md", size: "۵ کیلوبایت" },
    live: true,
  },
  {
    id: "idpay",
    monogram: "idp",
    name: "آیدی‌پی",
    latin: "idpay · REST",
    status: "success",
    statusLabel: "پایدار",
    summary: "وب‌سرویس نسخه ۱.۱، پرداخت مستقیم با هدر احراز هویت X-API-KEY.",
    spec: [
      ["پروتکل", "REST JSON"],
      ["مسیر", "/idpay/payment", true],
      ["پاسخ", "فیلدهای status و track_id"],
    ],
    doc: { href: "/docs/idpay-api-reference.md", size: "۴ کیلوبایت" },
    live: true,
  },
  {
    id: "behpardakht",
    monogram: "bp",
    name: "به‌پرداخت ملت",
    latin: "behpardakht mellat · SOAP/WSDL",
    status: "success",
    statusLabel: "پایدار",
    summary: "پروتکل SOAP و WSDL بانک ملت با متدهای bpPaymentRequest، bpVerifyRequest و bpReversalRequest.",
    spec: [
      ["پروتکل", "SOAP 1.1 XML & WSDL"],
      ["مسیر", "/behpardakht/MellatPaymentGateway", true],
      ["کال‌بک", "فرم POST شاپرکی با ResCode"],
    ],
    doc: { href: "/docs/behpardakht-mellat-api-reference.md", size: "۴ کیلوبایت" },
    live: true,
  },
  {
    id: "saman",
    monogram: "sep",
    name: "سامان کیش (سپ)",
    latin: "saman sep · REST/SOAP",
    status: "success",
    statusLabel: "پایدار",
    summary: "توکن‌سازی با متد onlinepg، صفحه اختصاصی پرداخت، تایید وریفای و استرداد تراکنش.",
    spec: [
      ["پروتکل", "REST & SOAP WSDL"],
      ["مسیر", "/saman/onlinepg/onlinepg", true],
      ["تایید", "متد verifyTxn با کدهای خطای منفی"],
    ],
    doc: { href: "/docs/saman-sep-api-reference.md", size: "۴ کیلوبایت" },
    live: true,
  },
  {
    id: "sadad",
    monogram: "sd",
    name: "سداد (بانک ملی)",
    latin: "sadad melli · REST",
    status: "success",
    statusLabel: "پایدار",
    summary: "درگاه پرداخت سداد با متدهای PaymentRequest، کال‌بک شاپرکی و Advice/Verify.",
    spec: [
      ["پروتکل", "REST JSON & WSDL"],
      ["مسیر", "/sadad/api/v0/Request/PaymentRequest", true],
      ["شناسه‌ها", "RetrivalReferenceNumber و SystemTraceNo"],
    ],
    doc: { href: "/docs/sadad-melli-api-reference.md", size: "۴ کیلوبایت" },
    live: true,
  },
  {
    id: "parsian",
    monogram: "pec",
    name: "تجارت الکترونیک پارسیان (تاپ)",
    latin: "parsian pec · SOAP",
    status: "success",
    statusLabel: "پایدار",
    summary: "وب‌سرویس EShopService با پروتکل SOAP و متدهای SalePaymentRequest و ConfirmPayment.",
    spec: [
      ["پروتکل", "SOAP WSDL / ASMX"],
      ["مسیر", "/parsian/EShopService.asmx", true],
      ["احراز هویت", "کد پین پذیرنده (PIN)"],
    ],
    doc: { href: "/docs/parsian-pec-api-reference.md", size: "۴ کیلوبایت" },
    live: true,
  },
  {
    id: "pasargad",
    monogram: "pep",
    name: "پرداخت الکترونیک پاسارگاد",
    latin: "pasargad pep · REST",
    status: "success",
    statusLabel: "پایدار",
    summary: "درگاه پرداخت پاسارگاد با امضای دیجیتال RSA و تایید پرداخت دو مرحله‌ای.",
    spec: [
      ["پروتکل", "REST JSON با امضای اختیاری"],
      ["مسیر", "/pasargad/api/payment/purchase", true],
      ["کال‌بک", "ارسال invoiceNumber و trackId"],
    ],
    doc: { href: "/docs/pasargad-pep-api-reference.md", size: "۴ کیلوبایت" },
    live: true,
  },
  {
    id: "asan_pardakht",
    monogram: "ap",
    name: "آسان پرداخت (آپ)",
    latin: "asan pardakht · REST/SOAP",
    status: "success",
    statusLabel: "پایدار",
    summary: "درگاه آسان پرداخت با متد Token و استعلام وریفای، سازگار با SDKهای بانکی.",
    spec: [
      ["پروتکل", "REST & SOAP WSDL"],
      ["مسیر", "/asan_pardakht/Token", true],
      ["پاسخ", "مقادیر PayResult و شماره پیگیری"],
    ],
    doc: { href: "/docs/asan-pardakht-api-reference.md", size: "۴ کیلوبایت" },
    live: true,
  },
  {
    id: "pardakht_novin",
    monogram: "pna",
    name: "پرداخت نوین آرین",
    latin: "pardakht novin · REST/SOAP",
    status: "success",
    statusLabel: "پایدار",
    summary: "وب‌سرویس GenerateToken و متد Verify پرداخت نوین اقتصاد نوین.",
    spec: [
      ["پروتکل", "REST & SOAP WSDL"],
      ["مسیر", "/pardakht_novin/GenerateToken", true],
      ["کال‌بک", "RefNum و ResNum با وضعیت State"],
    ],
    doc: { href: "/docs/pardakht-novin-api-reference.md", size: "۴ کیلوبایت" },
    live: true,
  },
  {
    id: "irankish",
    monogram: "ik",
    name: "کارت اعتباری ایران‌کیش",
    latin: "irankish · REST",
    status: "success",
    statusLabel: "پایدار",
    summary: "وب‌سرویس توکن نسخه ۱ و متد verify با شناسه پایانه و شناسه پذیرنده.",
    spec: [
      ["پروتکل", "REST JSON"],
      ["مسیر", "/irankish/api/v1/token", true],
      ["کد نتیجه", "resultCode: 00 برای تراکنش موفق"],
    ],
    doc: { href: "/docs/irankish-api-reference.md", size: "۴ کیلوبایت" },
    live: true,
  },
  {
    id: "fanava",
    monogram: "fn",
    name: "فن‌آوا کارت",
    latin: "fanava card · REST/SOAP",
    status: "success",
    statusLabel: "پایدار",
    summary: "درگاه پرداخت فن‌آوا کارت با متدهای payment و verify.",
    spec: [
      ["پروتکل", "REST & SOAP WSDL"],
      ["مسیر", "/fanava/payment", true],
      ["تایید", "فیلد Status عددی"],
    ],
    doc: { href: "/docs/fanava-api-reference.md", size: "۴ کیلوبایت" },
    live: true,
  },
  {
    id: "sarmayeh",
    monogram: "sm",
    name: "پرداخت الکترونیک سرمایه",
    latin: "sarmayeh bank · REST/SOAP",
    status: "success",
    statusLabel: "پایدار",
    summary: "درگاه پرداخت بانک سرمایه با متدهای payment و verify.",
    spec: [
      ["پروتکل", "REST & SOAP WSDL"],
      ["مسیر", "/sarmayeh/payment", true],
      ["شناسه‌ها", "Terminal ID و کد بازگشتی"],
    ],
    doc: { href: "/docs/sarmayeh-api-reference.md", size: "۴ کیلوبایت" },
    live: true,
  },
  {
    id: "sizpay",
    monogram: "sz",
    name: "سیزپی (پرداخت‌یار)",
    latin: "sizpay · REST",
    status: "success",
    statusLabel: "پایدار",
    summary: "پرداخت‌یار سیزپی با متدهای Token و Confirm و پشتیبانی از سناریوهای مختلف.",
    spec: [
      ["پروتکل", "REST JSON"],
      ["مسیر", "/sizpay/api/Payment/Token", true],
      ["پاسخ", "کد وضعیت ResCode: 0"],
    ],
    doc: { href: "/docs/sizpay-api-reference.md", size: "۴ کیلوبایت" },
    live: true,
  },
];

function DownloadIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
    </svg>
  );
}

export default async function ProvidersPage({
  params: { locale },
}: {
  params: { locale: string };
}) {
  setRequestLocale(locale);

  return (
    <MarketingShell locale={locale} active="providers">
      <PageHead
        eyebrow="آداپتورها"
        title="درگاه‌های پشتیبانی‌شده"
        badges={
          <>
            <Badge dot>۱۳ درگاه</Badge>
            <Badge tone="success" dot>
              ۱۳ پایدار
            </Badge>
            <Badge tone="success" dot>
              شاپرک و پرداخت‌یار
            </Badge>
          </>
        }
      >
        هر آداپتور مسیر، امضای پاسخ و کدهای خطای درگاه اصلی را بازتولید می‌کند.
        کافی است دامنه را به <code className="font-mono">localhost:8080</code> تغییر
        دهید.
      </PageHead>

      <section className="w-full max-w-[1180px] mx-auto px-4 md:px-6 grid gap-4">
        {GATEWAYS.map((g) => (
          <article
            key={g.id}
            className="bg-surface border border-border rounded-lg p-6 grid gap-4 transition-colors duration-base ease-standard hover:border-accent-border hover:shadow-raised"
          >
            <div className="flex items-start justify-between gap-4 flex-wrap">
              <div className="flex items-center gap-3">
                <span
                  className="w-10 h-10 grid place-items-center rounded-md border border-accent-border bg-accent-subtle text-accent-ink font-mono text-sm font-semibold shrink-0"
                  aria-hidden="true"
                >
                  {g.monogram}
                </span>
                <h2 className="text-[17px] font-semibold">
                  {g.name}
                  <span
                    className="block font-mono text-xs text-muted font-normal"
                    dir="ltr"
                  >
                    {g.latin}
                  </span>
                </h2>
              </div>
              <Badge tone={g.status} dot>
                {g.statusLabel}
              </Badge>
            </div>

            <p className="text-sm text-muted">{g.summary}</p>

            <table className="w-full border-collapse text-sm">
              <tbody>
                {g.spec.map(([label, value, mono]) => (
                  <tr key={label}>
                    <th
                      scope="row"
                      className="text-start font-medium text-text-2 py-3 border-t border-border align-top w-[168px] max-md:block max-md:w-auto max-md:border-t-0 max-md:pb-0"
                    >
                      {label}
                    </th>
                    <td
                      className={`py-3 border-t border-border align-top max-md:pt-1 ${mono ? "font-mono text-xs" : ""}`}
                      dir={mono ? "ltr" : undefined}
                    >
                      {value}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div className="flex items-center justify-between gap-4 flex-wrap border-t border-border pt-4">
              <a
                href={g.doc.href}
                download
                className="inline-flex items-center gap-2 min-h-11 px-4 rounded-sm border border-border bg-surface text-text text-sm font-medium hover:bg-surface-elevated transition-colors duration-fast ease-standard"
              >
                <DownloadIcon />
                دانلود مرجع API
              </a>
              <span className="text-xs text-text-2 font-mono">
                Markdown · {g.doc.size}
                <span className="block text-muted" dir="ltr">
                  {g.doc.href.replace("/docs/", "")}
                </span>
                {g.live && (
                  <a
                    href={`/${locale}/settings`}
                    className="block mt-1 text-accent-ink hover:text-accent"
                  >
                    باز کردن آداپتور در داشبورد
                  </a>
                )}
              </span>
            </div>
          </article>
        ))}
      </section>

      <section className="w-full max-w-[1180px] mx-auto px-4 md:px-6 my-12 md:my-28">
        <div className="border border-border bg-surface-subtle rounded-lg p-8 flex flex-wrap items-center justify-between gap-6">
          <div>
            <h2 className="font-display text-xl font-semibold mb-2">
              یکی را انتخاب کنید و اولین درخواست را بزنید
            </h2>
            <p className="text-sm text-muted">
              داشبورد تستی هر سیزده آداپتور را با داده‌های نمونه و سناریوهای آماده در
              اختیار شما می‌گذارد.
            </p>
          </div>
          <a
            href={`/${locale}/transactions`}
            className="inline-flex items-center justify-center min-h-12 px-6 rounded-md bg-accent text-accent-on text-[17px] font-medium hover:bg-accent/92 transition-colors duration-fast ease-standard"
          >
            باز کردن داشبورد تستی
          </a>
        </div>
      </section>
    </MarketingShell>
  );
}
