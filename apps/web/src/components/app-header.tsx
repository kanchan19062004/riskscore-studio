import Link from "next/link";

import { logout } from "@/app/actions/auth";

export function AppHeader() {
  return (
    <header className="flex items-center justify-between border-b border-zinc-800 px-6 py-4">
      <div className="flex items-center gap-6">
        <Link href="/dashboard" className="text-sm uppercase tracking-[0.2em] text-emerald-400">
          RiskScore Studio
        </Link>
        <nav className="flex gap-4 text-sm text-zinc-400">
          <Link href="/dashboard" className="hover:text-zinc-100">
            Dashboard
          </Link>
          <Link href="/score" className="hover:text-zinc-100">
            Score
          </Link>
          <Link href="/history" className="hover:text-zinc-100">
            History
          </Link>
        </nav>
      </div>
      <form action={logout}>
        <button
          type="submit"
          className="rounded-md border border-zinc-700 px-3 py-1.5 text-sm hover:bg-zinc-800"
        >
          Log out
        </button>
      </form>
    </header>
  );
}
