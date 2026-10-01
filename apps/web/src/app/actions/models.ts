"use server";

import { revalidatePath } from "next/cache";

import { readApiError, type ModelVersion } from "@/lib/api";
import { authedFetch } from "@/lib/dal";

export type TrainState = { ok: boolean; message: string } | undefined;

export async function trainModel(): Promise<TrainState> {
  const res = await authedFetch("/models/train", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  if (!res.ok) {
    const error = await readApiError(res);
    return { ok: false, message: error.message ?? "Training failed." };
  }

  const {
    version,
    promoted,
    champion_pr_auc: championPrAuc,
  }: { version: ModelVersion; promoted: boolean; champion_pr_auc: number | null } =
    await res.json();
  revalidatePath("/dashboard");

  const comparison =
    championPrAuc === null
      ? ""
      : ` On the same test data: new ${version.metrics.pr_auc} vs active ${championPrAuc} PR-AUC.`;
  return {
    ok: true,
    message: promoted
      ? `v${version.id} trained and promoted to active.${comparison}`
      : `v${version.id} trained but kept inactive.${comparison}`,
  };
}

export async function activateModel(versionId: number) {
  const res = await authedFetch(`/models/${versionId}/activate`, { method: "POST" });
  if (!res.ok) {
    const error = await readApiError(res);
    throw new Error(error.message ?? "Could not activate model.");
  }
  revalidatePath("/dashboard");
}
