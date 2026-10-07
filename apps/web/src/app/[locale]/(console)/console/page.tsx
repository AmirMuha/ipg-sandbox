import Link from "next/link";
import { getTranslations, setRequestLocale } from "next-intl/server";

// Every console page reads live engine state (transactions, deliveries, project defaults),
// so prerendering them would freeze a snapshot of whatever the engine held at build time.
// The drawer's `useSearchParams()` already forced this for the shell, but each page has to
// opt in for itself.
export const dynamic = "force-dynamic";
import {
  AdapterConfig,
  getAdapters,
  getAnalyticsOverview,
  getProject,
  listTransactions,
  Paginated,
  Project,
  ProjectAnalyticsOverview,
  Transaction,
} from "../../../../lib/api";
import { formatDate, formatRial, formatToman } from "../../../../lib/format";
import { StatusBadge } from "../../../../components/StatusBadge";
import { ScenarioRibbon } from "../../../../components/ScenarioRibbon";
import { OutcomeDistribution } from "../../../../components/OutcomeDistribution";
import { StatCards } from "../../../../components/StatCards";
import { TransactionFilters } from "../../../../components/TransactionFilters";
import { PaginationControls } from "../../../../components/PaginationControls";
import { CopyButton } from "../../../../components/CopyButton";

export default async function TransactionsPage({
  params: { locale },
  searchParams,
}: {
  params: { locale: string };
  searchParams: Record<string, string | string[] | undefined>;
}) {
  setRequestLocale(locale);
  const t = await getTranslations("transactions");
  const tStatus = await getTranslations("status");
  const tSettings = await getTranslations("settings");
  const tCommon = await getTranslations("common");

  const num = (v: string | string[] | undefined, fallback: number) => {
    const n = Number(Array.isArray(v) ? v[0] : v);
    return Number.isFinite(n) && n > 0 ? n : fallback;
  };
  const str = (v: string | string[] | undefined) => (Array.isArray(v) ? v[0] : v) || undefined;

  const page = num(searchParams.page, 1);
  const pageSize = num(searchParams.page_size, 20);
  const filters = {
    q: str(searchParams.q),
    status: str(searchParams.status),
    adapter: str(searchParams.adapter),
    from_date: str(searchParams.from_date),
    to_date: str(searchParams.to_date),
  };

  let txData: Paginated<Transaction> = {
    items: [],
    page: 1,
    page_size: pageSize,
    total: 0,
    total_pages: 0,
  };
  let overview: ProjectAnalyticsOverview | null = null;
  let adapters: AdapterConfig[] = [];
  let project: Project | null = null;
  let loadError: string | null = null;

  try {
    const [txs, ov, adps, prj] = await Promise.all([
      listTransactions({ ...filters, page, page_size: pageSize }),
      getAnalyticsOverview(),
      getAdapters(),
      getProject(),
    ]);
    txData = txs;
    overview = ov;
    adapters = adps;
    project = prj;
  } catch (err: unknown) {
    loadError = err instanceof Error ? err.message : "Failed to load data";
  }

  const adapterMap = new Map(adapters.map((a) => [a.id, a.provider]));

  return (
    <>
      {/* The export's .phead carries Refresh and "new transaction" buttons. Both are
          skipped: the topbar already owns the simulate CTA, and a manual refresh control
          would be a new affordance on a page that refetches on every filter change. */}
      <div className="phead">
        <div className="phead__text">
          <h1>{t("title")}</h1>
          <p>{t("subtitle")}</p>
        </div>
      </div>

      {loadError && (
        <div className="banner banner--danger mb-4" role="alert">
          <svg className="ic" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" />
            <path d="M12 9v4M12 17h.01" />
          </svg>
          <span>{loadError}</span>
        </div>
      )}

      {project && <ScenarioRibbon project={project} locale={locale} />}

      <StatCards overview={overview} historyCap={project?.history_cap} locale={locale} />

      <OutcomeDistribution
        distribution={overview?.scenario_distribution ?? {}}
        total={overview?.total_transactions ?? 0}
        locale={locale}
      />

      <TransactionFilters adapters={adapters.map((a) => a.provider)} />

      <div className="tablewrap">
        <table className="table" data-testid="transactions-table">
          <caption className="sr-only">{t("title")}</caption>
          <thead>
            <tr>
              <th scope="col">{t("authority")}</th>
              <th scope="col">{t("gateway")}</th>
              <th scope="col">{t("order_id")}</th>
              <th scope="col">{t("amount")}</th>
              <th scope="col">{t("scenario")}</th>
              <th scope="col">{t("status")}</th>
              <th scope="col">{t("date")}</th>
              <th scope="col">
                <span className="sr-only">{t("inspect")}</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {txData.items.length === 0 ? (
              <tr>
                <td colSpan={8}>
                  <div className="empty">
                    <svg className="ic" viewBox="0 0 24 24" aria-hidden="true">
                      <rect x="3" y="3" width="18" height="18" rx="2" />
                      <path d="M3 9h18M9 21V9" />
                    </svg>
                    <h3>{t("empty")}</h3>
                  </div>
                </td>
              </tr>
            ) : (
              txData.items.map((tx: any) => {
                const providerName = adapterMap.get(tx.adapter_id) || tx.adapter_id;
                return (
                  <tr key={tx.id} data-testid="tx-row">
                    <td>
                      <div className="row-flex">
                        <span className="t-id truncate max-w-[220px]">{tx.authority}</span>
                        <CopyButton value={tx.authority} label={tCommon("copy")} />
                      </div>
                    </td>
                    <td>
                      <span className="badge badge--failed" dir="ltr" data-testid="tx-adapter">
                        .{providerName}
                      </span>
                    </td>
                    <td className="t-ref">{tx.app_reference || "—"}</td>
                    <td data-testid="tx-amount">
                      <span className="t-amount">{formatRial(tx.amount_rial, locale)}</span>
                      <span className="small muted block">
                        {formatToman(tx.amount_rial, locale)} {tSettings("toman")}
                      </span>
                    </td>
                    <td data-testid="tx-scenario">
                      <span className="t-ref">{tx.effective_scenario}</span>
                      {tx.forced_scenario && (
                        <span className="badge badge--accent ms-1.5">{t("forced")}</span>
                      )}
                    </td>
                    <td data-testid="tx-status">
                      <StatusBadge status={tx.status}>
                        {tStatus.has(tx.status) ? tStatus(tx.status) : tx.status}
                      </StatusBadge>
                    </td>
                    <td className="t-time">{formatDate(tx.created_at, locale)}</td>
                    <td className="text-end">
                      <Link
                        href={`/${locale}/console?tx=${tx.id}`}
                        scroll={false}
                        className="btn btn--secondary btn--sm"
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

      <PaginationControls
        page={txData.page}
        totalPages={txData.total_pages}
        total={txData.total}
      />
    </>
  );
}
