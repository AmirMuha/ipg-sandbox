"use client";

import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { AdapterConfig, patchAdapter, testAdapter } from "../lib/api";

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
        setTestResult({ ok: true, message: "Credentials valid! Adapter responded successfully." });
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
      className="bg-surface border border-border rounded-lg p-5 space-y-4"
      data-testid={`adapter-card-${adapter.provider}`}
    >
      <div className="flex items-center justify-between border-b border-border pb-3">
        <div>
          <h3 className="font-semibold text-base capitalize">{adapter.provider}</h3>
          <p className="text-xs text-muted font-mono">
            {adapter.endpoint_path_prefix} &bull; {adapter.api_unit}
          </p>
          {/* T075: the status half of FR-008's "per-adapter configuration and status". */}
          {adapter.status && (
            <p
              className="text-xs mt-1"
              data-testid={`adapter-status-${adapter.provider}`}
              title={`${tAdapter("tx_total")}: ${adapter.status.transactions_total} · ${tAdapter("settled")}: ${adapter.status.transactions_settled} · ${tAdapter("failed_deliveries")}: ${adapter.status.failed_deliveries}`}
            >
              <span
                className={`inline-block w-2 h-2 rounded-full mr-1 ${
                  adapter.status.state === "healthy"
                    ? "bg-green-500"
                    : adapter.status.state === "degraded"
                      ? "bg-amber-500"
                      : adapter.status.state === "disabled"
                        ? "bg-gray-400"
                        : "bg-blue-400"
                }`}
              />
              {tAdapter(`state_${adapter.status.state}`)}
              {adapter.status.last_activity_at && (
                <span className="text-muted">
                  {" · "}
                  {tAdapter("last_activity")}: {adapter.status.last_activity_at.slice(0, 10)}
                </span>
              )}
            </p>
          )}
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 cursor-pointer text-xs">
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
          <button
            onClick={handleTest}
            disabled={loading}
            className="text-xs bg-surface-2 border border-border hover:border-accent px-3 py-1 rounded transition-colors disabled:opacity-50"
            data-testid={`test-adapter-btn-${adapter.provider}`}
          >
            {loading ? tAdapter("testing") : tAdapter("test_credentials")}
          </button>
        </div>
      </div>

      {testResult && (
        <div
          className={`p-3 rounded text-xs border ${
            testResult.ok
              ? "bg-success/10 text-success border-success/30"
              : "bg-danger/10 text-danger border-danger/30"
          }`}
          data-testid={`test-result-${adapter.provider}`}
        >
          {testResult.message}
        </div>
      )}

      {adapter.credentials !== undefined && (
        <div className="space-y-2">
          <label className="block text-xs text-muted font-mono">
            {tAdapter("credentials_json_label")}
          </label>
          <textarea
            rows={4}
            value={credentials}
            onChange={(e) => setCredentials(e.target.value)}
            className="w-full bg-surface-2 border border-border rounded p-2.5 text-xs font-mono focus:outline-none focus:border-accent"
            data-testid={`credentials-input-${adapter.provider}`}
          />
          <button
            onClick={handleSaveCredentials}
            disabled={loading}
            className="text-xs bg-surface-2 border border-border hover:border-accent px-3 py-1 rounded transition-colors disabled:opacity-50"
          >
            {tAdapter("save_credentials")}
          </button>
        </div>
      )}
    </div>
  );
}
