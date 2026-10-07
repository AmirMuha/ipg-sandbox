import { redirect } from "next/navigation";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { AdminProviderList } from "../../../../components/AdminProviderList";
import { AdminSubscriptionList } from "../../../../components/AdminSubscriptionList";
import { getAdminSubscriptions, getMe, getPlatformProviders } from "../../../../lib/api";

export const dynamic = "force-dynamic";

export default async function AdminPage({ params: { locale } }: { params: { locale: string } }) {
  setRequestLocale(locale);
  const t = await getTranslations("admin");
  const tProviders = await getTranslations("admin_providers");

  let isAuthorized = false;
  try {
    const me = await getMe();
    isAuthorized = Boolean(me?.user?.is_admin);
  } catch {
    isAuthorized = false;
  }

  // FR-004: Non-administrators cannot access the gateway management surface
  if (!isAuthorized) {
    redirect(`/${locale}/console`);
  }

  let initialOffered: string[] = ["zarinpal"];
  try {
    const res = await getPlatformProviders();
    initialOffered = res.providers;
  } catch {
    // fallback if fetch fails
  }
  const adminSubscriptions = await getAdminSubscriptions().catch(() => []);

  return (
    <>
      <div className="phead">
        <div className="phead__text">
          <h1>{t("title")}</h1>
          <p>{t("subtitle")}</p>
        </div>
      </div>

      <section className="card mb-4" data-testid="admin-gateways-panel">
        <div className="card__head">
          <h2 className="card__title">{tProviders("title")}</h2>
        </div>
        <div className="card__body stack-md">
          <p className="small muted">{tProviders("subtitle")}</p>
          <AdminProviderList initialOffered={initialOffered} />
        </div>
      </section>

      <AdminSubscriptionList initialSubscriptions={adminSubscriptions} />
    </>
  );
}
