import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";

import { AuthShell } from "@/components/auth/auth-shell";
import { getCurrentUser } from "@/lib/dal";

import { LoginForm } from "./login-form";

export const metadata: Metadata = { title: "Log in · RiskScore Studio" };

export default async function LoginPage() {
  if (await getCurrentUser()) redirect("/dashboard");

  return (
    <AuthShell
      title="Log in"
      subtitle="Score transactions and review risk history."
      footer={
        <>
          No account yet?{" "}
          <Link href="/register" className="text-emerald-400 hover:underline">
            Create one
          </Link>
        </>
      }
    >
      <LoginForm />
    </AuthShell>
  );
}
