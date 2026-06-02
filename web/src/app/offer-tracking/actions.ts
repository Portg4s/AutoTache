"use server";

import { revalidatePath } from "next/cache";
import { createClient } from "@/lib/supabase/server";
import { isOfferTrackingStatus } from "@/lib/offerTracking";

export type OfferTrackingActionState = {
  error?: string;
  success?: string;
};

const uuidPattern =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const trackingUpdateError = "Impossible de mettre à jour le suivi de cette offre.";

function getOfferId(formData: FormData) {
  const offerId = String(formData.get("offerId") ?? "").trim();

  if (!uuidPattern.test(offerId)) {
    return { error: trackingUpdateError, offerId: "" };
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

function refreshOfferTrackingViews() {
  revalidatePath("/dashboard");
}

export async function updateOfferTrackingStatusAction(
  _previousState: OfferTrackingActionState,
  formData: FormData,
): Promise<OfferTrackingActionState> {
  const { offerId, error: offerIdError } = getOfferId(formData);
  if (offerIdError) {
    return { error: offerIdError };
  }

  const status = String(formData.get("status") ?? "").trim();
  if (!isOfferTrackingStatus(status)) {
    return { error: "Statut de suivi invalide." };
  }

  const supabase = await createClient();
  const { data: claimsData } = await supabase.auth.getClaims();
  const authenticatedUserId = getAuthenticatedUserId(claimsData?.claims);

  if (!authenticatedUserId) {
    return { error: trackingUpdateError };
  }

  const { data: existingTracking, error: existingError } = await supabase
    .from("offer_tracking")
    .select("offer_id")
    .eq("owner_id", authenticatedUserId)
    .eq("offer_id", offerId)
    .maybeSingle();

  if (existingError) {
    return { error: trackingUpdateError };
  }

  if (existingTracking) {
    const { data: updatedTracking, error: updateError } = await supabase
      .from("offer_tracking")
      .update({ status })
      .eq("owner_id", authenticatedUserId)
      .eq("offer_id", offerId)
      .select("offer_id")
      .maybeSingle();

    if (updateError || !updatedTracking) {
      return { error: trackingUpdateError };
    }

    refreshOfferTrackingViews();
    return { success: "Suivi mis à jour." };
  }

  const { data: createdTracking, error: insertError } = await supabase
    .from("offer_tracking")
    .insert({
      owner_id: authenticatedUserId,
      offer_id: offerId,
      status,
    })
    .select("offer_id")
    .maybeSingle();

  if (insertError || !createdTracking) {
    return { error: trackingUpdateError };
  }

  refreshOfferTrackingViews();
  return { success: "Suivi mis à jour." };
}
