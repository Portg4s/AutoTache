from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "supabase" / "migrations" / "0004_create_offer_tracking.sql"
TRACKING_ACTION = ROOT / "web" / "src" / "app" / "offer-tracking" / "actions.ts"
FAVORITES_ACTION = ROOT / "web" / "src" / "app" / "favorites" / "actions.ts"
DASHBOARD_PAGE = ROOT / "web" / "src" / "app" / "dashboard" / "page.tsx"


def _compact(sql: str) -> str:
    return " ".join(sql.lower().split())


def test_offer_tracking_migration_restricts_rows_to_owned_offers() -> None:
    sql = _compact(MIGRATION.read_text(encoding="utf-8"))

    assert "create table public.offer_tracking" in sql
    assert "constraint offer_tracking_pkey primary key (owner_id, offer_id)" in sql
    assert "foreign key (offer_id, owner_id) references public.offers (id, owner_id)" in sql
    assert "alter table public.offer_tracking enable row level security" in sql
    assert "revoke all on table public.offer_tracking from anon, authenticated" in sql
    assert "owner_id = (select auth.uid())" in sql
    assert "where offer.id = offer_tracking.offer_id" in sql
    assert "offer.owner_id = offer_tracking.owner_id" in sql
    assert "offer.owner_id = (select auth.uid())" in sql


def test_offer_tracking_statuses_are_strictly_limited() -> None:
    sql = _compact(MIGRATION.read_text(encoding="utf-8"))

    assert "constraint offer_tracking_status_check check" in sql
    assert "status in ('to_review', 'interested', 'to_apply', 'archived')" in sql
    assert "applications_status_check" not in sql


def test_offer_tracking_action_does_not_create_applications_or_documents() -> None:
    action = TRACKING_ACTION.read_text(encoding="utf-8")

    assert '.from("offer_tracking")' in action
    assert ".insert(" in action
    assert ".update(" in action
    assert "applications" not in action
    assert "candidate_documents" not in action
    assert "generate_cv" not in action
    assert "CV" not in action
    assert "pdf" not in action.lower()
    assert "docx" not in action.lower()


def test_offer_tracking_ui_keeps_favorites_independent() -> None:
    favorites_action = FAVORITES_ACTION.read_text(encoding="utf-8")
    dashboard_page = DASHBOARD_PAGE.read_text(encoding="utf-8")

    assert '.from("offer_favorites")' in favorites_action
    assert "offer_tracking" not in favorites_action
    assert 'supabase.from("offer_favorites").select("offer_id")' in dashboard_page
    assert 'supabase.from("offer_tracking").select("offer_id,status")' in dashboard_page
