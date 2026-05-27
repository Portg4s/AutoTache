"use client";

import { useMemo, useState } from "react";
import type { Offer } from "@/lib/supabase/types";

type OfferFilter = "review" | "relevant" | "all" | "rejected";

const decisionStyle: Record<Offer["decision"], string> = {
  Pertinent: "border-teal-200 bg-teal-50 text-teal-800",
  "À vérifier": "border-amber-200 bg-amber-50 text-amber-800",
  Rejeté: "border-slate-200 bg-slate-100 text-slate-700",
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
    <section className="flex flex-col gap-3">
      <div className="flex flex-col gap-3">
        <h1 className="text-lg font-semibold text-slate-950">Offres scorées</h1>
        <div className="flex flex-wrap gap-2" aria-label="Filtres des offres">
          {visibleFilters.map((filter) => {
            const isActive = activeFilter === filter.key;

            return (
              <button
                key={filter.key}
                type="button"
                onClick={() => setActiveFilter(filter.key)}
                aria-pressed={isActive}
                className={`flex min-h-11 items-center gap-2 rounded-lg border px-3 text-sm font-semibold transition ${
                  isActive
                    ? "border-slate-950 bg-slate-950 text-white"
                    : "border-slate-300 bg-white text-slate-700 hover:bg-slate-50"
                }`}
              >
                <span>{filter.label}</span>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs ${
                    isActive ? "bg-white/15 text-white" : "bg-slate-100 text-slate-600"
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
        <div className="rounded-lg border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">
          {emptyMessages[activeFilter]}
        </div>
      ) : (
        visibleOffers.map((offer) => (
          <article key={offer.id} className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
            <div className="flex flex-col gap-3">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h2 className="text-base font-semibold text-slate-950">{offer.title}</h2>
                  <p className="mt-1 text-sm text-slate-600">{offer.company || "Entreprise non renseignée"}</p>
                </div>
                <span
                  className={`shrink-0 rounded-full border px-3 py-1 text-xs font-semibold ${
                    decisionStyle[offer.decision]
                  }`}
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
