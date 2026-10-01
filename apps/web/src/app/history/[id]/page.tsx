import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { AppHeader } from "@/components/app-header";
import { ScoreResultCard } from "@/components/scores/score-result";
import { getScore, requireUser } from "@/lib/dal";

export const metadata: Metadata = { title: "Score detail · RiskScore Studio" };

export default async function ScoreDetailPage({ params }: { params: Promise<{ id: string }> }) {
  await requireUser();
  const { id } = await params;
  const score = await getScore(id);
  if (!score) notFound();

  const payload = score.payload;

  return (
    <div className="flex flex-1 flex-col bg-zinc-950 text-zinc-100">
      <AppHeader />
      <main className="mx-auto flex w-full max-w-3xl flex-col gap-8 px-6 py-12">
        <p>
          <Link href="/history" className="text-sm text-zinc-400 hover:text-zinc-100">
            ← All scores
          </Link>
        </p>
        <h1 className="text-3xl font-semibold tracking-tight">Score detail</h1>
        <ScoreResultCard score={score} />
        <section>
          <h2 className="text-sm font-medium text-zinc-300">Raw input (what the model saw)</h2>
          <dl className="mt-3 grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
            {Object.entries(payload).map(([key, value]) => (
              <div key={key} className="contents">
                <dt className="text-zinc-500">{key.replaceAll("_", " ")}</dt>
                <dd className="text-zinc-200">{String(value)}</dd>
              </div>
            ))}
          </dl>
        </section>
        <p className="text-xs text-zinc-600">id {score.id}</p>
      </main>
    </div>
  );
}
