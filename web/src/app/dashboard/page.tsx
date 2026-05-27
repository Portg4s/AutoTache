import Link from "next/link";
import { redirect } from "next/navigation";
import { logoutAction } from "@/app/actions";
import { createClient } from "@/lib/supabase/server";
import type { Offer, Run } from "@/lib/supabase/types";

export const dynamic = "force-dynamic";

const decisionStyle: Record<Offer["decision"], string> = {
  Pertinent: "border-teal-200 bg-teal-50 text-teal-800",
  "À vérifier": "border-amber-200 bg-amber-50 text-amber-800",
  Rejeté: "border-slate-200 bg-slate-100 text-slate-700",
};

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

        <section className="flex flex-col gap-3">
          <h1 className="text-lg font-semibold text-slate-950">Offres scorées</h1>
          {offers.length === 0 ? (
            <div className="rounded-lg border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">
              Aucune offre synchronisée pour le moment.
            </div>
          ) : (
            offers.map((offer) => (
              <article key={offer.id} className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
                <div className="flex flex-col gap-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h2 className="text-base font-semibold text-slate-950">{offer.title}</h2>
                      <p className="mt-1 text-sm text-slate-600">{offer.company || "Entreprise non renseignée"}</p>
                    </div>
                    <span
                      className={`shrink-0 rounded-full border px-3 py-1 text-xs font-semibold ${decisionStyle[offer.decision]}`}
                    >
                      {offer.decision}
                    </span>
                  </div>

                  <div className="flex flex-wrap gap-2 text-xs font-medium text-slate-600">
                    {offer.location ? <span className="rounded-full bg-slate-100 px-3 py-1">{offer.location}</span> : null}
                    {offer.contract_type ? (
                      <span className="rounded-full bg-slate-100 px-3 py-1">{offer.contract_type}</span>
                    ) : null}
                    <span className="rounded-full bg-slate-100 px-3 py-1">Score {offer.score_total}/100</span>
                  </div>

                  {offer.score_reason ? <p className="text-sm leading-6 text-slate-600">{offer.score_reason}</p> : null}

                  <div className="flex items-center justify-between gap-3 border-t border-slate-100 pt-3 text-sm">
                    <span className="text-slate-500">Vu le {formatDate(offer.last_seen_at)}</span>
                    {offer.offer_url ? (
                      <a
                        href={offer.offer_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="font-semibold text-teal-700 hover:text-teal-900"
                      >
                        Voir l’offre
                      </a>
                    ) : null}
                  </div>
                </div>
              </article>
            ))
          )}
        </section>
      </div>
    </main>
  );
}
