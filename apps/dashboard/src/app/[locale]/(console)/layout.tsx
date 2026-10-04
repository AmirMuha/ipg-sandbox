import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { Shell } from "../../../components/Shell";

/**
 * Console frame. Sits in a route group so its URLs stay `/[locale]/console`
 * etc. Guarded so unauthenticated requests are redirected to login.
 */
export default function ConsoleLayout({
  children,
  params: { locale },
}: {
  children: React.ReactNode;
  params: { locale: string };
}) {
  const cookieStore = cookies();
  if (!cookieStore.has("ipg_session")) {
    redirect(`/${locale}/login`);
  }

  return <Shell locale={locale}>{children}</Shell>;
}
