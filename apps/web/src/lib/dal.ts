import { redirect } from "next/navigation";
import { cache } from "react";

import { apiFetch, type ApiUser, type ModelVersion, type ScoreList, type ScoreOptions, type ScoreResult } from "./api";
import { getSessionToken } from "./session";

export async function authedFetch(path: string, init?: RequestInit) {
  const token = await getSessionToken();
  return apiFetch(path, {
    ...init,
    headers: { ...init?.headers, Authorization: `Bearer ${token}` },
  });
}

// Secure check: FastAPI verifies the token's signature and expiry and that the
// user still exists. cache() dedupes the call within a single render.
export const getCurrentUser = cache(async (): Promise<ApiUser | null> => {
  const token = await getSessionToken();
  if (!token) return null;

  const res = await authedFetch("/auth/me");
  if (!res.ok) return null;
  return res.json();
});

export async function requireUser(): Promise<ApiUser> {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  return user;
}

export async function getModelVersions(): Promise<ModelVersion[]> {
  const res = await authedFetch("/models");
  if (!res.ok) throw new Error(`Failed to load model versions (${res.status})`);
  return res.json();
}

export async function getScoreOptions(): Promise<ScoreOptions> {
  const res = await authedFetch("/scores/options");
  if (!res.ok) throw new Error(`Failed to load score options (${res.status})`);
  return res.json();
}

export async function getRecentScores(limit = 8): Promise<ScoreResult[]> {
  const data = await getScoreHistory({ page: 1, page_size: limit });
  return data.items;
}

export async function getScoreHistory(filters: Record<string, string | number | undefined>): Promise<ScoreList> {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value === undefined || value === "") continue;
    params.set(key, String(value));
  }
  const res = await authedFetch(`/scores?${params.toString()}`);
  if (!res.ok) throw new Error(`Failed to load score history (${res.status})`);
  return res.json();
}

export async function getScore(id: string): Promise<ScoreResult | null> {
  const res = await authedFetch(`/scores/${id}`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`Failed to load score (${res.status})`);
  return res.json();
}
