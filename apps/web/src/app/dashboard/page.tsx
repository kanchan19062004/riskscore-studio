import type { Metadata } from "next";
import Link from "next/link";

import { AppHeader } from "@/components/app-header";
import { ActiveModel } from "@/components/models/active-model";
import { TrainButton } from "@/components/models/train-button";
import { VersionsTable } from "@/components/models/versions-table";
import { RecentScores } from "@/components/scores/recent-scores";
import { getModelVersions, getRecentScores, requireUser } from "@/lib/dal";

export const metadata: Metadata = { title: "Dashboard · RiskScore Studio" };

export default async function DashboardPage() {
  const user = await requireUser();
  const [versions, recent] = await Promise.all([getModelVersions(), getRecentScores(5)]);
  const active = versions.find((v) => v.is_active);
  const isAdmin = user.role === "admin";
  const memberSince = new Date(user.created_at).toLocaleDateString("en-IN", {
    dateStyle: "medium",
  });

  return (
    <div className="flex flex-1 flex-col bg-zinc-950 text-zinc-100">
      <AppHeader />

      <main className="mx-auto flex w-full max-w-5xl flex-col gap-10 px-6 py-12">
        <section>
          <h1 className="text-3xl font-semibold tracking-tight">Welcome, {user.full_name}</h1>
          <p className="mt-2 text-zinc-400">
            {user.email} · <span className="capitalize">{user.role}</span> · member since{" "}
            {memberSince}
          </p>
        </section>

        <section className="flex flex-col gap-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <h2 className="text-xl font-semibold">Risk model</h2>
            {isAdmin && <TrainButton />}
          </div>
          {active ? (
            <ActiveModel model={active} />
          ) : (
            <p className="rounded-lg border border-dashed border-zinc-700 p-6 text-zinc-400">
              No model trained yet.{" "}
              {isAdmin ? "Click “Train new model” to create v1." : "Ask an admin to train one."}
            </p>
          )}
        </section>

        {versions.length > 0 && (
          <section className="flex flex-col gap-3">
            <h2 className="text-xl font-semibold">Model versions</h2>
            <p className="text-sm text-zinc-500">
              A new version becomes active only if it scores at least as well as the active model
              when both are tested on the new version&apos;s test data. Each row&apos;s scores come from
              its own test set, so small differences between rows are noise. Admins can roll back
              by activating an older version.
            </p>
            <VersionsTable versions={versions} canActivate={isAdmin} />
          </section>
        )}

        <section className="flex flex-col gap-3">
          <div className="flex items-baseline justify-between gap-4">
            <h2 className="text-xl font-semibold">Recent scores</h2>
            <div className="flex gap-4 text-sm">
              <Link href="/score" className="text-emerald-400 hover:underline">
                Score a transaction
              </Link>
              <Link href="/history" className="text-emerald-400 hover:underline">
                View history
              </Link>
            </div>
          </div>
          <RecentScores scores={recent} />
        </section>
      </main>
    </div>
  );
}
