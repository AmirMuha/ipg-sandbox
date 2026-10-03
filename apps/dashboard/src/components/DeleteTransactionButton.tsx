"use client";

import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { ApiError, deleteTransaction } from "../lib/api";

/**
 * US5: purge a test record. Destructive and irreversible, so it confirms first — and the
 * confirmation names what goes with it, since the engine cascades the delivery logs too.
 */
export function DeleteTransactionButton({ transactionId }: { transactionId: string }) {
  const router = useRouter();
  const t = useTranslations("delete");
  const [confirming, setConfirming] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleDelete() {
    setDeleting(true);
    setError(null);
    try {
      await deleteTransaction(transactionId);
      router.push(".."); // detail page: the record it described is gone
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
        className="px-3 py-1.5 rounded-[6px] text-[13px] font-medium bg-danger-bg text-danger-ink border border-danger-border hover:bg-danger/10 transition-colors"
        data-testid={`delete-tx-${transactionId}`}
      >
        {t("button")}
      </button>
    );
  }

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <span className="text-xs text-danger-ink">{t("confirm")}</span>
      <button
        type="button"
        onClick={handleDelete}
        disabled={deleting}
        className="px-3 py-1.5 rounded-[6px] text-[13px] font-semibold bg-danger text-white hover:bg-danger/90 transition-colors disabled:opacity-50"
        data-testid={`delete-tx-confirm-${transactionId}`}
      >
        {deleting ? t("deleting") : t("button")}
      </button>
      <button
        type="button"
        onClick={() => setConfirming(false)}
        disabled={deleting}
        className="px-3 py-1.5 rounded-[6px] text-[13px] text-muted hover:text-text transition-colors"
      >
        <span data-testid={`delete-tx-cancel-${transactionId}`}>×</span>
      </button>
      {error && <span className="text-xs text-danger-ink">{error}</span>}
    </div>
  );
}
