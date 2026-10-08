import { getTranslations, setRequestLocale } from "next-intl/server";
import { ApiKeysList } from "../../../../../components/api-keys/ApiKeysList";

// The key list is live engine state.
export const dynamic = "force-dynamic";

export default async function ApiKeysPage({ params: { locale } }: { params: { locale: string } }) {
  setRequestLocale(locale);
  const t = await getTranslations("api_keys");

  return (
    <div className="stack-lg">
      <div className="phead">
        <div className="phead__text">
          <h1>{t("title")}</h1>
          <p>{t("subtitle")}</p>
        </div>
      </div>

      <ApiKeysList />
    </div>
  );
}
