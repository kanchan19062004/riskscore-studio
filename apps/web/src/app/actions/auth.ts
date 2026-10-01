"use server";

import { redirect } from "next/navigation";

import { apiFetch, readApiError, type ApiError } from "@/lib/api";
import { createSession, deleteSession } from "@/lib/session";

export type AuthFormState = ApiError | undefined;

async function signIn(email: string, password: string): Promise<ApiError | null> {
  const res = await apiFetch("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ username: email, password }),
  });
  if (!res.ok) return readApiError(res);

  const { access_token, expires_in } = await res.json();
  await createSession(access_token, expires_in);
  return null;
}

export async function login(_prev: AuthFormState, formData: FormData): Promise<AuthFormState> {
  const error = await signIn(
    String(formData.get("email") ?? ""),
    String(formData.get("password") ?? ""),
  );
  if (error) return error;
  redirect("/dashboard");
}

export async function register(_prev: AuthFormState, formData: FormData): Promise<AuthFormState> {
  const payload = {
    full_name: String(formData.get("full_name") ?? ""),
    email: String(formData.get("email") ?? ""),
    password: String(formData.get("password") ?? ""),
  };

  const res = await apiFetch("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) return readApiError(res);

  const error = await signIn(payload.email, payload.password);
  if (error) return error;
  redirect("/dashboard");
}

export async function logout() {
  await deleteSession();
  redirect("/login");
}
