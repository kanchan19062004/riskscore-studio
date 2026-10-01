import Link from "next/link";

import type { ScoreOptions } from "@/lib/api";
import { exportHref, one } from "@/lib/history-query";

const SELECT =
  "rounded-md border border-zinc-700 bg-zinc-900 px-2 py-1.5 text-sm text-zinc-100";

export function HistoryFilters({
  params,
  options,
  isAdmin,
}: {
  params: Record<string, string | string[] | undefined>;
  options: ScoreOptions;
  isAdmin: boolean;
}) {
  return (
    <form method="get" action="/history" className="flex flex-wrap items-end gap-3">
      <label className="flex flex-col gap-1 text-xs text-zinc-500">
        Risk
        <select name="risk_level" defaultValue={one(params, "risk_level")} className={SELECT}>
          <option value="">Any</option>
          <option value="LOW">LOW</option>
          <option value="MEDIUM">MEDIUM</option>
          <option value="HIGH">HIGH</option>
        </select>
      </label>
      <label className="flex flex-col gap-1 text-xs text-zinc-500">
        Category
        <select
          name="merchant_category"
          defaultValue={one(params, "merchant_category")}
          className={SELECT}
        >
          <option value="">Any</option>
          {options.merchant_categories.map((category) => (
            <option key={category} value={category}>
              {category.replaceAll("_", " ")}
            </option>
          ))}
        </select>
      </label>
      <label className="flex flex-col gap-1 text-xs text-zinc-500">
        Cache
        <select name="cache_hit" defaultValue={one(params, "cache_hit")} className={SELECT}>
          <option value="">Any</option>
          <option value="true">Hit</option>
          <option value="false">Miss</option>
        </select>
      </label>
      {isAdmin && (
        <label className="flex flex-col gap-1 text-xs text-zinc-500">
          Whose scores
          <select name="scope" defaultValue={one(params, "scope") || "mine"} className={SELECT}>
            <option value="mine">Mine</option>
            <option value="all">Everyone</option>
          </select>
        </label>
      )}
      <button
        type="submit"
        className="rounded-md bg-emerald-500 px-3 py-1.5 text-sm font-medium text-zinc-950 hover:bg-emerald-400"
      >
        Apply
      </button>
      <Link href="/history" className="px-2 py-1.5 text-sm text-zinc-400 hover:text-zinc-100">
        Clear
      </Link>
      <a href={exportHref(params)} className="px-2 py-1.5 text-sm text-emerald-400 hover:underline">
        Export CSV
      </a>
    </form>
  );
}
