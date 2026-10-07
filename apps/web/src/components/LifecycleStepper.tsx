import { ScenarioOutcome, TransactionStatus } from "@/lib/api";

/**
 * Four-stage lifecycle track. Which stage a transaction sits in is derived from
 * the status it actually reached plus the scenario the engine resolved, rather
 * than stored per-stage — the engine exposes no lifecycle field, and a step
 * timeline that disagrees with the status badge is worse than none.
 */
type StepState = "done" | "failed" | "in_progress" | "pending";

const DONE: TransactionStatus[] = ["approved", "settled", "refunded"];
const HOSTED_FAILED: TransactionStatus[] = ["declined", "failed", "expired"];
const HOSTED_LIVE: TransactionStatus[] = ["initiated", "pending"];

function steps(status: TransactionStatus, scenario: string): StepState[] {
  return [
    // A row in this table is itself proof the request was created.
    "done",
    HOSTED_LIVE.includes(status)
      ? "in_progress"
      : HOSTED_FAILED.includes(status)
        ? "failed"
        : DONE.includes(status)
          ? "done"
          : "pending",
    scenario === "timeout"
      ? "failed"
      : DONE.includes(status)
        ? "done"
        : "pending",
    scenario === "verify_fail" ? "failed" : DONE.includes(status) ? "done" : "pending",
  ];
}

const LABEL: Record<string, [string, string]> = {
  request: ["Payment Request", "ایجاد تراکنش"],
  hosted: ["Hosted Checkout", "درگاه پرداخت"],
  callback: ["Callback Delivery", "تحویل وب‌هوک"],
  verify: ["Verification Stage", "اعتبارسنجی"],
};

// .step draws its own connector through .step__rail::after on every row but the last.
const STEP_CLASS: Record<StepState, string> = {
  done: "step step--done",
  failed: "step step--fail",
  in_progress: "step step--live",
  pending: "step",
};

function glyph(state: StepState) {
  if (state === "done") {
    return (
      <svg className="ic" viewBox="0 0 24 24" aria-hidden="true">
        <path d="M20 6L9 17l-5-5" />
      </svg>
    );
  }
  if (state === "failed") {
    return (
      <svg className="ic" viewBox="0 0 24 24" aria-hidden="true">
        <path d="M18 6L6 18M6 6l12 12" />
      </svg>
    );
  }
  return (
    <svg className="ic" viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="10" />
      <path d="M12 6v6l4 2" />
    </svg>
  );
}

export function LifecycleStepper({
  status,
  effectiveScenario,
  locale = "fa",
}: {
  status: TransactionStatus;
  effectiveScenario: ScenarioOutcome | string;
  locale?: string;
}) {
  const fa = locale !== "en";
  const states = steps(status, effectiveScenario);

  return (
    <ol className="stepper" data-testid="lifecycle-stepper">
      {Object.keys(LABEL).map((key, i) => {
        const state = states[i];
        return (
          <li key={key} className={STEP_CLASS[state]} data-testid={`step-${key}`}>
            <span className="step__rail">
              <span className="step__node" data-testid={`step-${key}-${state}`}>
                {glyph(state)}
              </span>
            </span>
            <span className="step__body">
              <span className="step__title">{fa ? LABEL[key][1] : LABEL[key][0]}</span>
            </span>
          </li>
        );
      })}
    </ol>
  );
}
