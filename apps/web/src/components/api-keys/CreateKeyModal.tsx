"use client";

import { useState } from "react";
import { createApiKey } from "../../lib/api";
import { CopyButton } from "../CopyButton";

interface CreateKeyModalProps {
  onClose: () => void;
  onCreated: () => void;
}

export function CreateKeyModal({ onClose, onCreated }: CreateKeyModalProps) {
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [createdKey, setCreatedKey] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const result = await createApiKey(name.trim());
      setCreatedKey(result.token);
      onCreated();
    } catch (err: any) {
      setError(err.message || "Failed to create API key");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="modal-backdrop fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="card card__body stack-md w-full max-w-md bg-white dark:bg-slate-900 shadow-xl">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">
            {createdKey ? "API Key Created" : "Create New API Key"}
          </h2>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-700 dark:hover:text-slate-300">
            ✕
          </button>
        </div>

        {createdKey ? (
          <div className="stack-md">
            <div className="banner banner--warning" role="alert">
              Please copy this key now. You will not be able to see it again!
            </div>
            <div className="flex items-center gap-2 p-3 bg-slate-100 dark:bg-slate-800 rounded-md break-all font-mono text-sm">
              <span className="flex-1">{createdKey}</span>
              <CopyButton value={createdKey} label="Copy" />
            </div>
            <div className="flex justify-end mt-4">
              <button onClick={onClose} className="btn btn--primary">
                Done
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="stack-md">
            {error && (
              <div className="banner banner--danger" role="alert">
                {error}
              </div>
            )}
            <div className="field">
              <label htmlFor="key-name" className="field__label">
                Key Name
              </label>
              <input
                id="key-name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Production App"
                className="input"
                required
                autoFocus
                data-testid="api-key-name-input"
              />
            </div>
            <div className="flex justify-end gap-3 mt-4">
              <button type="button" onClick={onClose} className="btn btn--secondary" disabled={loading}>
                Cancel
              </button>
              <button type="submit" className="btn btn--primary" disabled={loading || !name.trim()} data-testid="create-api-key-btn">
                {loading ? "Creating..." : "Create Key"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
