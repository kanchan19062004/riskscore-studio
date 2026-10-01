import type { Metadata } from "next";
import Link from "next/link";

import { AppHeader } from "@/components/app-header";
import { RecentScores } from "@/components/scores/recent-scores";
import { ScoreForm } from "@/components/scores/score-form";
import { getModelVersions, getRecentScores, getScoreOptions, requireUser } from "@/lib/dal";

export const metadata: Metadata = { title: "Score a transaction · RiskScore Studio" };

export default async function ScorePage() {
  await requireUser();
  const [options, versions, recent] = await Promise.all([
    getScoreOptions(),
    getModelVersions(),
    getRecentScores(),
  ]);
  const hasModel = versions.some((v) => v.is_active);

  return (
    <div className="flex flex-1 flex-col bg-zinc-950 text-zinc-100">
      <AppHeader />
      <main className="mx-auto flex w-full max-w-5xl flex-col gap-10 px-6 py-12">
        <section>
          <h1 className="text-3xl font-semibold tracking-tight">Score a transaction</h1>
          <p className="mt-2 max-w-2xl text-zinc-400">
            The active model scores raw fields (the same ones used in training). Identical
            requests are served from Redis for one hour.
          </p>
        </section>

        {hasModel ? (
          <ScoreForm options={options} />
        ) : (
          <p className="rounded-lg border border-dashed border-zinc-700 p-6 text-zinc-400">
            No active model yet.{" "}
            <Link href="/dashboard" className="text-emerald-400 hover:underline">
              Train one from the dashboard
            </Link>
            .
          </p>
        )}

        <section className="flex flex-col gap-3">
          <h2 className="text-xl font-semibold">Your recent scores</h2>
          <p className="text-sm text-zinc-500">
            Every request is stored, including cache hits. Open{" "}
            <Link href="/history" className="text-emerald-400 hover:underline">
              scoring history
            </Link>{" "}
            to filter, page through, or export CSV.
          </p>
          <RecentScores scores={recent} />
        </section>
      </main>
    </div>
  );
}
