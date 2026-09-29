"use client";

import { useRouter } from "next/navigation";
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

  async function handleTxSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!transaction) return;
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const scenario = forcedScenario ? (forcedScenario as ScenarioOutcome) : null;
      await patchTransaction(transaction.id, scenario);
      setSuccess("Scenario updated");
      router.refresh();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update scenario");
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
      });
      setSuccess("Project defaults updated");
      router.refresh();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update project");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      {error && (
        <div className="p-3 text-sm text-danger bg-danger/10 border border-danger/20 rounded">
          {error}
        </div>
      )}
      {success && (
        <div className="p-3 text-sm text-success bg-success/10 border border-success/20 rounded">
          {success}
        </div>
      )}

      {transaction && (
        <form
          onSubmit={handleTxSubmit}
          className="bg-surface border border-border p-4 rounded-lg space-y-4"
          data-testid="per-tx-scenario-form"
        >
          <h3 className="font-semibold text-sm">Force Transaction Scenario</h3>
          <div className="flex items-center gap-3">
            <select
              value={forcedScenario}
              onChange={(e) => setForcedScenario(e.target.value)}
              className="bg-surface-2 border border-border rounded px-3 py-1.5 text-sm font-mono focus:outline-none focus:border-accent"
              data-testid="per-tx-scenario-select"
            >
              <option value="">Project Default (No Force)</option>
              {SCENARIOS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
            <button
              type="submit"
              disabled={loading}
              className="bg-accent text-white px-4 py-1.5 rounded text-sm hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              Apply
            </button>
          </div>
        </form>
      )}

      {project && (
        <form
          onSubmit={handleProjectSubmit}
          className="bg-surface border border-border p-4 rounded-lg space-y-4"
          data-testid="project-scenario-form"
        >
          <h3 className="font-semibold text-sm">Project Default Scenario & Delays</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs text-muted mb-1">Default Scenario</label>
              <select
                value={defaultScenario}
                onChange={(e) => setDefaultScenario(e.target.value as ScenarioOutcome)}
                className="w-full bg-surface-2 border border-border rounded px-3 py-1.5 text-sm font-mono focus:outline-none focus:border-accent"
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
              <label className="block text-xs text-muted mb-1">Pending Settle Delay (s)</label>
              <input
                type="number"
                min="0"
                max="299"
                value={pendingSettleDelay}
                onChange={(e) => setPendingSettleDelay(Number(e.target.value))}
                className="w-full bg-surface-2 border border-border rounded px-3 py-1.5 text-sm font-mono focus:outline-none focus:border-accent"
                data-testid="pending-delay-input"
              />
            </div>
            <div>
              <label className="block text-xs text-muted mb-1">Timeout Delay (s)</label>
              <input
                type="number"
                min="0"
                max="299"
                value={timeoutDelay}
                onChange={(e) => setTimeoutDelay(Number(e.target.value))}
                className="w-full bg-surface-2 border border-border rounded px-3 py-1.5 text-sm font-mono focus:outline-none focus:border-accent"
                data-testid="timeout-delay-input"
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={loading}
            className="bg-accent text-white px-4 py-1.5 rounded text-sm hover:opacity-90 transition-opacity disabled:opacity-50"
            data-testid="save-project-btn"
          >
            Save Project Defaults
          </button>
        </form>
      )}
    </div>
  );
}
