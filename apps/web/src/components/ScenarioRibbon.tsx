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
    <div className="ribbon" data-testid="scenario-ribbon">
      <span className="ribbon__dot" aria-hidden="true" />
      <span className="ribbon__label">{t("title")}</span>

      <div className="seg" role="group" aria-label={t("title")}>
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
            data-testid={`scenario-pill-${s}`}
          >
            {tScenario.has(s) ? tScenario(s) : s}
          </button>
        ))}
      </div>

      <label className="ribbon__meta flex items-center gap-2 whitespace-nowrap">
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
        <span className="mono" data-testid="pending-delay-value">
          {delay} {t("seconds")}
        </span>
      </label>

      <span className="ms-auto">
        <WebhookPingButton targetUrl={project.webhook_url} />
      </span>
    </div>
  );
}