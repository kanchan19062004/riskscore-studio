"use server";

import { revalidatePath } from "next/cache";

import { readApiError, type ScoreResult } from "@/lib/api";
import { authedFetch } from "@/lib/dal";

export type ScoreState =
  | { ok: true; score: ScoreResult }
  | { ok: false; message?: string; fieldErrors?: Record<string, string> }
  | undefined;

function num(form: FormData, name: string) {
  return Number(form.get(name));
}

export async function scoreTransaction(_prev: ScoreState, formData: FormData): Promise<ScoreState> {
  const ageRaw = String(formData.get("account_age_days") ?? "").trim();
  const payload = {
    amount: num(formData, "amount"),
    merchant_category: String(formData.get("merchant_category") ?? ""),
    channel: String(formData.get("channel") ?? ""),
    hour: num(formData, "hour"),
    account_age_days: ageRaw === "" ? null : Number(ageRaw),
    avg_amount_30d: num(formData, "avg_amount_30d"),
    txn_count_24h: num(formData, "txn_count_24h"),
    failed_attempts_24h: num(formData, "failed_attempts_24h"),
    is_new_device: formData.get("is_new_device") === "on",
    country_mismatch: formData.get("country_mismatch") === "on",
  };

  const res = await authedFetch("/scores", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const error = await readApiError(res);
    return { ok: false, message: error.message, fieldErrors: error.fieldErrors };
  }

  revalidatePath("/score");
  revalidatePath("/dashboard");
  return { ok: true, score: await res.json() };
}
