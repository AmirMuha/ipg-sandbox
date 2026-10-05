"use client";

import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useState } from "react";
import {
  patchProject,
  patchTransaction,
  Project,
  ScenarioOutcome,
  Transaction,
} from "../lib/api";

const SCENARIOS: ScenarioOutcome[] = [
  "approve",
  "decline",
  "timeout",
  "refund",
  "pending_settle",
  "verify_fail",
];

export function ScenarioControls({
  transaction,
  project,
}: {
  transaction?: Transaction;
  project?: Project;
}) {
  const router = useRouter();
  // T073: this panel is one of SC-006\'s primary flows and was rendering in English
  // under /fa/ because every string here was hardcoded.
  const tScenario = useTranslations("scenario_controls");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Per-tx state
  const [forcedScenario, setForcedScenario] = useState<string>(
    transaction?.forced_scenario ?? ""
  );

  // Project state
  const [defaultScenario, setDefaultScenario] = useState<ScenarioOutcome>(
    project?.default_scenario ?? "approve"
  );
  const [pendingSettleDelay, setPendingSettleDelay] = useState<number>(
    project?.pending_settle_delay_s ?? 5
  );
  const [timeoutDelay, setTimeoutDelay] = useState<number>(
    project?.timeout_delay_s ?? 30
  );
  const [webhookUrl, setWebhookUrl] = useState<string>(project?.webhook_url ?? "");
  const [historyCap, setHistoryCap] = useState<number>(project?.history_cap ?? 500);
  const [webhookRetryMax, setWebhookRetryMax] = useState<number>(
    project?.webhook_retry_max ?? 3
  );

  async function handleTxSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!transaction) return;
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const scenario = forcedScenario ? (forcedScenario as ScenarioOutcome) : null;
      await patchTransaction(transaction.id, scenario);
      setSuccess(tScenario("updated"));
      router.refresh();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : tScenario("update_failed"));
    } finally {
      setLoading(false);
    }
  }

  async function handleProjectSubmit(e: React.FormEvent) {
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
      setSuccess(tScenario("project_updated"));
      router.refresh();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : tScenario("project_update_failed"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      {error && (
        <div className="p-3 text-sm text-danger-ink bg-danger-bg border border-danger-border rounded">
          {error}
        </div>
      )}
      {success && (
        <div className="p-3 text-sm text-success-ink bg-success-bg border border-success-border rounded">
          {success}
        </div>
      )}

      {transaction && (
        <form
          onSubmit={handleTxSubmit}
          className="panel bg-surface border border-border rounded-console p-5 space-y-4"
          data-testid="per-tx-scenario-form"
        >
          <h3 className="font-semibold text-sm">{tScenario("per_tx_title")}</h3>
          <div className="flex items-center gap-3">
            <select
              value={forcedScenario}
              onChange={(e) => setForcedScenario(e.target.value)}
              className="bg-surface-subtle border border-border rounded-[6px] px-3 py-1.5 text-[13px] font-mono text-text focus:outline-none focus:border-accent"
              data-testid="per-tx-scenario-select"
            >
              <option value="">{tScenario("clear_force")}</option>
              {SCENARIOS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
            <button
              type="submit"
              disabled={loading}
              className="btn-primary bg-accent text-accent-on px-3.5 py-1.5 rounded-[6px] text-[13px] font-medium hover:bg-accent/92 transition-colors duration-fast ease-standard disabled:opacity-50"
            >
              {tScenario("apply")}
            </button>
          </div>
        </form>
      )}

      {project && (
        <form
          onSubmit={handleProjectSubmit}
          className="panel bg-surface border border-border rounded-console p-5 space-y-4"
          data-testid="project-scenario-form"
        >
          <h3 className="font-semibold text-sm">{tScenario("title_compact")}</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs text-muted mb-1">{tScenario("default_scenario_label")}</label>
              <select
                value={defaultScenario}
                onChange={(e) => setDefaultScenario(e.target.value as ScenarioOutcome)}
                className="w-full bg-surface-subtle border border-border rounded-[6px] px-3 py-1.5 text-[13px] font-mono text-text focus:outline-none focus:border-accent"
                data-testid="project-default-select"
              >
                {SCENARIOS.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-muted mb-1">{tScenario("pending_delay_label")}</label>
              <input
                type="number"
                min="0"
                max="299"
                value={pendingSettleDelay}
                onChange={(e) => setPendingSettleDelay(Number(e.target.value))}
                className="w-full bg-surface-subtle border border-border rounded-[6px] px-3 py-1.5 text-[13px] font-mono text-text focus:outline-none focus:border-accent"
                data-testid="pending-delay-input"
              />
            </div>
            <div>
              <label className="block text-xs text-muted mb-1">{tScenario("timeout_delay_label")}</label>
              <input
                type="number"
                min="0"
                max="299"
                value={timeoutDelay}
                onChange={(e) => setTimeoutDelay(Number(e.target.value))}
                className="w-full bg-surface-subtle border border-border rounded-[6px] px-3 py-1.5 text-[13px] font-mono text-text focus:outline-none focus:border-accent"
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
                className="w-full bg-surface-subtle border border-border rounded-[6px] px-3 py-1.5 text-[13px] font-mono text-text focus:outline-none focus:border-accent"
                data-testid="project-webhook-url-input"
              />
            </div>
            <div>
              <label className="block text-xs text-muted mb-1">
                {tScenario("history_cap_label")}
              </label>
              <input
                type="number"
                min="1"
                value={historyCap}
                onChange={(e) => setHistoryCap(Number(e.target.value))}
                className="w-full bg-surface-subtle border border-border rounded-[6px] px-3 py-1.5 text-[13px] font-mono text-text focus:outline-none focus:border-accent"
                data-testid="project-history-cap-input"
              />
            </div>
            <div>
              <label className="block text-xs text-muted mb-1">
                {tScenario("webhook_retry_max_label")}
              </label>
              <input
                type="number"
                min="0"
                max="10"
                value={webhookRetryMax}
                onChange={(e) => setWebhookRetryMax(Number(e.target.value))}
                className="w-full bg-surface-subtle border border-border rounded-[6px] px-3 py-1.5 text-[13px] font-mono text-text focus:outline-none focus:border-accent"
                data-testid="project-webhook-retry-max-input"
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={loading}
            className="btn-primary bg-accent text-accent-on px-3.5 py-1.5 rounded-[6px] text-[13px] font-medium hover:bg-accent/92 transition-colors duration-fast ease-standard disabled:opacity-50"
            data-testid="save-project-btn"
          >
            {tScenario("save_project")}
          </button>
        </form>
      )}
    </div>
  );
}
