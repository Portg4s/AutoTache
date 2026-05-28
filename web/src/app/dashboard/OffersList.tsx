"use client";

import { useMemo, useState } from "react";
import { ExternalLink, SlidersHorizontal } from "lucide-react";
import type { Offer } from "@/lib/supabase/types";

type OfferFilter = "review" | "relevant" | "all" | "rejected";

const decisionStyle: Record<Offer["decision"], string> = {
  Pertinent: "border-teal-200 bg-teal-50 text-teal-800 dark:border-teal-400/30 dark:bg-teal-400/10 dark:text-teal-200",
  "À vérifier": "border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-400/30 dark:bg-amber-400/10 dark:text-amber-200",
  Rejeté: "border-slate-200 bg-slate-100 text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300",
};

const emptyMessages: Record<OfferFilter, string> = {
  review: "Aucune offre à vérifier pour le moment.",
  relevant: "Aucune offre pertinente pour le moment.",
  all: "Aucune offre synchronisée.",
  rejected: "Aucune offre rejetée.",
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

function filterOffers(offers: Offer[], filter: OfferFilter) {
  if (filter === "review") {
    return offers.filter((offer) => offer.decision === "À vérifier");
  }

  if (filter === "relevant") {
    return offers.filter((offer) => offer.decision === "Pertinent");
  }

  if (filter === "rejected") {
    return offers.filter((offer) => offer.decision === "Rejeté");
  }

  return offers;
}

export function OffersList({ offers }: { offers: Offer[] }) {
  const [activeFilter, setActiveFilter] = useState<OfferFilter>("review");
  const counts = useMemo(
    () => ({
      review: offers.filter((offer) => offer.decision === "À vérifier").length,
      relevant: offers.filter((offer) => offer.decision === "Pertinent").length,
      all: offers.length,
      rejected: offers.filter((offer) => offer.decision === "Rejeté").length,
    }),
    [offers],
  );
  const visibleFilters: { key: OfferFilter; label: string; count: number }[] = [
    { key: "review", label: "À vérifier", count: counts.review },
    ...(counts.relevant > 0 ? [{ key: "relevant" as const, label: "Pertinentes", count: counts.relevant }] : []),
    { key: "all", label: "Toutes", count: counts.all },
    { key: "rejected", label: "Rejetées", count: counts.rejected },
  ];
  const visibleOffers = filterOffers(offers, activeFilter);

  return (
    <section className="flex flex-col gap-4">
      <div className="flex flex-col gap-3">
        <div className="flex items-center gap-2">
          <SlidersHorizontal aria-hidden="true" className="h-5 w-5 text-teal-700 dark:text-teal-300" />
          <h1 className="text-lg font-semibold text-slate-950 dark:text-slate-50">Offres scorées</h1>
        </div>
        <div className="flex flex-wrap gap-2 rounded-2xl border border-slate-200/80 bg-white p-2 shadow-sm shadow-slate-200/60 dark:border-slate-800 dark:bg-slate-900/90 dark:shadow-none" aria-label="Filtres des offres">
          {visibleFilters.map((filter) => {
            const isActive = activeFilter === filter.key;

            return (
              <button
                key={filter.key}
                type="button"
                onClick={() => setActiveFilter(filter.key)}
                aria-pressed={isActive}
                className={`flex min-h-11 items-center gap-2 rounded-2xl border px-3 text-sm font-semibold transition ${
                  isActive
                    ? "border-slate-950 bg-slate-950 text-white dark:border-teal-400 dark:bg-teal-400 dark:text-slate-950"
                    : "border-transparent bg-white text-slate-700 hover:bg-slate-50 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
                }`}
              >
                <span>{filter.label}</span>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs ${
                    isActive ? "bg-white/15 text-white dark:bg-slate-950/15 dark:text-slate-950" : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300"
                  }`}
                >
                  {filter.count}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {visibleOffers.length === 0 ? (
        <div className="rounded-2xl border border-slate-200/80 bg-white p-6 text-sm text-slate-600 shadow-sm shadow-slate-200/60 dark:border-slate-800 dark:bg-slate-900/90 dark:text-slate-300 dark:shadow-none">
          {emptyMessages[activeFilter]}
        </div>
      ) : (
        visibleOffers.map((offer) => (
          <article key={offer.id} className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm shadow-slate-200/60 dark:border-slate-800 dark:bg-slate-900/90 dark:shadow-none">
            <div className="flex flex-col gap-3">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h2 className="text-base font-semibold text-slate-950 dark:text-slate-50">{offer.title}</h2>
                  <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{offer.company || "Entreprise non renseignée"}</p>
                </div>
                <span
                  className={`shrink-0 rounded-full border px-3 py-1 text-xs font-semibold ${
                    decisionStyle[offer.decision]
                  }`}
                >
                  {offer.decision}
                </span>
              </div>

              <div className="flex flex-wrap gap-2 text-xs font-medium text-slate-600 dark:text-slate-300">
                {offer.location ? <span className="rounded-full bg-slate-100 px-3 py-1 dark:bg-slate-800">{offer.location}</span> : null}
                {offer.contract_type ? (
                  <span className="rounded-full bg-slate-100 px-3 py-1 dark:bg-slate-800">{offer.contract_type}</span>
                ) : null}
                <span className="rounded-full bg-slate-100 px-3 py-1 dark:bg-slate-800">Score {offer.score_total}/100</span>
              </div>

              {offer.score_reason ? <p className="text-sm leading-6 text-slate-600 dark:text-slate-300">{offer.score_reason}</p> : null}

              <div className="flex items-center justify-between gap-3 border-t border-slate-100 pt-3 text-sm dark:border-slate-800">
                <span className="text-slate-500 dark:text-slate-400">Vu le {formatDate(offer.last_seen_at)}</span>
                {offer.offer_url ? (
                  <a
                    href={offer.offer_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1.5 font-semibold text-teal-700 hover:text-teal-900 dark:text-teal-300 dark:hover:text-teal-200"
                  >
                    <ExternalLink aria-hidden="true" className="h-4 w-4" />
                    Voir l&apos;offre
                  </a>
                ) : null}
              </div>
            </div>
          </article>
        ))
      )}
    </section>
  );
}
