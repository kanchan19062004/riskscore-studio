import type { ModelVersion } from "@/lib/api";

import { algorithmLabel, pct, shortDate } from "./format";

function Tile({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
      <p className="text-xs uppercase tracking-wider text-zinc-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
      <p className="mt-1 text-xs text-zinc-500">{hint}</p>
    </div>
  );
}

export function ActiveModel({ model }: { model: ModelVersion }) {
  const { metrics, dataset } = model;
  const cm = metrics.confusion_matrix;
  const categories = Object.entries(dataset.fraud_rate_by_category);
  const maxRate = Math.max(...categories.map(([, rate]) => rate));
  const threshold = pct(metrics.review_threshold);

  return (
    <div className="flex flex-col gap-6">
      <p className="text-zinc-400">
        <span className="font-medium text-zinc-100">v{model.id}</span> ·{" "}
        {algorithmLabel(model.algorithm)} · trained {shortDate(model.created_at)} on{" "}
        {dataset.n_samples.toLocaleString("en-IN")} transactions ({pct(dataset.fraud_rate)} fraud)
      </p>

      <div className="grid gap-4 sm:grid-cols-4">
        <Tile label="ROC-AUC" value={metrics.roc_auc.toFixed(3)} hint="0.5 = coin flip, 1.0 = perfect ranking" />
        <Tile
          label="PR-AUC"
          value={metrics.pr_auc.toFixed(3)}
          hint={`Random guessing scores ${dataset.fraud_rate.toFixed(3)}`}
        />
        <Tile label="Recall" value={pct(metrics.recall)} hint={`Share of fraud flagged at ≥ ${threshold}`} />
        <Tile label="Precision" value={pct(metrics.precision)} hint="Share of flagged that is really fraud" />
      </div>

      <p className="rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-200">
        Accuracy is {pct(metrics.accuracy)}, but calling every transaction legitimate would score{" "}
        {pct(metrics.baseline_accuracy)}. With rare fraud, accuracy is misleading, so models are
        compared on PR-AUC.
      </p>

      <div className="grid gap-6 lg:grid-cols-2">
        <div>
          <h3 className="text-sm font-medium text-zinc-300">
            Test set results at review threshold {threshold}
          </h3>
          <table className="mt-3 w-full text-sm">
            <thead className="text-zinc-500">
              <tr>
                <th />
                <th className="py-1 font-normal">Flagged</th>
                <th className="py-1 font-normal">Not flagged</th>
              </tr>
            </thead>
            <tbody className="text-center">
              <tr>
                <th className="py-2 text-left font-normal text-zinc-500">Actually fraud</th>
                <td className="bg-emerald-950/60 py-2">{cm.tp} caught</td>
                <td className="bg-red-950/60 py-2">{cm.fn} missed</td>
              </tr>
              <tr>
                <th className="py-2 text-left font-normal text-zinc-500">Actually legit</th>
                <td className="bg-amber-950/50 py-2">{cm.fp} false alarms</td>
                <td className="bg-zinc-900 py-2">{cm.tn} cleared</td>
              </tr>
            </tbody>
          </table>

          <h3 className="mt-6 text-sm font-medium text-zinc-300">Candidates compared</h3>
          <ul className="mt-2 space-y-1 text-sm text-zinc-400">
            {model.candidates.map((c) => (
              <li key={c.algorithm}>
                {algorithmLabel(c.algorithm)}: PR-AUC {c.pr_auc.toFixed(3)}, ROC-AUC{" "}
                {c.roc_auc.toFixed(3)}
                {c.algorithm === model.algorithm && (
                  <span className="ml-2 text-emerald-400">selected</span>
                )}
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h3 className="text-sm font-medium text-zinc-300">Fraud rate by merchant category</h3>
          <ul className="mt-3 space-y-2">
            {categories.map(([category, rate]) => (
              <li key={category} className="grid grid-cols-[8rem_1fr_3.5rem] items-center gap-2 text-sm">
                <span className="truncate text-zinc-400">{category.replace("_", " ")}</span>
                <span className="h-2 rounded bg-zinc-800">
                  <span
                    className="block h-2 rounded bg-emerald-500"
                    style={{ width: `${(rate / maxRate) * 100}%` }}
                  />
                </span>
                <span className="text-right text-zinc-300">{pct(rate)}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
