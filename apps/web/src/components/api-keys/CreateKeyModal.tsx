"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { ApiError, createApiKey } from "../../lib/api";
import { CopyButton } from "../CopyButton";

/**
 * Two steps in one panel: name the key, then read the secret. The engine returns the
 * plaintext token exactly once and stores only its hash, so closing this modal loses
 * it for good — that is why the reveal step cannot be dismissed by accident and why
 * the warning is a banner rather than a line of muted text.
 */
export function CreateKeyModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: () => void;
}) {
  const t = useTranslations("api_keys");
  const tc = useTranslations("common");
  const [name, setName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;

    setSubmitting(true);
    setError(null);
    try {
      const created = await createApiKey(name.trim());
      setToken(created.token);
      onCreated();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("create_failed"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      className="scrim grid place-items-center p-4 overflow-y-auto"
      data-open="true"
      role="dialog"
      aria-modal="true"
      aria-label={token ? t("created_title") : t("create")}
      data-testid="create-key-modal"
    >
      <div className="card animate-modal w-full max-w-lg my-auto">
        <div className="card__head">
          <h2 className="card__title">{token ? t("created_title") : t("create")}</h2>
        </div>

        {token ? (
          <div className="card__body stack-md">
            <div className="banner banner--danger" role="alert" data-testid="key-once-warning">
              {t("once_warning")}
            </div>

            <label className="field">
              <span className="field__label">{t("token_label")}</span>
              <div className="row-flex">
                <input
                  className="input mono flex-1 min-w-0"
                  dir="ltr"
                  readOnly
                  value={token}
                  data-testid="api-key-token"
                  onFocus={(e) => e.currentTarget.select()}
                />
                <CopyButton value={token} label={tc("copy")} testId="copy-api-key" />
              </div>
            </label>

            <div className="modal__foot">
              <button
                type="button"
                onClick={onClose}
                className="btn btn--primary"
                data-testid="api-key-done"
              >
                {t("done")}
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="card__body stack-md">
            {error && (
              <div className="banner banner--danger" role="alert" data-testid="create-key-error">
                {error}
              </div>
            )}

            <label className="field">
              <span className="field__label">{t("name_label")}</span>
              <input
                className="input"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder={t("name_placeholder")}
                required
                autoFocus
                data-testid="api-key-name-input"
              />
            </label>

            <div className="row-flex justify-between">
              <button
                type="button"
                onClick={onClose}
                className="btn btn--secondary"
                disabled={submitting}
              >
                {tc("cancel")}
              </button>
              <button
                type="submit"
                className="btn btn--primary"
                disabled={submitting || !name.trim()}
                data-testid="create-api-key-btn"
              >
                {submitting ? t("creating") : t("create")}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
