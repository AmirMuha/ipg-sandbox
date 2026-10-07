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
    <>
      <div className="phead">
        <div className="phead__text">
          <h1>{t("title")}</h1>
          <p>{t("subtitle")}</p>
        </div>
      </div>

      {errorMsg && (
        <div className="banner banner--danger mb-4" role="alert">
          <svg className="ic" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" />
            <path d="M12 9v4M12 17h.01" />
          </svg>
          <span>{errorMsg}</span>
        </div>
      )}

      <div className="gws">
        {adapters.map((adapter) => (
          <AdapterSettings key={adapter.id} adapter={adapter} />
        ))}
      </div>
    </>
  );
}
