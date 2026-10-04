"use client";

import { useLocale, useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  AdapterConfig,
  ApiError,
  ScenarioOutcome,
  simulateTransaction,
} from "../lib/api";
import { formatRial, formatToman } from "../lib/format";
import { useToast } from "./Toast";

const SCENARIOS: ScenarioOutcome[] = [
  "approve",
  "decline",
  "timeout",
  "verify_fail",
  "pending_settle",
  "refund",
];

/**
 * US1: create a payment without writing client code. Step 1 collects the payment parameters,
 * step 2 walks the emulated gateway checkout the way a shopper would — the card face is scenery
 * (FR-011); pressing Pay issues a single `auto_complete` call.
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
  const locale = useLocale();
  const t = useTranslations("simulate");
  const tCommon = useTranslations("common");
  const tScenario = useTranslations("scenario");
  const tGateway = useTranslations("gateway_checkout");
  const { showToast } = useToast();

  const enabled = adapters.filter((a) => a.enabled);
  const [adapter, setAdapter] = useState<AdapterConfig["provider"]>(
    enabled[0]?.provider ?? "zarinpal"
  );

  useEffect(() => {
    if (enabled.length > 0 && !enabled.some((a) => a.provider === adapter)) {
      setAdapter(enabled[0].provider);
    }
  }, [adapters, adapter, enabled]);

  const [amount, setAmount] = useState("1000000");
  const [scenario, setScenario] = useState<ScenarioOutcome | "">("");
  const [description, setDescription] = useState("");
  const [appReference, setAppReference] = useState("");
  const [callbackUrl, setCallbackUrl] = useState("");
  const [autoComplete, setAutoComplete] = useState(false);
  const [step, setStep] = useState<1 | 2>(1);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  const rial = Number(amount) || 0;

  function handleClose() {
    setStep(1);
    setError(null);
    onClose();
  }

  async function submit(complete: boolean) {
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
        auto_complete: complete,
      });
      showToast(complete ? t("success_auto") : t("success_interactive"), "success");
      handleClose();
      if (result.checkout_url && !complete) window.open(result.checkout_url, "_blank");
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

  const scenarioLabel = scenario || "approve";

  return (
    <div
      className="fixed inset-0 z-50 grid place-items-center bg-black/50 p-4 overflow-y-auto"
      role="dialog"
      aria-modal="true"
      aria-label={t("title")}
    >
      <div className="w-full max-w-lg bg-surface-elevated border border-border rounded-console shadow-raised p-5 space-y-4 my-auto">
        <div className="flex items-center justify-between gap-3">
          <h2 className="font-display text-[17px] font-semibold tracking-display">
            {step === 1 ? t("title") : tGateway("title")}
          </h2>
          <span
            className="version-tag font-mono text-[11px] px-1.5 py-0.5 rounded bg-surface-subtle border border-border text-text"
            data-testid="simulate-step"
          >
            {step} / 2
          </span>
        </div>

        {error && (
          <div
            className="p-3 bg-danger-bg border border-danger-border text-danger-ink rounded-console text-sm"
            data-testid="simulate-error"
            role="alert"
          >
            {error}
          </div>
        )}

        {step === 1 ? (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              setStep(2);
            }}
            className="space-y-3"
          >
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
              <span className="block text-xs text-muted font-mono" data-testid="simulate-amount-toman">
                {formatToman(rial, locale)} {t("toman")}
              </span>
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
                {SCENARIOS.map((s) => (
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
                onClick={handleClose}
                className="btn-secondary px-3 py-1.5 rounded-[6px] bg-surface text-text border border-border text-[13px] font-medium hover:bg-surface-subtle transition-colors"
              >
                {tCommon("cancel")}
              </button>
              <button
                type="submit"
                disabled={enabled.length === 0}
                className="btn-primary px-3.5 py-1.5 rounded-[6px] bg-accent text-accent-on text-[13px] font-medium hover:bg-accent/92 transition-colors disabled:opacity-50"
                data-testid="simulate-next"
              >
                {t("next_gateway")}
              </button>
            </div>
          </form>
        ) : (
          <div className="space-y-3" data-testid="simulate-gateway-step">
            <div className="bg-[#201914] text-[#fffdf8] rounded-xl p-5 shadow-lg relative overflow-hidden font-mono">
              <div className="flex items-start justify-between gap-3">
                <div className="w-9 h-7 rounded-[4px] bg-gradient-to-br from-[#e6c583] to-[#b8933f] shadow-inner" />
                <span className="text-[11px] tracking-[0.18em] uppercase opacity-80">{tGateway("shaparak")}</span>
              </div>

              <p className="mt-5 text-lg tracking-[0.12em] tabular-nums" dir="ltr" data-testid="gateway-card-number">
                {tGateway("masked_card_number")}
              </p>

              <div className="mt-4 flex items-end justify-between gap-3">
                <div>
                  <p className="text-[10px] uppercase opacity-60">{tGateway("cardholder")}</p>
                  {/* ponytail: visual preview only; engine never collects or stores card data */}
                  <input
                    value={tGateway("dummy_cardholder")}
                    readOnly
                    disabled
                    className="mt-0.5 w-40 bg-transparent border-0 p-0 text-sm text-[#fffdf8] opacity-90 focus:outline-none disabled:opacity-90"
                    dir="ltr"
                    data-testid="gateway-cardholder"
                  />
                </div>
                <div className="flex gap-2">
                  <span className="text-[10px] uppercase opacity-60 block">CVV2</span>
                  <input
                    value="•••"
                    readOnly
                    disabled
                    className="w-12 bg-transparent border-0 p-0 text-sm tracking-[0.2em] text-[#fffdf8] focus:outline-none"
                    dir="ltr"
                    data-testid="gateway-cvv"
                  />
                </div>
              </div>

              <div className="mt-4 flex items-center justify-between gap-3">
                <div>
                  <p className="text-[10px] uppercase opacity-60">{tGateway("otp")}</p>
                  <input
                    value={tGateway("dummy_otp")}
                    readOnly
                    disabled
                    className="mt-0.5 w-32 bg-transparent border-0 p-0 text-sm tracking-[0.3em] text-[#fffdf8] focus:outline-none"
                    dir="ltr"
                    data-testid="gateway-otp"
                  />
                </div>
                <span className="text-[11px] px-2 py-0.5 rounded bg-[#b8933f] text-[#201914] font-medium">
                  {tGateway("scenario_tag", { scenario: tScenario.has(scenarioLabel) ? tScenario(scenarioLabel) : scenarioLabel })}
                </span>
              </div>
            </div>

            <div className="rounded-console border border-border bg-surface-subtle p-3 space-y-0.5 font-mono text-sm">
              <p className="flex justify-between gap-3">
                <span className="text-muted text-xs">{t("amount_rial")}</span>
                <span className="tabular-nums" data-testid="gateway-amount-rial">
                  {formatRial(rial, locale)}
                </span>
              </p>
              <p className="flex justify-between gap-3">
                <span className="text-muted text-xs">{t("toman")}</span>
                <span className="tabular-nums" data-testid="gateway-amount-toman">
                  {formatToman(rial, locale)}
                </span>
              </p>
            </div>

            <div className="flex items-center justify-between gap-2 pt-1 flex-wrap">
              <button
                type="button"
                onClick={handleClose}
                className="btn-secondary px-3 py-1.5 rounded-[6px] bg-surface text-text border border-border text-[13px] font-medium hover:bg-surface-subtle transition-colors"
              >
                {tCommon("cancel")}
              </button>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="btn-secondary px-3 py-1.5 rounded-[6px] bg-surface text-text border border-border text-[13px] font-medium hover:bg-surface-subtle transition-colors"
                  data-testid="simulate-back"
                >
                  {tCommon("back")}
                </button>
                <button
                  type="button"
                  onClick={() => void submit(autoComplete)}
                  disabled={submitting}
                  className="btn-primary px-3.5 py-1.5 rounded-[6px] bg-accent text-accent-on text-[13px] font-medium hover:bg-accent/92 transition-colors disabled:opacity-50"
                  data-testid="simulate-submit"
                >
                  {submitting ? t("submitting") : tGateway("pay_and_complete")}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}