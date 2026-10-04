import Link from "next/link";
import { notFound } from "next/navigation";
import { getTranslations, setRequestLocale } from "next-intl/server";
import {
  AdapterConfig,
  getAdapters,
  getTransaction,
  listDeliveries,
  Transaction,
  WebhookDelivery,
} from "../../../../../lib/api";
import { formatDate, formatRial, getStatusColor } from "../../../../../lib/format";
import { ScenarioControls } from "../../../../../components/ScenarioControls";
import { DeleteTransactionButton } from "../../../../../components/DeleteTransactionButton";

// The transaction, its deliveries, and its adapter are all read live per request.
export const dynamic = "force-dynamic";

export default async function TransactionDetailPage({
  params: { locale, id },
}: {
  params: { locale: string; id: string };
}) {
  setRequestLocale(locale);
  const t = await getTranslations("transactions");
  const tStatus = await getTranslations("status");
  const tCheckout = await getTranslations("checkout");

  let tx: Transaction | null = null;
  let deliveries: WebhookDelivery[] = [];
  let adapters: AdapterConfig[] = [];

  try {
    const [txRes, delRes, adpRes] = await Promise.all([
      getTransaction(id),
      listDeliveries({ transaction_id: id }),
      getAdapters(),
    ]);
    tx = txRes;
    deliveries = delRes.items;
    adapters = adpRes;
  } catch {
    notFound();
  }

  const adapter = adapters.find((a) => a.id === tx.adapter_id);
  const providerName = adapter ? adapter.provider : tx.adapter_id;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link
          href={`/${locale}/transactions`}
          className="text-xs text-muted hover:text-text border border-border px-3 py-1.5 rounded transition-colors"
        >
          &larr; Back
        </Link>
        <div>
          <h1 className="font-display text-xl font-semibold tracking-tight flex items-center gap-3">
            <span>{t("details_title")}</span>
            <span className="font-mono text-sm text-muted font-normal" dir="ltr">{tx.id}</span>
          </h1>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-surface border border-border p-4 rounded-lg shadow-raised">
          <div className="text-xs text-muted mb-1">{t("status")}</div>
          <div className="text-sm font-semibold">
            <span
              className={`inline-block px-2.5 py-0.5 rounded text-xs border font-medium ${getStatusColor(
                tx.status
              )}`}
            >
              {tStatus.has(tx.status) ? tStatus(tx.status) : tx.status}
            </span>
          </div>
        </div>

        <div className="bg-surface border border-border p-4 rounded-lg shadow-raised">
          <div className="text-xs text-muted mb-1">{t("amount")}</div>
          <div className="text-base font-mono font-semibold">
            {formatRial(tx.amount_rial, locale)} {tx.currency}
          </div>
        </div>

        <div className="bg-surface border border-border p-4 rounded-lg shadow-raised">
          <div className="text-xs text-muted mb-1">{t("adapter")}</div>
          <div className="text-sm font-mono font-semibold">{providerName}</div>
        </div>

        <div className="bg-surface border border-border p-4 rounded-lg shadow-raised">
          <div className="text-xs text-muted mb-1">{t("authority")}</div>
          <div className="text-xs font-mono truncate" dir="ltr">{tx.authority}</div>
        </div>
      </div>

      <div className="flex items-center gap-3 flex-wrap">
        {/* Only meaningful while the buyer still has something to pay — a settled link is a
            dead link, and the hosted page rejects it anyway. */}
        {(tx.status === "initiated" || tx.status === "pending") && tx.checkout_url && (
          <a
            href={tx.checkout_url}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-primary inline-flex items-center gap-2 px-4 py-2 rounded-[6px] bg-accent text-white text-sm font-medium hover:opacity-90 transition-opacity"
            data-testid="checkout-link"
          >
            {tCheckout("open")}
          </a>
        )}
        <DeleteTransactionButton transactionId={tx.id} />
      </div>
      {(tx.status === "initiated" || tx.status === "pending") && tx.checkout_url && (
        <p className="text-xs text-muted -mt-3">{tCheckout("hint")}</p>
      )}

      <ScenarioControls transaction={tx} />

      <div className="bg-surface border border-border rounded-lg p-5 space-y-4 shadow-raised">
        <h2 className="text-base font-semibold">Webhook Deliveries ({deliveries.length})</h2>
        {deliveries.length === 0 ? (
          <p className="text-sm text-muted">No webhook deliveries recorded for this transaction.</p>
        ) : (
          <div className="space-y-3">
            {deliveries.map((del) => (
              <div
                key={del.id}
                className="bg-surface-2 border border-border p-3 rounded text-xs font-mono flex items-center justify-between"
                dir="ltr"
              >
                <div>
                  <span className="font-bold uppercase text-[10px] me-2 px-1.5 py-0.5 rounded bg-surface">
                    {del.stage}
                  </span>
                  <span dir="ltr">{del.target_url}</span>
                  <span className="ms-2 text-muted" dir="ltr">Attempt #{del.attempt}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                      del.result === "delivered" ? "text-success-ink" : "text-danger-ink"
                    }`}
                  >
                    {del.result}
                  </span>
                  {del.response_status && (
                    <span className="text-muted" dir="ltr">HTTP {del.response_status}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-surface border border-border rounded-lg p-4 space-y-2 shadow-raised">
          <h3 className="font-semibold text-sm">{t("raw_request")}</h3>
          <pre
            className="p-3 bg-surface-2 border border-border rounded text-xs font-mono overflow-auto max-h-[350px]"
            dir="ltr"
            data-testid="raw-request"
          >
            {JSON.stringify(tx.raw_request ?? {}, null, 2)}
          </pre>
        </div>

        <div className="bg-surface border border-border rounded-lg p-4 space-y-2 shadow-raised">
          <h3 className="font-semibold text-sm">{t("raw_response")}</h3>
          <pre
            className="p-3 bg-surface-2 border border-border rounded text-xs font-mono overflow-auto max-h-[350px]"
            dir="ltr"
            data-testid="raw-response"
          >
            {JSON.stringify(tx.raw_response ?? {}, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
}
