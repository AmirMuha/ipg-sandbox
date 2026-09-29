import { getTranslations, setRequestLocale } from "next-intl/server";
import { listDeliveries, Paginated, WebhookDelivery } from "../../../lib/api";
import { formatDate } from "../../../lib/format";
import { RetryButton } from "../../../components/RetryButton";

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
        <h1 className="text-2xl font-bold tracking-tight">{t("title")}</h1>
        <p className="text-sm text-muted">{t("subtitle")}</p>
      </div>

      {errorMsg && (
        <div className="p-4 bg-danger/10 border border-danger/20 text-danger rounded-lg text-sm">
          {errorMsg}
        </div>
      )}

      <div className="bg-surface border border-border rounded-lg overflow-hidden">
        <table className="w-full text-sm text-start" data-testid="deliveries-table">
          <thead>
            <tr className="border-b border-border bg-surface-2/50 text-xs text-muted">
              <th className="py-3 px-4 text-start font-medium">{t("target_url")}</th>
              <th className="py-3 px-4 text-start font-medium">{t("stage")}</th>
              <th className="py-3 px-4 text-start font-medium">{t("attempt")}</th>
              <th className="py-3 px-4 text-start font-medium">{t("result")}</th>
              <th className="py-3 px-4 text-start font-medium">{t("response_status")}</th>
              <th className="py-3 px-4 text-start font-medium">{t("timestamp")}</th>
              <th className="py-3 px-4 text-start font-medium"></th>
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
                <tr key={del.id} className="hover:bg-surface-2/30 transition-colors" data-testid="delivery-row">
                  <td className="py-3 px-4 font-mono text-xs max-w-[200px] truncate" data-testid="delivery-target">
                    {del.target_url}
                  </td>
                  <td className="py-3 px-4 font-mono text-xs uppercase text-muted">
                    {del.stage}
                  </td>
                  <td className="py-3 px-4 text-xs font-mono" data-testid="delivery-attempt">
                    #{del.attempt}
                  </td>
                  <td className="py-3 px-4" data-testid="delivery-result">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-[11px] font-bold uppercase ${
                        del.result === "delivered"
                          ? "bg-success/10 text-success border border-success/30"
                          : del.result === "failed"
                          ? "bg-danger/10 text-danger border border-danger/30"
                          : "bg-warning/10 text-warning border border-warning/30"
                      }`}
                    >
                      {del.result}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-mono text-xs text-muted">
                    {del.response_status ? `HTTP ${del.response_status}` : "—"}
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

      {deliveriesData.items.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-base font-semibold">Delivery Payloads Inspection</h2>
          <div className="space-y-3">
            {deliveriesData.items.map((del: any) => (
              <details
                key={del.id}
                className="bg-surface border border-border rounded-lg p-3 text-xs font-mono"
                data-testid="delivery-details"
              >
                <summary className="cursor-pointer text-muted hover:text-text font-semibold flex items-center justify-between">
                  <span>
                    Attempt #{del.attempt} to {del.target_url} ({del.stage})
                  </span>
                  <span
                    className={del.result === "delivered" ? "text-success" : "text-danger"}
                  >
                    {del.result}
                  </span>
                </summary>
                <div className="mt-3 pt-3 border-t border-border space-y-2">
                  {del.error && (
                    <div className="text-danger bg-danger/10 p-2 rounded">
                      Error: {del.error}
                    </div>
                  )}
                  <div>
                    <div className="text-muted mb-1 text-[11px] uppercase tracking-wider">
                      Payload JSON
                    </div>
                    <pre className="bg-surface-2 p-2.5 rounded overflow-auto max-h-[250px]">
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
