import { getTranslations, setRequestLocale } from "next-intl/server";
import {
  AdapterConfig,
  apiBase,
  getAdapters,
  getProject,
  getQuotaMeters,
  getSubscription,
  Project,
  QuotaMeters,
  Subscription,
} from "../../../../lib/api";
import { AdapterSettings } from "../../../../components/AdapterSettings";
import { ProjectSettingsForm } from "../../../../components/ProjectSettingsForm";
import { ScenarioCiGuide } from "../../../../components/ScenarioCiGuide";

// Adapter credentials and project defaults are live engine state.
export const dynamic = "force-dynamic";

export default async function SettingsPage({
  params: { locale },
  searchParams,
}: {
  params: { locale: string };
  searchParams?: { payment?: string };
}) {
  setRequestLocale(locale);
  const t = await getTranslations("settings");

  let project: Project | null = null;
  let adapters: AdapterConfig[] = [];
  let subscription: Subscription | null = null;
  let meters: QuotaMeters | null = null;
  let errorMsg: string | null = null;

  try {
    const [prj, adps, sub, qm] = await Promise.all([
      getProject(),
      getAdapters(),
      getSubscription().catch(() => null),
      getQuotaMeters().catch(() => null),
    ]);
    project = prj;
    adapters = adps;
    subscription = sub;
    meters = qm;
  } catch (err: unknown) {
    errorMsg = err instanceof Error ? err.message : "Failed to load settings";
  }

  const paymentStatus = searchParams?.payment;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-2xl font-semibold tracking-tight">{t("title")}</h1>
        <p className="text-sm text-muted">{t("subtitle")}</p>
      </div>

      {paymentStatus === "success" && (
        <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-console text-sm">
          پرداخت شما با موفقیت در زرین‌پال تأیید شد. پلن پروژه به تیم حرفه‌ای ارتقا یافت!
        </div>
      )}

      {paymentStatus === "cancelled" && (
        <div className="p-4 bg-amber-500/10 border border-amber-500/20 text-amber-400 rounded-console text-sm">
          پرداخت ارتقای پلن لغو شد.
        </div>
      )}

      {paymentStatus === "failed" && (
        <div className="p-4 bg-danger-bg border border-danger-border text-danger-ink rounded-console text-sm">
          خطا در تأیید پرداخت درگاه زرین‌پال. لطفاً مجدداً تلاش کنید یا با پشتیبانی تماس بگیرید.
        </div>
      )}

      {errorMsg && (
        <div className="p-4 bg-danger-bg border border-danger-border text-danger-ink rounded-console text-sm">
          {errorMsg}
        </div>
      )}

      {/* Subscription Tier & Quota Status Card */}
      <div className="p-6 bg-surface border border-border rounded-console space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-display text-[17px] font-semibold tracking-display">
              پلن و محدودیت‌های مصرف
            </h2>
            <p className="text-xs text-muted">
              وضعیت اشتراک تجاری و سقف مجاز درخواست‌ها در ۲۴ ساعت جاری
            </p>
          </div>
          <span className="px-3 py-1 text-xs font-semibold rounded-full bg-accent/15 text-accent border border-accent/25">
            {subscription?.tier === "team" || project?.tier === "team"
              ? "پلن تیم حرفه‌ای (فعال)"
              : "پلن توسعه‌دهنده (رایگان)"}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-2">
          <div className="p-3 bg-surface-subtle border border-border rounded-sm">
            <div className="text-xs text-muted">درخواست‌های امروز</div>
            <div className="text-lg font-semibold mt-1 font-mono">
              {meters?.requests_today ?? 0}
              <span className="text-xs text-muted font-sans mr-1">
                / {meters?.daily_requests_cap === 0 ? "نامحدود" : (meters?.daily_requests_cap ?? 100)}
              </span>
            </div>
          </div>

          <div className="p-3 bg-surface-subtle border border-border rounded-sm">
            <div className="text-xs text-muted">درگاه‌های هم‌زمان فعال</div>
            <div className="text-lg font-semibold mt-1 font-mono">
              {meters?.active_adapters_count ?? 0}
              <span className="text-xs text-muted font-sans mr-1">
                / {meters?.max_active_adapters === 0 ? "۱۳ (همه)" : (meters?.max_active_adapters ?? 2)}
              </span>
            </div>
          </div>

          <div className="p-3 bg-surface-subtle border border-border rounded-sm">
            <div className="text-xs text-muted">کل تراکنش‌های ثبت‌شده</div>
            <div className="text-lg font-semibold mt-1 font-mono">
              {meters?.transactions_total ?? 0}
            </div>
          </div>

          <div className="p-3 bg-surface-subtle border border-border rounded-sm">
            <div className="text-xs text-muted">سقف نگهداری لاگ</div>
            <div className="text-lg font-semibold mt-1 font-mono">
              {meters?.history_retained ?? 0}
              <span className="text-xs text-muted font-sans mr-1">
                / {meters?.history_cap ?? 1000}
              </span>
            </div>
          </div>
        </div>

        {project?.tier !== "team" && subscription?.tier !== "team" && (
          <div className="flex items-center justify-between pt-2 border-t border-border">
            <span className="text-xs text-muted">
              نیاز به درخواست‌های بیشتر و همه ۱۳ درگاه پرداخت دارید؟
            </span>
            <a
              href={`/${locale}/pricing`}
              className="text-xs text-accent hover:underline font-medium"
            >
              ارتقا به پلن تیمی با زرین‌پال &larr;
            </a>
          </div>
        )}
      </div>

      {project && (
        <div className="space-y-4">
          <h2 className="font-display text-[17px] font-semibold tracking-display">{t("project_settings")}</h2>
          <ProjectSettingsForm project={project} locale={locale} />
        </div>
      )}

      <div className="space-y-4">
        <h2 className="font-display text-[17px] font-semibold tracking-display">{t("adapter_settings")}</h2>
        <div className="grid grid-cols-1 gap-4">
          {adapters.map((adapter) => (
            <AdapterSettings key={adapter.id} adapter={adapter} />
          ))}
        </div>
      </div>

      <ScenarioCiGuide apiBase={apiBase} />
    </div>
  );
}
