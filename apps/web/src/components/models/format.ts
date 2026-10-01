export const ALGORITHM_LABELS: Record<string, string> = {
  logistic_regression: "Logistic Regression",
  hist_gradient_boosting: "Gradient Boosting",
};

export function algorithmLabel(algorithm: string) {
  return ALGORITHM_LABELS[algorithm] ?? algorithm;
}

export function pct(value: number) {
  return `${(value * 100).toFixed(1)}%`;
}

export function shortDate(iso: string) {
  return new Date(iso).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" });
}
