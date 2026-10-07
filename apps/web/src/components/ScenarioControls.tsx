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
    <div className="stack-lg">
      {error && <div className="banner banner--danger">{error}</div>}
      {success && <div className="banner">{success}</div>}

      {transaction && (
        <form
          onSubmit={handleTxSubmit}
          className="card card__body stack-md"
          data-testid="per-tx-scenario-form"
        >
          <h3 className="card__title">{tScenario("per_tx_title")}</h3>
          <div className="row-flex">
            <select
              value={forcedScenario}
              onChange={(e) => setForcedScenario(e.target.value)}
              className="select mono"
              aria-label={tScenario("force_scenario")}
              data-testid="per-tx-scenario-select"
            >
              <option value="">{tScenario("clear_force")}</option>
              {SCENARIOS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
            <button type="submit" disabled={loading} className="btn btn--primary">
              {tScenario("apply")}
            </button>
          </div>
        </form>
      )}

      {project && (
        <form
          onSubmit={handleProjectSubmit}
          className="card card__body stack-md"
          data-testid="project-scenario-form"
        >
          <h3 className="card__title">{tScenario("title_compact")}</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="field">
              <label className="field__label" htmlFor="scenario-project-default">
                {tScenario("default_scenario_label")}
              </label>
              <select
                id="scenario-project-default"
                value={defaultScenario}
                onChange={(e) => setDefaultScenario(e.target.value as ScenarioOutcome)}
                className="select mono"
                data-testid="project-default-select"
              >
                {SCENARIOS.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label className="field__label" htmlFor="scenario-pending-delay">
                {tScenario("pending_delay_label")}
              </label>
              <input
                id="scenario-pending-delay"
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
              <label className="field__label" htmlFor="scenario-timeout-delay">
                {tScenario("timeout_delay_label")}
              </label>
              <input
                id="scenario-timeout-delay"
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
              <label className="field__label" htmlFor="scenario-webhook-url">
                {tScenario("webhook_url_label")}
              </label>
              <input
                id="scenario-webhook-url"
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
              <label className="field__label" htmlFor="scenario-history-cap">
                {tScenario("history_cap_label")}
              </label>
              <input
                id="scenario-history-cap"
                type="number"
                min="1"
                value={historyCap}
                onChange={(e) => setHistoryCap(Number(e.target.value))}
                className="input mono"
                data-testid="project-history-cap-input"
              />
            </div>
            <div className="field">
              <label className="field__label" htmlFor="scenario-webhook-retry-max">
                {tScenario("webhook_retry_max_label")}
              </label>
              <input
                id="scenario-webhook-retry-max"
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
          <button
            type="submit"
            disabled={loading}
            className="btn btn--primary"
            data-testid="save-project-btn"
          >
            {tScenario("save_project")}
          </button>
        </form>
      )}
    </div>
  );
}
