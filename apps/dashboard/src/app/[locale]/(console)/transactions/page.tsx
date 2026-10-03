import Link from "next/link";
import { getTranslations, setRequestLocale } from "next-intl/server";
import {
  AdapterConfig,
  getAdapters,
  getProject,
  listDeliveries,
  listTransactions,
  Paginated,
  Project,
  Transaction,
} from "../../../../lib/api";
import { formatDate, formatRial, getStatusColor } from "../../../../lib/format";
import { ScenarioControls } from "../../../../components/ScenarioControls";
import { StatCards } from "../../../../components/StatCards";

export default async function TransactionsPage({
  params: { locale },
}: {
  params: { locale: string };
}) {
  setRequestLocale(locale);
  const t = await getTranslations("transactions");
  const tStatus = await getTranslations("status");

  let txData: Paginated<Transaction> = { items: [], page: 1, page_size: 50, total: 0 };
  let adapters: AdapterConfig[] = [];
  let project: Project | null = null;
  let deliveryTotal: number | undefined;
  let deliveryFailed: number | undefined;
  let loadError: string | null = null;

  try {
    const [txs, adps, prj, deliveries] = await Promise.all([
      listTransactions({ page: 1, page_size: 50 }),
      getAdapters(),
      getProject(),
      listDeliveries({ page: 1, page_size: 50 }),
    ]);
    txData = txs;
    adapters = adps;
    project = prj;
    deliveryTotal = deliveries.total ?? deliveries.items.length;
    deliveryFailed = deliveries.items.filter((d: any) => d.result !== "delivered").length;
  } catch (err: unknown) {
    loadError = err instanceof Error ? err.message : "Failed to load data";
  }

  const adapterMap = new Map(adapters.map((a) => [a.id, a.provider]));

  return (
    <>
      <StatCards
        transactions={txData.items as any[]}
        locale={locale}
        deliveryTotal={deliveryTotal}
        deliveryFailed={deliveryFailed}
      />

      {loadError && (
        <div className="p-4 bg-danger-bg border border-danger-border text-danger-ink rounded-console text-sm">
          {loadError}
        </div>
      )}

      {project && <ScenarioControls project={project} />}

      <div className="panel bg-surface border border-border rounded-console overflow-hidden">
        <div className="panel-header px-5 py-4 border-b border-border flex items-center justify-between gap-4 flex-wrap">
          <div className="panel-title font-display text-[17px] font-semibold tracking-display flex items-center gap-2">
            <span>{t("title")}</span>
            <span className="version-tag font-mono text-[11px] px-1.5 py-0.5 rounded bg-surface-subtle border border-border text-text">
              {txData.total} {locale === "fa" ? "رکورد" : "Records"}
            </span>
          </div>
        </div>

        <div className="table-container overflow-x-auto">
          <table
            className="data-table w-full border-collapse text-start text-[13px]"
            data-testid="transactions-table"
          >
            <thead>
              <tr>
                <th className="bg-surface-subtle text-text-2 font-medium px-4 py-2.5 border-b border-border whitespace-nowrap text-xs uppercase tracking-[0.03em] text-start">
                  {t("adapter")}
                </th>
                <th className="bg-surface-subtle text-text-2 font-medium px-4 py-2.5 border-b border-border whitespace-nowrap text-xs uppercase tracking-[0.03em] text-start">
                  {t("amount")}
                </th>
                <th className="bg-surface-subtle text-text-2 font-medium px-4 py-2.5 border-b border-border whitespace-nowrap text-xs uppercase tracking-[0.03em] text-start">
                  {t("status")}
                </th>
                <th className="bg-surface-subtle text-text-2 font-medium px-4 py-2.5 border-b border-border whitespace-nowrap text-xs uppercase tracking-[0.03em] text-start">
                  {t("scenario")}
                </th>
                <th className="bg-surface-subtle text-text-2 font-medium px-4 py-2.5 border-b border-border whitespace-nowrap text-xs uppercase tracking-[0.03em] text-start">
                  {t("authority")}
                </th>
                <th className="bg-surface-subtle text-text-2 font-medium px-4 py-2.5 border-b border-border whitespace-nowrap text-xs uppercase tracking-[0.03em] text-start">
                  {t("date")}
                </th>
                <th className="bg-surface-subtle text-text-2 font-medium px-4 py-2.5 border-b border-border whitespace-nowrap text-xs uppercase tracking-[0.03em] text-start"></th>
              </tr>
            </thead>
            <tbody>
              {txData.items.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-muted text-sm">
                    {t("empty")}
                  </td>
                </tr>
              ) : (
                txData.items.map((tx: any) => {
                  const providerName = adapterMap.get(tx.adapter_id) || tx.adapter_id;
                  return (
                    <tr
                      key={tx.id}
                      className="hover:bg-surface-subtle transition-colors"
                      data-testid="tx-row"
                    >
                      <td className="px-4 py-3 border-b border-border-soft align-middle">
                        <span
                          className="gateway-badge inline-flex items-center gap-1.5 px-2 py-[3px] rounded-sm text-xs font-medium bg-bg border border-border text-text whitespace-nowrap"
                          dir="ltr"
                          data-testid="tx-adapter"
                        >
                          {providerName}
                        </span>
                      </td>
                      <td
                        className="currency-cell px-4 py-3 border-b border-border-soft align-middle font-mono font-semibold text-text tabular-nums"
                        data-testid="tx-amount"
                      >
                        {formatRial(tx.amount_rial, locale)}
                      </td>
                      <td className="px-4 py-3 border-b border-border-soft align-middle" data-testid="tx-status">
                        <span
                          className={`status-badge inline-flex items-center gap-1.5 px-2 py-[3px] rounded-sm text-xs font-medium whitespace-nowrap border ${getStatusColor(
                            tx.status
                          )}`}
                        >
                          {tStatus.has(tx.status) ? tStatus(tx.status) : tx.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 border-b border-border-soft align-middle" data-testid="tx-scenario">
                        <span className="version-tag font-mono text-[11px] px-1.5 py-0.5 rounded bg-surface-subtle border border-border text-text">
                          {tx.effective_scenario}
                        </span>
                        {tx.forced_scenario && (
                          <span className="ms-1.5 text-[10px] text-accent-ink font-sans">
                            {t("forced")}
                          </span>
                        )}
                      </td>
                      <td
                        className="code-cell px-4 py-3 border-b border-border-soft align-middle font-mono text-xs text-text truncate max-w-[220px]"
                        dir="ltr"
                      >
                        {tx.authority}
                      </td>
                      <td className="px-4 py-3 border-b border-border-soft align-middle text-xs text-muted">
                        {formatDate(tx.created_at, locale)}
                      </td>
                      <td className="px-4 py-3 border-b border-border-soft align-middle text-end">
                        <Link
                          href={`/${locale}/transactions/${tx.id}`}
                          className="btn-secondary inline-flex items-center px-2.5 py-1 rounded-[6px] text-xs font-medium bg-surface text-text border border-border hover:bg-surface-subtle transition-colors duration-fast ease-standard"
                          data-testid={`tx-detail-link-${tx.id}`}
                        >
                          {t("inspect")}
                        </Link>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}