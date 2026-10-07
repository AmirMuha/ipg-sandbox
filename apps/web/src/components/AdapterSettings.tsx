"use client";

import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { AdapterConfig, apiBase, patchAdapter, testAdapter } from "../lib/api";
import { CopyButton } from "./CopyButton";

/** Behpardakht's Mellat surface is SOAP/WSDL; the other two are plain REST JSON. */
const usesSoap = (provider: AdapterConfig["provider"]) => provider === "behpardakht";

export function AdapterSettings({ adapter }: { adapter: AdapterConfig }) {
  const router = useRouter();
  const tAdapter = useTranslations("adapter_settings");
  const tCommon = useTranslations("common");
  const [loading, setLoading] = useState(false);
  const [testResult, setTestResult] = useState<{ ok: boolean; message: string } | null>(null);
  const [credentials, setCredentials] = useState<string>(
    JSON.stringify(adapter.credentials ?? {}, null, 2)
  );

  const isWithdrawn = Boolean(adapter.withdrawn_by_operator);
  const isEnabled = adapter.enabled && !isWithdrawn;

  // What a merchant's client actually posts to: the engine's own base URL, which the
  // browser already knows (NEXT_PUBLIC_API_URL) but the server-only ENGINE_URL may differ.
  const endpoint = `${apiBase}${adapter.endpoint_path_prefix}`;

  // Health reads from the last request the engine served, so it only means something
  // while the adapter is actually offered.
  const health = isWithdrawn
    ? "disabled"
    : !isEnabled
      ? "idle"
      : adapter.status?.state === "degraded"
        ? "degraded"
        : "healthy";

  async function handleSaveCredentials() {
    setLoading(true);
    setTestResult(null);
    try {
      const parsed = JSON.parse(credentials);
      await patchAdapter(adapter.id, { credentials: parsed });
      setTestResult({ ok: true, message: tAdapter("credentials_saved") });
      router.refresh();
    } catch (err: unknown) {
      setTestResult({
        ok: false,
        message: err instanceof Error ? err.message : tAdapter("invalid_json"),
      });
    } finally {
      setLoading(false);
    }
  }

  async function handleTest() {
    setLoading(true);
    setTestResult(null);
    try {
      const res = await testAdapter(adapter.id);
      if (res.ok) {
        setTestResult({ ok: true, message: tAdapter("credentials_valid") });
      }
    } catch (err: unknown) {
      setTestResult({
        ok: false,
        message: err instanceof Error ? err.message : tAdapter("test_failed"),
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="gw" data-testid={`adapter-card-${adapter.provider}`}>
      {/* Provider label · health dot · protocol tag · the operator's own lock state */}
      <div className="gw__head flex-wrap">
        <span className="badge badge--failed mono" dir="ltr">
          .{adapter.provider}
        </span>
        <span
          className={`health health--${health}`}
          data-testid={`adapter-status-${adapter.provider}`}
        >
          <i className="health__dot" aria-hidden="true" />
          <span>
            {isWithdrawn
              ? tAdapter("withdrawn_badge")
              : isEnabled
                ? tCommon("enabled")
                : tCommon("disabled")}
          </span>
        </span>
        <span className="badge badge--refunded" data-testid={`adapter-protocol-${adapter.provider}`}>
          {tAdapter(usesSoap(adapter.provider) ? "version_soap" : "version_rest")}
        </span>
        {adapter.status && (
          <span
            className="small muted"
            title={`${tAdapter("tx_total")}: ${adapter.status.transactions_total} · ${tAdapter("settled")}: ${adapter.status.transactions_settled} · ${tAdapter("failed_deliveries")}: ${adapter.status.failed_deliveries}`}
          >
            {tAdapter(`state_${adapter.status.state}`)}
          </span>
        )}

        {/* 006-admin-ipg-visibility (FR-016, FR-017): Merchant cannot toggle availability. */}
        <span className="ms-auto">
          {isWithdrawn ? (
            <span
              className="badge badge--pending"
              data-testid={`adapter-withdrawn-badge-${adapter.provider}`}
            >
              <svg className="ic" viewBox="0 0 24 24" aria-hidden="true">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                <path d="M7 11V7a5 5 0 0 1 10 0v4" />
              </svg>
              <span>{tAdapter("withdrawn_badge")}</span>
            </span>
          ) : (
            <span
              className="small muted mono"
              title={tAdapter("not_editable")}
              data-testid={`adapter-locked-status-${adapter.provider}`}
            >
              {isEnabled ? tCommon("enabled") : tCommon("disabled")}
            </span>
          )}
        </span>
      </div>

      {isWithdrawn && (
        <div className="banner" data-testid={`adapter-withdrawn-notice-${adapter.provider}`}>
          <svg className="ic" viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="12" cy="12" r="10" />
            <path d="M12 8v4M12 16h.01" />
          </svg>
          <span>{tAdapter("withdrawn_by_operator")}</span>
        </div>
      )}

      {/* Endpoint snippet — the one line a merchant copies into their client config. */}
      <div className="term">
        <div className="term__bar">
          <span className="term__dots" aria-hidden="true">
            <i />
            <i />
            <i />
          </span>
          <span className="term__file">{tAdapter("endpoint_label")}</span>
          <CopyButton
            value={endpoint}
            label={tAdapter("copy_endpoint")}
            testId={`copy-endpoint-${adapter.provider}`}
          />
        </div>
        <div className="term__body">
          <pre dir="ltr" data-testid={`adapter-endpoint-${adapter.provider}`}>
            {endpoint}
          </pre>
        </div>
      </div>

      {testResult && (
        <div
          className={testResult.ok ? "banner" : "banner banner--danger"}
          role="status"
          data-testid={`test-result-${adapter.provider}`}
        >
          <svg className="ic" viewBox="0 0 24 24" aria-hidden="true">
            {testResult.ok ? (
              <path d="M20 6L9 17l-5-5" />
            ) : (
              <>
                <circle cx="12" cy="12" r="10" />
                <path d="M12 8v4M12 16h.01" />
              </>
            )}
          </svg>
          <span>{testResult.message}</span>
        </div>
      )}

      {adapter.credentials !== undefined && (
        <div className="field">
          {/* Credential keys are adapter-specific; name the two the real gateways use. */}
          {Object.keys(adapter.credentials).length > 0 && (
            <div className="chips">
              {Object.keys(adapter.credentials).map((key) => (
                <span key={key} className="badge badge--failed mono">
                  {key}
                </span>
              ))}
            </div>
          )}
          <label className="field__label" htmlFor={`credentials-input-${adapter.provider}`}>
            {tAdapter("credentials_json_label")}
          </label>
          <div className="term">
            <div className="term__bar">
              <span className="term__dots" aria-hidden="true">
                <i />
                <i />
                <i />
              </span>
            </div>
            <div className="term__body">
              <textarea
                id={`credentials-input-${adapter.provider}`}
                rows={4}
                value={credentials}
                onChange={(e) => setCredentials(e.target.value)}
                spellCheck={false}
                dir="ltr"
                data-testid={`credentials-input-${adapter.provider}`}
              />
            </div>
          </div>
          <div className="row-flex">
            <button
              onClick={handleSaveCredentials}
              disabled={loading}
              className="btn btn--primary btn--sm"
              data-testid={`save-credentials-btn-${adapter.provider}`}
            >
              {tAdapter("save_credentials")}
            </button>
            <button
              onClick={handleTest}
              disabled={loading}
              className="btn btn--secondary btn--sm"
              data-testid={`test-adapter-btn-${adapter.provider}`}
            >
              {loading ? tAdapter("testing") : tAdapter("test_credentials")}
            </button>
            <span className="small muted mono" dir="ltr">
              POST /adapters/{adapter.id}/test
            </span>
          </div>
        </div>
      )}

      <a
        href={`/docs/${adapter.provider}-api-reference.md`}
        className="btn btn--secondary btn--sm justify-self-start"
        data-testid={`adapter-docs-${adapter.provider}`}
      >
        <svg className="ic" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="7 10 12 15 17 10" />
          <line x1="12" y1="15" x2="12" y2="3" />
        </svg>
        <span>{tAdapter("docs_link")}</span>
      </a>
    </div>
  );
}
