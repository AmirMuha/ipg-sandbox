import { redirect } from "next/navigation";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { AdminProviderList } from "../../../../../components/AdminProviderList";
import { getMe, getPlatformProviders } from "../../../../../lib/api";

export const dynamic = "force-dynamic";

export default async function AdminProvidersPage({
  params: { locale },
}: {
  params: { locale: string };
}) {
  setRequestLocale(locale);
  const t = await getTranslations("admin_providers");

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

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-semibold tracking-tight">{t("title")}</h1>
        <p className="text-sm text-muted">{t("subtitle")}</p>
      </div>

      <AdminProviderList initialOffered={initialOffered} />
    </div>
  );
}
