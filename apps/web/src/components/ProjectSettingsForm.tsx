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
      className="card card__body stack-md"
      data-testid="project-settings-form"
    >
      {error && (
        <div className="banner banner--danger" role="alert">
          {error}
        </div>
      )}
      {success && (
        <div className="banner" role="status">
          {success}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="field">
          <label className="field__label" htmlFor="project-default-scenario">
            {t("default_scenario")}
          </label>
          <select
            id="project-default-scenario"
            value={defaultScenario}
            onChange={(e) => setDefaultScenario(e.target.value as ScenarioOutcome)}
            className="select"
            data-testid="project-default-select"
          >
            {SCENARIOS.map((s) => (
              <option key={s} value={s}>
                {tScenario.has(s) ? tScenario(s) : s}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label className="field__label" htmlFor="project-pending-delay">
            {t("pending_settle_delay")}
          </label>
          <input
            id="project-pending-delay"
            type="number"
            min="0"
            max="299"
            value={pendingSettleDelay}
            onChange={(e) => setPendingSettleDelay(Number(e.target.value))}
            className="input mono"
            data-testid="pending-delay-input"
          />
        </div>
        <div className="field">
          <label className="field__label" htmlFor="project-timeout-delay">
            {t("timeout_delay")}
          </label>
          <input
            id="project-timeout-delay"
            type="number"
            min="0"
            max="299"
            value={timeoutDelay}
            onChange={(e) => setTimeoutDelay(Number(e.target.value))}
            className="input mono"
            data-testid="timeout-delay-input"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="field md:col-span-3">
          <label className="field__label" htmlFor="project-webhook-url">
            {tScenario("webhook_url_label")}
          </label>
          <input
            id="project-webhook-url"
            type="url"
            dir="ltr"
            placeholder="https://example.com/webhooks/payment"
            value={webhookUrl}
            onChange={(e) => setWebhookUrl(e.target.value)}
            className="input mono"
            data-testid="project-webhook-url-input"
          />
        </div>
        <div className="field">
          <label className="field__label" htmlFor="project-history-cap">
            {t("history_cap")}
          </label>
          <input
            id="project-history-cap"
            type="number"
            min="1"
            value={historyCap}
            onChange={(e) => setHistoryCap(Number(e.target.value))}
            className="input mono"
            data-testid="project-history-cap-input"
          />
        </div>
        <div className="field">
          <label className="field__label" htmlFor="project-webhook-retry-max">
            {t("webhook_retry_max")}
          </label>
          <input
            id="project-webhook-retry-max"
            type="number"
            min="0"
            max="10"
            value={webhookRetryMax}
            onChange={(e) => setWebhookRetryMax(Number(e.target.value))}
            className="input mono"
            data-testid="project-webhook-retry-max-input"
          />
        </div>
      </div>

      <div className="row-flex justify-between">
        <WebhookPingButton targetUrl={webhookUrl || null} />
        <button
          type="submit"
          disabled={loading}
          className="btn btn--primary"
          data-testid="save-project-btn"
        >
          {loading ? t("saving") : tScenario("save_project")}
        </button>
      </div>
    </form>
  );
}
