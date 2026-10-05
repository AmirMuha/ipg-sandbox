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
import { formatDate, formatRial, formatToman, getStatusColor } from "@/lib/format";
import { LifecycleStepper } from "./LifecycleStepper";
import { JsonTabs } from "./JsonTabs";
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
    <div className="fixed inset-0 z-50 flex justify-end" data-testid="tx-drawer">
      <button
        type="button"
        aria-label={fa ? "بستن" : "Close"}
        onClick={close}
        className="absolute inset-0 bg-overlay backdrop-blur-sm"
        data-testid="tx-drawer-backdrop"
      />
      <aside
        className="relative bg-surface border-s border-border shadow-raised animate-drawer w-full max-w-[560px] h-full flex flex-col"
        role="dialog"
        aria-modal="true"
      >
        <header className="flex items-start gap-3 p-5 border-b border-border">
          <div className="min-w-0 flex-1">
            <div className="font-mono text-sm text-text truncate" dir="ltr" data-testid="drawer-authority">
              {tx?.authority ?? id}
            </div>
            <div className="flex items-center gap-2 mt-2 flex-wrap">
              <span className="gateway-badge inline-flex items-center px-2 py-[3px] rounded-sm text-xs font-medium bg-bg border border-border text-text" dir="ltr" data-testid="drawer-gateway">
                {tx?.adapter_id ?? "…"}
              </span>
              <span className="font-mono text-sm font-semibold text-text tabular-nums" data-testid="drawer-amount">
                {tx ? `${formatRial(tx.amount_rial, locale)} ریال` : "…"}
                {tx && (
                  <span className="ms-2 text-xs font-normal text-muted">
                    {fa ? "تومان" : "Toman"}: {formatToman(tx.amount_rial, locale)}
                  </span>
                )}
              </span>
              {tx && (
                <span
                  className={`status-badge inline-flex items-center px-2 py-[3px] rounded-sm text-xs font-medium border ${getStatusColor(tx.status)}`}
                  data-testid="drawer-status"
                >
                  {STATUS_LABEL[tx.status]?.[fa ? 1 : 0] ?? tx.status}
                </span>
              )}
            </div>
          </div>
          <button
            type="button"
            onClick={close}
            aria-label={fa ? "بستن" : "Close"}
            className="text-muted hover:text-text text-lg leading-none px-1"
            data-testid="tx-drawer-close"
          >
            ✕
          </button>
        </header>

        <div className="flex-1 overflow-y-auto p-5 flex flex-col gap-6">
          {error && (
            <p className="p-3 bg-danger-bg border border-danger-border text-danger-ink rounded-md text-xs">
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

              <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-xs">
                <dt className="text-muted">{fa ? "زمان ایجاد" : "Created at"}</dt>
                <dd className="text-text font-mono" data-testid="drawer-created-at">
                  {formatDate(tx.created_at, locale)}
                </dd>
                <dt className="text-muted">{fa ? "شناسه اپلیکیشن" : "App reference"}</dt>
                <dd className="text-text font-mono truncate" dir="ltr">
                  {tx.app_reference || "—"}
                </dd>
                <dt className="text-muted">{fa ? "توضیحات" : "Description"}</dt>
                <dd className="text-text">{tx.description || "—"}</dd>
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

        <footer className="flex items-center gap-2 p-5 border-t border-border">
          <button
            type="button"
            onClick={replay}
            disabled={busy}
            className="px-3 py-1.5 rounded-[6px] text-xs font-medium bg-surface-2 border border-border text-text hover:bg-surface-elevated transition-colors disabled:opacity-50"
            data-testid="replay-callback"
          >
            {fa ? "ارسال مجدد کال‌بک" : "Replay Callback"}
          </button>
          <button
            type="button"
            onClick={refund}
            disabled={busy || !tx}
            className="px-3 py-1.5 rounded-[6px] text-xs font-medium bg-accent text-accent-on hover:bg-accent/92 transition-colors disabled:opacity-50"
            data-testid="simulate-refund"
          >
            {fa ? "شبیه‌سازی مرجوعی" : "Simulate Refund"}
          </button>
        </footer>
      </aside>
    </div>
  );
}