import { APPLICATION_STATUSES, type ApplicationStatus } from "@/lib/supabase/types";

export const MAX_APPLICATION_NOTES_LENGTH = 2000;

export const applicationStatusLabels: Record<ApplicationStatus, string> = {
  new: "Nouvelle",
  to_review: "À examiner",
  to_apply: "À candidater",
  applied: "Candidature envoyée",
  interview: "Entretien",
  rejected: "Refusée",
  archived: "Archivée",
};

export const applicationStatusStyles: Record<ApplicationStatus, string> = {
  new: "border-slate-200 bg-slate-100 text-slate-700",
  to_review: "border-amber-200 bg-amber-50 text-amber-800",
  to_apply: "border-sky-200 bg-sky-50 text-sky-800",
  applied: "border-teal-200 bg-teal-50 text-teal-800",
  interview: "border-indigo-200 bg-indigo-50 text-indigo-800",
  rejected: "border-red-200 bg-red-50 text-red-700",
  archived: "border-slate-300 bg-white text-slate-600",
};

export function isApplicationStatus(value: string): value is ApplicationStatus {
  return APPLICATION_STATUSES.includes(value as ApplicationStatus);
}

export function normalizeApplicationNotes(value: FormDataEntryValue | null) {
  const notes = String(value ?? "").trim();

  if (notes.length > MAX_APPLICATION_NOTES_LENGTH) {
    return {
      error: `Les notes sont limitées à ${MAX_APPLICATION_NOTES_LENGTH} caractères.`,
      notes: "",
    };
  }

  return { notes };
}

export function parseAppliedAtDate(value: FormDataEntryValue | null) {
  const rawValue = String(value ?? "").trim();

  if (!rawValue) {
    return { appliedAt: null };
  }

  if (!/^\d{4}-\d{2}-\d{2}$/.test(rawValue)) {
    return { error: "La date de candidature est invalide.", appliedAt: null };
  }

  const date = new Date(`${rawValue}T00:00:00.000Z`);

  if (Number.isNaN(date.getTime())) {
    return { error: "La date de candidature est invalide.", appliedAt: null };
  }

  if (date.toISOString().slice(0, 10) !== rawValue) {
    return { error: "La date de candidature est invalide.", appliedAt: null };
  }

  return { appliedAt: date.toISOString() };
}

export function formatDateInputValue(value: string | null) {
  if (!value) {
    return "";
  }

  return value.slice(0, 10);
}
