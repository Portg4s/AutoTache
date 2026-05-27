import Link from "next/link";
import { redirect } from "next/navigation";
import { logoutAction } from "@/app/actions";
import { ApplicationCard } from "./ApplicationCard";
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
              hasDocx: Boolean(document.docx_storage_path),
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
          .select("id,offer_id,pdf_storage_path,docx_storage_path,created_at,updated_at")
          .in("offer_id", offerIds)
      : { data: [], error: null };

  const applications = mapApplicationRows(applicationRows, (documentsResult.data ?? []) as CandidateDocument[]);
  const hasLoadError = Boolean(applicationResult.error || documentsResult.error);
  const resolvedSearchParams = await searchParams;
  const hasDocumentError = resolvedSearchParams?.document === "unavailable";

  return (
    <main className="min-h-svh bg-slate-100">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex w-full max-w-5xl flex-col gap-4 px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xl font-semibold text-slate-950">AutoTache</p>
            <p className="text-sm text-slate-500">Suivi des candidatures</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Link
              href="/dashboard"
              className="flex h-10 items-center rounded-lg border border-slate-300 bg-white px-3 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
            >
              Offres
            </Link>
            <Link
              href="/candidatures"
              aria-current="page"
              className="flex h-10 items-center rounded-lg bg-slate-950 px-3 text-sm font-semibold text-white"
            >
              Candidatures
            </Link>
            <form action={logoutAction}>
              <button
                type="submit"
                className="h-10 rounded-lg border border-slate-300 bg-white px-3 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
              >
                Se déconnecter
              </button>
            </form>
          </div>
        </div>
      </header>

      <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-4 py-6">
        <section className="flex flex-col gap-2">
          <h1 className="text-lg font-semibold text-slate-950">Candidatures</h1>
          <p className="text-sm leading-6 text-slate-600">
            {applications.length} candidature{applications.length > 1 ? "s" : ""} suivie
            {applications.length > 1 ? "s" : ""}.
          </p>
        </section>

        {hasDocumentError ? (
          <section className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
            Document indisponible pour le moment.
          </section>
        ) : null}

        {hasLoadError ? (
          <section className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            Impossible de charger toutes les candidatures pour le moment.
          </section>
        ) : null}

        {applications.length === 0 ? (
          <section className="rounded-lg border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">
            Aucune candidature à suivre pour le moment.
          </section>
        ) : (
          <section className="flex flex-col gap-4">
            {applications.map((application) => (
              <ApplicationCard key={application.id} application={application} />
            ))}
          </section>
        )}
      </div>
    </main>
  );
}
