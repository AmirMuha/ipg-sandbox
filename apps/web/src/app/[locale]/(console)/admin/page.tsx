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
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-2xl font-semibold tracking-tight">{t("title")}</h1>
        <p className="text-sm text-muted">{t("subtitle")}</p>
      </div>

      <section className="space-y-4" data-testid="admin-gateways-panel">
        <div>
          <h2 className="font-display text-[17px] font-semibold tracking-display">
            {tProviders("title")}
          </h2>
          <p className="text-xs text-muted mt-1">{tProviders("subtitle")}</p>
        </div>
        <AdminProviderList initialOffered={initialOffered} />
      </section>

      <AdminSubscriptionList initialSubscriptions={adminSubscriptions} />
    </div>
  );
}
