"""Synchronize one AutoTache run to Supabase."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from autotache_jobs.scoring import DECISION_REJECTED, DECISION_RELEVANT, DECISION_REVIEW
from autotache_jobs.supabase.settings import SupabaseSettings


PDF_MIME_TYPE = "application/pdf"
DOCX_MIME_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
VALID_SCORING_DECISIONS = {DECISION_RELEVANT, DECISION_REVIEW, DECISION_REJECTED}


@dataclass(frozen=True)
class SupabaseSyncResult:
    enabled: bool
    success: bool
    run_synced: bool = False
    offers_synced_count: int = 0
    applications_synced_count: int = 0
    documents_synced_count: int = 0
    error: str | None = None


def sync_run_to_supabase(
    *,
    client: Any,
    settings: SupabaseSettings,
    summary: dict[str, Any],
    scored_offers: list[dict[str, Any]],
    new_offers: list[dict[str, Any]],
    generated_docx_paths: list[Path],
    generated_pdf_paths: list[Path],
    candidate_pack_paths: list[Path],
    bucket_name: str,
) -> SupabaseSyncResult:
    """Publish scored offers, run history, and generated candidate packs."""

    _validate_candidate_pack_inputs(new_offers, generated_docx_paths, generated_pdf_paths, candidate_pack_paths)
    _validate_scored_offer_decisions(scored_offers)

    now = datetime.now(timezone.utc).isoformat()
    offers_payload = [_offer_payload(offer, settings.owner_id, now) for offer in scored_offers if offer.get("id_offre")]
    offers_data = _execute(
        client.table("offers")
        .upsert(offers_payload, on_conflict="owner_id,source,external_offer_id")
        .execute()
    ) if offers_payload else []
    offer_ids = _offer_id_map(offers_data)

    if len(offer_ids) < len(offers_payload):
        offer_ids.update(_fetch_offer_ids(client, settings.owner_id, offers_payload))

    applications_synced = 0
    documents_synced = 0
    for offer, docx_path, pdf_path, _pack_path in zip(
        new_offers, generated_docx_paths, generated_pdf_paths, candidate_pack_paths
    ):
        key = _offer_key(settings.owner_id, offer)
        offer_uuid = offer_ids.get(key)
        if not offer_uuid:
            raise RuntimeError("Identifiant Supabase introuvable pour une candidature.")

        if _insert_application_if_missing(client, settings.owner_id, offer_uuid):
            applications_synced += 1

        pdf_storage_path = _storage_path(settings.owner_id, offer_uuid, pdf_path)
        docx_storage_path = _storage_path(settings.owner_id, offer_uuid, docx_path)
        _upload_file(client, bucket_name, pdf_storage_path, pdf_path, PDF_MIME_TYPE)
        _upload_file(client, bucket_name, docx_storage_path, docx_path, DOCX_MIME_TYPE)
        _upsert_candidate_document(
            client,
            owner_id=settings.owner_id,
            offer_id=offer_uuid,
            pdf_storage_path=pdf_storage_path,
            docx_storage_path=docx_storage_path,
            docx_path=docx_path,
            pdf_path=pdf_path,
            generated_at=now,
        )
        documents_synced += 1

    _sync_run(client, settings, summary)

    return SupabaseSyncResult(
        enabled=True,
        success=True,
        run_synced=True,
        offers_synced_count=len(offers_payload),
        applications_synced_count=applications_synced,
        documents_synced_count=documents_synced,
    )


def disabled_result() -> SupabaseSyncResult:
    return SupabaseSyncResult(enabled=False, success=False)


def error_result(error: str) -> SupabaseSyncResult:
    return SupabaseSyncResult(enabled=True, success=False, error=error)


def _offer_payload(offer: dict[str, Any], owner_id: str, now: str) -> dict[str, Any]:
    return {
        "owner_id": owner_id,
        "external_offer_id": str(offer.get("id_offre") or ""),
        "source": str(offer.get("source") or ""),
        "title": str(offer.get("titre") or ""),
        "company": str(offer.get("entreprise") or ""),
        "location": str(offer.get("localisation") or ""),
        "contract_type": str(offer.get("type_contrat") or ""),
        "description": str(offer.get("description") or ""),
        "technologies": _technologies(offer.get("technologies")),
        "offer_url": str(offer.get("url_offre") or ""),
        "decision": str(offer.get("decision") or ""),
        "score_total": int(offer.get("score_total") or 0),
        "score_reason": str(offer.get("score_reason") or ""),
        "score_details": offer.get("score_details") if isinstance(offer.get("score_details"), dict) else {},
        "last_seen_at": now,
    }


def _validate_candidate_pack_inputs(
    new_offers: list[dict[str, Any]],
    generated_docx_paths: list[Path],
    generated_pdf_paths: list[Path],
    candidate_pack_paths: list[Path],
) -> None:
    has_candidate_documents = bool(generated_docx_paths or generated_pdf_paths or candidate_pack_paths)
    if not has_candidate_documents:
        return

    expected_count = len(new_offers)
    lengths = {
        "new_offers": expected_count,
        "generated_docx_paths": len(generated_docx_paths),
        "generated_pdf_paths": len(generated_pdf_paths),
        "candidate_pack_paths": len(candidate_pack_paths),
    }
    if len(set(lengths.values())) != 1:
        raise ValueError("Packs candidature incoherents: nombres de documents incompatibles.")

    for docx_path, pdf_path, pack_path in zip(generated_docx_paths, generated_pdf_paths, candidate_pack_paths):
        docx_path = Path(docx_path)
        pdf_path = Path(pdf_path)
        pack_path = Path(pack_path)
        if docx_path.suffix.lower() != ".docx" or not docx_path.is_file():
            raise ValueError("Pack candidature incoherent: DOCX manquant ou invalide.")
        if pdf_path.suffix.lower() != ".pdf" or not pdf_path.is_file():
            raise ValueError("Pack candidature incoherent: PDF manquant ou invalide.")
        if docx_path.parent != pack_path or pdf_path.parent != pack_path:
            raise ValueError("Pack candidature incoherent: dossier de candidature inattendu.")


def _validate_scored_offer_decisions(scored_offers: list[dict[str, Any]]) -> None:
    for offer in scored_offers:
        if not offer.get("id_offre"):
            continue
        if offer.get("decision") not in VALID_SCORING_DECISIONS:
            raise ValueError("Offre sans decision de scoring valide pour la synchronisation Supabase.")


def _sync_run(client: Any, settings: SupabaseSettings, summary: dict[str, Any]) -> None:
    payload = {
        "owner_id": settings.owner_id,
        "triggered_at": datetime.now(timezone.utc).isoformat(),
        "trigger_type": settings.trigger_type,
        "github_run_id": settings.github_run_id or None,
        "status": "completed",
        "total_raw": int(summary.get("total_raw", 0) or 0),
        "total_relevant": int(summary.get("total_relevant", 0) or 0),
        "total_new": int(summary.get("total_new", 0) or 0),
        "total_generated_cvs": int(summary.get("total_generated_cvs", 0) or 0),
        "source_stats": summary.get("source_stats") if isinstance(summary.get("source_stats"), dict) else {},
        "summary": _minimal_summary(summary),
    }
    query = client.table("runs")
    if settings.github_run_id:
        query = query.upsert(payload, on_conflict="owner_id,github_run_id")
    else:
        query = query.insert(payload)
    _execute(query.execute())


def _minimal_summary(summary: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "total_raw",
        "total_normalized",
        "total_unique_normalized",
        "total_relevant",
        "total_exportable",
        "total_new",
        "total_generated_cvs",
        "decision_counts",
        "best_score",
        "sources_enabled",
        "source_status",
    ]
    return {key: summary[key] for key in keys if key in summary}


def _fetch_offer_ids(client: Any, owner_id: str, offers_payload: list[dict[str, Any]]) -> dict[tuple[str, str, str], str]:
    result: dict[tuple[str, str, str], str] = {}
    for offer in offers_payload:
        rows = _execute(
            client.table("offers")
            .select("id,owner_id,source,external_offer_id")
            .eq("owner_id", owner_id)
            .eq("source", offer["source"])
            .eq("external_offer_id", offer["external_offer_id"])
            .execute()
        )
        result.update(_offer_id_map(rows))
    return result


def _insert_application_if_missing(client: Any, owner_id: str, offer_id: str) -> bool:
    existing = _execute(
        client.table("applications")
        .select("id")
        .eq("owner_id", owner_id)
        .eq("offer_id", offer_id)
        .execute()
    )
    if existing:
        return False

    _execute(
        client.table("applications")
        .insert(
            {
                "owner_id": owner_id,
                "offer_id": offer_id,
                "status": "new",
                "favorite": False,
                "notes": "",
            }
        )
        .execute()
    )
    return True


def _upload_file(client: Any, bucket_name: str, storage_path: str, path: Path, mime_type: str) -> None:
    client.storage.from_(bucket_name).upload(
        storage_path,
        path.read_bytes(),
        file_options={"content-type": mime_type, "upsert": "true"},
    )


def _upsert_candidate_document(
    client: Any,
    *,
    owner_id: str,
    offer_id: str,
    pdf_storage_path: str,
    docx_storage_path: str,
    docx_path: Path,
    pdf_path: Path,
    generated_at: str,
) -> None:
    _execute(
        client.table("candidate_documents")
        .upsert(
            {
                "owner_id": owner_id,
                "offer_id": offer_id,
                "pdf_storage_path": pdf_storage_path,
                "docx_storage_path": docx_storage_path,
                "metadata": {
                    "generated_at": generated_at,
                    "generated_docx": docx_path.name,
                    "generated_pdf": pdf_path.name,
                },
            },
            on_conflict="offer_id",
        )
        .execute()
    )


def _offer_id_map(rows: list[dict[str, Any]]) -> dict[tuple[str, str, str], str]:
    result = {}
    for row in rows:
        offer_id = row.get("id")
        owner_id = row.get("owner_id")
        source = row.get("source")
        external_offer_id = row.get("external_offer_id")
        if offer_id and owner_id and source and external_offer_id:
            result[(str(owner_id), str(source), str(external_offer_id))] = str(offer_id)
    return result


def _offer_key(owner_id: str, offer: dict[str, Any]) -> tuple[str, str, str]:
    return (owner_id, str(offer.get("source") or ""), str(offer.get("id_offre") or ""))


def _storage_path(owner_id: str, offer_id: str, path: Path) -> str:
    return f"{owner_id}/offers/{offer_id}/{path.name}"


def _technologies(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [item.strip() for item in str(value).split(",") if item.strip()]


def _execute(response: Any) -> list[dict[str, Any]]:
    data = getattr(response, "data", response)
    if data is None:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    return []
