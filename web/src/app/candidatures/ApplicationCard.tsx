"use client";

import { useActionState, useState } from "react";
import {
  saveAppliedAtAction,
  saveNotesAction,
  toggleFavoriteAction,
  updateStatusAction,
  type ApplicationActionState,
} from "./actions";
import {
  applicationStatusLabels,
  applicationStatusStyles,
  formatDateInputValue,
  MAX_APPLICATION_NOTES_LENGTH,
} from "@/lib/applications";
import { APPLICATION_STATUSES, type ApplicationWithOffer } from "@/lib/supabase/types";

const initialState: ApplicationActionState = {};

function ActionMessage({ state }: { state: ApplicationActionState }) {
  if (state.error) {
    return <p className="text-sm font-medium text-red-700">{state.error}</p>;
  }

  if (state.success) {
    return <p className="text-sm font-medium text-teal-700">{state.success}</p>;
  }

  return null;
}

function formatDate(value: string | null) {
  if (!value) {
    return "Non renseignée";
  }

  return new Intl.DateTimeFormat("fr-FR", {
    dateStyle: "medium",
  }).format(new Date(value));
}

export function ApplicationCard({ application }: { application: ApplicationWithOffer }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [favoriteState, favoriteAction, isFavoritePending] = useActionState(toggleFavoriteAction, initialState);
  const [statusState, statusAction, isStatusPending] = useActionState(updateStatusAction, initialState);
  const [notesState, notesAction, isNotesPending] = useActionState(saveNotesAction, initialState);
  const [dateState, dateAction, isDatePending] = useActionState(saveAppliedAtAction, initialState);
  const document = application.document;
  const detailsId = `application-details-${application.id}`;

  return (
    <article className="rounded-lg border border-slate-200 bg-white p-3 shadow-sm">
      <div className="flex flex-col gap-3">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h2 className="text-base font-semibold text-slate-950">{application.offer.title}</h2>
            <p className="mt-1 text-sm text-slate-600">
              {application.offer.company || "Entreprise non renseignée"}
            </p>
          </div>
          <form action={favoriteAction}>
            <input type="hidden" name="applicationId" value={application.id} />
            <button
              type="submit"
              disabled={isFavoritePending}
              aria-pressed={application.favorite}
              className={`h-11 min-w-11 rounded-lg border px-3 text-lg font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${
                application.favorite
                  ? "border-amber-300 bg-amber-50 text-amber-700"
                  : "border-slate-300 bg-white text-slate-500 hover:bg-slate-50"
              }`}
              title={application.favorite ? "Retirer des favoris" : "Ajouter aux favoris"}
            >
              ★
            </button>
          </form>
        </div>

        <div className="flex flex-wrap gap-1.5 text-xs font-medium text-slate-600">
          {application.offer.location ? (
            <span className="rounded-full bg-slate-100 px-3 py-1">{application.offer.location}</span>
          ) : null}
          {application.offer.contract_type ? (
            <span className="rounded-full bg-slate-100 px-3 py-1">{application.offer.contract_type}</span>
          ) : null}
          <span className="rounded-full bg-slate-100 px-3 py-1">Score {application.offer.score_total}/100</span>
          <span className="rounded-full bg-slate-100 px-3 py-1">{application.offer.decision}</span>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-2">
          <span
            className={`rounded-full border px-3 py-1 text-xs font-semibold ${
              applicationStatusStyles[application.status]
            }`}
          >
            {applicationStatusLabels[application.status]}
          </span>
          <button
            type="button"
            aria-expanded={isExpanded}
            aria-controls={detailsId}
            onClick={() => setIsExpanded((current) => !current)}
            className="h-11 rounded-lg border border-slate-300 bg-white px-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
          >
            {isExpanded ? "Masquer les détails" : "Voir les détails"}
          </button>
        </div>

        <ActionMessage state={favoriteState} />

        {isExpanded ? (
          <div id={detailsId} className="flex flex-col gap-4 border-t border-slate-100 bg-slate-50/60 pt-4">
            <div className="text-sm text-slate-500">Date: {formatDate(application.applied_at)}</div>

            <form action={statusAction} className="flex flex-col gap-2">
              <input type="hidden" name="applicationId" value={application.id} />
              <label className="flex flex-col gap-2 text-sm font-medium text-slate-700">
                Statut
                <select
                  key={`${application.id}-status-${application.status}`}
                  name="status"
                  defaultValue={application.status}
                  className="h-12 rounded-lg border border-slate-300 bg-white px-3 text-base text-slate-950 outline-none transition focus:border-teal-600 focus:ring-3 focus:ring-teal-100"
                >
                  {APPLICATION_STATUSES.map((status) => (
                    <option key={status} value={status}>
                      {applicationStatusLabels[status]}
                    </option>
                  ))}
                </select>
              </label>
              <button
                type="submit"
                disabled={isStatusPending}
                className="h-11 rounded-lg bg-slate-950 px-4 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
              >
                {isStatusPending ? "Mise à jour..." : "Mettre à jour le statut"}
              </button>
              <ActionMessage state={statusState} />
            </form>

            <form action={dateAction} className="flex flex-col gap-2">
              <input type="hidden" name="applicationId" value={application.id} />
              <label className="flex flex-col gap-2 text-sm font-medium text-slate-700">
                Date de candidature
                <input
                  key={`${application.id}-applied-at-${application.applied_at ?? "empty"}`}
                  name="appliedAt"
                  type="date"
                  defaultValue={formatDateInputValue(application.applied_at)}
                  className="h-12 rounded-lg border border-slate-300 bg-white px-3 text-base text-slate-950 outline-none transition focus:border-teal-600 focus:ring-3 focus:ring-teal-100"
                />
              </label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="submit"
                  name="intent"
                  value="save"
                  disabled={isDatePending}
                  className="h-11 rounded-lg border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isDatePending ? "Sauvegarde..." : "Enregistrer"}
                </button>
                <button
                  type="submit"
                  name="intent"
                  value="clear"
                  disabled={isDatePending}
                  className="h-11 rounded-lg border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  Vider
                </button>
              </div>
              <ActionMessage state={dateState} />
            </form>

            <form action={notesAction} className="flex flex-col gap-2">
              <input type="hidden" name="applicationId" value={application.id} />
              <label className="flex flex-col gap-2 text-sm font-medium text-slate-700">
                Notes
                <textarea
                  key={`${application.id}-notes-${application.notes}`}
                  name="notes"
                  defaultValue={application.notes}
                  maxLength={MAX_APPLICATION_NOTES_LENGTH}
                  rows={4}
                  className="rounded-lg border border-slate-300 bg-white px-3 py-3 text-base text-slate-950 outline-none transition focus:border-teal-600 focus:ring-3 focus:ring-teal-100"
                />
              </label>
              <button
                type="submit"
                disabled={isNotesPending}
                className="h-11 rounded-lg bg-teal-700 px-4 text-sm font-semibold text-white transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:bg-slate-400"
              >
                {isNotesPending ? "Enregistrement..." : "Enregistrer les notes"}
              </button>
              <ActionMessage state={notesState} />
            </form>

            <div className="flex flex-col gap-2">
              <div className="grid grid-cols-2 gap-2">
                {document?.hasPdf ? (
                  <a
                    href={`/candidatures/documents/${document.id}?type=pdf`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex h-11 items-center justify-center rounded-lg border border-slate-300 bg-white px-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
                  >
                    Ouvrir PDF
                  </a>
                ) : (
                  <span className="flex h-11 items-center justify-center rounded-lg border border-slate-200 bg-white px-3 text-sm font-medium text-slate-400">
                    PDF absent
                  </span>
                )}
                {document?.hasDocx ? (
                  <a
                    href={`/candidatures/documents/${document.id}?type=docx`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex h-11 items-center justify-center rounded-lg border border-slate-300 bg-white px-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
                  >
                    Ouvrir DOCX
                  </a>
                ) : (
                  <span className="flex h-11 items-center justify-center rounded-lg border border-slate-200 bg-white px-3 text-sm font-medium text-slate-400">
                    DOCX absent
                  </span>
                )}
              </div>
              {application.offer.offer_url ? (
                <a
                  href={application.offer.offer_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm font-semibold text-teal-700 hover:text-teal-900"
                >
                  Voir l&apos;offre d&apos;origine
                </a>
              ) : null}
            </div>
          </div>
        ) : null}
      </div>
    </article>
  );
}
