"use client";

import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useState } from "react";
import {
  AdapterConfig,
  ApiError,
  ScenarioOutcome,
  simulateTransaction,
} from "../lib/api";

/**
 * US1: create a payment without writing client code. Two paths out of one form — leave
 * `auto_complete` off to get a hosted checkout URL to click through, or on to run checkout
 * and verify in one step (FR-011).
 */
export function SimulateModal({
  adapters,
  open,
  onClose,
}: {
  adapters: AdapterConfig[];
  open: boolean;
  onClose: () => void;
}) {
  const router = useRouter();
  const t = useTranslations("simulate");
  const tCommon = useTranslations("common");
  const tScenario = useTranslations("scenario");

  const enabled = adapters.filter((a) => a.enabled);
  const [adapter, setAdapter] = useState<AdapterConfig["provider"]>(
    enabled[0]?.provider ?? "zarinpal"
  );
  const [amount, setAmount] = useState("1000000");
  const [scenario, setScenario] = useState<ScenarioOutcome | "">("");
  const [description, setDescription] = useState("");
  const [appReference, setAppReference] = useState("");
  const [callbackUrl, setCallbackUrl] = useState("");
  const [autoComplete, setAutoComplete] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const result = await simulateTransaction({
        adapter,
        amount_rial: Number(amount),
        forced_scenario: scenario || null,
        description: description || undefined,
        app_reference: appReference || undefined,
        callback_url: callbackUrl || undefined,
        auto_complete: autoComplete,
      });
      onClose();
      if (result.checkout_url && !autoComplete) window.open(result.checkout_url, "_blank");
      router.refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("error"));
    } finally {
      setSubmitting(false);
    }
  }

  const input =
    "w-full px-3 py-2 rounded-[6px] bg-surface border border-border text-sm text-text " +
    "focus:border-accent focus:outline-none";

  return (
    <div
      className="fixed inset-0 z-50 grid place-items-center bg-black/50 p-4"
      role="dialog"
      aria-modal="true"
      aria-label={t("title")}
    >
      <div className="w-full max-w-lg bg-surface-elevated border border-border rounded-console shadow-raised p-5 space-y-4">
        <h2 className="font-display text-[17px] font-semibold tracking-display">{t("title")}</h2>

        {error && (
          <div
            className="p-3 bg-danger-bg border border-danger-border text-danger-ink rounded-console text-sm"
            data-testid="simulate-error"
            role="alert"
          >
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-3">
          <label className="block space-y-1">
            <span className="text-xs text-text-2 font-medium">{t("adapter")}</span>
            <select
              value={adapter}
              onChange={(e) => setAdapter(e.target.value as AdapterConfig["provider"])}
              className={input}
              data-testid="simulate-adapter"
            >
              {enabled.map((a) => (
                <option key={a.id} value={a.provider}>
                  {a.provider}
                </option>
              ))}
            </select>
          </label>

          <label className="block space-y-1">
            <span className="text-xs text-text-2 font-medium">{t("amount_rial")}</span>
            <input
              type="number"
              min={0}
              required
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className={`${input} font-mono`}
              dir="ltr"
              data-testid="simulate-amount"
            />
          </label>

          <label className="block space-y-1">
            <span className="text-xs text-text-2 font-medium">{t("scenario")}</span>
            <select
              value={scenario}
              onChange={(e) => setScenario(e.target.value as ScenarioOutcome | "")}
              className={input}
              data-testid="simulate-scenario"
            >
              <option value="">—</option>
              {(
                [
                  "approve",
                  "decline",
                  "timeout",
                  "verify_fail",
                  "pending_settle",
                  "refund",
                ] as ScenarioOutcome[]
              ).map((s) => (
                <option key={s} value={s}>
                  {tScenario.has(s) ? tScenario(s) : s}
                </option>
              ))}
            </select>
          </label>

          <div className="grid grid-cols-2 gap-3">
            <label className="block space-y-1">
              <span className="text-xs text-text-2 font-medium">{t("app_reference")}</span>
              <input
                value={appReference}
                onChange={(e) => setAppReference(e.target.value)}
                className={input}
                dir="ltr"
                data-testid="simulate-reference"
              />
            </label>
            <label className="block space-y-1">
              <span className="text-xs text-text-2 font-medium">{t("description")}</span>
              <input
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className={input}
                data-testid="simulate-description"
              />
            </label>
          </div>

          <label className="block space-y-1">
            <span className="text-xs text-text-2 font-medium">{t("callback_url")}</span>
            <input
              type="url"
              value={callbackUrl}
              onChange={(e) => setCallbackUrl(e.target.value)}
              placeholder="http://localhost:3000/api/webhook"
              className={`${input} font-mono`}
              dir="ltr"
              data-testid="simulate-callback"
            />
          </label>

          <label className="flex items-start gap-2 text-sm">
            <input
              type="checkbox"
              checked={autoComplete}
              onChange={(e) => setAutoComplete(e.target.checked)}
              className="mt-1"
              data-testid="simulate-auto-complete"
            />
            <span>
              {t("auto_complete")}
              <span className="block text-xs text-muted">{t("auto_complete_hint")}</span>
            </span>
          </label>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary px-3 py-1.5 rounded-[6px] bg-surface text-text border border-border text-[13px] font-medium hover:bg-surface-subtle transition-colors"
            >
              {tCommon("cancel")}
            </button>
            <button
              type="submit"
              disabled={submitting || enabled.length === 0}
              className="btn-primary px-3.5 py-1.5 rounded-[6px] bg-accent text-accent-on text-[13px] font-medium hover:bg-accent/92 transition-colors disabled:opacity-50"
              data-testid="simulate-submit"
            >
              {submitting ? t("submitting") : t("submit")}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
