import { getTranslations, setRequestLocale } from "next-intl/server";
import { getAdapters, AdapterConfig } from "../../../../lib/api";
import { AdapterSettings } from "../../../../components/AdapterSettings";

// Adapter credentials are live engine state.
export const dynamic = "force-dynamic";

export default async function GatewaysPage({ params: { locale } }: { params: { locale: string } }) {
  setRequestLocale(locale);
  const t = await getTranslations("gateways");

  let adapters: AdapterConfig[] = [];
  let errorMsg: string | null = null;
  try {
    adapters = await getAdapters();
  } catch (err: unknown) {
    errorMsg = err instanceof Error ? err.message : "Failed to load gateways";
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-2xl font-semibold tracking-tight">{t("title")}</h1>
        <p className="text-sm text-muted">{t("subtitle")}</p>
      </div>

      {errorMsg && (
        <div className="p-4 bg-danger-bg border border-danger-border text-danger-ink rounded-console text-sm">
          {errorMsg}
        </div>
      )}

      <div className="grid grid-cols-1 gap-4">
        {adapters.map((adapter) => (
          <AdapterSettings key={adapter.id} adapter={adapter} />
        ))}
      </div>
    </div>
  );
}
