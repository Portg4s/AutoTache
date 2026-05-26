"use client";

import { useActionState } from "react";
import { loginAction } from "@/app/actions";

export function LoginForm() {
  const [state, formAction, isPending] = useActionState(loginAction, {});

  return (
    <form action={formAction} className="mt-8 flex flex-col gap-5">
      <label className="flex flex-col gap-2 text-sm font-medium text-slate-700">
        E-mail
        <input
          name="email"
          type="email"
          autoComplete="email"
          required
          className="h-12 rounded-lg border border-slate-300 bg-white px-4 text-base text-slate-950 outline-none transition focus:border-teal-600 focus:ring-3 focus:ring-teal-100"
        />
      </label>
      <label className="flex flex-col gap-2 text-sm font-medium text-slate-700">
        Mot de passe
        <input
          name="password"
          type="password"
          autoComplete="current-password"
          required
          className="h-12 rounded-lg border border-slate-300 bg-white px-4 text-base text-slate-950 outline-none transition focus:border-teal-600 focus:ring-3 focus:ring-teal-100"
        />
      </label>
      {state.error ? (
        <p className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {state.error}
        </p>
      ) : null}
      <button
        type="submit"
        disabled={isPending}
        className="h-12 rounded-lg bg-slate-950 px-5 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
      >
        {isPending ? "Connexion..." : "Se connecter"}
      </button>
    </form>
  );
}
