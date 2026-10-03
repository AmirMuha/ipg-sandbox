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
    <div className="flex items-center gap-3 flex-wrap">
      <button
        type="button"
        onClick={handlePing}
        disabled={pinging}
        className="btn-secondary inline-flex items-center gap-2 px-3 py-1.5 rounded-[6px] bg-surface text-text border border-border text-[13px] font-medium hover:bg-surface-subtle transition-colors disabled:opacity-50"
        data-testid="webhook-ping-btn"
      >
        {pinging ? t("pinging") : t("ping")}
      </button>

      {result && (
        <span
          className={`text-xs font-medium ${result.ok ? "text-success-ink" : "text-danger-ink"}`}
          role="status"
          data-testid="webhook-ping-result"
          dir="ltr"
        >
          {result.ok ? t("ok") : t("failed")}
          {result.status_code ? ` · ${t("http_status", { code: result.status_code })}` : ""}
          {` · ${t("latency", { ms: result.latency_ms })}`}
          {result.error ? ` · ${result.error}` : ""}
        </span>
      )}
    </div>
  );
}
