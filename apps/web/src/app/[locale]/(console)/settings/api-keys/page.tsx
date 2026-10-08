import Link from "next/link";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { ApiKeysList } from "../../../../../components/api-keys/ApiKeysList";

// The key list is live engine state.
export const dynamic = "force-dynamic";

export default async function ApiKeysPage({ params: { locale } }: { params: { locale: string } }) {
  setRequestLocale(locale);
  const t = await getTranslations("api_keys");
  const tc = await getTranslations("common");

  return (
    <div className="stack-lg">
      <div className="phead">
        <div className="phead__text">
          <h1>{t("title")}</h1>
          <p>{t("subtitle")}</p>
        </div>
        {/* Settings is the only way in to this page, so "back" is a fixed link, not
            history.back() — deep links and reloads would otherwise leave nowhere to go.
            The arrow flips with the locale rather than following dir, because the
            glyph itself does not reorder. */}
        <div className="phead__actions">
          <Link
            href={`/${locale}/settings`}
            className="btn btn--secondary btn--sm"
            data-testid="back-to-settings"
          >
            {locale === "fa" ? "→" : "←"} {tc("back")}
          </Link>
        </div>
      </div>

      <ApiKeysList />
    </div>
  );
}
