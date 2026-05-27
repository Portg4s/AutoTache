"use server";

import { revalidatePath } from "next/cache";
import { createClient } from "@/lib/supabase/server";
import {
  isApplicationStatus,
  normalizeApplicationNotes,
  parseAppliedAtDate,
} from "@/lib/applications";
import type { ApplicationStatus } from "@/lib/supabase/types";

export type ApplicationActionState = {
  error?: string;
  success?: string;
};

const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function getApplicationId(formData: FormData) {
  const applicationId = String(formData.get("applicationId") ?? "").trim();

  if (!uuidPattern.test(applicationId)) {
    return { error: "Candidature introuvable.", applicationId: "" };
  }

  return { applicationId };
}

async function getAuthenticatedSupabase() {
  const supabase = await createClient();
  const { data } = await supabase.auth.getClaims();

  if (!data?.claims) {
    return { error: "Connectez-vous pour modifier vos candidatures.", supabase: null };
  }

  return { supabase };
}

function refreshApplicationViews() {
  revalidatePath("/candidatures");
  revalidatePath("/dashboard");
}

export async function toggleFavoriteAction(
  _previousState: ApplicationActionState,
  formData: FormData,
): Promise<ApplicationActionState> {
  const { applicationId, error: idError } = getApplicationId(formData);
  if (idError) {
    return { error: idError };
  }

  const { supabase, error: authError } = await getAuthenticatedSupabase();
  if (!supabase) {
    return { error: authError };
  }

  const { data, error: readError } = await supabase
    .from("applications")
    .select("favorite")
    .eq("id", applicationId)
    .single();

  if (readError || !data) {
    return { error: "Impossible de mettre à jour cette candidature." };
  }

  const { data: updatedApplication, error: updateError } = await supabase
    .from("applications")
    .update({ favorite: !data.favorite })
    .eq("id", applicationId)
    .select("id")
    .maybeSingle();

  if (updateError || !updatedApplication) {
    return { error: "Impossible de mettre à jour cette candidature." };
  }

  refreshApplicationViews();
  return { success: data.favorite ? "Favori retiré." : "Candidature ajoutée aux favoris." };
}

export async function updateStatusAction(
  _previousState: ApplicationActionState,
  formData: FormData,
): Promise<ApplicationActionState> {
  const { applicationId, error: idError } = getApplicationId(formData);
  if (idError) {
    return { error: idError };
  }

  const status = String(formData.get("status") ?? "").trim();
  if (!isApplicationStatus(status)) {
    return { error: "Statut de candidature invalide." };
  }

  const { supabase, error: authError } = await getAuthenticatedSupabase();
  if (!supabase) {
    return { error: authError };
  }

  const updatePayload: { status: ApplicationStatus; applied_at?: string } = { status };

  if (status === "applied") {
    const { data, error: readError } = await supabase
      .from("applications")
      .select("applied_at")
      .eq("id", applicationId)
      .single();

    if (readError || !data) {
      return { error: "Impossible de mettre à jour cette candidature." };
    }

    if (!data.applied_at) {
      updatePayload.applied_at = new Date().toISOString();
    }
  }

  const { data: updatedApplication, error: updateError } = await supabase
    .from("applications")
    .update(updatePayload)
    .eq("id", applicationId)
    .select("id")
    .maybeSingle();

  if (updateError || !updatedApplication) {
    return { error: "Impossible de mettre à jour cette candidature." };
  }

  refreshApplicationViews();
  return { success: "Statut mis à jour." };
}

export async function saveNotesAction(
  _previousState: ApplicationActionState,
  formData: FormData,
): Promise<ApplicationActionState> {
  const { applicationId, error: idError } = getApplicationId(formData);
  if (idError) {
    return { error: idError };
  }

  const { notes, error: notesError } = normalizeApplicationNotes(formData.get("notes"));
  if (notesError) {
    return { error: notesError };
  }

  const { supabase, error: authError } = await getAuthenticatedSupabase();
  if (!supabase) {
    return { error: authError };
  }

  const { data: updatedApplication, error: updateError } = await supabase
    .from("applications")
    .update({ notes })
    .eq("id", applicationId)
    .select("id")
    .maybeSingle();

  if (updateError || !updatedApplication) {
    return { error: "Impossible d'enregistrer les notes." };
  }

  refreshApplicationViews();
  return { success: "Notes enregistrées." };
}

export async function saveAppliedAtAction(
  _previousState: ApplicationActionState,
  formData: FormData,
): Promise<ApplicationActionState> {
  const { applicationId, error: idError } = getApplicationId(formData);
  if (idError) {
    return { error: idError };
  }

  const intent = String(formData.get("intent") ?? "save");
  const { appliedAt, error: dateError } =
    intent === "clear" ? { appliedAt: null } : parseAppliedAtDate(formData.get("appliedAt"));

  if (dateError) {
    return { error: dateError };
  }

  const { supabase, error: authError } = await getAuthenticatedSupabase();
  if (!supabase) {
    return { error: authError };
  }

  const { data: updatedApplication, error: updateError } = await supabase
    .from("applications")
    .update({ applied_at: appliedAt })
    .eq("id", applicationId)
    .select("id")
    .maybeSingle();

  if (updateError || !updatedApplication) {
    return { error: "Impossible d'enregistrer la date." };
  }

  refreshApplicationViews();
  return { success: appliedAt ? "Date enregistrée." : "Date effacée." };
}
