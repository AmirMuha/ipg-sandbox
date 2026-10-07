/* Load order matters: theme.css carries the @tailwind directives and the
 * @font-face declarations, then the design layer lands on top. tokens.css
 * precedes ui.css because ui.css reads its variables; console.css last so its
 * page furniture (.wrap/.phead/.filters) can override shared defaults. */
import "../../styles/theme.css";
import "../../styles/tokens.css";
import "../../styles/ui.css";
import "../../styles/console.css";
import { notFound } from "next/navigation";
import { getMessages, setRequestLocale } from "next-intl/server";
import { NextIntlClientProvider } from "next-intl";
import { routing, isRtl } from "../../i18n/routing";

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

export default async function LocaleLayout({
  children,
  params: { locale },
}: {
  children: React.ReactNode;
  params: { locale: string };
}) {
  if (!routing.locales.includes(locale as "fa" | "en")) {
    notFound();
  }

  setRequestLocale(locale);
  const dir = isRtl(locale) ? "rtl" : "ltr";
  const messages = await getMessages();

  return (
    <html lang={locale} dir={dir}>
      <body>
        <NextIntlClientProvider messages={messages}>
          {children}
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
