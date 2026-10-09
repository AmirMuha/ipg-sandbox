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
    <div className="stack-md" data-testid="admin-provider-list">
      {feedback && (
        <div
          role="status"
          className={feedback.ok ? "banner" : "banner banner--danger"}
          data-testid="admin-feedback-banner"
        >
          <svg className="ic" viewBox="0 0 24 24" aria-hidden="true">
            {feedback.ok ? (
              <path d="M20 6L9 17l-5-5" />
            ) : (
              <>
                <circle cx="12" cy="12" r="10" />
                <path d="M12 8v4M12 16h.01" />
              </>
            )}
          </svg>
          <span>{feedback.message}</span>
        </div>
      )}

      <div className="kv">
        {ALL_GATEWAYS.map((g) => {
          const isOffered = offered.includes(g.id);
          const isLoading = loadingProvider === g.id;

          return (
            <div className="kv__row" key={g.id} data-testid={`admin-gateway-card-${g.id}`}>
              <span className="kv__label">
                {g.name}
                <small className="mono ltr text-end" dir="ltr">
                  {g.latin}
                </small>
              </span>

              <span className="kv__val row-flex">
                <span
                  className={`health ${isOffered ? "health--healthy" : "health--disabled"}`}
                  data-testid={`admin-status-${g.id}`}
                >
                  <i className="health__dot" aria-hidden="true" />
                  <span>{isOffered ? t("offered") : t("withdrawn")}</span>
                </span>

                <label className="row-flex cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={isOffered}
                    disabled={isLoading}
                    onChange={(e) => handleToggle(g.id, e.target.checked)}
                    className="w-4 h-4"
                    data-testid={`admin-toggle-${g.id}`}
                  />
                  <span className="small mono">
                    {isOffered ? t("offered") : t("withdrawn")}
                  </span>
                </label>
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
