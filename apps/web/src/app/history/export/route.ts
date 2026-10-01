import { NextRequest } from "next/server";

import { getSessionToken } from "@/lib/session";

const API_URL = process.env.API_URL ?? "http://127.0.0.1:8000";

export async function GET(request: NextRequest) {
  const token = await getSessionToken();
  if (!token) {
    return new Response("Unauthorized", { status: 401 });
  }

  const res = await fetch(`${API_URL}/api/v1/scores/export${request.nextUrl.search}`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });

  return new Response(res.body, {
    status: res.status,
    headers: {
      "Content-Type": res.headers.get("Content-Type") ?? "text/csv",
      "Content-Disposition":
        res.headers.get("Content-Disposition") ?? 'attachment; filename="riskscore-history.csv"',
    },
  });
}
