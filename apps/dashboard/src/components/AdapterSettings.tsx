"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { AdapterConfig, patchAdapter, testAdapter } from "../lib/api";

export function AdapterSettings({ adapter }: { adapter: AdapterConfig }) {
  const router = useRouter();
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
      alert(err instanceof Error ? err.message : "Failed to update adapter status");
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
      setTestResult({ ok: true, message: "Credentials saved." });
      router.refresh();
    } catch (err: unknown) {
      setTestResult({
        ok: false,
        message: err instanceof Error ? err.message : "Invalid JSON",
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
        message: err instanceof Error ? err.message : "Adapter credentials check failed",
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
            <span>{enabled ? "Enabled" : "Disabled"}</span>
          </label>
          <button
            onClick={handleTest}
            disabled={loading}
            className="text-xs bg-surface-2 border border-border hover:border-accent px-3 py-1 rounded transition-colors disabled:opacity-50"
            data-testid={`test-adapter-btn-${adapter.provider}`}
          >
            {loading ? "Testing..." : "Test Credentials"}
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
            Test Credentials (JSON)
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
            Save Credentials
          </button>
        </div>
      )}
    </div>
  );
}
