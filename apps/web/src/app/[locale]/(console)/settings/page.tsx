import { getTranslations, setRequestLocale } from "next-intl/server";
import {
  getProject,
  getQuotaMeters,
  getSubscription,
  Project,
  QuotaMeters,
  Subscription,
} from "../../../../lib/api";
import { ProjectSettingsForm } from "../../../../components/ProjectSettingsForm";

// Project defaults are live engine state.
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
  let subscription: Subscription | null = null;
  let meters: QuotaMeters | null = null;
  let errorMsg: string | null = null;

  try {
    const [prj, sub, qm] = await Promise.all([
      getProject(),
      getSubscription().catch(() => null),
      getQuotaMeters().catch(() => null),
    ]);
    project = prj;
    subscription = sub;
    meters = qm;
  } catch (err: unknown) {
    errorMsg = err instanceof Error ? err.message : "Failed to load settings";
  }

  const paymentStatus = searchParams?.payment;
  const isTeam = project?.tier === "team" || subscription?.tier === "team";

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-2xl font-semibold tracking-tight">{t("title")}</h1>
        <p className="text-sm text-muted">{t("subtitle")}</p>
      </div>

      {paymentStatus === "success" && (
        <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-console text-sm">
          {t("pay_success")}
        </div>
      )}

      {paymentStatus === "cancelled" && (
        <div className="p-4 bg-amber-500/10 border border-amber-500/20 text-amber-400 rounded-console text-sm">
          {t("pay_cancelled")}
        </div>
      )}

      {paymentStatus === "failed" && (
        <div className="p-4 bg-danger-bg border border-danger-border text-danger-ink rounded-console text-sm">
          {t("pay_failed")}
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
              {t("plan_title")}
            </h2>
            <p className="text-xs text-muted">{t("plan_subtitle")}</p>
          </div>
          <span className="px-3 py-1 text-xs font-semibold rounded-full bg-accent/15 text-accent border border-accent/25">
            {isTeam ? t("tier_team") : t("tier_free")}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-2">
          <div className="p-3 bg-surface-subtle border border-border rounded-sm">
            <div className="text-xs text-muted">{t("meter_requests")}</div>
            <div className="text-lg font-semibold mt-1 font-mono">
              {meters?.requests_today ?? 0}
              <span className="text-xs text-muted font-sans mr-1">
                / {meters?.daily_requests_cap === 0 ? t("meter_unlimited") : (meters?.daily_requests_cap ?? 100)}
              </span>
            </div>
          </div>

          <div className="p-3 bg-surface-subtle border border-border rounded-sm">
            <div className="text-xs text-muted">{t("meter_adapters")}</div>
            <div className="text-lg font-semibold mt-1 font-mono">
              {meters?.active_adapters_count ?? 0}
              <span className="text-xs text-muted font-sans mr-1">
                / {meters?.max_active_adapters === 0 ? t("meter_all_gateways") : (meters?.max_active_adapters ?? 2)}
              </span>
            </div>
          </div>

          <div className="p-3 bg-surface-subtle border border-border rounded-sm">
            <div className="text-xs text-muted">{t("meter_transactions")}</div>
            <div className="text-lg font-semibold mt-1 font-mono">
              {meters?.transactions_total ?? 0}
            </div>
          </div>

          <div className="p-3 bg-surface-subtle border border-border rounded-sm">
            <div className="text-xs text-muted">{t("meter_history")}</div>
            <div className="text-lg font-semibold mt-1 font-mono">
              {meters?.history_retained ?? 0}
              <span className="text-xs text-muted font-sans mr-1">
                / {meters?.history_cap ?? 1000}
              </span>
            </div>
          </div>
        </div>

        {!isTeam && (
          <div className="flex items-center justify-between pt-2 border-t border-border">
            <span className="text-xs text-muted">{t("upgrade_hint")}</span>
            <a
              href={`/${locale}/pricing`}
              className="text-xs text-accent hover:underline font-medium"
            >
              {t("upgrade_cta")} &larr;
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
    </div>
  );
}
