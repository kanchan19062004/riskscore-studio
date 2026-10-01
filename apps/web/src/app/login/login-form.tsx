"use client";

import { useActionState } from "react";

import { login } from "@/app/actions/auth";
import { Field, FormMessage, SubmitButton } from "@/components/auth/field";

export function LoginForm() {
  const [state, formAction, pending] = useActionState(login, undefined);

  return (
    <form action={formAction} className="flex flex-col gap-4">
      <FormMessage message={state?.message} />
      <Field label="Email" name="email" type="email" autoComplete="email" required />
      <Field
        label="Password"
        name="password"
        type="password"
        autoComplete="current-password"
        required
      />
      <SubmitButton pending={pending}>Log in</SubmitButton>
    </form>
  );
}
