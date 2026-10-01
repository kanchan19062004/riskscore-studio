import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";

import { AuthShell } from "@/components/auth/auth-shell";
import { getCurrentUser } from "@/lib/dal";

import { RegisterForm } from "./register-form";

export const metadata: Metadata = { title: "Create account · RiskScore Studio" };

export default async function RegisterPage() {
  if (await getCurrentUser()) redirect("/dashboard");

  return (
    <AuthShell
      title="Create your account"
      subtitle="Analyst access to the risk scoring dashboard."
      footer={
        <>
          Already have an account?{" "}
          <Link href="/login" className="text-emerald-400 hover:underline">
            Log in
          </Link>
        </>
      }
    >
      <RegisterForm />
    </AuthShell>
  );
}
