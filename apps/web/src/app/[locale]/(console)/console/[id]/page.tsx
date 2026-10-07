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
import { formatRial } from "../../../../../lib/format";
import { StatusBadge } from "../../../../../components/StatusBadge";
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
    <div className="stack-lg">
      <div className="phead">
        <div className="phead__text">
          <h1 className="flex items-center gap-3">
            <span>{t("details_title")}</span>
            <span className="mono muted small" dir="ltr">
              {tx.id}
            </span>
          </h1>
        </div>
        <div className="phead__actions">
          <Link href={`/${locale}/console`} className="btn btn--secondary btn--sm">
            &larr; Back
          </Link>
        </div>
      </div>

      <div className="stats">
        <div className="stat">
          <div className="stat__cap">{t("status")}</div>
          <div>
            <StatusBadge status={tx.status}>
              {tStatus.has(tx.status) ? tStatus(tx.status) : tx.status}
            </StatusBadge>
          </div>
        </div>

        <div className="stat">
          <div className="stat__cap">{t("amount")}</div>
          <div className="stat__num num">
            {formatRial(tx.amount_rial, locale)}{" "}
            <span className="small muted">{tx.currency}</span>
          </div>
        </div>

        <div className="stat">
          <div className="stat__cap">{t("adapter")}</div>
          <div className="mono">{providerName}</div>
        </div>

        <div className="stat">
          <div className="stat__cap">{t("authority")}</div>
          <div className="mono small truncate" dir="ltr">
            {tx.authority}
          </div>
        </div>
      </div>

      <div className="row-flex">
        {/* Only meaningful while the buyer still has something to pay — a settled link is a
            dead link, and the hosted page rejects it anyway. */}
        {(tx.status === "initiated" || tx.status === "pending") && tx.checkout_url && (
          <a
            href={tx.checkout_url}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn--primary"
            data-testid="checkout-link"
          >
            {tCheckout("open")}
          </a>
        )}
        <DeleteTransactionButton transactionId={tx.id} />
      </div>
      {(tx.status === "initiated" || tx.status === "pending") && tx.checkout_url && (
        <p className="small muted -mt-3">{tCheckout("hint")}</p>
      )}

      <ScenarioControls transaction={tx} />

      <div className="card">
        <div className="card__head">
          <h2 className="card__title">Webhook Deliveries ({deliveries.length})</h2>
        </div>
        <div className="card__body">
          {deliveries.length === 0 ? (
            <p className="muted">No webhook deliveries recorded for this transaction.</p>
          ) : (
            <div className="kv">
              {deliveries.map((del) => (
                <div key={del.id} className="kv__row" dir="ltr">
                  <span className="kv__label row-flex">
                    <span className="badge">{del.stage}</span>
                    <span className="mono small" dir="ltr">
                      {del.target_url}
                    </span>
                    <span className="small muted" dir="ltr">
                      Attempt #{del.attempt}
                    </span>
                  </span>
                  <span className="kv__val row-flex justify-end">
                    <span
                      className={
                        del.result === "delivered" ? "badge badge--settled" : "badge badge--declined"
                      }
                    >
                      {del.result}
                    </span>
                    {del.response_status && (
                      <span className="mono small" dir="ltr">
                        HTTP {del.response_status}
                      </span>
                    )}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="term">
          <div className="term__bar">
            <span className="term__dots" aria-hidden="true">
              <i />
              <i />
              <i />
            </span>
            <span className="term__file">{t("raw_request")}</span>
          </div>
          <div className="term__body max-h-[350px] overflow-auto">
            <pre dir="ltr" data-testid="raw-request">
              {JSON.stringify(tx.raw_request ?? {}, null, 2)}
            </pre>
          </div>
        </div>

        <div className="term">
          <div className="term__bar">
            <span className="term__dots" aria-hidden="true">
              <i />
              <i />
              <i />
            </span>
            <span className="term__file">{t("raw_response")}</span>
          </div>
          <div className="term__body max-h-[350px] overflow-auto">
            <pre dir="ltr" data-testid="raw-response">
              {JSON.stringify(tx.raw_response ?? {}, null, 2)}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}
