"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useTranslations } from "next-intl";

/** US3: page controls over the server's `total_pages`. Same URL-state model as the filters. */
export function PaginationControls({
  page,
  totalPages,
  total,
}: {
  page: number;
  totalPages: number;
  total: number;
}) {
  const router = useRouter();
  const params = useSearchParams();
  const t = useTranslations("pagination");

  function goTo(next: number) {
    const sp = new URLSearchParams(params.toString());
    if (next <= 1) sp.delete("page");
    else sp.set("page", String(next));
    const qs = sp.toString();
    router.push(qs ? `?${qs}` : "?");
  }

  // Nothing to page through; rendering dead controls is worse than rendering nothing.
  if (totalPages <= 1) return null;

  const btn =
    "px-3 py-1.5 rounded-[6px] text-[13px] font-medium border transition-colors " +
    "disabled:opacity-40 disabled:cursor-not-allowed";
  const enabledBtn = `${btn} bg-surface text-text border-border hover:bg-surface-subtle`;

  return (
    <div
      className="flex items-center justify-between gap-3 px-5 py-3 border-t border-border"
      data-testid="pagination-controls"
    >
      <span className="text-xs text-muted">
        {t("summary", { page, total: totalPages })} · {total}
      </span>
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => goTo(page - 1)}
          disabled={page <= 1}
          className={enabledBtn}
          data-testid="pagination-prev"
        >
          {t("prev")}
        </button>
        <button
          type="button"
          onClick={() => goTo(page + 1)}
          disabled={page >= totalPages}
          className={enabledBtn}
          data-testid="pagination-next"
        >
          {t("next")}
        </button>
      </div>
    </div>
  );
}
