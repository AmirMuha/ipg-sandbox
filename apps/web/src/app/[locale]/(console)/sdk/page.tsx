import { getTranslations, setRequestLocale } from "next-intl/server";
import { apiBase } from "../../../../lib/api";
import { ScenarioCiGuide } from "../../../../components/ScenarioCiGuide";

export default async function SdkPage({ params: { locale } }: { params: { locale: string } }) {
  setRequestLocale(locale);
  const t = await getTranslations("sdk");

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-2xl font-semibold tracking-tight">{t("title")}</h1>
        <p className="text-sm text-muted">{t("subtitle")}</p>
      </div>

      <ScenarioCiGuide apiBase={apiBase} />
    </div>
  );
}
