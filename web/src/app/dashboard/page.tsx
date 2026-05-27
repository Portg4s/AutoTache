import Link from "next/link";
import { redirect } from "next/navigation";
import { logoutAction } from "@/app/actions";
import { OffersList } from "./OffersList";
import { createClient } from "@/lib/supabase/server";
import type { Offer, Run } from "@/lib/supabase/types";

export const dynamic = "force-dynamic";

function formatDate(value?: string) {
  if (!value) {
    return "Non disponible";
  }

  return new Intl.DateTimeFormat("fr-FR", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function sortOffers(offers: Offer[]) {
  return [...offers].sort((first, second) => {
    if (first.decision === "À vérifier" && second.decision !== "À vérifier") {
      return -1;
    }
    if (first.decision !== "À vérifier" && second.decision === "À vérifier") {
      return 1;
    }

    return second.score_total - first.score_total;
  });
}

function SummaryCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p>
    </div>
  );
}

function RunSummary({ run }: { run: Run | null }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm sm:col-span-2">
      <p className="text-sm text-slate-500">Dernier run synchronisé</p>
      <p className="mt-2 text-lg font-semibold text-slate-950">
        {run ? formatDate(run.triggered_at) : "Aucun run"}
      </p>
      <div className="mt-3 flex flex-wrap gap-2 text-xs font-medium text-slate-600">
        <span className="rounded-full bg-slate-100 px-3 py-1">
          {run?.status === "completed" ? "Synchronisé" : run?.status ?? "Non disponible"}
        </span>
        {run ? <span className="rounded-full bg-slate-100 px-3 py-1">{run.trigger_type}</span> : null}
        {run ? <span className="rounded-full bg-slate-100 px-3 py-1">{run.total_raw} brutes</span> : null}
        {run ? (
          <span className="rounded-full bg-slate-100 px-3 py-1">{run.total_relevant} pertinentes</span>
        ) : null}
        {run ? <span className="rounded-full bg-slate-100 px-3 py-1">{run.total_new} nouvelles</span> : null}
        {run ? (
          <span className="rounded-full bg-slate-100 px-3 py-1">{run.total_generated_cvs} CV</span>
        ) : null}
      </div>
    </div>
  );
}

export default async function DashboardPage() {
  const supabase = await createClient();
  const { data } = await supabase.auth.getClaims();

  if (!data?.claims) {
    redirect("/login");
  }

  const [offersResult, runsResult, applicationsCountResult] = await Promise.all([
    supabase
      .from("offers")
      .select("id,title,company,location,contract_type,decision,score_total,score_reason,offer_url,last_seen_at"),
    supabase
      .from("runs")
      .select("triggered_at,trigger_type,status,total_raw,total_relevant,total_new,total_generated_cvs")
      .order("triggered_at", { ascending: false })
      .limit(1),
    supabase.from("applications").select("id", { count: "exact", head: true }),
  ]);

  const offers = sortOffers((offersResult.data ?? []) as Offer[]);
  const latestRun = ((runsResult.data?.[0] ?? null) as Run | null);
  const applicationsCount = applicationsCountResult.count ?? 0;
  const hasLoadError = Boolean(offersResult.error || runsResult.error || applicationsCountResult.error);
  const toReview = offers.filter((offer) => offer.decision === "À vérifier").length;
  const rejected = offers.filter((offer) => offer.decision === "Rejeté").length;

  return (
    <main className="min-h-svh bg-slate-100">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex w-full max-w-5xl flex-col gap-4 px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xl font-semibold text-slate-950">AutoTache</p>
            <p className="text-sm text-slate-500">Suivi de recherche</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Link
              href="/dashboard"
              aria-current="page"
              className="flex h-10 items-center rounded-lg bg-slate-950 px-3 text-sm font-semibold text-white"
            >
              Offres
            </Link>
            <Link
              href="/candidatures"
              className="flex h-10 items-center rounded-lg border border-slate-300 bg-white px-3 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
            >
              Candidatures
              {applicationsCount > 0 ? (
                <span className="ml-2 rounded-full bg-teal-50 px-2 py-0.5 text-xs font-semibold text-teal-700">
                  {applicationsCount}
                </span>
              ) : null}
            </Link>
            <form action={logoutAction}>
              <button
                type="submit"
                className="h-10 rounded-lg border border-slate-300 bg-white px-3 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
              >
                Se déconnecter
              </button>
            </form>
          </div>
        </div>
      </header>

      <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-4 py-6">
        <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <SummaryCard label="Offres totales" value={offers.length} />
          <SummaryCard label="À vérifier" value={toReview} />
          <SummaryCard label="Rejeté" value={rejected} />
          <RunSummary run={latestRun} />
        </section>

        {hasLoadError ? (
          <section className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            Impossible de charger toutes les données pour le moment.
          </section>
        ) : null}

        <OffersList offers={offers} />
      </div>
    </main>
  );
}
