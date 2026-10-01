import Link from "next/link";
import type { ReactNode } from "react";

type AuthShellProps = {
  title: string;
  subtitle: string;
  footer: ReactNode;
  children: ReactNode;
};

export function AuthShell({ title, subtitle, footer, children }: AuthShellProps) {
  return (
    <div className="flex flex-1 items-center justify-center bg-zinc-950 px-6 py-16 text-zinc-100">
      <div className="w-full max-w-sm">
        <Link href="/" className="text-sm uppercase tracking-[0.2em] text-emerald-400">
          RiskScore Studio
        </Link>
        <h1 className="mt-4 text-3xl font-semibold tracking-tight">{title}</h1>
        <p className="mt-2 text-sm text-zinc-400">{subtitle}</p>
        <div className="mt-8">{children}</div>
        <p className="mt-6 text-sm text-zinc-400">{footer}</p>
      </div>
    </div>
  );
}
