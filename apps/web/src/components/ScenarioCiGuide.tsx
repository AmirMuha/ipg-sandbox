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
    <div className="stack-md" data-testid="ci-guide">
      <h2 className="card__title">{t("ci_title")}</h2>

      <div className="card">
        <div className="card__body stack-md">
          <p className="muted">{t("ci_body")}</p>

          <div className="row-flex">
            <code className="badge badge--accent mono" dir="ltr" data-testid="ci-scenario-header">
              {HEADER}
            </code>
            {SCENARIOS.map((s) => (
              <code key={s} className="badge mono" dir="ltr">
                {s}
              </code>
            ))}
          </div>

          {/* Ready-to-paste command: this panel is read in CI config, not scanned. The
              header doubles as the terminal's filename line so the copy button sits on it. */}
          <div className="term">
            <div className="term__bar">
              <span className="term__file"># {t("ci_copy")}</span>
              <CopyButton value={command} label={t("ci_copy")} testId="copy-ci-command" />
            </div>
            <div className="term__body">
              <pre dir="ltr" data-testid="ci-command">
                {command}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
