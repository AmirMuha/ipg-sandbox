import { getTranslations, setRequestLocale } from "next-intl/server";
import {
  AdapterConfig,
  getAdapters,
  getProject,
  getTransaction,
  listDeliveries,
  Paginated,
  Project,
  WebhookDelivery,
} from "../../../../lib/api";
import { formatDate } from "../../../../lib/format";
import { RetryButton } from "../../../../components/RetryButton";
import { ScenarioRibbon } from "../../../../components/ScenarioRibbon";
import { StatusBadge, badgeClass } from "../../../../components/StatusBadge";
import { WebhookPingButton } from "../../../../components/WebhookPingButton";

// Delivery rows are live engine state; a prerendered page would show an empty log forever.
export const dynamic = "force-dynamic";

/** Engine stage -> the event name a merchant's handler switches on. */
const EVENT_STAGE: Record<string, string> = {
  settle: "payment.approved",
  refund: "payment.refunded",
  notify: "payment.notify",
  verify: "payment.verify_failed",
};

export default async function WebhooksPage({
  params: { locale },
}: {
  params: { locale: string };
}) {
  setRequestLocale(locale);
  const t = await getTranslations("webhooks");

  let deliveriesData: Paginated<WebhookDelivery> = {
    items: [],
    page: 1,
    page_size: 50,
    total: 0,
    total_pages: 0,
  };
  let project: Project | null = null;
  let adapters: AdapterConfig[] = [];
  // delivery.transaction_id -> gateway provider name. The deliveries API returns no adapter
  // field, so the column is resolved per transaction; a row whose transaction has since
  // been deleted falls back to "—" rather than failing the whole table.
  const gatewayByTx = new Map<string, string>();
  let errorMsg: string | null = null;

  try {
    const [dels, prj, adps] = await Promise.all([
      listDeliveries({ page: 1, page_size: 50 }),
      getProject(),
      getAdapters(),
    ]);
    deliveriesData = dels;
    project = prj;
    adapters = adps;

    const byId = new Map(adps.map((a) => [a.id, a.provider]));
    const txIds = [...new Set(dels.items.map((d) => d.transaction_id))];
    const txs = await Promise.all(
      txIds.map((id) =>
        getTransaction(id).then(
          (tx) => [id, byId.get(tx.adapter_id)] as const,
          () => null
        )
      )
    );
    for (const entry of txs) {
      if (entry?.[1]) gatewayByTx.set(entry[0], entry[1]);
    }
  } catch (err: unknown) {
    errorMsg = err instanceof Error ? err.message : "Failed to load webhook deliveries";
  }

  const delivered = deliveriesData.items.filter((d) => d.result === "delivered").length;
  const failed = deliveriesData.items.filter((d) => d.result === "failed").length;
  const retryMax = project?.webhook_retry_max ?? 3;

  return (
    <>
      <div className="phead">
        <div className="phead__text">
          <h1 className="row-flex">
            <span>{t("title")}</span>
            {/* The engine POSTs from inside this compose network — every target the
                dashboard records is a loopback address, never a real merchant URL. */}
            <span className="badge badge--refunded" data-testid="webhook-dispatcher-tag">
              {t("local_dispatcher")}
            </span>
          </h1>
          <p>{t("subtitle")}</p>
        </div>

        <div className="phead__actions">
          <div className="row-flex small">
            <span className="health health--healthy">
              <i className="health__dot" aria-hidden="true" />
              <span>{t("delivered")}</span>
              <span className="mono" data-testid="webhook-delivered-count">
                {delivered}
              </span>
            </span>
            <span className="health health--degraded">
              <i className="health__dot" aria-hidden="true" />
              <span>{t("failed")}</span>
              <span className="mono" data-testid="webhook-failed-count">
                {failed}
              </span>
            </span>
            <span className="muted">
              <span className="mono" data-testid="webhook-total-count">
                {deliveriesData.total}
              </span>{" "}
              {t("total_deliveries")}
            </span>
          </div>
          {/* The ping button is the page's only proof the target is reachable; it must be
              mounted unconditionally, not behind `project &&`. */}
          <WebhookPingButton targetUrl={project?.webhook_url ?? null} />
        </div>
      </div>

      {errorMsg && (
        <div className="banner banner--danger mb-4" role="alert">
          <svg className="ic" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" />
            <path d="M12 9v4M12 17h.01" />
          </svg>
          <span>{errorMsg}</span>
        </div>
      )}

      {project && (
        <div className="stack-md mb-4">
          <div className="card">
            <div className="card__head">
              <h2 className="card__title">{t("endpoint_title")}</h2>
            </div>
            <div className="card__body">
              <div className="field">
                <span className="field__label">{t("target_url")}</span>
                <code
                  className="input mono truncate flex items-center"
                  dir="ltr"
                  data-testid="webhook-target-url"
                >
                  {project.webhook_url || "—"}
                </code>
              </div>
            </div>
          </div>
          <ScenarioRibbon project={project} locale={locale} />
        </div>
      )}

      <div className="card mb-4">
        <div className="card__head">
          <h2 className="card__title">{t("title")}</h2>
        </div>
        <div className="card__body">
          <div className="tablewrap">
            <table className="table" data-testid="deliveries-table">
              <caption className="sr-only">{t("title")}</caption>
              <thead>
                <tr>
                  <th scope="col">{t("event")}</th>
                  <th scope="col">{t("target_url")}</th>
                  <th scope="col">{t("gateway")}</th>
                  <th scope="col">{t("status_col")}</th>
                  <th scope="col">{t("attempt")}</th>
                  <th scope="col">{t("time")}</th>
                  <th scope="col">
                    <span className="sr-only">{t("actions")}</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {deliveriesData.items.length === 0 ? (
                  <tr>
                    <td colSpan={7}>
                      <div className="empty">
                        <p>{t("empty")}</p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  deliveriesData.items.map((del: any) => (
                    <tr key={del.id} data-testid="delivery-row">
                      <td>
                        <span className="t-id" dir="ltr" data-testid="delivery-event">
                          {EVENT_STAGE[del.stage] ?? del.stage}
                        </span>
                        {del.error && (
                          <span className="small block">{del.error}</span>
                        )}
                      </td>
                      <td>
                        <span
                          className="t-ref truncate max-w-[200px]"
                          dir="ltr"
                          data-testid="delivery-target"
                        >
                          {del.target_url}
                        </span>
                      </td>
                      <td data-testid="delivery-gateway">
                        {gatewayByTx.get(del.transaction_id) ?? "—"}
                      </td>
                      <td data-testid="delivery-result">
                        {del.response_status ? (
                          <span
                            className={`${badgeClass(
                              del.response_status >= 200 && del.response_status < 300
                                ? "delivered"
                                : "failed"
                            )} mono`}
                            dir="ltr"
                          >
                            {del.response_status}
                          </span>
                        ) : (
                          <StatusBadge status={del.result} data-testid="delivery-status">
                            {del.result}
                          </StatusBadge>
                        )}
                      </td>
                      <td className="mono small" data-testid="delivery-attempt">
                        {del.attempt}/{retryMax}
                      </td>
                      <td className="t-time">{formatDate(del.created_at, locale)}</td>
                      <td className="text-end">
                        <div className="row-flex justify-end">
                          <RetryButton deliveryId={del.id} />
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {deliveriesData.items.length > 0 && (
        <>
          <h2 className="card__title mb-3">{t("payloads_title")}</h2>
          <div className="stack-md">
            {deliveriesData.items.map((del: any) => (
              <details className="card" key={del.id} data-testid="delivery-details">
                <summary className="cursor-pointer">
                  <span className="card__head">
                    <span className="mono small flex-1 min-w-0 truncate" dir="ltr">
                      Attempt #{del.attempt} to {del.target_url} ({del.stage})
                    </span>
                    <StatusBadge status={del.result}>{del.result}</StatusBadge>
                  </span>
                </summary>
                <div className="card__body stack-sm">
                  {del.error && (
                    <div className="banner banner--danger">
                      <svg className="ic" viewBox="0 0 24 24" aria-hidden="true">
                        <circle cx="12" cy="12" r="10" />
                        <path d="M12 8v4M12 16h.01" />
                      </svg>
                      <span>
                        {t("error")}: {del.error}
                      </span>
                    </div>
                  )}
                  <div className="field">
                    <span className="field__label">{t("payload")}</span>
                    <div className="term">
                      <div className="term__bar">
                        <span className="term__dots" aria-hidden="true">
                          <i />
                          <i />
                          <i />
                        </span>
                      </div>
                      <div className="term__body max-h-[250px] overflow-y-auto">
                        <pre dir="ltr">{JSON.stringify(del.payload, null, 2)}</pre>
                      </div>
                    </div>
                  </div>
                </div>
              </details>
            ))}
          </div>
        </>
      )}
    </>
  );
}
