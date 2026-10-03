"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

/**
 * US3: search + filter. State lives in the URL, not in React, so a filtered view is
 * shareable and survives a refresh — and so the server component refetches on navigation.
 */
export function TransactionFilters({ adapters }: { adapters: string[] }) {
  const router = useRouter();
  const params = useSearchParams();
  const t = useTranslations("filters");
  const tStatus = useTranslations("status");

  const [q, setQ] = useState(params.get("q") ?? "");

  // Keep the input in sync when the URL changes underneath us (back button, clear).
  useEffect(() => setQ(params.get("q") ?? ""), [params]);

  function apply(next: Record<string, string>) {
    const sp = new URLSearchParams(params.toString());
    for (const [key, value] of Object.entries(next)) {
      if (value) sp.set(key, value);
      else sp.delete(key);
    }
    sp.delete("page"); // any filter change invalidates the current page number
    const qs = sp.toString();
    router.push(qs ? `?${qs}` : "?");
  }

  const input =
    "px-3 py-1.5 rounded-[6px] bg-surface border border-border text-sm text-text " +
    "focus:border-accent focus:outline-none";

  return (
    <div className="flex items-end gap-3 flex-wrap" data-testid="transaction-filters">
      <label className="flex flex-col gap-1">
        <span className="text-xs text-text-2 font-medium">{t("search")}</span>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") apply({ q: e.currentTarget.value });
          }}
          placeholder={t("search_placeholder")}
          className={`${input} w-64`}
          data-testid="filter-search"
        />
      </label>

      <label className="flex flex-col gap-1">
        <span className="text-xs text-text-2 font-medium">{t("status")}</span>
        <select
          value={params.get("status") ?? ""}
          onChange={(e) => apply({ status: e.target.value })}
          className={input}
          data-testid="filter-status"
        >
          <option value="">{t("all")}</option>
          {["initiated", "pending", "settled", "declined", "failed", "expired", "refunded"].map(
            (s) => (
              <option key={s} value={s}>
                {tStatus.has(s) ? tStatus(s) : s}
              </option>
            )
          )}
        </select>
      </label>

      <label className="flex flex-col gap-1">
        <span className="text-xs text-text-2 font-medium">{t("adapter")}</span>
        <select
          value={params.get("adapter") ?? ""}
          onChange={(e) => apply({ adapter: e.target.value })}
          className={input}
          data-testid="filter-adapter"
        >
          <option value="">{t("all")}</option>
          {adapters.map((a) => (
            <option key={a} value={a}>
              {a}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col gap-1">
        <span className="text-xs text-text-2 font-medium">{t("from_date")}</span>
        {/* Native date input: no picker dependency for a date range that is optional. */}
        <input
          type="date"
          value={params.get("from_date") ?? ""}
          onChange={(e) => apply({ from_date: e.target.value })}
          className={input}
          data-testid="filter-from-date"
        />
      </label>

      <label className="flex flex-col gap-1">
        <span className="text-xs text-text-2 font-medium">{t("to_date")}</span>
        <input
          type="date"
          value={params.get("to_date") ?? ""}
          onChange={(e) => apply({ to_date: e.target.value })}
          className={input}
          data-testid="filter-to-date"
        />
      </label>

      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => apply({ q })}
          className="btn-secondary px-3 py-1.5 rounded-[6px] bg-surface text-text border border-border text-[13px] font-medium hover:bg-surface-subtle transition-colors"
          data-testid="filter-apply"
        >
          {t("search")}
        </button>
        <button
          type="button"
          onClick={() => {
            setQ("");
            router.push("?");
          }}
          className="px-3 py-1.5 rounded-[6px] text-[13px] text-muted hover:text-text transition-colors"
          data-testid="filter-clear"
        >
          {t("clear")}
        </button>
      </div>
    </div>
  );
}
