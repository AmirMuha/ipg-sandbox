"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import {
  getTransaction,
  listDeliveries,
  patchTransaction,
  retryDelivery,
  Transaction,
  WebhookDelivery,
} from "@/lib/api";
import { formatDate, formatRial, formatToman } from "@/lib/format";
import { LifecycleStepper } from "./LifecycleStepper";
import { JsonTabs } from "./JsonTabs";
import { StatusBadge } from "./StatusBadge";
import { useToast } from "./Toast";

const STATUS_LABEL: Record<string, [string, string]> = {
  initiated: ["Initiated", "در حال ایجاد"],
  pending: ["Pending", "در انتظار"],
  settled: ["Settled", "تسویه‌شده"],
  approved: ["Approved", "تأییدشده"],
  refunded: ["Refunded", "مرجوع‌شده"],
  expired: ["Expired", "منقضی‌شده"],
  declined: ["Declined", "ناموفق"],
  failed: ["Failed", "خطا"],
};

/**
 * Slide-over transaction inspector, addressed by `?tx=<id>` so the row link and
 * the drawer share one URL: back/forward and reload all land on the same panel.
 */
export function TransactionDrawer({ locale = "fa" }: { locale?: string }) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const id = params.get("tx");
  const { showToast } = useToast();
  const fa = locale !== "en";

  const [tx, setTx] = useState<Transaction | null>(null);
  const [deliveries, setDeliveries] = useState<WebhookDelivery[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const close = useCallback(() => router.push(pathname), [router, pathname]);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    setTx(null);
    setError(null);
    (async () => {
      try {
        const [t, d] = await Promise.all([
          getTransaction(id),
          listDeliveries({ transaction_id: id, page_size: 50 }),
        ]);
        if (cancelled) return;
        setTx(t);
        setDeliveries(d.items);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "load failed");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [id]);

  useEffect(() => {
    if (!id) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [id, close]);

  if (!id) return null;

  async function replay() {
    const target = deliveries[deliveries.length - 1];
    if (!target) {
      showToast(fa ? "تحویلی برای ارسال مجدد وجود ندارد" : "No delivery to replay", "warning");
      return;
    }
    setBusy(true);
    try {
      await retryDelivery(target.id);
      showToast(fa ? "ارسال مجدد انجام شد" : "Callback replayed", "success");
    } catch (err) {
      showToast(err instanceof Error ? err.message : "replay failed", "danger");
    } finally {
      setBusy(false);
    }
  }

  async function refund() {
    if (!tx) return;
    setBusy(true);
    try {
      const next = await patchTransaction(tx.id, "refund");
      setTx(next);
      showToast(fa ? "مرجوعی شبیه‌سازی شد" : "Refund simulated", "success");
      router.refresh();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "refund failed", "danger");
    } finally {
      setBusy(false);
    }
  }

  const callback = deliveries.find((d) => d.stage === "callback") ?? deliveries[0];

  return (
    <div data-testid="tx-drawer">
      <button
        type="button"
        aria-label={fa ? "بستن" : "Close"}
        onClick={close}
        className="scrim"
        data-open="true"
        data-testid="tx-drawer-backdrop"
      />
      {/* .drawer anchors itself to the inline-end edge, which is the LEFT in this
          RTL-first app — matching `[dir="rtl"] .animate-drawer`, which slides in
          from -100%. The entrance animation lives in theme.css rather than in
          .drawer, because this panel mounts on demand (?tx=<id>) and a
          data-open transition would never fire. */}
      <aside className="drawer animate-drawer" role="dialog" aria-modal="true">
        <header className="drawer__head">
          <div className="min-w-0 flex-1">
            <div className="mono truncate" dir="ltr" data-testid="drawer-authority">
              {tx?.authority ?? id}
            </div>
            <div className="row-flex mt-2">
              <span className="badge badge--failed" dir="ltr" data-testid="drawer-gateway">
                {tx?.adapter_id ?? "…"}
              </span>
              <span className="mono" data-testid="drawer-amount">
                {tx ? `${formatRial(tx.amount_rial, locale)} ریال` : "…"}
                {tx && (
                  <span className="small muted ms-2">
                    {fa ? "تومان" : "Toman"}: {formatToman(tx.amount_rial, locale)}
                  </span>
                )}
              </span>
              {tx && (
                <StatusBadge status={tx.status} data-testid="drawer-status">
                  {STATUS_LABEL[tx.status]?.[fa ? 1 : 0] ?? tx.status}
                </StatusBadge>
              )}
            </div>
          </div>
          <button
            type="button"
            onClick={close}
            aria-label={fa ? "بستن" : "Close"}
            className="iconbtn"
            data-testid="tx-drawer-close"
          >
            ✕
          </button>
        </header>

        <div className="drawer__body">
          {error && (
            <p className="banner banner--danger" role="alert">
              {error}
            </p>
          )}

          {tx && (
            <>
              <LifecycleStepper
                status={tx.status}
                effectiveScenario={tx.effective_scenario}
                locale={locale}
              />

              <dl className="kv">
                <div className="kv__row">
                  <dt className="kv__label">{fa ? "زمان ایجاد" : "Created at"}</dt>
                  <dd className="kv__val mono" data-testid="drawer-created-at">
                    {formatDate(tx.created_at, locale)}
                  </dd>
                </div>
                <div className="kv__row">
                  <dt className="kv__label">{fa ? "شناسه اپلیکیشن" : "App reference"}</dt>
                  <dd className="kv__val mono truncate">{tx.app_reference || "—"}</dd>
                </div>
                <div className="kv__row">
                  <dt className="kv__label">{fa ? "توضیحات" : "Description"}</dt>
                  <dd className="kv__val">{tx.description || "—"}</dd>
                </div>
              </dl>

              <JsonTabs
                rawRequest={tx.raw_request ?? undefined}
                callbackPayload={callback?.payload}
                rawResponse={tx.raw_response ?? undefined}
                locale={locale}
              />
            </>
          )}
        </div>

        <footer className="modal__foot">
          <button
            type="button"
            onClick={replay}
            disabled={busy}
            className="btn btn--secondary btn--sm"
            data-testid="replay-callback"
          >
            {fa ? "ارسال مجدد کال‌بک" : "Replay Callback"}
          </button>
          <button
            type="button"
            onClick={refund}
            disabled={busy || !tx}
            className="btn btn--primary btn--sm"
            data-testid="simulate-refund"
          >
            {fa ? "شبیه‌سازی مرجوعی" : "Simulate Refund"}
          </button>
        </footer>
      </aside>
    </div>
  );
}