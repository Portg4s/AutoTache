import { redirect } from "next/navigation";
import { BriefcaseBusiness, CheckCircle2, SlidersHorizontal, XCircle } from "lucide-react";
import { OffersList } from "./OffersList";
import { AppHeader } from "@/components/app/AppHeader";
import { MobileBottomNavigation } from "@/components/app/MobileBottomNavigation";
import { createClient } from "@/lib/supabase/server";
import type { Offer, OfferFavorite, OfferTracking, OfferWithFavorite, Run } from "@/lib/supabase/types";

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

function OffersMetrics({ total, toReview, rejected }: { total: number; toReview: number; rejected: number }) {
  const metrics = [
    { label: "Total", value: total, icon: BriefcaseBusiness, className: "text-slate-500 dark:text-slate-400" },
    { label: "À vérifier", value: toReview, icon: CheckCircle2, className: "text-amber-600 dark:text-amber-300" },
    { label: "Rejetées", value: rejected, icon: XCircle, className: "text-slate-500 dark:text-slate-400" },
  ];

  return (
    <section className="grid grid-cols-3 overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-sm shadow-slate-200/60 dark:border-slate-800 dark:bg-slate-900/90 dark:shadow-none">
      {metrics.map((metric, index) => {
        const Icon = metric.icon;

        return (
          <div
            key={metric.label}
            className={`flex min-w-0 flex-col items-center justify-center gap-1 px-2 py-3 text-center ${
              index > 0 ? "border-l border-slate-200/80 dark:border-slate-800" : ""
            }`}
          >
            <Icon aria-hidden="true" className={`h-4 w-4 ${metric.className}`} />
            <p className="text-2xl font-semibold leading-none tracking-tight text-slate-950 dark:text-slate-50">
              {metric.value}
            </p>
            <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
              {metric.label}
            </p>
          </div>
        );
      })}
    </section>
  );
}

function RunSummary({ run }: { run: Run | null }) {
  return (
    <div className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm shadow-slate-200/60 dark:border-slate-800 dark:bg-slate-900/90 dark:shadow-none">
      <div className="flex items-center gap-2 text-sm font-medium text-slate-500">
        <SlidersHorizontal aria-hidden="true" className="h-4 w-4" />
        Dernier run synchronisé
      </div>
      <p className="mt-2 text-base font-semibold text-slate-950 dark:text-slate-50">
        {run ? formatDate(run.triggered_at) : "Aucun run"}
      </p>
      <div className="mt-3 flex flex-wrap gap-2 text-xs font-medium text-slate-600 dark:text-slate-300">
        <span className="rounded-full bg-slate-100 px-3 py-1 dark:bg-slate-800">
          {run?.status === "completed" ? "Synchronisé" : run?.status ?? "Non disponible"}
        </span>
        {run ? <span className="rounded-full bg-slate-100 px-3 py-1 dark:bg-slate-800">{run.trigger_type}</span> : null}
        {run ? <span className="rounded-full bg-slate-100 px-3 py-1 dark:bg-slate-800">{run.total_raw} brutes</span> : null}
        {run ? (
          <span className="rounded-full bg-slate-100 px-3 py-1 dark:bg-slate-800">{run.total_relevant} pertinentes</span>
        ) : null}
        {run ? <span className="rounded-full bg-slate-100 px-3 py-1 dark:bg-slate-800">{run.total_new} nouvelles</span> : null}
        {run ? (
          <span className="rounded-full bg-slate-100 px-3 py-1 dark:bg-slate-800">{run.total_generated_cvs} CV</span>
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

  const [offersResult, runsResult, favoritesResult, trackingResult, applicationsCountResult] = await Promise.all([
    supabase
      .from("offers")
      .select("id,title,company,location,contract_type,decision,score_total,score_reason,offer_url,last_seen_at"),
    supabase
      .from("runs")
      .select("triggered_at,trigger_type,status,total_raw,total_relevant,total_new,total_generated_cvs")
      .order("triggered_at", { ascending: false })
      .limit(1),
    supabase.from("offer_favorites").select("offer_id"),
    supabase.from("offer_tracking").select("offer_id,status"),
    supabase.from("applications").select("id", { count: "exact", head: true }),
  ]);

  const offers = sortOffers((offersResult.data ?? []) as Offer[]);
  const favoriteOfferIds = new Set(
    ((favoritesResult.data ?? []) as Pick<OfferFavorite, "offer_id">[]).map((favorite) => favorite.offer_id),
  );
  const trackingByOfferId = new Map(
    ((trackingResult.data ?? []) as Pick<OfferTracking, "offer_id" | "status">[]).map((tracking) => [
      tracking.offer_id,
      tracking.status,
    ]),
  );
  const offersWithFavorites: OfferWithFavorite[] = offers.map((offer) => ({
    ...offer,
    isFavorite: favoriteOfferIds.has(offer.id),
    trackingStatus: trackingByOfferId.get(offer.id) ?? null,
  }));
  const latestRun = ((runsResult.data?.[0] ?? null) as Run | null);
  const applicationsCount = applicationsCountResult.count ?? 0;
  const hasLoadError = Boolean(
    offersResult.error || runsResult.error || favoritesResult.error || trackingResult.error || applicationsCountResult.error,
  );
  const toReview = offers.filter((offer) => offer.decision === "À vérifier").length;
  const rejected = offers.filter((offer) => offer.decision === "Rejeté").length;

  return (
    <main className="min-h-svh">
      <AppHeader subtitle="Recherche d'emploi" active="offers" applicationsCount={applicationsCount} />

      <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-4 pb-28 pt-6 md:pb-8">
        <section className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
          <OffersMetrics total={offers.length} toReview={toReview} rejected={rejected} />
          <RunSummary run={latestRun} />
        </section>

        {hasLoadError ? (
          <section className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-200">
            Impossible de charger toutes les données pour le moment.
          </section>
        ) : null}

        <OffersList offers={offersWithFavorites} />
      </div>
      <MobileBottomNavigation active="offers" applicationsCount={applicationsCount} />
    </main>
  );
}
