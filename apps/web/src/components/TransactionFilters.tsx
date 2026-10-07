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
    router.push(qs ? `?${qs}` : window.location.pathname);
  }

  return (
    <div className="filters" data-testid="transaction-filters">
      <label className="field field--grow">
        <span className="field__label">{t("search")}</span>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") apply({ q: e.currentTarget.value });
          }}
          placeholder={t("search_placeholder")}
          className="input"
          data-testid="filter-search"
        />
      </label>

      <label className="field field--w">
        <span className="field__label">{t("status")}</span>
        <select
          value={params.get("status") ?? ""}
          onChange={(e) => apply({ status: e.target.value })}
          className="select"
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

      <label className="field field--w">
        <span className="field__label">{t("adapter")}</span>
        <select
          value={params.get("adapter") ?? ""}
          onChange={(e) => apply({ adapter: e.target.value })}
          className="select"
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

      <label className="field field--w">
        <span className="field__label">{t("from_date")}</span>
        {/* Native date input: no picker dependency for a date range that is optional. */}
        <input
          type="date"
          value={params.get("from_date") ?? ""}
          onChange={(e) => apply({ from_date: e.target.value })}
          className="input"
          data-testid="filter-from-date"
        />
      </label>

      <label className="field field--w">
        <span className="field__label">{t("to_date")}</span>
        <input
          type="date"
          value={params.get("to_date") ?? ""}
          onChange={(e) => apply({ to_date: e.target.value })}
          className="input"
          data-testid="filter-to-date"
        />
      </label>

      <div className="row-flex">
        <button
          type="button"
          onClick={() => apply({ q })}
          className="btn btn--secondary"
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
          className="btn btn--ghost"
          data-testid="filter-clear"
        >
          {t("clear")}
        </button>
      </div>
    </div>
  );
}
