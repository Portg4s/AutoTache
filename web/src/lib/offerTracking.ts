import { OFFER_TRACKING_STATUSES, type OfferTrackingStatus } from "@/lib/supabase/types";

export const offerTrackingStatusLabels: Record<OfferTrackingStatus, string> = {
  to_review: "À examiner",
  interested: "Intéressante",
  to_apply: "À candidater",
  archived: "Archivée",
};

export const offerTrackingStatusStyles: Record<OfferTrackingStatus, string> = {
  to_review: "border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-400/30 dark:bg-amber-400/10 dark:text-amber-200",
  interested: "border-teal-200 bg-teal-50 text-teal-800 dark:border-teal-400/30 dark:bg-teal-400/10 dark:text-teal-200",
  to_apply: "border-sky-200 bg-sky-50 text-sky-800 dark:border-sky-400/30 dark:bg-sky-400/10 dark:text-sky-200",
  archived: "border-slate-300 bg-white text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300",
};

export function isOfferTrackingStatus(value: string): value is OfferTrackingStatus {
  return OFFER_TRACKING_STATUSES.includes(value as OfferTrackingStatus);
}
