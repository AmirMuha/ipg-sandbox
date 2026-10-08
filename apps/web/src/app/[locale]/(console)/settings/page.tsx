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
    <div className="stack-lg">
      <div className="phead">
        <div className="phead__text">
          <h1>{t("title")}</h1>
          <p>{t("subtitle")}</p>
        </div>
      </div>

      {/* Payment outcomes and load errors share the banner surface; only the failure case
          earns the danger tint, the design has no success/warning variant. */}
      {paymentStatus === "success" && <div className="banner">{t("pay_success")}</div>}

      {paymentStatus === "cancelled" && <div className="banner">{t("pay_cancelled")}</div>}

      {paymentStatus === "failed" && (
        <div className="banner banner--danger">{t("pay_failed")}</div>
      )}

      {errorMsg && <div className="banner banner--danger">{errorMsg}</div>}

      {/* Subscription Tier & Quota Status Card */}
      <div className="card">
        <div className="card__head">
          <h2 className="card__title">{t("plan_title")}</h2>
          <span className="badge badge--accent">{isTeam ? t("tier_team") : t("tier_free")}</span>
        </div>
        <div className="card__body stack-md">
          <p className="muted">{t("plan_subtitle")}</p>

          <div className="kv">
            <div className="kv__row">
              <span className="kv__label">{t("meter_requests")}</span>
              <span className="kv__val mono">
                {meters?.requests_today ?? 0} /{" "}
                {meters?.daily_requests_cap === 0
                  ? t("meter_unlimited")
                  : (meters?.daily_requests_cap ?? 100)}
              </span>
            </div>

            <div className="kv__row">
              <span className="kv__label">{t("meter_adapters")}</span>
              <span className="kv__val mono">
                {meters?.active_adapters_count ?? 0} /{" "}
                {meters?.max_active_adapters === 0
                  ? t("meter_all_gateways")
                  : (meters?.max_active_adapters ?? 2)}
              </span>
            </div>

            <div className="kv__row">
              <span className="kv__label">{t("meter_transactions")}</span>
              <span className="kv__val mono">{meters?.transactions_total ?? 0}</span>
            </div>

            <div className="kv__row">
              <span className="kv__label">{t("meter_history")}</span>
              <span className="kv__val mono">
                {meters?.history_retained ?? 0} / {meters?.history_cap ?? 1000}
              </span>
            </div>
          </div>

          {!isTeam && (
            <>
              <div className="divider" />
              <div className="row-flex justify-between">
                <span className="small muted">{t("upgrade_hint")}</span>
                <a href={`/${locale}/pricing`} className="btn btn--secondary btn--sm">
                  {t("upgrade_cta")} &larr;
                </a>
              </div>
            </>
          )}
        </div>
      </div>

            <div className="card">
        <div className="card__head">
          <h2 className="card__title">API Keys</h2>
        </div>
        <div className="card__body stack-md">
          <p className="muted">Manage API keys for programmatic access to your sandbox.</p>
          <div className="row-flex">
            <a href={`/${locale}/settings/api-keys`} className="btn btn--secondary btn--sm">
              Manage API Keys &rarr;
            </a>
          </div>
        </div>
      </div>

      {project && (
        <div className="stack-md">
          <h2 className="card__title">{t("project_settings")}</h2>
          <ProjectSettingsForm project={project} locale={locale} />
        </div>
      )}
    </div>
  );
}
