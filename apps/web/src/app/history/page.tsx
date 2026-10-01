import type { Metadata } from "next";

import { AppHeader } from "@/components/app-header";
import { HistoryFilters } from "@/components/scores/history-filters";
import { Pagination } from "@/components/scores/pagination";
import { ScoreTable } from "@/components/scores/score-table";
import { getScoreHistory, getScoreOptions, requireUser } from "@/lib/dal";
import { one } from "@/lib/history-query";

export const metadata: Metadata = { title: "Scoring history · RiskScore Studio" };

type Search = Record<string, string | string[] | undefined>;

export default async function HistoryPage({ searchParams }: { searchParams: Promise<Search> }) {
  const user = await requireUser();
  const params = await searchParams;
  const page = Math.max(1, Number(one(params, "page") || "1"));
  const cacheHit = one(params, "cache_hit");

  const [options, history] = await Promise.all([
    getScoreOptions(),
    getScoreHistory({
      page,
      page_size: 20,
      risk_level: one(params, "risk_level") || undefined,
      merchant_category: one(params, "merchant_category") || undefined,
      cache_hit: cacheHit || undefined,
      model_version_id: one(params, "model_version_id") || undefined,
      scope: one(params, "scope") || "mine",
    }),
  ]);

  return (
    <div className="flex flex-1 flex-col bg-zinc-950 text-zinc-100">
      <AppHeader />
      <main className="mx-auto flex w-full max-w-5xl flex-col gap-8 px-6 py-12">
        <section>
          <h1 className="text-3xl font-semibold tracking-tight">Scoring history</h1>
          <p className="mt-2 max-w-2xl text-zinc-400">
            Every scoring request is an audit row, including Redis cache hits. Filters live in the
            URL so you can bookmark or share a view. Analysts only see their own scores.
          </p>
        </section>
        <HistoryFilters params={params} options={options} isAdmin={user.role === "admin"} />
        <ScoreTable scores={history.items} />
        <Pagination
          page={history.page}
          pageSize={history.page_size}
          total={history.total}
          params={params}
        />
      </main>
    </div>
  );
}
