import { getTranslations, setRequestLocale } from "next-intl/server";
import { apiBase } from "../../../../lib/api";
import { ScenarioCiGuide } from "../../../../components/ScenarioCiGuide";

export default async function SdkPage({ params: { locale } }: { params: { locale: string } }) {
  setRequestLocale(locale);
  const t = await getTranslations("sdk");

  return (
    <>
      <div className="phead">
        <div className="phead__text">
          <h1>{t("title")}</h1>
          <p>{t("subtitle")}</p>
        </div>
      </div>

      <ScenarioCiGuide apiBase={apiBase} />
    </>
  );
}
