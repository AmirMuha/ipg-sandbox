import Link from "next/link";
import { useTranslations } from "next-intl";

export function Shell({
  children,
  locale,
}: {
  children: React.ReactNode;
  locale: string;
}) {
  const t = useTranslations("nav");
  const otherLocale = locale === "fa" ? "en" : "fa";

  return (
    <div className="min-h-screen bg-bg text-text flex flex-col">
      <header className="border-b border-border bg-surface px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Link
            href={`/${locale}/transactions`}
            className="text-lg font-semibold text-text tracking-tight flex items-center gap-2"
          >
            <span className="w-2.5 h-2.5 rounded-full bg-accent inline-block"></span>
            {t("title")}
          </Link>
          <nav className="flex items-center gap-4 text-sm">
            <Link
              href={`/${locale}/transactions`}
              className="text-muted hover:text-text transition-colors px-2 py-1 rounded"
              data-testid="nav-transactions"
            >
              {t("transactions")}
            </Link>
            <Link
              href={`/${locale}/webhooks`}
              className="text-muted hover:text-text transition-colors px-2 py-1 rounded"
              data-testid="nav-webhooks"
            >
              {t("webhooks")}
            </Link>
            <Link
              href={`/${locale}/settings`}
              className="text-muted hover:text-text transition-colors px-2 py-1 rounded"
              data-testid="nav-settings"
            >
              {t("settings")}
            </Link>
          </nav>
        </div>
        <div>
          <Link
            href={`/${otherLocale}/transactions`}
            className="text-xs font-mono bg-surface-2 border border-border px-3 py-1.5 rounded hover:border-accent transition-colors"
            data-testid="locale-switch"
          >
            {t("switch_lang")}
          </Link>
        </div>
      </header>
      <main className="flex-1 p-6 max-w-7xl w-full mx-auto">{children}</main>
    </div>
  );
}
