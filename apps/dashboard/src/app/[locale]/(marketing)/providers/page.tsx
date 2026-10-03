import type { Metadata } from "next";
import { setRequestLocale } from "next-intl/server";
import { MarketingShell } from "../../../../components/marketing/MarketingShell";
import { Badge, PageHead } from "../../../../components/marketing/PageHead";

export const metadata: Metadata = {
  title: "درگاه‌های پشتیبانی‌شده | سندباکس درگاه",
  description:
    "مشخصات فنی آداپتورهای زرین‌پال، آیدی‌پی، به‌پرداخت ملت و سامان کیش در سندباکس درگاه.",
};

/** `[label, value, mono?]`. The third slot only exists on some rows, so it is
 *  part of the tuple type rather than inferred as `string | boolean | undefined`
 *  off the union of array literal shapes. */
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
    latin: "zarinpal · pg/v4",
    status: "success",
    statusLabel: "پایدار",
    summary:
      "درخواست پرداخت، تایید تراکنش، تسهیم و استعلام. خطاهای رایج درگاه مثل -51 و -33 هم قابل اجرا هستند.",
    spec: [
      ["پروتکل", "REST نسخه ۴ (همچنین SOAP)"],
      ["مسیر", "/zarinpal/pg/v4/payment/request.json", true],
      [
        "سناریوها",
        "تایید، رد شدن، تایم‌اوت ۵۰۴، شکست در مرحله تایید، بازگشت وجه",
      ],
    ],
    doc: { href: "/docs/zarinpal-api-reference.md", size: "۵ کیلوبایت" },
    live: true,
  },
  {
    id: "idpay",
    monogram: "idp",
    name: "آیدی‌پی",
    latin: "idpay · v1.1",
    status: "success",
    statusLabel: "پایدار",
    summary:
      "وب‌سرویس نسخه ۱.۱، پرداخت مستقیم، ساخت درگاه شخصی و ارسال کال‌بک وضعیت پرداخت.",
    spec: [
      ["پروتکل", "REST نسخه ۱.۱ با هدر X-API-KEY"],
      ["مسیر", "/idpay/v1.1/payment", true],
      ["پاسخ", "فیلدهای status و track_id مطابق درگاه اصلی"],
    ],
    doc: { href: "/docs/idpay-api-reference.md", size: "۴ کیلوبایت" },
    live: true,
  },
  {
    id: "behpardakht",
    monogram: "bp",
    name: "به‌پرداخت ملت",
    latin: "behpardakht mellat · pgw",
    status: "success",
    statusLabel: "پایدار",
    summary:
      "پروتکل SOAP و REST با متدهای bpPayRequest، bpVerifyRequest و bpSettleRequest؛ کال‌بک‌های بانک ملت هم بازتولید می‌شود.",
    spec: [
      ["پروتکل", "WSDL (SOAP) و REST"],
      ["مسیر", "/behpardakht/services/pgw", true],
      ["خطاها", "کدهای ۴۱ و ۴۳ قابل شبیه‌سازی است"],
    ],
    doc: {
      href: "/docs/behpardakht-mellat-api-reference.md",
      size: "۴ کیلوبایت",
    },
    live: true,
  },
  {
    id: "saman-kish",
    monogram: "sk",
    name: "سامان کیش (سپ)",
    latin: "saman kish · beta",
    status: "warn",
    statusLabel: "آزمایشی",
    summary:
      "توکن‌سازی، خرید مستقیم و وریفای دو مرحله‌ای. خطاهای شبکه شاپرک در این آداپتور هنوز کامل پوشش داده نشده است.",
    spec: [
      ["پروتکل", "REST با توکن‌سازی"],
      ["محدودیت", "وریفای دو مرحله‌ای در حال تکمیل است"],
    ],
    doc: { href: "/docs/saman-kish-coverage.md", size: "۳ کیلوبایت" },
    live: false,
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
            <Badge dot>۴ درگاه</Badge>
            <Badge tone="success" dot>
              ۳ پایدار
            </Badge>
            <Badge tone="warn" dot>
              ۱ آزمایشی
            </Badge>
            <Badge>۴ سند قابل دانلود</Badge>
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
                {g.id === "saman-kish" ? "دانلود گزارش پوشش" : "دانلود مرجع API"}
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
              داشبورد تستی هر چهار آداپتور را با داده‌های نمونه و سناریوهای آماده در
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
