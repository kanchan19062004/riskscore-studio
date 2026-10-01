"use client";

import type { InputHTMLAttributes } from "react";
import { useActionState, useState } from "react";

import { scoreTransaction } from "@/app/actions/scores";
import { FormMessage } from "@/components/auth/field";
import { ScoreResultCard } from "@/components/scores/score-result";
import type { ScoreOptions } from "@/lib/api";

const TYPICAL = {
  amount: "42.50",
  merchant_category: "grocery",
  channel: "pos",
  hour: "14",
  account_age_days: "900",
  avg_amount_30d: "48",
  txn_count_24h: "2",
  failed_attempts_24h: "0",
  is_new_device: false,
  country_mismatch: false,
};

const RISKY = {
  amount: "9200",
  merchant_category: "crypto",
  channel: "online",
  hour: "3",
  account_age_days: "8",
  avg_amount_30d: "180",
  txn_count_24h: "11",
  failed_attempts_24h: "4",
  is_new_device: true,
  country_mismatch: true,
};

type Preset = typeof TYPICAL;

export function ScoreForm({ options }: { options: ScoreOptions }) {
  const [preset, setPreset] = useState<Preset>(TYPICAL);
  const [state, formAction, pending] = useActionState(scoreTransaction, undefined);
  const errors = state && !state.ok ? state.fieldErrors : undefined;

  return (
    <div className="grid gap-8 lg:grid-cols-2">
      <div>
        <div className="mb-4 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setPreset(TYPICAL)}
            className="rounded-md border border-zinc-700 px-3 py-1.5 text-sm hover:bg-zinc-800"
          >
            Typical grocery
          </button>
          <button
            type="button"
            onClick={() => setPreset(RISKY)}
            className="rounded-md border border-zinc-700 px-3 py-1.5 text-sm hover:bg-zinc-800"
          >
            Risky crypto at 3am
          </button>
        </div>

        <form key={JSON.stringify(preset)} action={formAction} className="grid gap-4 sm:grid-cols-2">
          {state && !state.ok && (
            <div className="sm:col-span-2">
              <FormMessage message={state.message} />
            </div>
          )}
          <NumberField label="Amount" name="amount" defaultValue={preset.amount} error={errors?.amount} step="0.01" />
          <NumberField
            label="30-day average amount"
            name="avg_amount_30d"
            defaultValue={preset.avg_amount_30d}
            error={errors?.avg_amount_30d}
            step="0.01"
          />
          <SelectField
            label="Merchant category"
            name="merchant_category"
            defaultValue={preset.merchant_category}
            options={options.merchant_categories}
          />
          <SelectField label="Channel" name="channel" defaultValue={preset.channel} options={options.channels} />
          <NumberField label="Hour (0–23)" name="hour" defaultValue={preset.hour} error={errors?.hour} min={0} max={23} />
          <NumberField
            label="Account age (days, blank = missing)"
            name="account_age_days"
            defaultValue={preset.account_age_days}
            error={errors?.account_age_days}
          />
          <NumberField
            label="Transactions in last 24h"
            name="txn_count_24h"
            defaultValue={preset.txn_count_24h}
            error={errors?.txn_count_24h}
            min={0}
          />
          <NumberField
            label="Failed attempts in last 24h"
            name="failed_attempts_24h"
            defaultValue={preset.failed_attempts_24h}
            error={errors?.failed_attempts_24h}
            min={0}
          />
          <label className="flex items-center gap-2 text-sm text-zinc-300">
            <input type="checkbox" name="is_new_device" defaultChecked={preset.is_new_device} className="accent-emerald-500" />
            New device
          </label>
          <label className="flex items-center gap-2 text-sm text-zinc-300">
            <input
              type="checkbox"
              name="country_mismatch"
              defaultChecked={preset.country_mismatch}
              className="accent-emerald-500"
            />
            Country mismatch
          </label>
          <div className="sm:col-span-2">
            <button
              type="submit"
              disabled={pending}
              className="rounded-md bg-emerald-500 px-4 py-2 font-medium text-zinc-950 hover:bg-emerald-400 disabled:opacity-60"
            >
              {pending ? "Scoring…" : "Score transaction"}
            </button>
          </div>
        </form>
      </div>

      <div>
        {state?.ok ? (
          <ScoreResultCard score={state.score} />
        ) : (
          <p className="rounded-lg border border-dashed border-zinc-700 p-6 text-sm text-zinc-500">
            Submit a transaction to see LOW / MEDIUM / HIGH. Score the same payload twice to see the
            Redis cache hit.
          </p>
        )}
      </div>
    </div>
  );
}

function NumberField({
  label,
  name,
  defaultValue,
  error,
  ...rest
}: {
  label: string;
  name: string;
  defaultValue: string;
  error?: string;
} & InputHTMLAttributes<HTMLInputElement>) {
  return (
    <label className="flex flex-col gap-1.5 text-sm">
      <span className="text-zinc-300">{label}</span>
      <input
        name={name}
        type="number"
        defaultValue={defaultValue}
        className="rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-zinc-100 outline-none focus:border-emerald-500"
        {...rest}
      />
      {error && <span className="text-red-400">{error}</span>}
    </label>
  );
}

function SelectField({
  label,
  name,
  defaultValue,
  options,
}: {
  label: string;
  name: string;
  defaultValue: string;
  options: string[];
}) {
  return (
    <label className="flex flex-col gap-1.5 text-sm">
      <span className="text-zinc-300">{label}</span>
      <select
        name={name}
        defaultValue={defaultValue}
        className="rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-zinc-100 outline-none focus:border-emerald-500"
      >
        {options.map((option) => (
          <option key={option} value={option}>
            {option.replaceAll("_", " ")}
          </option>
        ))}
      </select>
    </label>
  );
}
