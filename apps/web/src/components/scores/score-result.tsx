import type { ScoreResult } from "@/lib/api";

const TONE: Record<ScoreResult["risk_level"], string> = {
  LOW: "border-emerald-800 bg-emerald-950/50 text-emerald-300",
  MEDIUM: "border-amber-800 bg-amber-950/50 text-amber-200",
  HIGH: "border-red-800 bg-red-950/50 text-red-300",
};

export function ScoreResultCard({ score }: { score: ScoreResult }) {
  return (
    <div className={`rounded-lg border p-5 ${TONE[score.risk_level]}`}>
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <p className="text-3xl font-semibold tracking-tight">{score.risk_level}</p>
        <p className="text-sm">
          {(score.probability * 100).toFixed(1)}% fraud probability · model v{score.model_version_id}
        </p>
      </div>
      <div className="mt-3 h-2 rounded bg-black/30">
        <span
          className="block h-2 rounded bg-current"
          style={{ width: `${Math.min(score.probability * 100, 100)}%` }}
        />
      </div>
      <p className="mt-3 text-sm opacity-80">
        {score.risk_level === "LOW" && `Below the ${Math.round(score.review_threshold * 100)}% review threshold — auto-approve in a real pipeline.`}
        {score.risk_level === "MEDIUM" && `At or above ${Math.round(score.review_threshold * 100)}% — send to a human reviewer.`}
        {score.risk_level === "HIGH" && `At or above ${Math.round(score.high_risk_threshold * 100)}% — block or step-up authentication.`}
      </p>
      {score.cache_hit && (
        <p className="mt-2 text-xs uppercase tracking-wider opacity-80">Served from Redis cache</p>
      )}
    </div>
  );
}
