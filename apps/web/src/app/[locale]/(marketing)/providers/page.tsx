import type { Metadata } from "next";
import { setRequestLocale } from "next-intl/server";
import { MarketingShell } from "../../../../components/marketing/MarketingShell";
import { Badge, PageHead } from "../../../../components/marketing/PageHead";
import { getPlatformProviders } from "../../../../lib/api";

export const dynamic = "force-dynamic";

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
    <svg className="ic" viewBox="0 0 24 24" aria-hidden="true">
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

  let offeredIds: string[] = [];
  try {
    const res = await getPlatformProviders();
    offeredIds = res.providers;
  } catch {
    offeredIds = [];
  }

  const visibleGateways = GATEWAYS.filter((g) => offeredIds.includes(g.id));
  const numFormatter = new Intl.NumberFormat(locale === "fa" ? "fa-IR" : "en-US");
  const countStr = numFormatter.format(visibleGateways.length);
  const countBadge = locale === "fa" ? `${countStr} درگاه` : `${countStr} Gateways`;
  const stableBadge = locale === "fa" ? `${countStr} پایدار` : `${countStr} Stable`;

  return (
    <MarketingShell locale={locale} active="providers">
      <PageHead
        eyebrow={locale === "fa" ? "آداپتورها" : "Adapters"}
        title={locale === "fa" ? "درگاه‌های پشتیبانی‌شده" : "Supported Gateways"}
        badges={
          <>
            <Badge dot>{countBadge}</Badge>
            <Badge tone="success" dot>
              {stableBadge}
            </Badge>
            <Badge tone="success" dot>
              {locale === "fa" ? "شاپرک و پرداخت‌یار" : "Shaparak & Payment Facilitators"}
            </Badge>
          </>
        }
      >
        {locale === "fa" ? (
          <>
            هر آداپتور مسیر، امضای پاسخ و کدهای خطای درگاه اصلی را بازتولید می‌کند.
            کافی است دامنه را به <code className="mono">localhost:8080</code> تغییر دهید.
          </>
        ) : (
          <>
            Each adapter replicates the routes, response signatures, and error codes of the real gateway.
            Simply point your domain to <code className="mono">localhost:8080</code>.
          </>
        )}
      </PageHead>

      <section className="wrap-m">
        {visibleGateways.length === 0 ? (
          <div className="empty" data-testid="no-providers-message">
            <p>
              {locale === "fa"
                ? "در حال حاضر هیچ درگاه پرداختی در دسترس نیست."
                : "No payment gateways are currently offered."}
            </p>
          </div>
        ) : (
          <div className="providers">
            {visibleGateways.map((g) => (
              <article className="provider" key={g.id} data-gateway-id={g.id}>
                <div className="provider__id">
                  <span className="provider__logo" aria-hidden="true">
                    <span className="provider__word">{g.monogram}</span>
                  </span>
                  <h2 className="provider__name">
                    {g.name}
                    <span className="mono small muted block" dir="ltr">
                      {g.latin}
                    </span>
                  </h2>
                  <Badge tone={g.status} dot>
                    {g.statusLabel}
                  </Badge>
                </div>

                <div className="provider__spec">
                  <p className="muted">{g.summary}</p>

                  <dl className="kv">
                    {g.spec.map(([label, value, mono]) => (
                      <div className="kv__row" key={label}>
                        <dt className="kv__label">{label}</dt>
                        <dd
                          className={`kv__val${mono ? " mono" : ""}`}
                          dir={mono ? "ltr" : undefined}
                        >
                          {value}
                        </dd>
                      </div>
                    ))}
                  </dl>

                  <div className="row-flex justify-between">
                    <a
                      href={g.doc.href}
                      download
                      className="btn btn--secondary btn--sm"
                    >
                      <DownloadIcon />
                      دانلود مرجع API
                    </a>
                    <div className="row-flex">
                      <span className="mono small muted">
                        Markdown · {g.doc.size}
                        <span className="block" dir="ltr">
                          {g.doc.href.replace("/docs/", "")}
                        </span>
                      </span>
                      {g.live && (
                        <a
                          href={`/${locale}/gateways`}
                          className="btn btn--ghost btn--sm"
                        >
                          باز کردن آداپتور در داشبورد
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </MarketingShell>
  );
}
