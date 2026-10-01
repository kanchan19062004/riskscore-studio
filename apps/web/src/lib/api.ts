// Server-side only: the browser never talks to FastAPI directly.
// 127.0.0.1 rather than localhost because Node may resolve localhost to IPv6 (::1)
// while uvicorn listens on IPv4 only.
const API_URL = process.env.API_URL ?? "http://127.0.0.1:8000";

export type ApiUser = {
  id: string;
  email: string;
  full_name: string;
  role: string;
  created_at: string;
};

export type ModelMetrics = {
  roc_auc: number;
  pr_auc: number;
  precision: number;
  recall: number;
  f1: number;
  accuracy: number;
  baseline_accuracy: number;
  review_threshold: number;
  confusion_matrix: { tn: number; fp: number; fn: number; tp: number };
};

export type ModelVersion = {
  id: number;
  algorithm: string;
  is_active: boolean;
  created_at: string;
  metrics: ModelMetrics;
  candidates: { algorithm: string; roc_auc: number; pr_auc: number }[];
  dataset: {
    n_samples: number;
    n_train: number;
    n_test: number;
    fraud_rate: number;
    seed: number;
    fraud_rate_by_category: Record<string, number>;
  };
};

export type ScoreResult = {
  id: string;
  probability: number;
  risk_level: "LOW" | "MEDIUM" | "HIGH";
  model_version_id: number;
  cache_hit: boolean;
  payload: Record<string, unknown>;
  created_at: string;
  review_threshold: number;
  high_risk_threshold: number;
};

export type ScoreList = {
  items: ScoreResult[];
  total: number;
  page: number;
  page_size: number;
};

export type ScoreOptions = {
  merchant_categories: string[];
  channels: string[];
  review_threshold: number;
  high_risk_threshold: number;
};

export type ApiError = {
  message?: string;
  fieldErrors?: Record<string, string>;
};

export function apiFetch(path: string, init?: RequestInit) {
  return fetch(`${API_URL}/api/v1${path}`, { ...init, cache: "no-store" });
}

type ValidationIssue = { loc?: (string | number)[]; msg?: string };

export async function readApiError(res: Response): Promise<ApiError> {
  if (res.status === 413) {
    return { message: "That request was too large." };
  }

  const retryAfter = res.headers.get("Retry-After");
  const body = await res.json().catch(() => null);
  const detail: unknown = body?.detail;
  const wait =
    retryAfter && Number.isFinite(Number(retryAfter))
      ? ` Try again in ${Number(retryAfter)} seconds.`
      : "";

  if (res.status === 429) {
    if (typeof detail === "string") {
      return { message: /try again/i.test(detail) ? detail : `${detail}${wait}` };
    }
    return { message: `Too many requests.${wait}` };
  }

  if (typeof detail === "string") {
    return { message: detail };
  }

  if (Array.isArray(detail)) {
    const fieldErrors: Record<string, string> = {};
    for (const issue of detail as ValidationIssue[]) {
      const field = issue.loc?.[issue.loc.length - 1];
      if (typeof field === "string" && !fieldErrors[field]) {
        fieldErrors[field] = String(issue.msg ?? "Invalid value").replace(/^Value error, /, "");
      }
    }
    return { message: "Please fix the highlighted fields.", fieldErrors };
  }

  return { message: "Something went wrong. Please try again." };
}
