import { activateModel } from "@/app/actions/models";
import type { ModelVersion } from "@/lib/api";

import { algorithmLabel, shortDate } from "./format";

export function VersionsTable({ versions, canActivate }: { versions: ModelVersion[]; canActivate: boolean }) {
  return (
    <table className="w-full text-left text-sm">
      <thead className="border-b border-zinc-800 text-zinc-500">
        <tr>
          <th className="py-2 font-normal">Version</th>
          <th className="py-2 font-normal">Algorithm</th>
          <th className="py-2 font-normal">PR-AUC</th>
          <th className="py-2 font-normal">ROC-AUC</th>
          <th className="py-2 font-normal">Trained</th>
          <th className="py-2 font-normal">Status</th>
        </tr>
      </thead>
      <tbody>
        {versions.map((v) => (
          <tr key={v.id} className="border-b border-zinc-900">
            <td className="py-2 font-medium">v{v.id}</td>
            <td className="py-2 text-zinc-400">{algorithmLabel(v.algorithm)}</td>
            <td className="py-2">{v.metrics.pr_auc.toFixed(3)}</td>
            <td className="py-2">{v.metrics.roc_auc.toFixed(3)}</td>
            <td className="py-2 text-zinc-400">{shortDate(v.created_at)}</td>
            <td className="py-2">
              {v.is_active ? (
                <span className="text-emerald-400">Active</span>
              ) : canActivate ? (
                <form action={activateModel.bind(null, v.id)}>
                  <button type="submit" className="text-zinc-400 underline hover:text-zinc-100">
                    Activate
                  </button>
                </form>
              ) : (
                <span className="text-zinc-500">Inactive</span>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
