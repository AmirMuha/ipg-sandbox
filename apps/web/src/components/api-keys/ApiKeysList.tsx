"use client";

import { useCallback, useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { ApiError, ApiKey, listApiKeys, revokeApiKey } from "../../lib/api";
import { CreateKeyModal } from "./CreateKeyModal";

const MAX_ACTIVE_KEYS = 10;

export function ApiKeysList() {
  const t = useTranslations("api_keys");
  const tc = useTranslations("common");
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [revokingId, setRevokingId] = useState<string | null>(null);
  const [confirmId, setConfirmId] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setKeys(await listApiKeys());
      setError(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("load_failed"));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleRevoke(id: string) {
    setRevokingId(id);
    setError(null);
    try {
      await revokeApiKey(id);
      setConfirmId(null);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("revoke_failed"));
    } finally {
      setRevokingId(null);
    }
  }

  const atLimit = keys.length >= MAX_ACTIVE_KEYS;

  return (
    <>
      <div className="card">
        <div className="card__head">
          <h2 className="card__title">{t("title")}</h2>
          <button
            type="button"
            onClick={() => setCreating(true)}
            className="btn btn--primary btn--sm"
            disabled={atLimit}
            data-testid="show-create-key-modal"
          >
            {t("create")}
          </button>
        </div>

        <div className="card__body stack-md">
          {error && (
            <div className="banner banner--danger" role="alert" data-testid="api-keys-error">
              {error}
            </div>
          )}

          {atLimit && <div className="banner">{t("limit_reached", { max: MAX_ACTIVE_KEYS })}</div>}

          <div className="tablewrap">
            <table className="table" data-testid="api-keys-table">
              <caption className="sr-only">{t("title")}</caption>
              <thead>
                <tr>
                  <th scope="col">{t("col_name")}</th>
                  <th scope="col">{t("col_token")}</th>
                  <th scope="col">{t("col_created")}</th>
                  <th scope="col">{t("col_last_used")}</th>
                  <th scope="col">
                    <span className="sr-only">{t("col_actions")}</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={5}>{t("loading")}</td>
                  </tr>
                ) : keys.length === 0 ? (
                  <tr>
                    <td colSpan={5}>
                      <div className="empty">
                        <p>{t("empty")}</p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  keys.map((key) => (
                    <tr key={key.id} data-testid={`api-key-row-${key.id}`}>
                      <td>{key.name}</td>
                      <td>
                        <span className="t-id" dir="ltr">
                          ••••{key.last_four}
                        </span>
                      </td>
                      <td>
                        <span className="t-time">{formatDate(key.created_at)}</span>
                      </td>
                      <td>
                        <span className="t-time">
                          {key.last_used_at ? formatDate(key.last_used_at) : t("never")}
                        </span>
                      </td>
                      <td>
                        {confirmId === key.id ? (
                          // Revoking is irreversible, so it asks once, inline — the same
                          // two-step DeleteTransactionButton uses rather than a native
                          // confirm(), which cannot be styled or translated.
                          <div className="row-flex">
                            <span className="small">{t("revoke_confirm")}</span>
                            <button
                              type="button"
                              onClick={() => handleRevoke(key.id)}
                              disabled={revokingId === key.id}
                              className="btn btn--danger btn--sm"
                              data-testid={`revoke-key-confirm-${key.id}`}
                            >
                              {revokingId === key.id ? t("revoking") : t("revoke")}
                            </button>
                            <button
                              type="button"
                              onClick={() => setConfirmId(null)}
                              disabled={revokingId === key.id}
                              className="iconbtn"
                              aria-label={tc("cancel")}
                            >
                              ×
                            </button>
                          </div>
                        ) : (
                          <button
                            type="button"
                            onClick={() => setConfirmId(key.id)}
                            className="btn btn--danger btn--sm"
                            data-testid={`revoke-key-${key.id}`}
                          >
                            {t("revoke")}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {creating && (
        <CreateKeyModal onClose={() => setCreating(false)} onCreated={() => void load()} />
      )}
    </>
  );
}

function formatDate(iso: string): string {
  return new Date(iso).toISOString().slice(0, 16).replace("T", " ");
}
