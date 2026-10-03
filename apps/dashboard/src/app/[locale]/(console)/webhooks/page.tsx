import { getTranslations, setRequestLocale } from "next-intl/server";
import { listDeliveries, Paginated, WebhookDelivery } from "../../../../lib/api";
import { formatDate } from "../../../../lib/format";
import { RetryButton } from "../../../../components/RetryButton";

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
  };
  let errorMsg: string | null = null;

  try {
    deliveriesData = await listDeliveries({ page: 1, page_size: 50 });
  } catch (err: unknown) {
    errorMsg = err instanceof Error ? err.message : "Failed to load webhook deliveries";
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-semibold tracking-tight">{t("title")}</h1>
        <p className="text-sm text-muted">{t("subtitle")}</p>
      </div>

      {errorMsg && (
        <div className="p-4 bg-danger/10 border border-danger/20 text-danger rounded-lg text-sm">
          {errorMsg}
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
              <th className="bg-surface-subtle text-text-2 font-medium px-4 py-2.5 border-b border-border whitespace-nowrap text-xs uppercase tracking-[0.03em] text-start">{t("target_url")}</th>
              <th className="bg-surface-subtle text-text-2 font-medium px-4 py-2.5 border-b border-border whitespace-nowrap text-xs uppercase tracking-[0.03em] text-start">{t("stage")}</th>
              <th className="bg-surface-subtle text-text-2 font-medium px-4 py-2.5 border-b border-border whitespace-nowrap text-xs uppercase tracking-[0.03em] text-start">{t("attempt")}</th>
              <th className="bg-surface-subtle text-text-2 font-medium px-4 py-2.5 border-b border-border whitespace-nowrap text-xs uppercase tracking-[0.03em] text-start">{t("result")}</th>
              <th className="bg-surface-subtle text-text-2 font-medium px-4 py-2.5 border-b border-border whitespace-nowrap text-xs uppercase tracking-[0.03em] text-start">{t("response_status")}</th>
              <th className="bg-surface-subtle text-text-2 font-medium px-4 py-2.5 border-b border-border whitespace-nowrap text-xs uppercase tracking-[0.03em] text-start">{t("timestamp")}</th>
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
                  <td className="py-3 px-4 font-mono text-xs max-w-[200px] truncate" dir="ltr" data-testid="delivery-target">
                    {del.target_url}
                  </td>
                  <td className="py-3 px-4 font-mono text-xs uppercase text-muted" dir="ltr">
                    {del.stage}
                  </td>
                  <td className="py-3 px-4 text-xs font-mono" data-testid="delivery-attempt">
                    #{del.attempt}
                  </td>
                  <td className="px-4 py-3 border-b border-border-soft align-middle" data-testid="delivery-result">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-[11px] font-bold uppercase border ${
                        del.result === "delivered"
                          ? "bg-success-bg text-success-ink border-success-border"
                          : del.result === "failed"
                          ? "bg-danger-bg text-danger-ink border-danger-border"
                          : "bg-warning-bg text-warning-ink border-warning-border"
                      }`}
                    >
                      {del.result}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-mono text-xs text-muted">
                    <span dir="ltr">{del.response_status ? `HTTP ${del.response_status}` : "—"}</span>
                  </td>
                  <td className="py-3 px-4 text-xs text-muted">
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
          <h2 className="font-display text-[17px] font-semibold tracking-display">Delivery Payloads Inspection</h2>
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
                      Error: {del.error}
                    </div>
                  )}
                  <div>
                    <div className="text-muted mb-1 text-[11px] uppercase tracking-wider">
                      Payload JSON
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
