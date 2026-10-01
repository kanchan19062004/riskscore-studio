import { ScoreTable } from "@/components/scores/score-table";
import type { ScoreResult } from "@/lib/api";

export function RecentScores({ scores }: { scores: ScoreResult[] }) {
  return <ScoreTable scores={scores} empty="No scores yet." />;
}
