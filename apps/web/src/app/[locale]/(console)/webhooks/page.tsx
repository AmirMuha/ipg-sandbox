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
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div className="min-w-0">
          <h1 className="font-display text-2xl font-semibold tracking-tight flex items-center gap-3 flex-wrap">
            <span>{t("title")}</span>
            {/* The engine POSTs from inside this compose network — every target the
                dashboard records is a loopback address, never a real merchant URL. */}
            <span
              className="version-tag font-mono text-[11px] px-1.5 py-0.5 rounded bg-surface-subtle border border-border text-text whitespace-nowrap"
              data-testid="webhook-dispatcher-tag"
            >
              {t("local_dispatcher")}
            </span>
          </h1>
          <p className="text-sm text-muted">{t("subtitle")}</p>
        </div>

        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-4 text-xs">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-success" aria-hidden="true" />
              <span className="text-muted">{t("delivered")}</span>
              <span className="font-mono tabular-nums" data-testid="webhook-delivered-count">
                {delivered}
              </span>
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-danger" aria-hidden="true" />
              <span className="text-muted">{t("failed")}</span>
              <span className="font-mono tabular-nums" data-testid="webhook-failed-count">
                {failed}
              </span>
            </span>
            <span className="text-muted">
              <span className="font-mono tabular-nums" data-testid="webhook-total-count">
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
        <div className="p-4 bg-danger-bg border border-danger-border text-danger-ink rounded-console text-sm">
          {errorMsg}
        </div>
      )}

      {project && (
        <div className="space-y-3">
          <div className="panel bg-surface border border-border rounded-console p-5 space-y-3">
            <div className="flex items-center justify-between gap-4 flex-wrap">
              <div className="min-w-0">
                <h2 className="font-semibold text-sm">{t("endpoint_title")}</h2>
                <p
                  className="text-xs text-muted font-mono truncate"
                  dir="ltr"
                  data-testid="webhook-target-url"
                >
                  {project.webhook_url || "—"}
                </p>
              </div>
            </div>
          </div>
          <ScenarioRibbon project={project} locale={locale} />
        </div>
      )}

      <div className="panel bg-surface border border-border rounded-console overflow-hidden">
        <div className="panel-header px-5 py-4 border-b border-border flex items-center justify-between gap-4 flex-wrap">
          <div className="panel-title font-display text-[17px] font-semibold tracking-display">{t("title")}</div>
        </div>
        <div className="table-container overflow-x-auto">
        <table className="data-table w-full border-collapse text-start text-[13px]" data-testid="deliveries-table">
          <thead>
            <tr>
              <th className="bg-surface-subtle text-text-2 font-medium px-4 py-2.5 border-b border-border whitespace-nowrap text-xs uppercase tracking-[0.03em] text-start">{t("event")}</th>
              <th className="bg-surface-subtle text-text-2 font-medium px-4 py-2.5 border-b border-border whitespace-nowrap text-xs uppercase tracking-[0.03em] text-start">{t("target_url")}</th>
              <th className="bg-surface-subtle text-text-2 font-medium px-4 py-2.5 border-b border-border whitespace-nowrap text-xs uppercase tracking-[0.03em] text-start">{t("gateway")}</th>
              <th className="bg-surface-subtle text-text-2 font-medium px-4 py-2.5 border-b border-border whitespace-nowrap text-xs uppercase tracking-[0.03em] text-start">{t("status_col")}</th>
              <th className="bg-surface-subtle text-text-2 font-medium px-4 py-2.5 border-b border-border whitespace-nowrap text-xs uppercase tracking-[0.03em] text-start">{t("attempt")}</th>
              <th className="bg-surface-subtle text-text-2 font-medium px-4 py-2.5 border-b border-border whitespace-nowrap text-xs uppercase tracking-[0.03em] text-start">{t("time")}</th>
              <th className="bg-surface-subtle text-text-2 font-medium px-4 py-2.5 border-b border-border whitespace-nowrap text-xs uppercase tracking-[0.03em] text-start"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {deliveriesData.items.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-8 text-center text-muted text-sm">
                  {t("empty")}
                </td>
              </tr>
            ) : (
              deliveriesData.items.map((del: any) => (
                <tr key={del.id} className="hover:bg-surface-subtle transition-colors" data-testid="delivery-row">
                  <td className="py-3 px-4 font-mono text-xs text-text whitespace-nowrap" dir="ltr">
                    <span data-testid="delivery-event">{EVENT_STAGE[del.stage] ?? del.stage}</span>
                    {del.error && (
                      <span className="block font-sans text-[11px] text-danger-ink">{del.error}</span>
                    )}
                  </td>
                  <td className="py-3 px-4 font-mono text-xs max-w-[200px] truncate" dir="ltr" data-testid="delivery-target">
                    {del.target_url}
                  </td>
                  <td className="py-3 px-4 text-xs" data-testid="delivery-gateway">
                    {gatewayByTx.get(del.transaction_id) ?? "—"}
                  </td>
                  <td className="px-4 py-3 align-middle" data-testid="delivery-result">
                    {del.response_status ? (
                      <span
                        className={`status-badge inline-block px-2 py-[3px] rounded-sm text-xs font-medium border font-mono ${
                          del.response_status >= 200 && del.response_status < 300
                            ? "text-success-ink bg-success-bg border-success-border"
                            : "text-danger-ink bg-danger-bg border-danger-border"
                        }`}
                        dir="ltr"
                      >
                        {del.response_status}
                      </span>
                    ) : (
                      <span
                        className="status-badge inline-block px-2 py-[3px] rounded-sm text-xs font-medium border text-warning-ink bg-warning-bg border-warning-border"
                        data-testid="delivery-status"
                      >
                        {del.result}
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-xs font-mono whitespace-nowrap" data-testid="delivery-attempt">
                    {del.attempt}/{retryMax}
                  </td>
                  <td className="py-3 px-4 text-xs text-muted whitespace-nowrap">
                    {formatDate(del.created_at, locale)}
                  </td>
                  <td className="py-3 px-4 text-end">
                    <div className="flex items-center justify-end gap-2">
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

      {deliveriesData.items.length > 0 && (
        <div className="space-y-4">
          <h2 className="font-display text-[17px] font-semibold tracking-display">{t("payloads_title")}</h2>
          <div className="space-y-3">
            {deliveriesData.items.map((del: any) => (
              <details
                key={del.id}
                className="bg-surface border border-border rounded-lg p-3 text-xs font-mono"
                data-testid="delivery-details"
              >
                <summary className="cursor-pointer text-muted hover:text-text font-semibold flex items-center justify-between">
                  <span dir="ltr" style={{ textAlign: "start" }}>
                    Attempt #{del.attempt} to {del.target_url} ({del.stage})
                  </span>
                  <span
                    className={
                      del.result === "delivered" ? "text-success-ink" : "text-danger-ink"
                    }
                  >
                    {del.result}
                  </span>
                </summary>
                <div className="mt-3 pt-3 border-t border-border space-y-2">
                  {del.error && (
                    <div className="text-danger-ink bg-danger-bg p-2 rounded">
                      {t("error")}: {del.error}
                    </div>
                  )}
                  <div>
                    <div className="text-muted mb-1 text-[11px] uppercase tracking-wider">
                      {t("payload")}
                    </div>
                    <pre className="bg-surface-2 p-2.5 rounded overflow-auto max-h-[250px]" dir="ltr">
                      {JSON.stringify(del.payload, null, 2)}
                    </pre>
                  </div>
                </div>
              </details>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
