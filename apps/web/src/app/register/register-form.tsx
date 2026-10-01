"use client";

import { useActionState } from "react";

import { register } from "@/app/actions/auth";
import { Field, FormMessage, SubmitButton } from "@/components/auth/field";

export function RegisterForm() {
  const [state, formAction, pending] = useActionState(register, undefined);
  const errors = state?.fieldErrors;

  return (
    <form action={formAction} className="flex flex-col gap-4">
      <FormMessage message={state?.message} />
      <Field
        label="Full name"
        name="full_name"
        autoComplete="name"
        required
        minLength={2}
        error={errors?.full_name}
      />
      <Field
        label="Email"
        name="email"
        type="email"
        autoComplete="email"
        required
        error={errors?.email}
      />
      <Field
        label="Password"
        name="password"
        type="password"
        autoComplete="new-password"
        required
        minLength={8}
        placeholder="8+ characters, letters and numbers"
        error={errors?.password}
      />
      <SubmitButton pending={pending}>Create account</SubmitButton>
    </form>
  );
}
