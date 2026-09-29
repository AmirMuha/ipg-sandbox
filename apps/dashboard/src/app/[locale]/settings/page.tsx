import { getTranslations, setRequestLocale } from "next-intl/server";
import { AdapterConfig, getAdapters, getProject, Project } from "../../../lib/api";
import { AdapterSettings } from "../../../components/AdapterSettings";
import { ScenarioControls } from "../../../components/ScenarioControls";

export default async function SettingsPage({
  params: { locale },
}: {
  params: { locale: string };
}) {
  setRequestLocale(locale);
  const t = await getTranslations("settings");

  let project: Project | null = null;
  let adapters: AdapterConfig[] = [];
  let errorMsg: string | null = null;

  try {
    const [prj, adps] = await Promise.all([getProject(), getAdapters()]);
    project = prj;
    adapters = adps;
  } catch (err: unknown) {
    errorMsg = err instanceof Error ? err.message : "Failed to load settings";
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{t("title")}</h1>
        <p className="text-sm text-muted">{t("subtitle")}</p>
      </div>

      {errorMsg && (
        <div className="p-4 bg-danger/10 border border-danger/20 text-danger rounded-lg text-sm">
          {errorMsg}
        </div>
      )}

      {project && (
        <div className="space-y-4">
          <h2 className="text-base font-semibold">{t("project_settings")}</h2>
          <ScenarioControls project={project} />
        </div>
      )}

      <div className="space-y-4">
        <h2 className="text-base font-semibold">{t("adapter_settings")}</h2>
        <div className="grid grid-cols-1 gap-4">
          {adapters.map((adapter) => (
            <AdapterSettings key={adapter.id} adapter={adapter} />
          ))}
        </div>
      </div>
    </div>
  );
}
