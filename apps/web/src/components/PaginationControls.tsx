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

  return (
    <div
      className="row-flex justify-between mt-3"
      data-testid="pagination-controls"
    >
      <span className="small muted num">
        {t("summary", { page, total: totalPages })} · {total}
      </span>
      <div className="row-flex">
        <button
          type="button"
          onClick={() => goTo(page - 1)}
          disabled={page <= 1}
          className="btn btn--secondary btn--sm"
          data-testid="pagination-prev"
        >
          {t("prev")}
        </button>
        <button
          type="button"
          onClick={() => goTo(page + 1)}
          disabled={page >= totalPages}
          className="btn btn--secondary btn--sm"
          data-testid="pagination-next"
        >
          {t("next")}
        </button>
      </div>
    </div>
  );
}
