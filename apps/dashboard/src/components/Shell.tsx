"use client";

import { useTranslations } from "next-intl";
import { useState, Suspense } from "react";
import { NavLinks } from "./NavLinks";
import { SimulateModal } from "./SimulateModal";
import { TransactionDrawer } from "./TransactionDrawer";
import { SiteNav } from "./SiteNav";
import { ToastProvider } from "./Toast";
import { getAdapters } from "../lib/api";

/**
 * Console frame, ported from ipg-sandbox-dashboard.html:
 *   SiteNav (.site-header, 64px, sticky) → .sub-bar (sticky under it)
 *   → .main-body (24px padding, 1480px max, 24px gap)
 *
 * The design's daemon indicator and capacity meter read engine state that
 * the dashboard has no endpoint for, so they are not invented here. The
 * scenario ribbon is skipped for the same reason — its pills are client-side
 * state over localStorage in the mock, and the real equivalent is the
 * project-settings form on /transactions.
 *
 * A client component because the sub-bar CTA opens `SimulateModal` (T009) and the
 * frame owns the ToastProvider every mutation button calls into. Its one non-prop
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
    <div className="min-h-screen bg-bg text-text flex flex-col">
      <SiteNav locale={locale} active="console" maxWidthClass="max-w-console" />

      <div className="sticky top-16 z-40 bg-surface/92 backdrop-blur-[12px] border-b border-border">
        <div className="w-full max-w-console mx-auto px-4 md:px-6 flex items-center justify-between gap-4 h-14">
          <NavLinks locale={locale} />

          <div className="flex items-center gap-2 shrink-0">
            <span className="hidden lg:inline-flex items-center gap-2 text-xs text-muted">
              <span className="status-dot" aria-hidden="true" />
              {isFa ? "سندباکس آنلاین" : "Sandbox Live"}
            </span>

            {/* Locale is fixed to Persian for now, so the .lang-toggle pill is hidden. */}

            <button
              type="button"
              onClick={openSimulate}
              className="btn-primary inline-flex items-center gap-2 min-h-9 px-3.5 py-1.5 rounded-[6px] bg-accent text-accent-on text-[13px] font-medium hover:bg-accent-hover active:bg-accent-active transition-colors duration-fast ease-standard"
              data-testid="simulate-payment-btn"
            >
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                aria-hidden="true"
              >
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
              <span>{t("simulate_payment")}</span>
            </button>
          </div>
        </div>
      </div>

      <ToastProvider>
        <main className="flex-1 w-full max-w-console mx-auto p-6 flex flex-col gap-6">
          {children}
          {/* useSearchParams() bails the whole route out of static prerender, so the
              drawer needs its own boundary or every console page fails to export. */}
          <Suspense fallback={null}>
            <TransactionDrawer locale={locale} />
          </Suspense>
        </main>
      </ToastProvider>

      <SimulateModal
        adapters={adapters}
        open={simulateOpen}
        onClose={() => setSimulateOpen(false)}
      />
    </div>
  );
}