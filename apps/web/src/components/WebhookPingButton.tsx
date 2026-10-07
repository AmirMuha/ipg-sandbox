"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { ApiError, pingWebhook, WebhookPingResponse } from "../lib/api";

/**
 * US4: prove the configured callback endpoint is reachable, without waiting for a real payment.
 * The engine's 3s timeout bounds this; a failure is a reported result, not an error state.
 */
export function WebhookPingButton({ targetUrl }: { targetUrl?: string | null }) {
  const t = useTranslations("webhook_diagnostics");
  const [pinging, setPinging] = useState(false);
  const [result, setResult] = useState<WebhookPingResponse | null>(null);

  async function handlePing() {
    setPinging(true);
    setResult(null);
    try {
      setResult(await pingWebhook(targetUrl));
    } catch (err) {
      // The engine itself is unreachable — that is a different failure than a bad endpoint.
      setResult({
        ok: false,
        target_url: targetUrl ?? "",
        status_code: null,
        latency_ms: 0,
        error: err instanceof ApiError ? err.message : String(err),
      });
    } finally {
      setPinging(false);
    }
  }

  return (
    <div className="row-flex">
      <button
        type="button"
        onClick={handlePing}
        disabled={pinging}
        className="btn btn--secondary"
        data-testid="webhook-ping-btn"
      >
        <svg className="ic" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
        </svg>
        <span>{pinging ? t("pinging") : t("ping")}</span>
      </button>

      {result && (
        <span
          className={`health ${result.ok ? "health--healthy" : "health--degraded"}`}
          role="status"
          data-testid="webhook-ping-result"
          dir="ltr"
        >
          <i className="health__dot" aria-hidden="true" />
          <span>
            {result.ok ? t("ok") : t("failed")}
            {result.status_code ? ` · ${t("http_status", { code: result.status_code })}` : ""}
            {` · ${t("latency", { ms: result.latency_ms })}`}
            {result.error ? ` · ${result.error}` : ""}
          </span>
        </span>
      )}
    </div>
  );
}
