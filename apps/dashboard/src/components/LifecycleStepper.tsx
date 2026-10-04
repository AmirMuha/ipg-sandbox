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
    <ol className="flex items-start gap-1" data-testid="lifecycle-stepper">
      {Object.keys(LABEL).map((key, i) => {
        const state = states[i];
        const ring =
          state === "done"
            ? "bg-success text-white border-success"
            : state === "failed"
              ? "bg-danger text-white border-danger"
              : state === "in_progress"
                ? "bg-accent text-accent-on border-accent"
                : "bg-surface-2 text-muted border-border";
        return (
          <li key={key} className="flex items-start flex-1 min-w-0" data-testid={`step-${key}`}>
            <div className="flex flex-col items-center gap-1.5 min-w-0">
              <span
                className={`w-7 h-7 rounded-full grid place-items-center border text-xs shrink-0 ${ring} ${
                  state === "in_progress" ? "animate-pulse" : ""
                }`}
                data-testid={`step-${key}-${state}`}
              >
                {state === "done" ? (
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                ) : state === "failed" ? (
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                ) : state === "in_progress" ? (
                  <span className="w-2 h-2 rounded-full bg-current" />
                ) : (
                  <span className="w-1.5 h-1.5 rounded-full bg-current" />
                )}
              </span>
              <span className="text-[10px] text-center leading-tight text-text-2">
                {fa ? LABEL[key][1] : LABEL[key][0]}
              </span>
            </div>
            {i < states.length - 1 && (
              <span
                className={`h-px flex-1 mt-3.5 mx-1 ${
                  states[i] === "done" ? "bg-success/40" : "bg-border"
                }`}
                aria-hidden
              />
            )}
          </li>
        );
      })}
    </ol>
  );
}