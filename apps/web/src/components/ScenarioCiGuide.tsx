"use client";

import { useTranslations } from "next-intl";
import { CopyButton } from "./CopyButton";

const SCENARIOS = [
  "approve",
  "decline",
  "timeout",
  "refund",
  "pending_settle",
  "verify_fail",
] as const;

/**
 * FR-010 / SC-004: the sandbox has to be drivable from a CI pipeline with no dashboard and
 * no browser. The scenario hint header is that mechanism — one request header resolves the
 * next payment's outcome, so a pipeline asserts a decline without pre-creating a row.
 */
const HEADER = "X-Sandbox-Scenario";

export function ScenarioCiGuide({ apiBase }: { apiBase: string }) {
  const t = useTranslations("settings");

  const command = `curl -s -X POST ${apiBase}/zarinpal/request/payment \\
  -H "Content-Type: application/json" \\
  -H "${HEADER}: decline" \\
  -d '{"amount":250000,"currency":"IRR","merchant_id":"sandbox-merchant"}'`;

  return (
    <div className="space-y-4" data-testid="ci-guide">
      <h2 className="font-display text-[17px] font-semibold tracking-display">
        {t("ci_title")}
      </h2>

      <div className="panel bg-surface border border-border rounded-console p-5 space-y-4">
        <p className="text-sm text-text-2">{t("ci_body")}</p>

        <div className="flex items-center gap-2 flex-wrap">
          <code
            className="version-tag font-mono text-[11px] px-1.5 py-0.5 rounded bg-surface-subtle border border-border text-text"
            dir="ltr"
            data-testid="ci-scenario-header"
          >
            {HEADER}
          </code>
          {SCENARIOS.map((s) => (
            <code
              key={s}
              className="version-tag font-mono text-[11px] px-1.5 py-0.5 rounded bg-surface-subtle border border-border text-text-2"
              dir="ltr"
            >
              {s}
            </code>
          ))}
        </div>

        {/* Ready-to-paste command: this panel is read in CI config, not scanned. */}
        <div className="bg-surface-2 border border-border rounded p-3" dir="ltr">
          <div className="flex items-center justify-between gap-2 mb-1.5">
            <span className="font-mono text-[11px] text-muted"># {t("ci_copy")}</span>
            <CopyButton value={command} label={t("ci_copy")} testId="copy-ci-command" />
          </div>
          <pre
            className="font-mono text-xs text-text whitespace-pre-wrap break-all"
            data-testid="ci-command"
          >
            {command}
          </pre>
        </div>
      </div>
    </div>
  );
}