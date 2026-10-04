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
  "pending_settle",
  "verify_fail",
  "refund",
];

/**
 * One-click scenario switcher sitting above the transactions table: pick the scenario the next
 * simulated payment resolves to, tune how long `pending_settle` waits, and prove the callback
 * endpoint is reachable — without leaving the list.
 */
export function ScenarioRibbon({
  project,
  locale,
}: {
  project: Project;
  locale?: string;
}) {
  const router = useRouter();
  const t = useTranslations("scenario_ribbon");
  const tScenario = useTranslations("scenario");
  const { showToast } = useToast();

  // Optimistic local mirror of the two fields the ribbon writes; router.refresh() re-syncs them.
  const [scenario, setScenario] = useState<ScenarioOutcome>(project.default_scenario);
  const [delay, setDelay] = useState<number>(project.pending_settle_delay_s);
  const [saving, setSaving] = useState(false);

  async function apply(updates: Partial<Project>, message: string) {
    setSaving(true);
    try {
      await patchProject(updates);
      showToast(message, "success");
      router.refresh();
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : t("update_failed"), "danger");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div
      className="panel bg-surface border border-border rounded-console px-4 py-3 flex items-center gap-4 flex-wrap"
      data-testid="scenario-ribbon"
    >
      <span className="text-xs font-medium text-muted whitespace-nowrap">{t("title")}</span>

      <div className="flex items-center gap-1.5 flex-wrap">
        {SCENARIOS.map((s) => (
          <button
            key={s}
            type="button"
            disabled={saving}
            aria-pressed={s === scenario}
            onClick={() => {
              setScenario(s);
              void apply({ default_scenario: s }, t("scenario_updated"));
            }}
            className={
              "px-2.5 py-1 rounded-[6px] text-xs font-medium transition-colors duration-fast ease-standard disabled:opacity-50 " +
              (s === scenario
                ? "bg-accent-subtle border border-accent text-accent-ink"
                : "bg-surface-subtle border border-border text-text hover:bg-surface")
            }
            data-testid={`scenario-pill-${s}`}
          >
            {tScenario.has(s) ? tScenario(s) : s}
          </button>
        ))}
      </div>

      <label className="flex items-center gap-2 text-xs text-muted whitespace-nowrap">
        <span>{t("delay_label")}</span>
        <input
          id="settle-delay-range"
          type="range"
          min={1}
          max={15}
          step={1}
          value={Math.min(15, Math.max(1, delay))}
          disabled={saving}
          onChange={(e) => setDelay(Number(e.target.value))}
          onMouseUp={() => void apply({ pending_settle_delay_s: delay }, t("delay_updated"))}
          onTouchEnd={() => void apply({ pending_settle_delay_s: delay }, t("delay_updated"))}
          onKeyUp={() => void apply({ pending_settle_delay_s: delay }, t("delay_updated"))}
          className="w-28 accent-[var(--accent)]"
          data-testid="pending-delay-input"
        />
        <span className="font-mono text-text tabular-nums" data-testid="pending-delay-value">
          {delay} {t("seconds")}
        </span>
      </label>

      <div className="ms-auto">
        <WebhookPingButton targetUrl={project.webhook_url} />
      </div>
    </div>
  );
}