"use client";

import { useParams, useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { ApiError, deleteTransaction } from "../lib/api";

/**
 * US5: purge a test record. Destructive and irreversible, so it confirms first — and the
 * confirmation names what goes with it, since the engine cascades the delivery logs too.
 */
export function DeleteTransactionButton({ transactionId }: { transactionId: string }) {
  const router = useRouter();
  const params = useParams();
  const locale = (params?.locale as string) || "fa";
  const t = useTranslations("delete");
  const [confirming, setConfirming] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleDelete() {
    setDeleting(true);
    setError(null);
    try {
      await deleteTransaction(transactionId);
      router.push(`/${locale}/console`);
      router.refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err));
      setDeleting(false);
      setConfirming(false);
    }
  }

  if (!confirming) {
    return (
      <button
        type="button"
        onClick={() => setConfirming(true)}
        className="btn btn--danger"
        data-testid={`delete-tx-${transactionId}`}
      >
        {t("button")}
      </button>
    );
  }

  return (
    <div className="row-flex">
      <span className="small">{t("confirm")}</span>
      <button
        type="button"
        onClick={handleDelete}
        disabled={deleting}
        className="btn btn--danger"
        data-testid={`delete-tx-confirm-${transactionId}`}
      >
        {deleting ? t("deleting") : t("button")}
      </button>
      <button
        type="button"
        onClick={() => setConfirming(false)}
        disabled={deleting}
        className="iconbtn"
      >
        <span data-testid={`delete-tx-cancel-${transactionId}`}>×</span>
      </button>
      {error && <span className="field__err">{error}</span>}
    </div>
  );
}
