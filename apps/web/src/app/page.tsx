import Link from "next/link";

const STACK = ["Next.js", "FastAPI", "Postgres", "Redis", "Docker"];

export default function Home() {
  return (
    <div className="flex flex-1 flex-col bg-zinc-950 text-zinc-100">
      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col justify-center gap-8 px-6 py-20">
        <p className="text-sm uppercase tracking-[0.2em] text-emerald-400">
          Project 1 · Fintech
        </p>
        <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
          RiskScore Studio
        </h1>
        <p className="max-w-xl text-lg leading-relaxed text-zinc-400">
          Full-stack transaction risk scoring: Next.js frontend, FastAPI + ML
          backend, Postgres, Redis cache, Docker, and CI. Built to apply an IIT
          Mandi Minor in AI &amp; Data Science in a production-style product.
        </p>
        <div className="flex flex-wrap gap-3 text-sm text-zinc-300">
          {STACK.map((item) => (
            <span key={item} className="rounded border border-zinc-700 px-3 py-1">
              {item}
            </span>
          ))}
        </div>
        <div className="flex gap-3">
          <Link
            href="/login"
            className="rounded-md bg-emerald-500 px-4 py-2 font-medium text-zinc-950 hover:bg-emerald-400"
          >
            Log in
          </Link>
          <Link
            href="/register"
            className="rounded-md border border-zinc-700 px-4 py-2 hover:bg-zinc-800"
          >
            Create account
          </Link>
        </div>
      </main>
    </div>
  );
}
