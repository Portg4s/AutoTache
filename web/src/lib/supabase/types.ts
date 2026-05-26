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

export type Database = {
  public: {
    Tables: {
      offers: {
        Row: Offer;
      };
      runs: {
        Row: Run;
      };
    };
  };
};
