"use client";

import { useActionState } from "react";

import { trainModel } from "@/app/actions/models";

export function TrainButton() {
  const [state, formAction, pending] = useActionState(trainModel, undefined);

  return (
    <form action={formAction} className="flex flex-col items-end gap-2">
      <button
        type="submit"
        disabled={pending}
        className="rounded-md bg-emerald-500 px-4 py-2 text-sm font-medium text-zinc-950 hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {pending ? "Training… (a few seconds)" : "Train new model"}
      </button>
      {state && (
        <p role="status" className={`text-sm ${state.ok ? "text-emerald-400" : "text-red-400"}`}>
          {state.message}
        </p>
      )}
    </form>
  );
}
