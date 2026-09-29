import Link from "next/link";
import { getTranslations, setRequestLocale } from "next-intl/server";
import {
  AdapterConfig,
  getAdapters,
  getProject,
  listTransactions,
  Paginated,
  Project,
  Transaction,
} from "../../../lib/api";
import { formatDate, formatRial, getStatusColor } from "../../../lib/format";
import { ScenarioControls } from "../../../components/ScenarioControls";

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
  let loadError: string | null = null;

  try {
    const [txs, adps, prj] = await Promise.all([
      listTransactions({ page: 1, page_size: 50 }),
      getAdapters(),
      getProject(),
    ]);
    txData = txs;
    adapters = adps;
    project = prj;
  } catch (err: unknown) {
    loadError = err instanceof Error ? err.message : "Failed to load data";
  }

  const adapterMap = new Map(adapters.map((a) => [a.id, a.provider]));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{t("title")}</h1>
          <p className="text-sm text-muted">{t("subtitle")}</p>
        </div>
      </div>

      {loadError && (
        <div className="p-4 bg-danger/10 border border-danger/20 text-danger rounded-lg text-sm">
          {loadError}
        </div>
      )}

      {project && <ScenarioControls project={project} />}

      <div className="bg-surface border border-border rounded-lg overflow-hidden">
        <table className="w-full text-sm text-start" data-testid="transactions-table">
          <thead>
            <tr className="border-b border-border bg-surface-2/50 text-xs text-muted">
              <th className="py-3 px-4 text-start font-medium">{t("adapter")}</th>
              <th className="py-3 px-4 text-start font-medium">{t("amount")}</th>
              <th className="py-3 px-4 text-start font-medium">{t("status")}</th>
              <th className="py-3 px-4 text-start font-medium">{t("scenario")}</th>
              <th className="py-3 px-4 text-start font-medium">{t("authority")}</th>
              <th className="py-3 px-4 text-start font-medium">{t("date")}</th>
              <th className="py-3 px-4 text-start font-medium"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
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
                  <tr key={tx.id} className="hover:bg-surface-2/30 transition-colors" data-testid="tx-row">
                    <td className="py-3 px-4 font-mono font-medium text-xs" data-testid="tx-adapter">
                      {providerName}
                    </td>
                    <td className="py-3 px-4 font-mono" data-testid="tx-amount">
                      {formatRial(tx.amount_rial, locale)}
                    </td>
                    <td className="py-3 px-4" data-testid="tx-status">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-xs border font-medium ${getStatusColor(
                          tx.status
                        )}`}
                      >
                        {tStatus.has(tx.status) ? tStatus(tx.status) : tx.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono text-xs" data-testid="tx-scenario">
                      <span className="bg-surface-2 border border-border px-1.5 py-0.5 rounded">
                        {tx.effective_scenario}
                      </span>
                      {tx.forced_scenario && (
                        <span className="ms-1.5 text-[10px] text-accent font-sans">
                          (forced)
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 font-mono text-xs text-muted truncate max-w-[150px]">
                      {tx.authority}
                    </td>
                    <td className="py-3 px-4 text-xs text-muted">
                      {formatDate(tx.created_at, locale)}
                    </td>
                    <td className="py-3 px-4 text-end">
                      <Link
                        href={`/${locale}/transactions/${tx.id}`}
                        className="text-xs text-accent hover:underline"
                        data-testid={`tx-detail-link-${tx.id}`}
                      >
                        View &rarr;
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
  );
}
