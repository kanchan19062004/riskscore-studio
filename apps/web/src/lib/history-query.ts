type ParamBag = Record<string, string | string[] | undefined>;

export function one(params: ParamBag, key: string) {
  const value = params[key];
  return Array.isArray(value) ? (value[0] ?? "") : (value ?? "");
}

const KEYS = ["risk_level", "merchant_category", "cache_hit", "model_version_id", "scope", "page"] as const;

export function historyQuery(
  params: ParamBag,
  overrides: Record<string, string | number | undefined> = {},
) {
  const next = new URLSearchParams();
  for (const key of KEYS) {
    const raw = key in overrides ? overrides[key] : one(params, key);
    const value = raw === undefined || raw === null ? "" : String(raw);
    if (!value || (key === "page" && value === "1")) continue;
    next.set(key, value);
  }
  const qs = next.toString();
  return qs ? `/history?${qs}` : "/history";
}

export function exportHref(params: ParamBag) {
  return historyQuery(params, { page: undefined }).replace("/history", "/history/export");
}
