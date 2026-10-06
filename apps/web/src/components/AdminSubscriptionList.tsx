"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";
import { AdminSubscription, deactivateAdminSubscription } from "../lib/api";

const STATUS_LABEL: Record<string, string> = {
  active: "status_active",
  pending: "status_pending",
  expired: "status_expired",
  cancelled: "status_cancelled",
};

export function AdminSubscriptionList({
  initialSubscriptions,
}: {
  initialSubscriptions: AdminSubscription[];
}) {
  const t = useTranslations("admin_subscriptions");
  const [rows, setRows] = useState<AdminSubscription[]>(initialSubscriptions);
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ ok: boolean; message: string } | null>(null);

  async function handleDeactivate(sub: AdminSubscription) {
    setLoadingId(sub.subscription_id);
    setFeedback(null);
    try {
      await deactivateAdminSubscription(sub.subscription_id);
      setRows((prev) =>
        prev.map((r) =>
          r.subscription_id === sub.subscription_id ? { ...r, status: "cancelled" } : r
        )
      );
      setFeedback({ ok: true, message: t("deactivated") });
    } catch (err: unknown) {
      setFeedback({
        ok: false,
        message: err instanceof Error ? err.message : t("deactivate_failed"),
      });
    } finally {
      setLoadingId(null);
    }
  }

  return (
    <div className="space-y-4" data-testid="admin-subscription-list">
      <div>
        <h3 className="text-sm font-semibold text-text">{t("title")}</h3>
        <p className="text-xs text-muted mt-1">{t("subtitle")}</p>
      </div>

      {feedback && (
        <div
          role="status"
          className={`p-3.5 rounded-md border text-xs font-medium ${
            feedback.ok
              ? "bg-success-bg border-success-border text-success-ink"
              : "bg-danger-bg border-danger-border text-danger-ink"
          }`}
          data-testid="admin-subscriptions-feedback"
        >
          {feedback.message}
        </div>
      )}

      {rows.length === 0 ? (
        <p className="text-xs text-muted" data-testid="admin-subscriptions-empty">
          {t("empty")}
        </p>
      ) : (
        <div className="grid grid-cols-1 gap-3">
          {rows.map((sub) => {
            const isLoading = loadingId === sub.subscription_id;
            return (
              <div
                key={sub.subscription_id}
                className="panel bg-surface border border-border rounded-console p-4 flex items-center justify-between gap-4 flex-wrap"
                data-testid={`admin-subscription-card-${sub.subscription_id}`}
              >
                <div className="min-w-0">
                  <h4 className="text-sm font-semibold text-text">
                    {sub.project_name ?? sub.project_id}
                  </h4>
                  <p className="text-[11px] text-muted font-mono" dir="ltr">
                    {sub.buyer_email ?? "—"}
                  </p>
                </div>

                <div className="flex items-center gap-3 flex-wrap text-xs">
                  <span
                    className={`px-2 py-0.5 rounded-full border font-semibold ${
                      sub.status === "active"
                        ? "bg-success/15 text-success-ink border-success-border"
                        : "bg-surface-subtle text-muted border-border"
                    }`}
                    data-testid={`admin-subscription-status-${sub.subscription_id}`}
                  >
                    {t(STATUS_LABEL[sub.status] ?? "status_pending")}
                  </span>
                  <span className="text-muted font-mono" dir="ltr">
                    {sub.amount_toman.toLocaleString("fa-IR")} {t("amount_unit")}
                  </span>
                  {sub.expires_at && (
                    <span className="text-muted font-mono" dir="ltr">
                      {t("expires")} {sub.expires_at.slice(0, 10)}
                    </span>
                  )}

                  {sub.status === "active" && (
                    <button
                      type="button"
                      onClick={() => handleDeactivate(sub)}
                      disabled={isLoading}
                      className="min-h-9 px-3 rounded-md border border-danger-border bg-danger-bg text-danger-ink text-xs font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
                      data-testid={`admin-deactivate-btn-${sub.subscription_id}`}
                    >
                      {isLoading ? t("deactivating") : t("deactivate")}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
