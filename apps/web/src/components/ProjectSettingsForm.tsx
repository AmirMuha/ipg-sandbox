"use client";

import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { patchProject, Project, ScenarioOutcome } from "../lib/api";
import { useToast } from "./Toast";
import { WebhookPingButton } from "./WebhookPingButton";

const SCENARIOS: ScenarioOutcome[] = [
  "approve",
  "decline",
  "timeout",
  "refund",
  "pending_settle",
  "verify_fail",
];

/** Project-wide defaults: the scenario a new payment resolves to and the timers the engine waits on. */
export function ProjectSettingsForm({ project }: { project: Project; locale?: string }) {
  const router = useRouter();
  const t = useTranslations("settings");
  const tScenario = useTranslations("scenario");
  const { showToast } = useToast();

  const [defaultScenario, setDefaultScenario] = useState<ScenarioOutcome>(
    project.default_scenario
  );
  const [webhookUrl, setWebhookUrl] = useState<string>(project.webhook_url ?? "");
  const [pendingSettleDelay, setPendingSettleDelay] = useState<number>(
    project.pending_settle_delay_s
  );
  const [timeoutDelay, setTimeoutDelay] = useState<number>(project.timeout_delay_s);
  const [historyCap, setHistoryCap] = useState<number>(project.history_cap);
  const [webhookRetryMax, setWebhookRetryMax] = useState<number>(project.webhook_retry_max);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const input =
    "w-full bg-surface-subtle border border-border rounded-[6px] px-3 py-1.5 text-[13px] font-mono text-text focus:outline-none focus:border-accent";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      await patchProject({
        default_scenario: defaultScenario,
        pending_settle_delay_s: Number(pendingSettleDelay),
        timeout_delay_s: Number(timeoutDelay),
        // Empty means "unset" — the engine stores null, which also disables auto-delivery.
        webhook_url: webhookUrl.trim() === "" ? null : webhookUrl.trim(),
        history_cap: Number(historyCap),
        webhook_retry_max: Number(webhookRetryMax),
      });
      setSuccess(t("saved"));
      showToast(t("saved"), "success");
      router.refresh();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : t("save_failed");
      setError(msg);
      showToast(msg, "danger");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="panel bg-surface border border-border rounded-console p-5 space-y-4"
      data-testid="project-settings-form"
    >
      {error && (
        <div
          className="p-3 text-sm text-danger-ink bg-danger-bg border border-danger-border rounded"
          role="alert"
        >
          {error}
        </div>
      )}
      {success && (
        <div
          className="p-3 text-sm text-success-ink bg-success-bg border border-success-border rounded"
          role="status"
        >
          {success}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-xs text-muted mb-1">{t("default_scenario")}</label>
          <select
            value={defaultScenario}
            onChange={(e) => setDefaultScenario(e.target.value as ScenarioOutcome)}
            className={input}
            data-testid="project-default-select"
          >
            {SCENARIOS.map((s) => (
              <option key={s} value={s}>
                {tScenario.has(s) ? tScenario(s) : s}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-muted mb-1">{t("pending_settle_delay")}</label>
          <input
            type="number"
            min="0"
            max="299"
            value={pendingSettleDelay}
            onChange={(e) => setPendingSettleDelay(Number(e.target.value))}
            className={input}
            data-testid="pending-delay-input"
          />
        </div>
        <div>
          <label className="block text-xs text-muted mb-1">{t("timeout_delay")}</label>
          <input
            type="number"
            min="0"
            max="299"
            value={timeoutDelay}
            onChange={(e) => setTimeoutDelay(Number(e.target.value))}
            className={input}
            data-testid="timeout-delay-input"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="md:col-span-3">
          <label className="block text-xs text-muted mb-1">
            {tScenario("webhook_url_label")}
          </label>
          <input
            type="url"
            dir="ltr"
            placeholder="https://example.com/webhooks/payment"
            value={webhookUrl}
            onChange={(e) => setWebhookUrl(e.target.value)}
            className={input}
            data-testid="project-webhook-url-input"
          />
        </div>
        <div>
          <label className="block text-xs text-muted mb-1">{t("history_cap")}</label>
          <input
            type="number"
            min="1"
            value={historyCap}
            onChange={(e) => setHistoryCap(Number(e.target.value))}
            className={input}
            data-testid="project-history-cap-input"
          />
        </div>
        <div>
          <label className="block text-xs text-muted mb-1">{t("webhook_retry_max")}</label>
          <input
            type="number"
            min="0"
            max="10"
            value={webhookRetryMax}
            onChange={(e) => setWebhookRetryMax(Number(e.target.value))}
            className={input}
            data-testid="project-webhook-retry-max-input"
          />
        </div>
      </div>

      <div className="flex items-center justify-between gap-4 flex-wrap pt-1">
        <WebhookPingButton targetUrl={webhookUrl || null} />
        <button
          type="submit"
          disabled={loading}
          className="btn-primary bg-accent text-accent-on px-3.5 py-1.5 rounded-[6px] text-[13px] font-medium hover:bg-accent/92 transition-colors duration-fast ease-standard disabled:opacity-50"
          data-testid="save-project-btn"
        >
          {loading ? t("saving") : tScenario("save_project")}
        </button>
      </div>
    </form>
  );
}