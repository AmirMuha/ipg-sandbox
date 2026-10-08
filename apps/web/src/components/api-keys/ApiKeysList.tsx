"use client";

import { useEffect, useState } from "react";
import { ApiKey, listApiKeys, revokeApiKey } from "../../lib/api";
import { CreateKeyModal } from "./CreateKeyModal";
import { useToast } from "../Toast";

export function ApiKeysList() {
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const { showToast } = useToast();

  const fetchKeys = async () => {
    try {
      const data = await listApiKeys();
      setKeys(data);
    } catch (err) {
      showToast("Failed to load API keys", "danger");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/exhaustive-deps
    void fetchKeys();
  }, []);

  const handleRevoke = async (id: string, name: string) => {
    if (!confirm(`Are you sure you want to revoke the key "${name}"? This action cannot be undone.`)) {
      return;
    }
    
    try {
      await revokeApiKey(id);
      showToast(`Key "${name}" revoked successfully`, "success");
      fetchKeys();
    } catch (err: any) {
      showToast(err.message || "Failed to revoke key", "danger");
    }
  };

  return (
    <div className="card card__body stack-md" data-testid="api-keys-list">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h2 className="text-xl font-semibold">API Keys</h2>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
            Manage API keys for programmatic access to your sandbox.
          </p>
        </div>
        <button 
          onClick={() => setShowModal(true)} 
          className="btn btn--primary"
          data-testid="show-create-key-modal"
          disabled={keys.length >= 10}
        >
          Create New Key
        </button>
      </div>

      {keys.length >= 10 && (
        <div className="banner banner--warning" role="alert">
          You have reached the maximum limit of 10 active API keys.
        </div>
      )}

      {loading ? (
        <div className="py-8 text-center text-slate-500">Loading API keys...</div>
      ) : keys.length === 0 ? (
        <div className="py-8 text-center border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-lg">
          <p className="text-slate-500 dark:text-slate-400">You don&apos;t have any active API keys.</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-800 text-sm text-slate-500">
                <th className="pb-2 font-medium">Name</th>
                <th className="pb-2 font-medium">Token</th>
                <th className="pb-2 font-medium">Created</th>
                <th className="pb-2 font-medium">Last Used</th>
                <th className="pb-2 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {keys.map((k) => (
                <tr key={k.id} className="border-b border-slate-100 dark:border-slate-800/50 last:border-0" data-testid={`api-key-row-${k.id}`}>
                  <td className="py-3 font-medium">{k.name}</td>
                  <td className="py-3 font-mono text-sm">...{k.last_four}</td>
                  <td className="py-3 text-sm text-slate-500">
                    {new Date(k.created_at).toLocaleDateString()}
                  </td>
                  <td className="py-3 text-sm text-slate-500">
                    {k.last_used_at ? new Date(k.last_used_at).toLocaleDateString() : "Never"}
                  </td>
                  <td className="py-3 text-right">
                    <button
                      onClick={() => handleRevoke(k.id, k.name)}
                      className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 text-sm font-medium"
                      data-testid={`revoke-key-${k.id}`}
                    >
                      Revoke
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showModal && (
        <CreateKeyModal 
          onClose={() => setShowModal(false)} 
          onCreated={() => fetchKeys()} 
        />
      )}
    </div>
  );
}
