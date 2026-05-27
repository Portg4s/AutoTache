import { redirect } from "next/navigation";
import { NextResponse, type NextRequest } from "next/server";
import { createClient } from "@/lib/supabase/server";

const signedUrlExpirationSeconds = 60;
const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

type DocumentKind = "pdf" | "docx";

function isDocumentKind(value: string | null): value is DocumentKind {
  return value === "pdf" || value === "docx";
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ documentId: string }> },
) {
  const { documentId } = await params;
  const kind = request.nextUrl.searchParams.get("type");

  if (!uuidPattern.test(documentId) || !isDocumentKind(kind)) {
    redirect("/candidatures?document=unavailable");
  }

  const supabase = await createClient();
  const { data: authData } = await supabase.auth.getClaims();

  if (!authData?.claims) {
    redirect("/login");
  }

  const { data: document, error: documentError } = await supabase
    .from("candidate_documents")
    .select("pdf_storage_path,docx_storage_path")
    .eq("id", documentId)
    .single();

  if (documentError || !document) {
    redirect("/candidatures?document=unavailable");
  }

  const storagePath = kind === "pdf" ? document.pdf_storage_path : document.docx_storage_path;

  if (!storagePath) {
    redirect("/candidatures?document=unavailable");
  }

  const { data: signedUrlData, error: signedUrlError } = await supabase.storage
    .from("candidate-documents")
    .createSignedUrl(storagePath, signedUrlExpirationSeconds);

  if (signedUrlError || !signedUrlData?.signedUrl) {
    redirect("/candidatures?document=unavailable");
  }

  return NextResponse.redirect(signedUrlData.signedUrl);
}
