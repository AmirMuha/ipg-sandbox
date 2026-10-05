"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";
import { setPlatformProvider } from "../lib/api";

const ALL_GATEWAYS = [
  { id: "zarinpal", monogram: "zp", name: "زرین‌پال", latin: "zarinpal · REST" },
  { id: "idpay", monogram: "idp", name: "آیدی‌پی", latin: "idpay · REST" },
  { id: "behpardakht", monogram: "bp", name: "به‌پرداخت ملت", latin: "behpardakht mellat · SOAP" },
  { id: "saman", monogram: "sep", name: "سامان کیش (سپ)", latin: "saman sep · REST/SOAP" },
  { id: "sadad", monogram: "sd", name: "سداد (بانک ملی)", latin: "sadad melli · REST" },
  { id: "parsian", monogram: "pec", name: "تجارت الکترونیک پارسیان (تاپ)", latin: "parsian pec · SOAP" },
  { id: "pasargad", monogram: "pep", name: "پرداخت الکترونیک پاسارگاد", latin: "pasargad pep · REST" },
  { id: "asan_pardakht", monogram: "ap", name: "آسان پرداخت (آپ)", latin: "asan pardakht · REST/SOAP" },
  { id: "pardakht_novin", monogram: "pna", name: "پرداخت نوین آرین", latin: "pardakht novin · REST/SOAP" },
  { id: "irankish", monogram: "ik", name: "کارت اعتباری ایران‌کیش", latin: "irankish · REST" },
  { id: "fanava", monogram: "fn", name: "فن‌آوا کارت", latin: "fanava card · REST/SOAP" },
  { id: "sarmayeh", monogram: "sm", name: "پرداخت الکترونیک سرمایه", latin: "sarmayeh bank · REST/SOAP" },
  { id: "sizpay", monogram: "sz", name: "سیزپی (پرداخت‌یار)", latin: "sizpay · REST" },
] as const;

export function AdminProviderList({
  initialOffered,
}: {
  initialOffered: string[];
}) {
  const t = useTranslations("admin_providers");
  const [offered, setOffered] = useState<string[]>(initialOffered);
  const [loadingProvider, setLoadingProvider] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{
    provider: string;
    ok: boolean;
    message: string;
  } | null>(null);

  async function handleToggle(providerId: string, newEnabled: boolean) {
    setLoadingProvider(providerId);
    setFeedback(null);
    try {
      const res = await setPlatformProvider(providerId, newEnabled);
      setOffered(res.providers);
      setFeedback({
        provider: providerId,
        ok: true,
        message: t("saved"),
      });
    } catch (err: unknown) {
      let msg = err instanceof Error ? err.message : t("save_failed");
      if (typeof msg === "string" && msg.includes("At least one")) {
        msg = t("last_gateway_guard");
      }
      setFeedback({
        provider: providerId,
        ok: false,
        message: msg,
      });
    } finally {
      setLoadingProvider(null);
    }
  }

  return (
    <div className="space-y-4" data-testid="admin-provider-list">
      {feedback && (
        <div
          role="status"
          className={`p-3.5 rounded-md border text-xs font-medium ${
            feedback.ok
              ? "bg-success-bg border-success-border text-success-ink"
              : "bg-danger-bg border-danger-border text-danger-ink"
          }`}
          data-testid="admin-feedback-banner"
        >
          {feedback.message}
        </div>
      )}

      <div className="grid grid-cols-1 gap-3">
        {ALL_GATEWAYS.map((g) => {
          const isOffered = offered.includes(g.id);
          const isLoading = loadingProvider === g.id;

          return (
            <div
              key={g.id}
              className="panel bg-surface border border-border rounded-console p-4 flex items-center justify-between gap-4 flex-wrap"
              data-testid={`admin-gateway-card-${g.id}`}
            >
              <div className="flex items-center gap-3 min-w-0">
                <span
                  className="w-9 h-9 grid place-items-center rounded-md border border-accent-border bg-accent-subtle text-accent-ink font-mono text-xs font-semibold shrink-0"
                  aria-hidden="true"
                >
                  {g.monogram}
                </span>
                <div>
                  <h3 className="text-sm font-semibold text-text">
                    {g.name}
                    <span className="block font-mono text-[11px] text-muted font-normal" dir="ltr">
                      {g.latin}
                    </span>
                  </h3>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <span
                  className="flex items-center gap-1.5 text-xs"
                  data-testid={`admin-status-${g.id}`}
                >
                  <span
                    className={`inline-block w-2 h-2 rounded-full ${
                      isOffered ? "bg-success" : "bg-border"
                    }`}
                    aria-hidden="true"
                  />
                  <span className={isOffered ? "text-success-ink" : "text-muted"}>
                    {isOffered ? t("offered") : t("withdrawn")}
                  </span>
                </span>

                <label className="flex items-center gap-2 cursor-pointer text-xs shrink-0 select-none">
                  <input
                    type="checkbox"
                    checked={isOffered}
                    disabled={isLoading}
                    onChange={(e) => handleToggle(g.id, e.target.checked)}
                    className="accent-accent"
                    data-testid={`admin-toggle-${g.id}`}
                  />
                  <span className="text-text-2 font-mono text-xs">
                    {isOffered ? t("offered") : t("withdrawn")}
                  </span>
                </label>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
