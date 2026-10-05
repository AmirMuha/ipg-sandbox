import { redirect } from "next/navigation";

/**
 * The locale root is the marketing home. The console keeps its own explicit
 * entry points (`/[locale]/transactions`, `/[locale]/settings`), so landing
 * here no longer drops you straight into the transaction table.
 */
export default function LocaleIndexPage({
  params: { locale },
}: {
  params: { locale: string };
}) {
  redirect(`/${locale}/home`);
}
