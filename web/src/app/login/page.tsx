import { redirect } from "next/navigation";
import { BriefcaseBusiness } from "lucide-react";
import { LoginForm } from "./LoginForm";
import { ThemeToggle } from "@/components/theme/ThemeToggle";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

export default async function LoginPage() {
  const supabase = await createClient();
  const { data } = await supabase.auth.getClaims();

  if (data?.claims) {
    redirect("/dashboard");
  }

  return (
    <main className="flex min-h-svh items-center justify-center px-4 py-10">
      <section className="w-full max-w-sm rounded-3xl border border-slate-200/80 bg-white p-6 shadow-xl shadow-slate-200/70 dark:border-slate-800 dark:bg-slate-900/90 dark:shadow-none">
        <div className="flex justify-end">
          <ThemeToggle />
        </div>
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-950 text-white shadow-sm dark:bg-teal-400 dark:text-slate-950">
            <BriefcaseBusiness aria-hidden="true" className="h-6 w-6" />
          </div>
          <div>
            <p className="text-sm font-semibold text-teal-700 dark:text-teal-300">AutoTache</p>
            <h1 className="text-2xl font-semibold tracking-tight text-slate-950 dark:text-slate-50">Suivi de recherche</h1>
          </div>
        </div>
        <p className="mt-5 text-sm leading-6 text-slate-600 dark:text-slate-300">
          Connectez-vous avec le compte Supabase déjà créé pour consulter vos offres et candidatures.
        </p>
        <LoginForm />
      </section>
    </main>
  );
}
