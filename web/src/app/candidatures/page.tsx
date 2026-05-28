import { redirect } from "next/navigation";
import { Star } from "lucide-react";
import { ApplicationCard } from "./ApplicationCard";
import { AppHeader } from "@/components/app/AppHeader";
import { MobileBottomNavigation } from "@/components/app/MobileBottomNavigation";
import { createClient } from "@/lib/supabase/server";
import type { Application, ApplicationWithOffer, CandidateDocument, Offer } from "@/lib/supabase/types";

export const dynamic = "force-dynamic";

type ApplicationQueryRow = Application & {
  offers:
    | Pick<Offer, "id" | "title" | "company" | "location" | "contract_type" | "decision" | "score_total" | "offer_url">
    | Pick<Offer, "id" | "title" | "company" | "location" | "contract_type" | "decision" | "score_total" | "offer_url">[]
    | null;
};

type CandidaturesPageProps = {
  searchParams?: Promise<{
    document?: string;
  }>;
};

function getOffer(row: ApplicationQueryRow) {
  return Array.isArray(row.offers) ? row.offers[0] : row.offers;
}

function mapApplicationRows(
  applications: ApplicationQueryRow[],
  documents: CandidateDocument[],
): ApplicationWithOffer[] {
  const documentsByOfferId = new Map(documents.map((document) => [document.offer_id, document]));

  return applications.flatMap((application) => {
    const offer = getOffer(application);

    if (!offer) {
      return [];
    }

    const document = documentsByOfferId.get(application.offer_id) ?? null;

    return [
      {
        id: application.id,
        offer_id: application.offer_id,
        status: application.status,
        favorite: application.favorite,
        notes: application.notes,
        applied_at: application.applied_at,
        created_at: application.created_at,
        updated_at: application.updated_at,
        offer,
        document: document
          ? {
              id: document.id,
              hasPdf: Boolean(document.pdf_storage_path),
            }
          : null,
      },
    ];
  });
}

export default async function CandidaturesPage({ searchParams }: CandidaturesPageProps) {
  const supabase = await createClient();
  const { data } = await supabase.auth.getClaims();

  if (!data?.claims) {
    redirect("/login");
  }

  const applicationResult = await supabase
    .from("applications")
    .select(
      `
        id,
        offer_id,
        status,
        favorite,
        notes,
        applied_at,
        created_at,
        updated_at,
        offers!applications_offer_owner_fk (
          id,
          title,
          company,
          location,
          contract_type,
          decision,
          score_total,
          offer_url
        )
      `,
    )
    .order("favorite", { ascending: false })
    .order("updated_at", { ascending: false });

  const applicationRows = (applicationResult.data ?? []) as ApplicationQueryRow[];
  const offerIds = applicationRows.map((application) => application.offer_id);
  const documentsResult =
    offerIds.length > 0
      ? await supabase
          .from("candidate_documents")
          .select("id,offer_id,pdf_storage_path,created_at,updated_at")
          .in("offer_id", offerIds)
      : { data: [], error: null };

  const applications = mapApplicationRows(applicationRows, (documentsResult.data ?? []) as CandidateDocument[]);
  const favoriteApplications = applications.filter((application) => application.favorite);
  const otherApplications = applications.filter((application) => !application.favorite);
  const hasLoadError = Boolean(applicationResult.error || documentsResult.error);
  const resolvedSearchParams = await searchParams;
  const hasDocumentError = resolvedSearchParams?.document === "unavailable";

  return (
    <main className="min-h-svh">
      <AppHeader subtitle="Suivi des candidatures" active="applications" applicationsCount={applications.length} />

      <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-4 pb-28 pt-6 md:pb-8">
        <section className="flex flex-col gap-2">
          <h1 className="text-lg font-semibold text-slate-950 dark:text-slate-50">Candidatures</h1>
          <p className="text-sm leading-6 text-slate-600 dark:text-slate-400">
            {applications.length} candidature{applications.length > 1 ? "s" : ""} suivie
            {applications.length > 1 ? "s" : ""}.
          </p>
        </section>

        {hasDocumentError ? (
          <section className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800 dark:border-amber-400/30 dark:bg-amber-400/10 dark:text-amber-200">
            Document indisponible pour le moment.
          </section>
        ) : null}

        {hasLoadError ? (
          <section className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-200">
            Impossible de charger toutes les candidatures pour le moment.
          </section>
        ) : null}

        {applications.length === 0 ? (
          <section className="rounded-2xl border border-slate-200/80 bg-white p-6 text-sm text-slate-600 shadow-sm shadow-slate-200/60 dark:border-slate-800 dark:bg-slate-900/90 dark:text-slate-300 dark:shadow-none">
            Aucune candidature à suivre pour le moment.
          </section>
        ) : (
          <div className="flex flex-col gap-6">
            {favoriteApplications.length > 0 ? (
              <section className="flex flex-col gap-3">
                <div className="flex items-center justify-between gap-3">
                  <h2 className="flex items-center gap-2 text-base font-semibold text-slate-950 dark:text-slate-50">
                    <Star aria-hidden="true" className="h-4 w-4 fill-amber-400 text-amber-500" />
                    Favoris
                  </h2>
                  <span className="text-sm text-slate-500 dark:text-slate-400">{favoriteApplications.length}</span>
                </div>
                <div className="flex flex-col gap-3">
                  {favoriteApplications.map((application) => (
                    <ApplicationCard key={application.id} application={application} />
                  ))}
                </div>
              </section>
            ) : null}

            {otherApplications.length > 0 ? (
              <section className="flex flex-col gap-3">
                <div className="flex items-center justify-between gap-3">
                  <h2 className="text-base font-semibold text-slate-950 dark:text-slate-50">Autres candidatures</h2>
                  <span className="text-sm text-slate-500 dark:text-slate-400">{otherApplications.length}</span>
                </div>
                <div className="flex flex-col gap-3">
                  {otherApplications.map((application) => (
                    <ApplicationCard key={application.id} application={application} />
                  ))}
                </div>
              </section>
            ) : null}
          </div>
        )}
      </div>
      <MobileBottomNavigation active="applications" applicationsCount={applications.length} />
    </main>
  );
}
