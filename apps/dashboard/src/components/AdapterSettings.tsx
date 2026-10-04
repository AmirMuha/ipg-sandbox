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
  // T073: per-adapter config/status is the FR-008 surface; it rendered in English under /fa/
  // because every string was hardcoded.
  const tAdapter = useTranslations("adapter_settings");
  const tCommon = useTranslations("common");
  const [loading, setLoading] = useState(false);
  const [testResult, setTestResult] = useState<{ ok: boolean; message: string } | null>(null);
  const [enabled, setEnabled] = useState(adapter.enabled);
  const [credentials, setCredentials] = useState<string>(
    JSON.stringify(adapter.credentials ?? {}, null, 2)
  );

  // What a merchant's client actually posts to: the engine's own base URL, which the
  // browser already knows (NEXT_PUBLIC_API_URL) but the server-only ENGINE_URL may differ.
  const endpoint = `${apiBase}${adapter.endpoint_path_prefix}`;

  async function handleToggle(newEnabled: boolean) {
    setLoading(true);
    try {
      await patchAdapter(adapter.id, { enabled: newEnabled });
      setEnabled(newEnabled);
      router.refresh();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : tAdapter("toggle_failed"));
    } finally {
      setLoading(false);
    }
  }

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
    <div
      className="panel bg-surface border border-border rounded-console p-5 space-y-4"
      data-testid={`adapter-card-${adapter.provider}`}
    >
      {/* Provider badge · status dot · protocol tag */}
      <div className="flex items-center justify-between gap-3 border-b border-border pb-3 flex-wrap">
        <div className="flex items-center gap-2.5 min-w-0 flex-wrap">
          <span
            className="gateway-badge inline-flex items-center gap-1.5 px-2 py-[3px] rounded-sm text-xs font-semibold bg-bg border border-border text-text whitespace-nowrap font-mono"
            dir="ltr"
          >
            .{adapter.provider}
          </span>
          <span className="flex items-center gap-1.5 text-xs" data-testid={`adapter-status-${adapter.provider}`}>
            <span
              className={`inline-block w-2 h-2 rounded-full ${
                enabled
                  ? adapter.status?.state === "degraded"
                    ? "bg-warning"
                    : "bg-success"
                  : "bg-border"
              }`}
              aria-hidden="true"
            />
            <span className={enabled ? "text-success-ink" : "text-muted"}>
              {enabled ? tCommon("enabled") : tCommon("disabled")}
            </span>
          </span>
          <span
            className="version-tag font-mono text-[11px] px-1.5 py-0.5 rounded bg-surface-subtle border border-border text-text whitespace-nowrap"
            data-testid={`adapter-protocol-${adapter.provider}`}
          >
            {tAdapter(usesSoap(adapter.provider) ? "version_soap" : "version_rest")}
          </span>
          {adapter.status && (
            <span
              className="text-[11px] text-muted"
              title={`${tAdapter("tx_total")}: ${adapter.status.transactions_total} · ${tAdapter("settled")}: ${adapter.status.transactions_settled} · ${tAdapter("failed_deliveries")}: ${adapter.status.failed_deliveries}`}
            >
              {tAdapter(`state_${adapter.status.state}`)}
            </span>
          )}
        </div>

        <label className="flex items-center gap-2 cursor-pointer text-xs shrink-0">
          <input
            type="checkbox"
            checked={enabled}
            disabled={loading}
            onChange={(e) => handleToggle(e.target.checked)}
            className="accent-accent"
            data-testid={`adapter-toggle-${adapter.provider}`}
          />
          <span>{enabled ? tCommon("enabled") : tCommon("disabled")}</span>
        </label>
      </div>

      {/* Endpoint snippet — the one line a merchant copies into their client config. */}
      <div className="bg-surface-2 border border-border rounded p-3" dir="ltr">
        <div className="flex items-center justify-between gap-2 mb-1.5">
          <span className="font-mono text-[11px] text-muted"># {tAdapter("endpoint_label")}</span>
          <CopyButton
            value={endpoint}
            label={tAdapter("copy_endpoint")}
            testId={`copy-endpoint-${adapter.provider}`}
          />
        </div>
        <code
          className="font-mono text-xs text-text block truncate"
          data-testid={`adapter-endpoint-${adapter.provider}`}
        >
          {endpoint}
        </code>
      </div>

      {/* Enable switch, spelled out as the control API call it maps to. */}
      <p className="text-[11px] text-muted font-mono" dir="ltr">
        PATCH /adapters/{adapter.id}
      </p>

      {testResult && (
        <div
          className={`p-3 rounded text-xs border ${
            testResult.ok
              ? "bg-success-bg text-success-ink border-success-border"
              : "bg-danger-bg text-danger-ink border-danger-border"
          }`}
          data-testid={`test-result-${adapter.provider}`}
        >
          {testResult.message}
        </div>
      )}

      {adapter.credentials !== undefined && (
        <div className="space-y-2">
          {/* Credential keys are adapter-specific; name the two the real gateways use. */}
          {Object.keys(adapter.credentials).length > 0 && (
            <div className="flex items-center gap-2 flex-wrap">
              {Object.keys(adapter.credentials).map((key) => (
                <span
                  key={key}
                  className="version-tag font-mono text-[11px] px-1.5 py-0.5 rounded bg-surface-subtle border border-border text-text whitespace-nowrap"
                >
                  {key}
                </span>
              ))}
            </div>
          )}
          <label className="block text-xs text-muted font-mono">
            {tAdapter("credentials_json_label")}
          </label>
          <textarea
            rows={4}
            value={credentials}
            onChange={(e) => setCredentials(e.target.value)}
            className="w-full bg-surface-2 border border-border rounded p-2.5 text-xs font-mono focus:outline-none focus:border-accent"
            dir="ltr"
            data-testid={`credentials-input-${adapter.provider}`}
          />
          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={handleSaveCredentials}
              disabled={loading}
              className="btn-secondary text-xs bg-surface border border-border text-text hover:bg-surface-subtle px-2.5 py-1 rounded-[6px] transition-colors duration-fast ease-standard disabled:opacity-50"
              data-testid={`save-credentials-btn-${adapter.provider}`}
            >
              {tAdapter("save_credentials")}
            </button>
            <button
              onClick={handleTest}
              disabled={loading}
              className="btn-secondary text-xs bg-surface border border-border text-text hover:bg-surface-subtle px-2.5 py-1 rounded-[6px] transition-colors duration-fast ease-standard disabled:opacity-50"
              data-testid={`test-adapter-btn-${adapter.provider}`}
            >
              {loading ? tAdapter("testing") : tAdapter("test_credentials")}
            </button>
            <span className="font-mono text-[11px] text-muted" dir="ltr">
              POST /adapters/{adapter.id}/test
            </span>
          </div>
        </div>
      )}

      <a
        href={`/docs/${adapter.provider}-api-reference.md`}
        className="inline-flex items-center gap-1.5 text-xs text-accent-ink hover:underline"
        data-testid={`adapter-docs-${adapter.provider}`}
      >
        <svg
          width="13"
          height="13"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="7 10 12 15 17 10" />
          <line x1="12" y1="15" x2="12" y2="3" />
        </svg>
        {tAdapter("docs_link")}
      </a>
    </div>
  );
}
