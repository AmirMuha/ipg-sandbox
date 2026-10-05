import createMiddleware from "next-intl/middleware";
import { NextRequest, NextResponse } from "next/server";
import { routing } from "./i18n/routing";

const intlMiddleware = createMiddleware(routing);

export default function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isConsoleRoute =
    pathname.includes("/console") ||
    pathname.includes("/settings") ||
    pathname.includes("/webhooks") ||
    pathname.includes("/admin");

  const hasSession = request.cookies.has("ipg_session");

  if (isConsoleRoute && !hasSession) {
    const locale = pathname.startsWith("/en") ? "en" : "fa";
    return NextResponse.redirect(new URL(`/${locale}/login`, request.url));
  }

  return intlMiddleware(request);
}

export const config = {
  matcher: ["/", "/(fa|en)/:path*"],
};
