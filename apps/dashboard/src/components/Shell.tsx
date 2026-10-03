"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { NavLinks } from "./NavLinks";
import { SimulateModal } from "./SimulateModal";
import { getAdapters } from "../lib/api";

/**
 * Console frame, ported from ipg-sandbox-dashboard.html:
 *   .top-header (56px, sticky) → .sub-bar (48px, bg + soft border)
 *   → .main-body (24px padding, 1480px max, 24px gap)
 *
 * The design's daemon indicator and capacity meter read engine state that
 * the dashboard has no endpoint for, so they are not invented here. The
 * scenario ribbon is skipped for the same reason — its pills are client-side
 * state over localStorage in the mock, and the real equivalent is the
 * project-settings form on /transactions.
 *
 * A client component because the header CTA opens `SimulateModal` (T009). Its one
 * non-prop dependency, `useTranslations`, already runs client-side under the layout's
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
  const otherLocale = locale === "fa" ? "en" : "fa";
  const [simulateOpen, setSimulateOpen] = useState(false);
  const [adapters, setAdapters] = useState<
    Awaited<ReturnType<typeof getAdapters>>
  >([]);

  async function openSimulate() {
    setSimulateOpen(true);
    // Fetched lazily on first open: the modal is the only consumer, and a console
    // frame that blocks its whole subtree on the adapters request is not worth it.
    if (adapters.length === 0) setAdapters(await getAdapters());
  }

  const links = [
    {
      href: `/${locale}/transactions`,
      label: t("transactions"),
      testId: "nav-transactions",
      icon: "list" as const,
    },
    {
      href: `/${locale}/webhooks`,
      label: t("webhooks"),
      testId: "nav-webhooks",
      icon: "bell" as const,
    },
    {
      href: `/${locale}/settings`,
      label: t("settings"),
      testId: "nav-settings",
      icon: "code" as const,
    },
  ];

  return (
    <div className="min-h-screen bg-bg text-text flex flex-col">
      <header className="sticky top-0 z-40 bg-surface border-b border-border">
        <div className="flex items-center justify-between gap-6 h-14 px-6">
          <div className="flex items-center gap-3.5">
            <Link
              href={`/${locale}/transactions`}
              className="logo-badge flex items-center gap-2.5 hover:[&_.logo-icon]:bg-accent/90 transition-colors duration-fast ease-standard"
            >
              <span className="logo-icon w-7 h-7 rounded-sm bg-accent text-accent-on grid place-items-center shrink-0">
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <rect x="2" y="5" width="20" height="14" rx="2" />
                  <line x1="2" y1="10" x2="22" y2="10" />
                  <line x1="7" y1="15" x2="7.01" y2="15" />
                  <line x1="11" y1="15" x2="13" y2="15" />
                </svg>
              </span>
              <span className="flex items-center gap-2">
                <span className="logo-title font-display font-bold text-[17px] tracking-display">
                  {t("title")}
                </span>
                <span className="version-tag font-mono text-[11px] px-1.5 py-0.5 rounded bg-surface-subtle border border-border text-text">
                  v0.1.0-mvp
                </span>
              </span>
            </Link>
          </div>

          <div className="flex items-center gap-3">
            {/* .lang-toggle — segmented control, active side raised */}
            <div className="flex items-center bg-surface border border-border rounded-sm p-0.5">
              <span
                className={`px-2 py-[3px] rounded text-xs font-semibold ${
                  locale === "en"
                    ? "bg-surface-elevated text-text"
                    : "text-muted"
                }`}
              >
                EN
              </span>
              <Link
                href={`/${otherLocale}/transactions`}
                className={`px-2 py-[3px] rounded text-xs font-semibold transition-colors duration-fast ease-standard ${
                  locale === "fa"
                    ? "bg-surface-elevated text-text"
                    : "text-muted hover:text-text"
                }`}
                data-testid="locale-switch"
              >
                فارسی
              </Link>
            </div>

            <button
              type="button"
              onClick={openSimulate}
              className="btn-primary inline-flex items-center gap-2 px-3.5 py-1.5 rounded-[6px] bg-accent text-accent-on text-[13px] font-medium hover:bg-accent/92 active:bg-accent/86 transition-colors duration-fast ease-standard"
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
              >
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
              <span>{t("simulate_payment")}</span>
            </button>
          </div>
        </div>
      </header>

      <div className="bg-bg border-b border-border-soft">
        <div className="flex items-center justify-between gap-4 h-12 px-6">
          <NavLinks links={links} />
        </div>
      </div>

      <main className="flex-1 w-full max-w-console mx-auto p-6 flex flex-col gap-6">
        {children}
      </main>

      <SimulateModal
        adapters={adapters}
        open={simulateOpen}
        onClose={() => setSimulateOpen(false)}
      />
    </div>
  );
}