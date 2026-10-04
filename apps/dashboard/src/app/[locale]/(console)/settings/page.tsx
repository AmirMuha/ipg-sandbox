import { getTranslations, setRequestLocale } from "next-intl/server";
import { AdapterConfig, apiBase, getAdapters, getProject, Project } from "../../../../lib/api";
import { AdapterSettings } from "../../../../components/AdapterSettings";
import { ProjectSettingsForm } from "../../../../components/ProjectSettingsForm";
import { ScenarioCiGuide } from "../../../../components/ScenarioCiGuide";

// Adapter credentials and project defaults are live engine state.
export const dynamic = "force-dynamic";

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
        <h1 className="font-display text-2xl font-semibold tracking-tight">{t("title")}</h1>
        <p className="text-sm text-muted">{t("subtitle")}</p>
      </div>

      {errorMsg && (
        <div className="p-4 bg-danger-bg border border-danger-border text-danger-ink rounded-console text-sm">
          {errorMsg}
        </div>
      )}

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
