"use server";

import { revalidatePath } from "next/cache";
import { createClient } from "@/lib/supabase/server";
import type { OfferDecision } from "@/lib/supabase/types";

export type OfferFavoriteActionState = {
  error?: string;
  success?: string;
};

const uuidPattern =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const eligibleDecisions = new Set<OfferDecision>(["À vérifier", "Pertinent"]);
const favoriteUpdateError = "Impossible de mettre à jour les favoris de cette offre.";

function getOfferId(formData: FormData) {
  const offerId = String(formData.get("offerId") ?? "").trim();

  if (!uuidPattern.test(offerId)) {
    return { error: favoriteUpdateError, offerId: "" };
  }

  return { offerId };
}

function getAuthenticatedUserId(claims: { sub?: unknown } | null | undefined) {
  const userId = typeof claims?.sub === "string" ? claims.sub : "";

  if (!uuidPattern.test(userId)) {
    return "";
  }

  return userId;
}

function refreshFavoriteViews() {
  revalidatePath("/dashboard");
  revalidatePath("/candidatures");
}

export async function toggleOfferFavoriteAction(
  _previousState: OfferFavoriteActionState,
  formData: FormData,
): Promise<OfferFavoriteActionState> {
  const { offerId, error: offerIdError } = getOfferId(formData);
  if (offerIdError) {
    return { error: offerIdError };
  }

  const supabase = await createClient();
  const { data: claimsData } = await supabase.auth.getClaims();
  const authenticatedUserId = getAuthenticatedUserId(claimsData?.claims);

  if (!authenticatedUserId) {
    return { error: favoriteUpdateError };
  }

  const { data: offer, error: offerError } = await supabase
    .from("offers")
    .select("id,decision")
    .eq("id", offerId)
    .maybeSingle();

  if (offerError) {
    return { error: favoriteUpdateError };
  }

  if (!offer) {
    return { error: favoriteUpdateError };
  }

  const { data: existingFavorite, error: existingError } = await supabase
    .from("offer_favorites")
    .select("offer_id")
    .eq("owner_id", authenticatedUserId)
    .eq("offer_id", offerId)
    .maybeSingle();

  if (existingError) {
    return { error: favoriteUpdateError };
  }

  if (existingFavorite) {
    const { data: deletedFavorite, error: deleteError } = await supabase
      .from("offer_favorites")
      .delete()
      .eq("owner_id", authenticatedUserId)
      .eq("offer_id", offerId)
      .select("offer_id")
      .maybeSingle();

    if (deleteError) {
      return { error: favoriteUpdateError };
    }

    if (!deletedFavorite) {
      return { error: favoriteUpdateError };
    }

    refreshFavoriteViews();
    return { success: "Offre retirée des favoris." };
  }

  if (!eligibleDecisions.has(offer.decision)) {
    return { error: favoriteUpdateError };
  }

  const { data: createdFavorite, error: insertError } = await supabase
    .from("offer_favorites")
    .insert({
      owner_id: authenticatedUserId,
      offer_id: offerId,
    })
    .select("offer_id")
    .maybeSingle();

  if (insertError) {
    return { error: favoriteUpdateError };
  }

  if (!createdFavorite) {
    return { error: favoriteUpdateError };
  }

  refreshFavoriteViews();
  return { success: "Offre ajoutée aux favoris." };
}
