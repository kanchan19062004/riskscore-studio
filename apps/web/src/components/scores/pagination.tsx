import Link from "next/link";

import { historyQuery } from "@/lib/history-query";

export function Pagination({
  page,
  pageSize,
  total,
  params,
}: {
  page: number;
  pageSize: number;
  total: number;
  params: Record<string, string | string[] | undefined>;
}) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  if (pages <= 1) {
    return (
      <p className="text-sm text-zinc-500">
        {total} {total === 1 ? "score" : "scores"}
      </p>
    );
  }

  return (
    <div className="flex items-center justify-between text-sm text-zinc-400">
      <p>
        Page {page} of {pages} · {total} scores
      </p>
      <div className="flex gap-3">
        {page > 1 ? (
          <Link href={historyQuery(params, { page: page - 1 })} className="hover:text-zinc-100">
            Previous
          </Link>
        ) : (
          <span className="text-zinc-600">Previous</span>
        )}
        {page < pages ? (
          <Link href={historyQuery(params, { page: page + 1 })} className="hover:text-zinc-100">
            Next
          </Link>
        ) : (
          <span className="text-zinc-600">Next</span>
        )}
      </div>
    </div>
  );
}
