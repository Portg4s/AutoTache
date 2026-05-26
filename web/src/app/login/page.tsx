import { redirect } from "next/navigation";
import { LoginForm } from "./LoginForm";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

export default async function LoginPage() {
  const supabase = await createClient();
  const { data } = await supabase.auth.getClaims();

  if (data?.claims) {
    redirect("/dashboard");
  }

  return (
    <main className="flex min-h-svh items-center justify-center bg-slate-100 px-4 py-10">
      <section className="w-full max-w-sm rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-medium text-teal-700">AutoTache</p>
        <h1 className="mt-2 text-3xl font-semibold text-slate-950">Suivi de recherche</h1>
        <p className="mt-3 text-sm leading-6 text-slate-600">
          Connectez-vous avec le compte Supabase déjà créé pour consulter les offres synchronisées.
        </p>
        <LoginForm />
      </section>
    </main>
  );
}
