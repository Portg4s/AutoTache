"use client";

import { useActionState, useMemo, useState } from "react";
import { ExternalLink, SlidersHorizontal, Star } from "lucide-react";
import { toggleOfferFavoriteAction, type OfferFavoriteActionState } from "@/app/favorites/actions";
import { updateOfferTrackingStatusAction, type OfferTrackingActionState } from "@/app/offer-tracking/actions";
import { offerTrackingStatusLabels, offerTrackingStatusStyles } from "@/lib/offerTracking";
import type { Offer, OfferWithFavorite } from "@/lib/supabase/types";

type OfferFilter = "review" | "favorites" | "all" | "rejected";

const decisionStyle: Record<Offer["decision"], string> = {
  Pertinent: "border-teal-200 bg-teal-50 text-teal-800 dark:border-teal-400/30 dark:bg-teal-400/10 dark:text-teal-200",
  "À vérifier": "border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-400/30 dark:bg-amber-400/10 dark:text-amber-200",
  Rejeté: "border-slate-200 bg-slate-100 text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300",
};

const emptyMessages: Record<OfferFilter, string> = {
  review: "Aucune offre à vérifier pour le moment.",
  favorites: "Aucune offre favorite pour le moment.",
  all: "Aucune offre synchronisée.",
  rejected: "Aucune offre rejetée.",
};

const initialFavoriteState: OfferFavoriteActionState = {};
const initialTrackingState: OfferTrackingActionState = {};

function canToggleFavorite(offer: OfferWithFavorite) {
  return offer.isFavorite || offer.decision === "À vérifier" || offer.decision === "Pertinent";
}

function formatDate(value?: string) {
  if (!value) {
    return "Non disponible";
  }

  return new Intl.DateTimeFormat("fr-FR", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function filterOffers(offers: OfferWithFavorite[], filter: OfferFilter) {
  if (filter === "review") {
    return offers.filter((offer) => offer.decision === "À vérifier");
  }

  if (filter === "favorites") {
    return offers.filter((offer) => offer.isFavorite);
  }

  if (filter === "rejected") {
    return offers.filter((offer) => offer.decision === "Rejeté");
  }

  return offers;
}

function FavoriteButton({ offer }: { offer: OfferWithFavorite }) {
  const [state, action, isPending] = useActionState(toggleOfferFavoriteAction, initialFavoriteState);

  if (!canToggleFavorite(offer)) {
    return null;
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <form action={action}>
        <input type="hidden" name="offerId" value={offer.id} />
        <button
          type="submit"
          disabled={isPending}
          aria-label={offer.isFavorite ? "Retirer des favoris" : "Ajouter aux favoris"}
          aria-pressed={offer.isFavorite}
          className={`flex h-11 min-w-11 items-center justify-center rounded-2xl border px-3 transition disabled:cursor-not-allowed disabled:opacity-60 ${
            offer.isFavorite
              ? "border-amber-300 bg-amber-50 text-amber-600 dark:border-amber-400/30 dark:bg-amber-400/10 dark:text-amber-300"
              : "border-slate-300 bg-white text-slate-500 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
          }`}
          title={offer.isFavorite ? "Retirer des favoris" : "Ajouter aux favoris"}
        >
          <Star aria-hidden="true" className={`h-5 w-5 ${offer.isFavorite ? "fill-amber-400" : ""}`} />
        </button>
      </form>
      {state.error ? <p className="max-w-36 text-right text-xs font-medium text-red-700 dark:text-red-300">{state.error}</p> : null}
      {state.success ? (
        <p className="max-w-36 text-right text-xs font-medium text-teal-700 dark:text-teal-300">{state.success}</p>
      ) : null}
    </div>
  );
}

function TrackingStatusControl({ offer }: { offer: OfferWithFavorite }) {
  const [state, action, isPending] = useActionState(updateOfferTrackingStatusAction, initialTrackingState);

  return (
    <form action={action} className="flex flex-col gap-1 sm:items-end">
      <input type="hidden" name="offerId" value={offer.id} />
      <label
        className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400"
        htmlFor={`tracking-${offer.id}`}
      >
        Suivi
      </label>
      <select
        id={`tracking-${offer.id}`}
        name="status"
        defaultValue={offer.trackingStatus ?? ""}
        disabled={isPending}
        onChange={(event) => event.currentTarget.form?.requestSubmit()}
        className="min-h-11 rounded-xl border border-slate-300 bg-white px-3 text-sm font-semibold text-slate-800 shadow-sm transition disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
      >
        <option value="" disabled>
          Non suivie
        </option>
        {Object.entries(offerTrackingStatusLabels).map(([status, label]) => (
          <option key={status} value={status}>
            {label}
          </option>
        ))}
      </select>
      {offer.trackingStatus ? (
        <span className={`w-fit rounded-full border px-3 py-1 text-xs font-semibold ${offerTrackingStatusStyles[offer.trackingStatus]}`}>
          {offerTrackingStatusLabels[offer.trackingStatus]}
        </span>
      ) : null}
      {state.error ? <p className="max-w-48 text-xs font-medium text-red-700 dark:text-red-300">{state.error}</p> : null}
      {state.success ? <p className="max-w-48 text-xs font-medium text-teal-700 dark:text-teal-300">{state.success}</p> : null}
    </form>
  );
}

export function OffersList({ offers }: { offers: OfferWithFavorite[] }) {
  const [activeFilter, setActiveFilter] = useState<OfferFilter>("review");
  const counts = useMemo(
    () => ({
      review: offers.filter((offer) => offer.decision === "À vérifier").length,
      favorites: offers.filter((offer) => offer.isFavorite).length,
      all: offers.length,
      rejected: offers.filter((offer) => offer.decision === "Rejeté").length,
    }),
    [offers],
  );
  const visibleFilters: { key: OfferFilter; label: string; count: number }[] = [
    { key: "review", label: "À vérifier", count: counts.review },
    { key: "favorites", label: "Favoris", count: counts.favorites },
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
                <div className="min-w-0">
                  <h2 className="text-base font-semibold text-slate-950 dark:text-slate-50">{offer.title}</h2>
                  <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{offer.company || "Entreprise non renseignée"}</p>
                </div>
                <div className="flex shrink-0 items-start gap-2">
                  <span
                    className={`rounded-full border px-3 py-1 text-xs font-semibold ${
                      decisionStyle[offer.decision]
                    }`}
                  >
                    {offer.decision}
                  </span>
                  <FavoriteButton offer={offer} />
                </div>
              </div>

              <div className="flex flex-wrap gap-2 text-xs font-medium text-slate-600 dark:text-slate-300">
                {offer.location ? <span className="rounded-full bg-slate-100 px-3 py-1 dark:bg-slate-800">{offer.location}</span> : null}
                {offer.contract_type ? (
                  <span className="rounded-full bg-slate-100 px-3 py-1 dark:bg-slate-800">{offer.contract_type}</span>
                ) : null}
                <span className="rounded-full bg-slate-100 px-3 py-1 dark:bg-slate-800">Score {offer.score_total}/100</span>
              </div>

              {offer.score_reason ? <p className="text-sm leading-6 text-slate-600 dark:text-slate-300">{offer.score_reason}</p> : null}

              <div className="flex flex-col gap-3 border-t border-slate-100 pt-3 text-sm dark:border-slate-800 sm:flex-row sm:items-end sm:justify-between">
                <div className="flex flex-col gap-3">
                  <span className="text-slate-500 dark:text-slate-400">Vu le {formatDate(offer.last_seen_at)}</span>
                  <TrackingStatusControl offer={offer} />
                </div>
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
