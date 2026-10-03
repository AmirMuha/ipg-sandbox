import { Shell } from "../../../components/Shell";

/**
 * Console frame. Sits in a route group so its URLs stay `/[locale]/transactions`
 * etc. while marketing pages render their own header/footer — one route tree,
 * two frames, no marketing header nested inside the console chrome.
 */
export default function ConsoleLayout({
  children,
  params: { locale },
}: {
  children: React.ReactNode;
  params: { locale: string };
}) {
  return <Shell locale={locale}>{children}</Shell>;
}
