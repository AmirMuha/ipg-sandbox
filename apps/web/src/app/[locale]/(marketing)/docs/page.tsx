import type { Metadata } from "next";
import Link from "next/link";
import { setRequestLocale } from "next-intl/server";
import { MarketingShell } from "../../../../components/marketing/MarketingShell";
import { Badge, PageHead } from "../../../../components/marketing/PageHead";

export const metadata: Metadata = {
  title: "مستندات | سندباکس درگاه",
  description:
    "راهنمای گام‌به‌گام اتصال به سندباکس درگاه: حساب، کلید API، ساخت پرداخت، صفحه پرداخت میزبان، تایید، وب‌هوک و سناریوها.",
};

function Section({
  id,
  eyebrow,
  title,
  children,
}: {
  id: string;
  eyebrow: string;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section id={id} className="section wrap-m">
      <div className="section__head">
        <span className="eyebrow">{eyebrow}</span>
        <h2>{title}</h2>
      </div>
      {children}
    </section>
  );
}

function Code({ title, code }: { title: string; code: string }) {
  return (
    <div className="term mt-4">
      <div className="term__bar">
        <span className="term__dots" aria-hidden="true">
          <i />
          <i />
          <i />
        </span>
        <span className="term__file">{title}</span>
      </div>
      <div className="term__body">
        <pre>{code}</pre>
      </div>
    </div>
  );
}

function Cell({
  children,
  mono = false,
}: {
  children: React.ReactNode;
  mono?: boolean;
}) {
  return (
    <td>
      {/* ponytail: static cell, so override the matrix's click-to-copy cursor. */}
      <div className="mx__cell" style={{ cursor: "default" }}>
        {mono ? <span className="mx__val">{children}</span> : children}
      </div>
    </td>
  );
}

const RAW_DOCS = [
  {
    href: "/docs/zarinpal-api-reference.md",
    title: "مرجع API زرین‌پال",
    note: "REST نسخه ۴ · درخواست، تایید، استرداد",
  },
  {
    href: "/docs/idpay-api-reference.md",
    title: "مرجع API آیدی‌پی",
    note: "نسخه ۱.۱ · هدر X-API-KEY",
  },
  {
    href: "/docs/behpardakht-mellat-api-reference.md",
    title: "مرجع API به‌پرداخت ملت",
    note: "SOAP/WSDL · bpPayRequest",
  },
  {
    href: "/docs/saman-kish-coverage.md",
    title: "پوشش آداپتور سامان",
    note: "میزان تطابق با درگاه واقعی",
  },
];

export default async function DocsPage({
  params: { locale },
}: {
  params: { locale: string };
}) {
  setRequestLocale(locale);

  return (
    <MarketingShell locale={locale} active="docs">
      <PageHead
        eyebrow="راهنمای اتصال"
        title="از کلید API تا وب‌هوک، در یک مسیر"
        badges={
          <>
            <Badge dot>محیط تست</Badge>
            <Badge tone="success" dot>
              زرین‌پال فعال
            </Badge>
            <Badge tone="neutral">بدون پول واقعی</Badge>
          </>
        }
      >
        این راهنما برای فروشنده‌ای است که می‌خواهد پرداخت را روی
        <code className="mono" dir="ltr">
          {" "}
          https://ipg.sandboxed.ir{" "}
        </code>
        بسازد. هیچ پول واقعی جابه‌جا نمی‌شود و هیچ داده کارت بانکی گرفته نمی‌شود.
      </PageHead>

      <Section id="what" eyebrow="۰۱ — پیش از شروع" title="این سندباکس چه می‌کند">
        <div className="cards">
          <article className="card">
            <span className="card__tag">میزبان</span>
            <h3>آدرس پایه</h3>
            <p>
              همه مثال‌های این صفحه روی
              <code dir="ltr"> https://ipg.sandboxed.ir </code>
              کار می‌کنند. مسیرهای <code dir="ltr">/api</code> و پیشوند هر درگاه به موتور
              سندباکس می‌روند و بقیه به داشبورد.
            </p>
          </article>
          <article className="card">
            <span className="card__tag">بدون کارت</span>
            <h3>صفحه پرداخت شبیه‌سازی</h3>
            <p>
              صفحه پرداخت هیچ فیلد شماره کارت، CVV، تاریخ انقضا یا رمز دوم ندارد؛ فقط سه
              دکمه تایید، انصراف و رها کردن.
            </p>
          </article>
          <article className="card">
            <span className="card__tag">فعال‌سازی</span>
            <h3>یک درگاه به‌صورت پیش‌فرض</h3>
            <p>
              در پروژه تازه فقط زرین‌پال فعال است. بقیه درگاه‌ها در داشبورد با برچسب
              «غیرفعال» دیده می‌شوند و فعال‌سازی آن‌ها در اختیار اپراتور سندباکس است.
            </p>
          </article>
        </div>

        <div className="card mt-6" style={{ padding: "var(--sp-5)" }}>
          <dl className="kv">
            <div className="kv__row">
              <dt className="kv__label">سقف روزانه</dt>
              <dd className="kv__val mono">۱۰۰ تراکنش</dd>
            </div>
            <div className="kv__row">
              <dt className="kv__label">
                تاریخچه
                <small>ردیف‌های قدیمی‌تر به‌صورت خودکار حذف می‌شوند</small>
              </dt>
              <dd className="kv__val mono">۱۰۰۰ ردیف</dd>
            </div>
            <div className="kv__row">
              <dt className="kv__label">مکث سناریوی timeout</dt>
              <dd className="kv__val mono">۳۰ ثانیه</dd>
            </div>
            <div className="kv__row">
              <dt className="kv__label">تسویه سناریوی pending_settle</dt>
              <dd className="kv__val mono">۵ ثانیه</dd>
            </div>
            <div className="kv__row">
              <dt className="kv__label">تلاش مجدد وب‌هوک</dt>
              <dd className="kv__val mono">۳ بار · ۱/۲/۴ ثانیه</dd>
            </div>
          </dl>
        </div>
      </Section>

      <Section id="api-key" eyebrow="۰۲ — دسترسی" title="حساب و کلید API">
        <ol className="oplist">
          <li>
            در <Link href={`/${locale}/login`}>صفحه ورود</Link> ثبت‌نام کنید. نشست شما در
            کوکی <code dir="ltr">ipg_session</code> نگه داشته می‌شود.
          </li>
          <li>
            به <Link href={`/${locale}/settings/api-keys`}>تنظیمات ← کلیدهای API</Link>{" "}
            بروید و یک کلید بسازید.
          </li>
          <li>
            توکن با پیشوند <code dir="ltr">ipg_key_</code> فقط یک بار نمایش داده می‌شود؛
            همان لحظه کپی کنید. حداکثر ۱۰ کلید فعال می‌توانید داشته باشید.
          </li>
          <li>
            کلید را در هر درخواست به‌صورت{" "}
            <code dir="ltr">Authorization: Bearer ipg_key_…</code> بفرستید تا تراکنش‌ها به
            پروژه خودتان نسبت داده شوند.
          </li>
        </ol>

        <Code
          title="GET /api/v1/project"
          code={`curl https://ipg.sandboxed.ir/api/v1/project \\
  -H "Authorization: Bearer ipg_key_..."`}
        />

        <div className="gap mt-6">
          <p>
            کلید API برای کنترل API و مدیریت تراکنش‌هاست. در سطح درگاه زرین‌پال، احراز
            هویت با مقدار <code dir="ltr">merchant_id</code> انجام می‌شود که در سندباکس
            همیشه <code dir="ltr">sandbox-merchant</code> است.
          </p>
        </div>
      </Section>

      <Section id="create" eyebrow="۰۳ — ساخت پرداخت" title="دو مسیر، یک نتیجه">
        <div className="cards">
          <article className="card">
            <span className="card__tag">سطح درگاه</span>
            <h3>مثل کد واقعی</h3>
            <p>
              همان قرارداد درگاه را صدا بزنید و فقط دامنه را به سندباکس تغییر دهید. برای
              زرین‌پال: <code dir="ltr">/zarinpal/request/payment</code>.
            </p>
          </article>
          <article className="card">
            <span className="card__tag">کنترل API</span>
            <h3>برای داشبورد و تست</h3>
            <p>
              با <code dir="ltr">POST /api/v1/transactions/simulate</code> یک پرداخت
              می‌سازید، سناریو را مستقیم انتخاب می‌کنید و لینک پرداخت مطلق می‌گیرید.
            </p>
          </article>
        </div>

        <h3 className="mt-6">مسیر درگاه زرین‌پال</h3>
        <Code
          title="POST /zarinpal/request/payment"
          code={`curl -X POST https://ipg.sandboxed.ir/zarinpal/request/payment \\
  -H "Content-Type: application/json" \\
  -d '{
    "merchant_id": "sandbox-merchant",
    "amount": 250000,
    "callback_url": "https://example.com/pay/callback",
    "description": "Order #1001"
  }'`}
        />
        <p className="muted mt-3">
          پاسخ موفق: <code dir="ltr">{`{ "code": 100, "authority": "A…", "payment_url": "…" }`}</code>{" "}
          — مبلغ به <strong>ریال</strong> است. مقدار{" "}
          <code dir="ltr">payment_url</code> نسبی است؛ آدرس میزبان را جلوی آن بگذارید.
        </p>

        <h3 className="mt-6">مسیر کنترل API</h3>
        <Code
          title="POST /api/v1/transactions/simulate"
          code={`curl -X POST https://ipg.sandboxed.ir/api/v1/transactions/simulate \\
  -H "Authorization: Bearer ipg_key_..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "adapter": "zarinpal",
    "amount_rial": 250000,
    "forced_scenario": "approve",
    "return_url": "https://example.com/return"
  }'`}
        />
        <p className="muted mt-3">
          پاسخ شامل <code dir="ltr">transaction</code>،{" "}
          <code dir="ltr">checkout_url</code> (مطلق) و{" "}
          <code dir="ltr">execution_mode</code> است. با{" "}
          <code dir="ltr">auto_complete: true</code> مرحله تایید و verify خودکار انجام
          می‌شود.
        </p>

        <div className="gap mt-6">
          <p>
            <code dir="ltr">callback_url</code> هم هدف بازگشت مرورگر است و هم هدف وب‌هوک.
            اگر این دو باید جدا باشند، برای مرورگر <code dir="ltr">return_url</code> بدهید
            و هدف وب‌هوک را در تنظیمات پروژه (
            <code dir="ltr">webhook_url</code>) تعیین کنید.
          </p>
        </div>
      </Section>

      <Section id="checkout" eyebrow="۰۴ — پرداخت" title="صفحه پرداخت میزبان">
        <p className="muted">
          کاربر را به <code dir="ltr">payment_url</code> یا{" "}
          <code dir="ltr">checkout_url</code> بفرستید؛ معادل‌ها:{" "}
          <code dir="ltr">GET /zarinpal/checkout/&#123;authority&#125;</code> و{" "}
          <code dir="ltr">GET /zarinpal/pg/StartPay/&#123;authority&#125;</code>.
        </p>

        <div className="cards mt-6">
          <article className="card">
            <span className="card__tag">confirm</span>
            <h3>تایید پرداخت</h3>
            <p>
              تراکنش به <code dir="ltr">pending</code> می‌رود و کاربر با{" "}
              <code dir="ltr">Authority</code> و <code dir="ltr">Status=OK</code> برمی‌گردد.
            </p>
          </article>
          <article className="card">
            <span className="card__tag">fail</span>
            <h3>انصراف</h3>
            <p>
              وضعیت <code dir="ltr">declined</code> می‌شود و{" "}
              <code dir="ltr">Status=NOK</code> برمی‌گردد.
            </p>
          </article>
          <article className="card">
            <span className="card__tag">abandon</span>
            <h3>رها کردن</h3>
            <p>
              ابتدا <code dir="ltr">pending</code> و سپس{" "}
              <code dir="ltr">expired</code>. صفحه پرداخت پس از ۱۵ دقیقه منقضی می‌شود.
            </p>
          </article>
        </div>
      </Section>

      <Section id="verify" eyebrow="۰۵ — تایید" title="پرداخت را سمت سرور تایید کنید">
        <Code
          title="POST /zarinpal/payment/verification"
          code={`curl -X POST https://ipg.sandboxed.ir/zarinpal/payment/verification \\
  -H "Content-Type: application/json" \\
  -d '{"authority": "A..."}'`}
        />
        <p className="muted mt-3">
          مسیر نسخه ۴: <code dir="ltr">POST /zarinpal/pg/v4/payment/verify.json</code>.
          سفارش را فقط بعد از پاسخ موفق نهایی کنید.
        </p>

        <div className="card mt-6" style={{ padding: "var(--sp-5)" }}>
          <dl className="kv">
            <div className="kv__row">
              <dt className="kv__label">تایید و تسویه شد</dt>
              <dd className="kv__val mono">code 100</dd>
            </div>
            <div className="kv__row">
              <dt className="kv__label">قبلاً تایید شده — دوباره تسویه نکنید</dt>
              <dd className="kv__val mono">code 101</dd>
            </div>
            <div className="kv__row">
              <dt className="kv__label">رد شده یا شکست در تایید</dt>
              <dd className="kv__val mono">code -51</dd>
            </div>
            <div className="kv__row">
              <dt className="kv__label">سناریوی timeout در مرحله ساخت</dt>
              <dd className="kv__val mono">code -33</dd>
            </div>
            <div className="kv__row">
              <dt className="kv__label">سناریوی refund — آماده استرداد</dt>
              <dd className="kv__val mono">code 100</dd>
            </div>
          </dl>
        </div>

        <p className="muted mt-3">
          برای استرداد تراکنش تسویه‌شده:{" "}
          <code dir="ltr">POST /zarinpal/payment/refund</code> با{" "}
          <code dir="ltr">{'{"authority": "A…"}'}</code>.
        </p>
      </Section>

      <Section id="webhook" eyebrow="۰۶ — رویدادها" title="وب‌هوک و تحویل">
        <div className="card" style={{ padding: "var(--sp-5)" }}>
          <dl className="kv">
            <div className="kv__row">
              <dt className="kv__label">هدف</dt>
              <dd className="kv__val mono">
                transaction.callback_url ← project.webhook_url
              </dd>
            </div>
            <div className="kv__row">
              <dt className="kv__label">مراحل</dt>
              <dd className="kv__val mono">settle · notify · refund</dd>
            </div>
            <div className="kv__row">
              <dt className="kv__label">تحویل موفق</dt>
              <dd className="kv__val mono">HTTP 2xx–3xx</dd>
            </div>
            <div className="kv__row">
              <dt className="kv__label">امضا</dt>
              <dd className="kv__val">ندارد</dd>
            </div>
          </dl>
        </div>

        <p className="muted mt-4">نمونه بدنه تحویل زرین‌پال:</p>
        <div className="card mt-3" style={{ padding: "var(--sp-4)" }}>
          <pre className="hookcode">{`{
  "Status": "OK",
  "Authority": "A...",
  "RefID": 123456,
  "PaymentID": "PID-..."
}`}</pre>
        </div>

        <Code
          title="PUT /api/v1/project/webhook-url"
          code={`curl -X PUT https://ipg.sandboxed.ir/api/v1/project/webhook-url \\
  -H "Authorization: Bearer ipg_key_..." \\
  -H "Content-Type: application/json" \\
  -d '{"webhook_url": "https://example.com/hook"}'`}
        />

        <p className="muted mt-3">
          ارسال آزمایشی: <code dir="ltr">POST /api/v1/project/webhook-ping</code>. تاریخچه
          تحویل: <code dir="ltr">GET /api/v1/deliveries</code>. تلاش دوباره:{" "}
          <code dir="ltr">POST /api/v1/deliveries/&#123;id&#125;/retry</code>.
        </p>

        <div className="gap mt-6">
          <p>
            وب‌هوک‌ها امضا ندارند. برای اطمینان از نتیجه، تراکنش را با API تایید
            (<code dir="ltr">verify</code>) بررسی کنید و به بدنه وب‌هوک به‌تنهایی اعتماد
            نکنید.
          </p>
        </div>
      </Section>

      <Section id="scenarios" eyebrow="۰۷ — سناریوها" title="ماتریس سناریو">
        <div className="mx-wrap">
          <table className="mx">
            <thead>
              <tr>
                <th>سناریو</th>
                <th>
                  هدر
                  <span className="mx__col-ver">X-Sandbox-Scenario</span>
                </th>
                <th>کنترل API</th>
                <th>
                  نتیجه verify
                  <span className="mx__col-ver">zarinpal</span>
                </th>
                <th>وضعیت نهایی</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <th scope="row">
                  تایید
                  <span className="mx__row-en">approve</span>
                </th>
                <Cell>✓</Cell>
                <Cell>✓</Cell>
                <Cell mono>100</Cell>
                <Cell>settled</Cell>
              </tr>
              <tr>
                <th scope="row">
                  رد شدن
                  <span className="mx__row-en">decline</span>
                </th>
                <Cell>✓</Cell>
                <Cell>✓</Cell>
                <Cell mono>-51</Cell>
                <Cell>declined</Cell>
              </tr>
              <tr>
                <th scope="row">
                  تایم‌اوت
                  <span className="mx__row-en">timeout</span>
                </th>
                <Cell>✓</Cell>
                <Cell>✓</Cell>
                <Cell mono>-33</Cell>
                <Cell>failed</Cell>
              </tr>
              <tr>
                <th scope="row">
                  استرداد
                  <span className="mx__row-en">refund</span>
                </th>
                <Cell>✓</Cell>
                <Cell>✓</Cell>
                <Cell mono>100</Cell>
                <Cell>refunded</Cell>
              </tr>
              <tr>
                <th scope="row">
                  تسویه تأخیری
                  <span className="mx__row-en">pending_settle</span>
                </th>
                <Cell>✓</Cell>
                <Cell>✓</Cell>
                <Cell mono>100</Cell>
                <Cell>settled</Cell>
              </tr>
              <tr>
                <th scope="row">
                  شکست در تایید
                  <span className="mx__row-en">verify_fail</span>
                </th>
                <Cell>✓</Cell>
                <Cell>✓</Cell>
                <Cell mono>-51</Cell>
                <Cell>declined</Cell>
              </tr>
            </tbody>
          </table>
        </div>

        <div className="gap mt-6">
          <p>
            هدر با نام دقیق <code dir="ltr">X-Sandbox-Scenario</code> فقط در مرحله ساخت
            پرداختِ زرین‌پال، آیدی‌پی و به‌پرداخت خوانده می‌شود. برای بقیه آداپتورها از{" "}
            <code dir="ltr">forced_scenario</code> در{" "}
            <code dir="ltr">/api/v1/transactions/simulate</code> یا{" "}
            <code dir="ltr">PATCH /api/v1/transactions/&#123;id&#125;</code> استفاده کنید.
            مقدار نامعتبر پاسخ <code dir="ltr">400 scenario_invalid</code> می‌دهد و نام
            درست <code dir="ltr">verify_fail</code> است، نه{" "}
            <code dir="ltr">verify_failed</code>. سناریوی پیش‌فرض پروژه هم با{" "}
            <code dir="ltr">PATCH /api/v1/project</code> قابل تغییر است.
          </p>
        </div>
      </Section>

      <Section id="statuses" eyebrow="۰۸ — مرجع" title="وضعیت‌های تراکنش">
        <div className="card" style={{ padding: "var(--sp-5)" }}>
          <dl className="kv">
            <div className="kv__row">
              <dt className="kv__label">ساخته شده، منتظر پرداخت</dt>
              <dd className="kv__val mono">initiated</dd>
            </div>
            <div className="kv__row">
              <dt className="kv__label">تایید شده، منتظر تسویه</dt>
              <dd className="kv__val mono">pending</dd>
            </div>
            <div className="kv__row">
              <dt className="kv__label">موفق و تسویه‌شده</dt>
              <dd className="kv__val mono">settled</dd>
            </div>
            <div className="kv__row">
              <dt className="kv__label">آماده استرداد</dt>
              <dd className="kv__val mono">approved</dd>
            </div>
            <div className="kv__row">
              <dt className="kv__label">استرداد شده — پایانی</dt>
              <dd className="kv__val mono">refunded</dd>
            </div>
            <div className="kv__row">
              <dt className="kv__label">رهاشده یا منقضی — پایانی</dt>
              <dd className="kv__val mono">expired</dd>
            </div>
            <div className="kv__row">
              <dt className="kv__label">رد شده — پایانی</dt>
              <dd className="kv__val mono">declined</dd>
            </div>
            <div className="kv__row">
              <dt className="kv__label">خطا یا تایم‌اوت — پایانی</dt>
              <dd className="kv__val mono">failed</dd>
            </div>
          </dl>
        </div>
      </Section>

      <Section id="console" eyebrow="۰۹ — داشبورد" title="مدیریت پرداخت‌ها">
        <ul className="links">
          <li>
            <Link className="link-card" href={`/${locale}/console`}>
              <span>
                تراکنش‌ها
                <span className="block small muted">
                  جست‌وجو، فیلتر وضعیت، جزئیات خام و حذف
                </span>
              </span>
              <span aria-hidden="true">←</span>
            </Link>
          </li>
          <li>
            <Link className="link-card" href={`/${locale}/webhooks`}>
              <span>
                وب‌هوک‌ها
                <span className="block small muted">لاگ تحویل، تلاش دوباره و ping</span>
              </span>
              <span aria-hidden="true">←</span>
            </Link>
          </li>
          <li>
            <Link className="link-card" href={`/${locale}/gateways`}>
              <span>
                درگاه‌ها
                <span className="block small muted">وضعیت و اعتبارنامه هر آداپتور</span>
              </span>
              <span aria-hidden="true">←</span>
            </Link>
          </li>
          <li>
            <Link className="link-card" href={`/${locale}/settings/api-keys`}>
              <span>
                کلیدهای API
                <span className="block small muted">ساخت، مشاهده یک‌باره و ابطال</span>
              </span>
              <span aria-hidden="true">←</span>
            </Link>
          </li>
          <li>
            <Link className="link-card" href={`/${locale}/settings`}>
              <span>
                تنظیمات
                <span className="block small muted">
                  وب‌هوک پیش‌فرض، تلاش مجدد، تاریخچه و تأخیرها
                </span>
              </span>
              <span aria-hidden="true">←</span>
            </Link>
          </li>
          <li>
            <Link className="link-card" href={`/${locale}/sdk`}>
              <span>
                راهنمای CI
                <span className="block small muted">اجرای سناریوها در پایپ‌لاین</span>
              </span>
              <span aria-hidden="true">←</span>
            </Link>
          </li>
        </ul>
      </Section>

      <Section id="errors" eyebrow="۱۰ — خطاها" title="قالب پاسخ خطا">
        <p className="muted">
          خطاهای کنترل API همیشه این شکل را دارند:{" "}
          <code dir="ltr">{`{ "code": "...", "message": "...", "details": {} }`}</code>.
          فیلد <code dir="ltr">details</code> اختیاری است.
        </p>

        <div className="mx-wrap mt-6">
          <table className="mx">
            <thead>
              <tr>
                <th>کد</th>
                <th>HTTP</th>
                <th>معنی</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <th scope="row">
                  <span className="mx__row-en">validation_error</span>
                </th>
                <Cell mono>400 / 422</Cell>
                <Cell>فیلد نامعتبر یا ناموجود</Cell>
              </tr>
              <tr>
                <th scope="row">
                  <span className="mx__row-en">invalid_credentials</span>
                </th>
                <Cell mono>401</Cell>
                <Cell>اعتبارنامه درگاه اشتباه است</Cell>
              </tr>
              <tr>
                <th scope="row">
                  <span className="mx__row-en">session_required</span>
                </th>
                <Cell mono>401</Cell>
                <Cell>نشست یا کلید معتبر نیست</Cell>
              </tr>
              <tr>
                <th scope="row">
                  <span className="mx__row-en">forbidden</span>
                </th>
                <Cell mono>403</Cell>
                <Cell>دسترسی به این بخش ندارید</Cell>
              </tr>
              <tr>
                <th scope="row">
                  <span className="mx__row-en">not_found</span>
                </th>
                <Cell mono>404</Cell>
                <Cell>تراکنش، آداپتور یا درگاه پیدا نشد</Cell>
              </tr>
              <tr>
                <th scope="row">
                  <span className="mx__row-en">scenario_invalid</span>
                </th>
                <Cell mono>400 / 422</Cell>
                <Cell>مقدار سناریو در لیست مجاز نیست</Cell>
              </tr>
              <tr>
                <th scope="row">
                  <span className="mx__row-en">unsupported_operation</span>
                </th>
                <Cell mono>400 / 405</Cell>
                <Cell>این عملیات در آداپتور پیاده‌سازی نشده</Cell>
              </tr>
              <tr>
                <th scope="row">
                  <span className="mx__row-en">daily_quota_exceeded</span>
                </th>
                <Cell mono>429</Cell>
                <Cell>سقف روزانه تراکنش پر شده</Cell>
              </tr>
              <tr>
                <th scope="row">
                  <span className="mx__row-en">rate_limited</span>
                </th>
                <Cell mono>429</Cell>
                <Cell>درخواست‌ها بیش از حد پشت سر هم</Cell>
              </tr>
              <tr>
                <th scope="row">
                  <span className="mx__row-en">internal_error</span>
                </th>
                <Cell mono>500</Cell>
                <Cell>خطای پیش‌بینی‌نشده سرور</Cell>
              </tr>
            </tbody>
          </table>
        </div>
      </Section>

      <Section id="more" eyebrow="۱۱ — بیشتر" title="مراجع و فایل‌های خام">
        <ul className="links">
          {RAW_DOCS.map((doc) => (
            <li key={doc.href}>
              <a className="link-card" href={doc.href} download>
                <span>
                  {doc.title}
                  <span className="block small muted">{doc.note}</span>
                </span>
                <span aria-hidden="true">↓</span>
              </a>
            </li>
          ))}
        </ul>

        <div className="gap mt-6">
          <p>
            فایل‌های Markdown بالا قدیمی‌ترند و ممکن است نام هدر یا برخی کدها با پیاده‌سازی
            فعلی فرق کند؛ این صفحه مرجع اصلی است.
          </p>
        </div>
      </Section>

      <Section id="faq" eyebrow="۱۲ — پرسش‌ها" title="پرسش‌های رایج">
        <div className="faq">
          <details>
            <summary>چرا درگاه دیگری پاسخ ۴۰۴ می‌دهد؟</summary>
            <p>
              در پروژه تازه فقط زرین‌پال فعال است. بقیه آداپتورها با وضعیت «غیرفعال»
              ساخته می‌شوند و فعال‌سازی آن‌ها در اختیار اپراتور سندباکس است، نه داشبورد
              فروشنده.
            </p>
          </details>
          <details>
            <summary>چرا verify کد ۱۰۱ برمی‌گرداند؟</summary>
            <p>
              یعنی این تراکنش قبلاً تایید شده است. آن را موفق در نظر بگیرید و دوباره
              تسویه نکنید؛ این پاسخ برای جلوگیری از پرداخت دوباره است.
            </p>
          </details>
          <details>
            <summary>وب‌هوک نرسید؛ چه کنم؟</summary>
            <p>
              آدرس هدف باید از اینترنت یا شبکه سندباکس در دسترس باشد. تحویل‌ها را در{" "}
              <code dir="ltr">GET /api/v1/deliveries</code> یا صفحه وب‌هوک‌های داشبورد
              ببینید و با <code dir="ltr">POST /api/v1/deliveries/&#123;id&#125;/retry</code>{" "}
              دوباره تلاش کنید. برای آزمایش مسیر، از webhook-ping استفاده کنید.
            </p>
          </details>
          <details>
            <summary>چرا درخواست حدود ۳۰ ثانیه طول کشید؟</summary>
            <p>
              سناریوی <code dir="ltr">timeout</code> روی زرین‌پال، آیدی‌پی و به‌پرداخت
              به‌اندازه تأخیر تنظیم‌شده (پیش‌فرض ۳۰ ثانیه) مکث می‌کند و بعد خطا می‌دهد.
              این رفتار عمدی است تا مسیر تایم‌اوت کلاینت شما هم تست شود.
            </p>
          </details>
          <details>
            <summary>چرا تراکنش‌های قدیمی ناپدید شدند؟</summary>
            <p>
              تاریخچه با سقف ردیف کنترل می‌شود (پیش‌فرض ۱۰۰۰ ردیف). با هر تراکنش جدید،
              قدیمی‌ترین ردیف حذف می‌شود؛ محدودیت زمانی نیست.
            </p>
          </details>
          <details>
            <summary>آیا داده کارت یا پول واقعی جابه‌جا می‌شود؟</summary>
            <p>
              نه. صفحه پرداخت هیچ ورودی کارتی ندارد و هیچ اتصالی به درگاه واقعی برقرار
              نمی‌شود. تنها اثر آن، ردیف تراکنش و وب‌هوک در همین سندباکس است.
            </p>
          </details>
          <details>
            <summary>چرا Swagger روی دامنه میزبان باز نمی‌شود؟</summary>
            <p>
              مسیرهای <code dir="ltr">/docs</code> و{" "}
              <code dir="ltr">/openapi.json</code> در دامنه میزبان به داشبورد می‌رسند، نه
              موتور. برای مشاهده Swagger موتور را محلی اجرا کنید.
            </p>
          </details>
        </div>
      </Section>
    </MarketingShell>
  );
}
