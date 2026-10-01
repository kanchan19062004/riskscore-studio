import type { InputHTMLAttributes } from "react";

type FieldProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  name: string;
  error?: string;
};

export function Field({ label, name, error, ...inputProps }: FieldProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={name} className="text-sm text-zinc-300">
        {label}
      </label>
      <input
        id={name}
        name={name}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? `${name}-error` : undefined}
        className="rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-zinc-100 outline-none focus:border-emerald-500 aria-[invalid=true]:border-red-500"
        {...inputProps}
      />
      {error && (
        <p id={`${name}-error`} className="text-sm text-red-400">
          {error}
        </p>
      )}
    </div>
  );
}

export function FormMessage({ message }: { message?: string }) {
  if (!message) return null;
  return (
    <p role="alert" className="rounded-md border border-red-900 bg-red-950/50 px-3 py-2 text-sm text-red-300">
      {message}
    </p>
  );
}

export function SubmitButton({ pending, children }: { pending: boolean; children: string }) {
  return (
    <button
      type="submit"
      disabled={pending}
      className="rounded-md bg-emerald-500 px-4 py-2 font-medium text-zinc-950 transition-colors hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-60"
    >
      {pending ? "Please wait…" : children}
    </button>
  );
}
