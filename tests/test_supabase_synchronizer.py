from pathlib import Path
from typing import Any

from autotache_jobs.supabase.settings import SupabaseSettings
from autotache_jobs.supabase.synchronizer import DOCX_MIME_TYPE, PDF_MIME_TYPE, sync_run_to_supabase


OWNER_ID = "11111111-1111-1111-1111-111111111111"
OFFER_UUID = "22222222-2222-2222-2222-222222222222"


class FakeResponse:
    def __init__(self, data: Any = None) -> None:
        self.data = data


class FakeTableQuery:
    def __init__(self, client: "FakeSupabaseClient", table_name: str) -> None:
        self.client = client
        self.table_name = table_name
        self.operation = ""
        self.payload: Any = None
        self.on_conflict: str | None = None
        self.filters: dict[str, Any] = {}

    def upsert(self, payload: Any, on_conflict: str | None = None) -> "FakeTableQuery":
        self.operation = "upsert"
        self.payload = payload
        self.on_conflict = on_conflict
        return self

    def insert(self, payload: Any) -> "FakeTableQuery":
        self.operation = "insert"
        self.payload = payload
        return self

    def select(self, columns: str) -> "FakeTableQuery":
        self.operation = "select"
        self.payload = columns
        return self

    def eq(self, column: str, value: Any) -> "FakeTableQuery":
        self.filters[column] = value
        return self

    def execute(self) -> FakeResponse:
        self.client.calls.append(
            {
                "table": self.table_name,
                "operation": self.operation,
                "payload": self.payload,
                "on_conflict": self.on_conflict,
                "filters": self.filters.copy(),
            }
        )
        if self.table_name == "offers" and self.operation == "upsert":
            rows = []
            for payload in self.payload:
                row = {**payload}
                offer_uuid = self.client.offer_ids.get(payload["external_offer_id"], self.client.default_offer_uuid)
                if offer_uuid:
                    row["id"] = offer_uuid
                rows.append(row)
            return FakeResponse(rows)
        if self.table_name == "applications" and self.operation == "select":
            offer_id = self.filters.get("offer_id")
            return FakeResponse([{"id": "existing"}] if offer_id in self.client.existing_applications else [])
        return FakeResponse([])


class FakeStorageBucket:
    def __init__(self, client: "FakeSupabaseClient", bucket_name: str) -> None:
        self.client = client
        self.bucket_name = bucket_name

    def upload(self, path: str, content: bytes, file_options: dict[str, str]) -> None:
        self.client.calls.append(
            {
                "table": "storage.objects",
                "operation": "upload",
                "payload": path,
                "on_conflict": None,
                "filters": {"bucket": self.bucket_name},
            }
        )
        if path in self.client.failing_upload_paths:
            raise RuntimeError("upload failed")
        self.client.uploads.append(
            {
                "bucket": self.bucket_name,
                "path": path,
                "content": content,
                "file_options": file_options,
            }
        )


class FakeStorage:
    def __init__(self, client: "FakeSupabaseClient") -> None:
        self.client = client

    def from_(self, bucket_name: str) -> FakeStorageBucket:
        return FakeStorageBucket(self.client, bucket_name)


class FakeSupabaseClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.uploads: list[dict[str, Any]] = []
        self.offer_ids = {"A1": OFFER_UUID, "R1": "33333333-3333-3333-3333-333333333333"}
        self.default_offer_uuid: str | None = OFFER_UUID
        self.existing_applications: set[str] = set()
        self.failing_upload_paths: set[str] = set()
        self.storage = FakeStorage(self)

    def table(self, table_name: str) -> FakeTableQuery:
        return FakeTableQuery(self, table_name)


def _settings(github_run_id: str = "12345") -> SupabaseSettings:
    return SupabaseSettings(
        url="https://example.supabase.co",
        secret_key="secret-value",
        owner_id=OWNER_ID,
        github_run_id=github_run_id,
        trigger_type="manual",
    )


def _offer(offer_id: str, decision: str = "Pertinent") -> dict[str, Any]:
    return {
        "id_offre": offer_id,
        "source": "France Travail",
        "titre": "Integrateur web",
        "entreprise": "Agence",
        "localisation": "Dijon",
        "type_contrat": "CDI",
        "description": "HTML CSS WordPress",
        "technologies": ["HTML", "CSS", "WordPress"],
        "url_offre": "https://example.test/offer",
        "decision": decision,
        "score_total": 87,
        "score_reason": "match",
        "score_details": {"technologies": 3},
    }


def test_sync_upserts_all_scored_offers_and_run_history() -> None:
    client = FakeSupabaseClient()

    result = sync_run_to_supabase(
        client=client,
        settings=_settings(),
        summary={"total_raw": 2, "total_relevant": 1, "total_new": 1, "total_generated_cvs": 0},
        scored_offers=[_offer("A1"), _offer("R1", decision="Rejet\u00e9")],
        new_offers=[],
        generated_docx_paths=[],
        generated_pdf_paths=[],
        candidate_pack_paths=[],
        bucket_name="candidate-documents",
    )

    offers_call = next(call for call in client.calls if call["table"] == "offers" and call["operation"] == "upsert")
    runs_call = next(call for call in client.calls if call["table"] == "runs")

    assert result.success is True
    assert result.offers_synced_count == 2
    assert offers_call["on_conflict"] == "owner_id,source,external_offer_id"
    assert [payload["decision"] for payload in offers_call["payload"]] == ["Pertinent", "Rejet\u00e9"]
    assert runs_call["operation"] == "upsert"
    assert runs_call["on_conflict"] == "owner_id,github_run_id"
    assert runs_call["payload"]["status"] == "completed"


def test_sync_uploads_private_documents_and_creates_application_without_html_or_profile(tmp_path: Path) -> None:
    client = FakeSupabaseClient()
    pdf_path = tmp_path / "CV_Bastien_Agence.pdf"
    docx_path = tmp_path / "CV_Bastien_Agence.docx"
    html_path = tmp_path / "preview.html"
    profile_path = tmp_path / "profile.yaml"
    pdf_path.write_bytes(b"%PDF")
    docx_path.write_bytes(b"DOCX")
    html_path.write_text("<html>preview</html>", encoding="utf-8")
    profile_path.write_text("private: true", encoding="utf-8")

    result = sync_run_to_supabase(
        client=client,
        settings=_settings(github_run_id=""),
        summary={"total_raw": 1, "total_relevant": 1, "total_new": 1, "total_generated_cvs": 1},
        scored_offers=[_offer("A1")],
        new_offers=[_offer("A1")],
        generated_docx_paths=[docx_path],
        generated_pdf_paths=[pdf_path],
        candidate_pack_paths=[tmp_path],
        bucket_name="candidate-documents",
    )

    application_insert = next(call for call in client.calls if call["table"] == "applications" and call["operation"] == "insert")
    document_upsert = next(call for call in client.calls if call["table"] == "candidate_documents")
    upload_paths = [upload["path"] for upload in client.uploads]

    assert result.applications_synced_count == 1
    assert result.documents_synced_count == 1
    assert application_insert["payload"]["status"] == "new"
    assert upload_paths == [
        f"{OWNER_ID}/offers/{OFFER_UUID}/CV_Bastien_Agence.pdf",
        f"{OWNER_ID}/offers/{OFFER_UUID}/CV_Bastien_Agence.docx",
    ]
    assert client.uploads[0]["file_options"] == {"content-type": PDF_MIME_TYPE, "upsert": "true"}
    assert client.uploads[1]["file_options"] == {"content-type": DOCX_MIME_TYPE, "upsert": "true"}
    assert document_upsert["payload"]["metadata"]["generated_pdf"] == pdf_path.name
    assert document_upsert["payload"]["metadata"]["generated_docx"] == docx_path.name
    assert all("preview.html" not in path and "profile.yaml" not in path for path in upload_paths)


def test_sync_does_not_overwrite_existing_application_status(tmp_path: Path) -> None:
    client = FakeSupabaseClient()
    client.existing_applications.add(OFFER_UUID)
    pdf_path = tmp_path / "cv.pdf"
    docx_path = tmp_path / "cv.docx"
    pdf_path.write_bytes(b"pdf")
    docx_path.write_bytes(b"docx")

    result = sync_run_to_supabase(
        client=client,
        settings=_settings(),
        summary={"total_raw": 1, "total_relevant": 1, "total_new": 1, "total_generated_cvs": 1},
        scored_offers=[_offer("A1")],
        new_offers=[_offer("A1")],
        generated_docx_paths=[docx_path],
        generated_pdf_paths=[pdf_path],
        candidate_pack_paths=[tmp_path],
        bucket_name="candidate-documents",
    )

    assert result.applications_synced_count == 0
    assert not any(call["table"] == "applications" and call["operation"] == "insert" for call in client.calls)
    assert len(client.uploads) == 2


def test_sync_rejects_mismatched_pack_lists_before_supabase_calls(tmp_path: Path) -> None:
    client = FakeSupabaseClient()
    docx_path = tmp_path / "cv.docx"
    docx_path.write_bytes(b"docx")

    try:
        sync_run_to_supabase(
            client=client,
            settings=_settings(),
            summary={"total_raw": 1},
            scored_offers=[_offer("A1")],
            new_offers=[_offer("A1")],
            generated_docx_paths=[docx_path],
            generated_pdf_paths=[],
            candidate_pack_paths=[tmp_path],
            bucket_name="candidate-documents",
        )
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("Une liste de packs incoherente devrait echouer.")

    assert "Packs candidature incoherents" in message
    assert client.calls == []
    assert client.uploads == []


def test_sync_rejects_missing_or_invalid_pdf_before_supabase_calls(tmp_path: Path) -> None:
    client = FakeSupabaseClient()
    docx_path = tmp_path / "cv.docx"
    pdf_path = tmp_path / "cv.txt"
    docx_path.write_bytes(b"docx")
    pdf_path.write_text("not a pdf", encoding="utf-8")

    try:
        sync_run_to_supabase(
            client=client,
            settings=_settings(),
            summary={"total_raw": 1},
            scored_offers=[_offer("A1")],
            new_offers=[_offer("A1")],
            generated_docx_paths=[docx_path],
            generated_pdf_paths=[pdf_path],
            candidate_pack_paths=[tmp_path],
            bucket_name="candidate-documents",
        )
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("Un PDF invalide devrait echouer.")

    assert "PDF manquant ou invalide" in message
    assert client.calls == []
    assert client.uploads == []


def test_sync_writes_run_only_after_documents_are_uploaded(tmp_path: Path) -> None:
    client = FakeSupabaseClient()
    pdf_path = tmp_path / "cv.pdf"
    docx_path = tmp_path / "cv.docx"
    pdf_path.write_bytes(b"pdf")
    docx_path.write_bytes(b"docx")

    sync_run_to_supabase(
        client=client,
        settings=_settings(),
        summary={"total_raw": 1, "total_relevant": 1, "total_new": 1, "total_generated_cvs": 1},
        scored_offers=[_offer("A1")],
        new_offers=[_offer("A1")],
        generated_docx_paths=[docx_path],
        generated_pdf_paths=[pdf_path],
        candidate_pack_paths=[tmp_path],
        bucket_name="candidate-documents",
    )

    run_index = next(index for index, call in enumerate(client.calls) if call["table"] == "runs")
    upload_indexes = [index for index, call in enumerate(client.calls) if call["operation"] == "upload"]
    document_index = next(index for index, call in enumerate(client.calls) if call["table"] == "candidate_documents")

    assert upload_indexes
    assert max(upload_indexes) < run_index
    assert document_index < run_index


def test_sync_upload_failure_does_not_write_completed_run(tmp_path: Path) -> None:
    client = FakeSupabaseClient()
    pdf_path = tmp_path / "cv.pdf"
    docx_path = tmp_path / "cv.docx"
    pdf_path.write_bytes(b"pdf")
    docx_path.write_bytes(b"docx")
    client.failing_upload_paths.add(f"{OWNER_ID}/offers/{OFFER_UUID}/cv.pdf")

    try:
        sync_run_to_supabase(
            client=client,
            settings=_settings(),
            summary={"total_raw": 1, "total_relevant": 1, "total_new": 1, "total_generated_cvs": 1},
            scored_offers=[_offer("A1")],
            new_offers=[_offer("A1")],
            generated_docx_paths=[docx_path],
            generated_pdf_paths=[pdf_path],
            candidate_pack_paths=[tmp_path],
            bucket_name="candidate-documents",
        )
    except RuntimeError:
        pass
    else:
        raise AssertionError("Un echec upload devrait remonter.")

    assert not any(call["table"] == "runs" for call in client.calls)


def test_sync_missing_offer_uuid_for_candidate_pack_fails_before_upload_or_completed_run(tmp_path: Path) -> None:
    client = FakeSupabaseClient()
    client.offer_ids = {}
    client.default_offer_uuid = None
    pdf_path = tmp_path / "cv.pdf"
    docx_path = tmp_path / "cv.docx"
    pdf_path.write_bytes(b"pdf")
    docx_path.write_bytes(b"docx")

    try:
        sync_run_to_supabase(
            client=client,
            settings=_settings(),
            summary={"total_raw": 1, "total_relevant": 1, "total_new": 1, "total_generated_cvs": 1},
            scored_offers=[_offer("A1")],
            new_offers=[_offer("A1")],
            generated_docx_paths=[docx_path],
            generated_pdf_paths=[pdf_path],
            candidate_pack_paths=[tmp_path],
            bucket_name="candidate-documents",
        )
    except RuntimeError as exc:
        message = str(exc)
    else:
        raise AssertionError("Un UUID offre manquant devrait faire echouer la synchro.")

    assert message == "Identifiant Supabase introuvable pour une candidature."
    assert client.uploads == []
    assert not any(call["table"] == "runs" for call in client.calls)
