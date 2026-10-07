"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";
import { AdminSubscription, deactivateAdminSubscription } from "../lib/api";
import { StatusBadge } from "./StatusBadge";

const STATUS_LABEL: Record<string, string> = {
  active: "status_active",
  pending: "status_pending",
  expired: "status_expired",
  cancelled: "status_cancelled",
};

/** Subscription status shares the badge vocabulary but not its names. */
const STATUS_BADGE: Record<string, string> = {
  active: "settled",
  pending: "pending",
  expired: "expired",
  cancelled: "failed",
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
    <div className="card" data-testid="admin-subscription-list">
      <div className="card__head">
        <h2 className="card__title">{t("title")}</h2>
      </div>
      <div className="card__body stack-md">
        <p className="small muted">{t("subtitle")}</p>

        {feedback && (
          <div
            role="status"
            className={feedback.ok ? "banner" : "banner banner--danger"}
            data-testid="admin-subscriptions-feedback"
          >
            <svg className="ic" viewBox="0 0 24 24" aria-hidden="true">
              {feedback.ok ? (
                <path d="M20 6L9 17l-5-5" />
              ) : (
                <>
                  <circle cx="12" cy="12" r="10" />
                  <path d="M12 8v4M12 16h.01" />
                </>
              )}
            </svg>
            <span>{feedback.message}</span>
          </div>
        )}

        {rows.length === 0 ? (
          <div className="empty" data-testid="admin-subscriptions-empty">
            <p>{t("empty")}</p>
          </div>
        ) : (
          <div className="kv">
            {rows.map((sub) => {
              const isLoading = loadingId === sub.subscription_id;
              return (
                <div
                  className="kv__row"
                  key={sub.subscription_id}
                  data-testid={`admin-subscription-card-${sub.subscription_id}`}
                >
                  <span className="kv__label">
                    {sub.project_name ?? sub.project_id}
                    <small className="mono ltr" dir="ltr">
                      {sub.buyer_email ?? "—"}
                    </small>
                  </span>

                  <span className="kv__val row-flex justify-end">
                    <StatusBadge
                      status={STATUS_BADGE[sub.status] ?? "failed"}
                      data-testid={`admin-subscription-status-${sub.subscription_id}`}
                    >
                      {t(STATUS_LABEL[sub.status] ?? "status_pending")}
                    </StatusBadge>
                    <span className="small muted mono" dir="ltr">
                      {sub.amount_toman.toLocaleString("fa-IR")} {t("amount_unit")}
                    </span>
                    {sub.expires_at && (
                      <span className="small muted mono" dir="ltr">
                        {t("expires")} {sub.expires_at.slice(0, 10)}
                      </span>
                    )}

                    {sub.status === "active" && (
                      <button
                        type="button"
                        onClick={() => handleDeactivate(sub)}
                        disabled={isLoading}
                        className="btn btn--danger btn--sm"
                        data-testid={`admin-deactivate-btn-${sub.subscription_id}`}
                      >
                        {isLoading ? t("deactivating") : t("deactivate")}
                      </button>
                    )}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
