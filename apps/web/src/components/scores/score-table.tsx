import Link from "next/link";

import type { ScoreResult } from "@/lib/api";

export const RISK_TONE: Record<ScoreResult["risk_level"], string> = {
  LOW: "text-emerald-400",
  MEDIUM: "text-amber-300",
  HIGH: "text-red-400",
};

function when(iso: string) {
  return new Date(iso).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" });
}

export function ScoreTable({
  scores,
  empty = "No scores match these filters.",
}: {
  scores: ScoreResult[];
  empty?: string;
}) {
  if (scores.length === 0) {
    return <p className="text-sm text-zinc-500">{empty}</p>;
  }

  return (
    <table className="w-full text-left text-sm">
      <thead className="border-b border-zinc-800 text-zinc-500">
        <tr>
          <th className="py-2 font-normal">When</th>
          <th className="py-2 font-normal">Risk</th>
          <th className="py-2 font-normal">Probability</th>
          <th className="py-2 font-normal">Category</th>
          <th className="py-2 font-normal">Amount</th>
          <th className="py-2 font-normal">Cache</th>
          <th className="py-2 font-normal">Model</th>
        </tr>
      </thead>
      <tbody>
        {scores.map((row) => (
          <tr key={row.id} className="border-b border-zinc-900">
            <td className="py-2">
              <Link href={`/history/${row.id}`} className="text-zinc-100 hover:underline">
                {when(row.created_at)}
              </Link>
            </td>
            <td className={`py-2 font-medium ${RISK_TONE[row.risk_level]}`}>{row.risk_level}</td>
            <td className="py-2">{(row.probability * 100).toFixed(1)}%</td>
            <td className="py-2 text-zinc-400">
              {String(row.payload.merchant_category ?? "").replaceAll("_", " ")}
            </td>
            <td className="py-2">{Number(row.payload.amount).toLocaleString("en-IN")}</td>
            <td className="py-2 text-zinc-500">{row.cache_hit ? "hit" : "miss"}</td>
            <td className="py-2 text-zinc-500">v{row.model_version_id}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
