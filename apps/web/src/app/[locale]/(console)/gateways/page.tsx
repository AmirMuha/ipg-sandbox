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

  // Providers the platform admin has withdrawn are not offered to this project, so they
  // cannot be routed to and their credentials form configures nothing a payment could
  // reach. Showing them only pads the grid with locked cards. `AdapterSettings` still
  // renders the withdrawn state correctly — this page just never hands it one.
  const offered = adapters.filter((a) => !a.withdrawn_by_operator);

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

      {offered.length === 0 && !errorMsg ? (
        <div className="empty">
          <svg className="ic" viewBox="0 0 24 24" aria-hidden="true">
            <rect x="2" y="6" width="20" height="12" rx="2" />
            <path d="M2 10h20" />
          </svg>
          <h3>{t("empty")}</h3>
          <p>{t("empty_hint")}</p>
        </div>
      ) : (
        <div className="gws">
          {offered.map((adapter) => (
            <AdapterSettings key={adapter.id} adapter={adapter} />
          ))}
        </div>
      )}
    </>
  );
}
