import { NextResponse, type NextRequest } from "next/server";

import { SESSION_COOKIE } from "@/lib/constants";

// Optimistic check only (is there a cookie at all?). The real check happens in
// requireUser(), which asks FastAPI to validate the token.
export function proxy(request: NextRequest) {
  if (!request.cookies.has(SESSION_COOKIE)) {
    return NextResponse.redirect(new URL("/login", request.url));
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/score", "/history", "/history/:path*"],
};
