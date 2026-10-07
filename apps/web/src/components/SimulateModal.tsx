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

  const scenarioLabel = scenario || "approve";

  return (
    <div
      className="scrim grid place-items-center p-4 overflow-y-auto"
      data-open="true"
      role="dialog"
      aria-modal="true"
      aria-label={t("title")}
    >
      <div className="card animate-modal w-full max-w-lg my-auto">
        <div className="card__head">
          <h2 className="card__title">{step === 1 ? t("title") : tGateway("title")}</h2>
          <span className="badge badge--accent mono" data-testid="simulate-step">
            {step} / 2
          </span>
        </div>

        <div className="card__body stack-md">
          {error && (
            <div className="banner banner--danger" data-testid="simulate-error" role="alert">
              {error}
            </div>
          )}

          {step === 1 ? (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                setStep(2);
              }}
              className="stack-md"
            >
              <div className="formrow">
                <label className="field">
                  <span className="field__label">{t("adapter")}</span>
                  <select
                    value={adapter}
                    onChange={(e) => setAdapter(e.target.value as AdapterConfig["provider"])}
                    className="select"
                    data-testid="simulate-adapter"
                  >
                    {enabled.map((a) => (
                      <option key={a.id} value={a.provider}>
                        {a.provider}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="field">
                  <span className="field__label">{t("scenario")}</span>
                  <select
                    value={scenario}
                    onChange={(e) => setScenario(e.target.value as ScenarioOutcome | "")}
                    className="select"
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
              </div>

              <label className="field">
                <span className="field__label">{t("amount_rial")}</span>
                <input
                  type="number"
                  min={0}
                  required
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  className="input mono"
                  dir="ltr"
                  data-testid="simulate-amount"
                />
                <span className="field__hint mono" data-testid="simulate-amount-toman">
                  {formatToman(rial, locale)} {t("toman")}
                </span>
              </label>

              <div className="formrow">
                <label className="field">
                  <span className="field__label">{t("app_reference")}</span>
                  <input
                    value={appReference}
                    onChange={(e) => setAppReference(e.target.value)}
                    className="input mono"
                    dir="ltr"
                    data-testid="simulate-reference"
                  />
                </label>
                <label className="field">
                  <span className="field__label">{t("description")}</span>
                  <input
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    className="input"
                    data-testid="simulate-description"
                  />
                </label>
              </div>

              <label className="field">
                <span className="field__label">{t("callback_url")}</span>
                <input
                  type="url"
                  value={callbackUrl}
                  onChange={(e) => setCallbackUrl(e.target.value)}
                  placeholder="http://localhost:3000/api/webhook"
                  className="input mono"
                  dir="ltr"
                  data-testid="simulate-callback"
                />
              </label>

              <label className="flex items-start gap-2">
                <input
                  type="checkbox"
                  checked={autoComplete}
                  onChange={(e) => setAutoComplete(e.target.checked)}
                  className="mt-1"
                  data-testid="simulate-auto-complete"
                />
                <span>
                  {t("auto_complete")}
                  <span className="field__hint block">{t("auto_complete_hint")}</span>
                </span>
              </label>

              <div className="row-flex justify-end">
                <button type="button" onClick={handleClose} className="btn btn--ghost">
                  {tCommon("cancel")}
                </button>
                <button
                  type="submit"
                  disabled={enabled.length === 0}
                  className="btn btn--primary"
                  data-testid="simulate-next"
                >
                  {t("next_gateway")}
                </button>
              </div>
            </form>
          ) : (
            <div className="stack-md" data-testid="simulate-gateway-step">
              <div className="checkout__panel">
                <div className="checkout__bank">
                  <span className="checkout__bankname">{tGateway("shaparak")}</span>
                  <span className="badge badge--accent">
                    {tGateway("scenario_tag", {
                      scenario: tScenario.has(scenarioLabel)
                        ? tScenario(scenarioLabel)
                        : scenarioLabel,
                    })}
                  </span>
                </div>

                <p className="checkout__cardno" dir="ltr" data-testid="gateway-card-number">
                  {tGateway("masked_card_number")}
                </p>

                <div className="checkout__meta">
                  <label className="field w-40">
                    <span className="field__label">{tGateway("cardholder")}</span>
                    {/* ponytail: visual preview only; engine never collects or stores card data */}
                    <input
                      value={tGateway("dummy_cardholder")}
                      readOnly
                      disabled
                      className="input mono"
                      dir="ltr"
                      data-testid="gateway-cardholder"
                    />
                  </label>
                  <label className="field w-20">
                    <span className="field__label">CVV2</span>
                    <input
                      value="•••"
                      readOnly
                      disabled
                      className="input mono"
                      dir="ltr"
                      data-testid="gateway-cvv"
                    />
                  </label>
                  <label className="field w-32">
                    <span className="field__label">{tGateway("otp")}</span>
                    <input
                      value={tGateway("dummy_otp")}
                      readOnly
                      disabled
                      className="input mono"
                      dir="ltr"
                      data-testid="gateway-otp"
                    />
                  </label>
                </div>

                <div className="checkout__meta">
                  <span className="stack-sm">
                    <span className="small muted">{t("amount_rial")}</span>
                    <span className="checkout__amount" data-testid="gateway-amount-rial">
                      {formatRial(rial, locale)}
                    </span>
                  </span>
                  <span className="stack-sm">
                    <span className="small muted">{t("toman")}</span>
                    <span className="checkout__amount" data-testid="gateway-amount-toman">
                      {formatToman(rial, locale)}
                    </span>
                  </span>
                </div>
              </div>

              <div className="row-flex justify-between">
                <button type="button" onClick={handleClose} className="btn btn--ghost">
                  {tCommon("cancel")}
                </button>
                <div className="row-flex">
                  <button
                    type="button"
                    onClick={() => setStep(1)}
                    className="btn btn--secondary"
                    data-testid="simulate-back"
                  >
                    {tCommon("back")}
                  </button>
                  <button
                    type="button"
                    onClick={() => void submit(autoComplete)}
                    disabled={submitting}
                    className="btn btn--primary"
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
    </div>
  );
}
