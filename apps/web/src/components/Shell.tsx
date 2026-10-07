"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { useState, Suspense } from "react";
import { NavLinks } from "./NavLinks";
import { SimulateModal } from "./SimulateModal";
import { TransactionDrawer } from "./TransactionDrawer";
import { ToastProvider } from "./Toast";
import { UserMenu } from "./UserMenu";
import { getAdapters } from "../lib/api";

/**
 * Console frame — `.app` from the design: a topbar, the console nav, and one
 * scrolling main region.
 *
 * The export's language toggle and sun/moon theme toggle are not ported: the
 * locale is fixed and the app ships dark-only, so both would be dead controls.
 * Its daemon indicator and capacity meter read engine state the dashboard has
 * no endpoint for, so the health chip stays the static label it already was
 * rather than implying a live reading.
 *
 * A client component because the topbar CTA opens `SimulateModal` and the frame
 * owns the ToastProvider every mutation button calls into. Its one non-prop
 * dependency, `useTranslations`, already runs client-side under the layout's
 * NextIntlClientProvider.
 */
export function Shell({
  children,
  locale,
}: {
  children: React.ReactNode;
  locale: string;
}) {
  const t = useTranslations("nav");
  const isFa = locale === "fa";
  const [simulateOpen, setSimulateOpen] = useState(false);
  const [adapters, setAdapters] = useState<Awaited<ReturnType<typeof getAdapters>>>([]);

  async function openSimulate() {
    setSimulateOpen(true);
    // Fetched lazily on first open: the modal is the only consumer, and a console
    // frame that blocks its whole subtree on the adapters request is not worth it.
    if (adapters.length === 0) setAdapters(await getAdapters());
  }

  return (
    <div className="app">
      <header className="topbar">
        <Link className="brand" href={`/${locale}/console`}>
          <span className="brand__mark" aria-hidden="true">
            IP
          </span>
          <span>
            <span className="brand__name">IPG Sandbox</span>
            <span className="brand__env ltr">
              {isFa ? "کنسول سندباکس" : "Sandbox console"}
            </span>
          </span>
        </Link>

        <span className="topbar__spacer" />

        <span className="health health--healthy hidden lg:inline-flex">
          <span className="health__dot" aria-hidden="true" />
          {isFa ? "سندباکس آنلاین" : "Sandbox Live"}
        </span>

        <Link href={`/${locale}/home`} className="btn btn--ghost btn--sm">
          {isFa ? "بازگشت به سایت" : "Back to Site"}
        </Link>

        <UserMenu locale={locale} active="console" />

        <button
          type="button"
          onClick={openSimulate}
          className="btn btn--primary btn--sm"
          data-testid="simulate-payment-btn"
        >
          <svg className="ic" viewBox="0 0 24 24" aria-hidden="true">
            <polygon points="6 4 20 12 6 20 6 4" />
          </svg>
          <span>{t("simulate_payment")}</span>
        </button>
      </header>

      <NavLinks locale={locale} />

      <main className="main">
        <div className="wrap">
          <ToastProvider>
            {children}
            {/* useSearchParams() bails the whole route out of static prerender, so the
                drawer needs its own boundary or every console page fails to export. */}
            <Suspense fallback={null}>
              <TransactionDrawer locale={locale} />
            </Suspense>
          </ToastProvider>
        </div>
      </main>

      <SimulateModal
        adapters={adapters}
        open={simulateOpen}
        onClose={() => setSimulateOpen(false)}
      />
    </div>
  );
}
