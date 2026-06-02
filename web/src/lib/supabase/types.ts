export const APPLICATION_STATUSES = [
  "new",
  "to_review",
  "to_apply",
  "applied",
  "interview",
  "rejected",
  "archived",
] as const;

export type ApplicationStatus = (typeof APPLICATION_STATUSES)[number];
export const OFFER_TRACKING_STATUSES = ["to_review", "interested", "to_apply", "archived"] as const;

export type OfferTrackingStatus = (typeof OFFER_TRACKING_STATUSES)[number];
export type OfferDecision = "Pertinent" | "À vérifier" | "Rejeté";
export type RunStatus = "running" | "completed" | "failed";
export type RunTriggerType = "scheduled" | "manual" | "local";

export type Offer = {
  id: string;
  title: string;
  company: string;
  location: string;
  contract_type: string;
  decision: OfferDecision;
  score_total: number;
  score_reason: string;
  offer_url: string;
  last_seen_at: string;
};

export type Run = {
  triggered_at: string;
  trigger_type: RunTriggerType;
  status: RunStatus;
  total_raw: number;
  total_relevant: number;
  total_new: number;
  total_generated_cvs: number;
};

export type Application = {
  id: string;
  offer_id: string;
  status: ApplicationStatus;
  favorite: boolean;
  notes: string;
  applied_at: string | null;
  created_at: string;
  updated_at: string;
};

export type OfferFavorite = {
  owner_id: string;
  offer_id: string;
  created_at: string;
};

export type OfferFavoriteInsert = Pick<OfferFavorite, "owner_id" | "offer_id">;

export type OfferTracking = {
  owner_id: string;
  offer_id: string;
  status: OfferTrackingStatus;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type OfferTrackingInsert = Pick<OfferTracking, "owner_id" | "offer_id" | "status"> &
  Partial<Pick<OfferTracking, "notes">>;

export type OfferTrackingUpdate = Partial<Pick<OfferTracking, "status" | "notes">>;

export type CandidateDocument = {
  id: string;
  offer_id: string;
  pdf_storage_path: string | null;
  docx_storage_path: string | null;
  created_at: string;
  updated_at: string;
};

export type OfferWithFavorite = Offer & {
  isFavorite: boolean;
  trackingStatus: OfferTrackingStatus | null;
};

export type ApplicationWithOffer = Application & {
  offer: Pick<
    Offer,
    "id" | "title" | "company" | "location" | "contract_type" | "decision" | "score_total" | "offer_url"
  >;
  document: {
    id: string;
    hasPdf: boolean;
  } | null;
};

export type Database = {
  public: {
    Tables: {
      offers: {
        Row: Offer;
        Insert: never;
        Update: never;
        Relationships: [];
      };
      runs: {
        Row: Run;
        Insert: never;
        Update: never;
        Relationships: [];
      };
      applications: {
        Row: Application;
        Insert: never;
        Update: Partial<Pick<Application, "status" | "favorite" | "notes" | "applied_at">>;
        Relationships: [];
      };
      offer_favorites: {
        Row: OfferFavorite;
        Insert: OfferFavoriteInsert;
        Update: never;
        Relationships: [];
      };
      offer_tracking: {
        Row: OfferTracking;
        Insert: OfferTrackingInsert;
        Update: OfferTrackingUpdate;
        Relationships: [];
      };
      candidate_documents: {
        Row: CandidateDocument;
        Insert: never;
        Update: never;
        Relationships: [];
      };
    };
    Views: Record<string, never>;
    Functions: Record<string, never>;
  };
};
