-- AutoTache initial private schema.
--
-- This migration is safe to version publicly: it contains no project URL,
-- user identifier, credential, secret, e-mail address, or personal data.
--
-- Security model:
-- - Every application row has an owner_id linked to auth.users(id).
-- - Row Level Security is enabled so the frontend can only read its own rows.
-- - Backend synchronization must use a Supabase secret service key and that key
--   must never be exposed to the browser or committed to the repository.
-- - Candidate documents are stored in a private Storage bucket. The frontend can
--   only read files under its own owner UUID folder.
-- - No frontend upload policy is created in this version; GitHub Actions will
--   upload documents later through the backend/service role.

create extension if not exists pgcrypto;

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

comment on function public.set_updated_at() is
  'Shared trigger helper for tables with an updated_at timestamp.';

create table if not exists public.runs (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  triggered_at timestamptz not null default now(),
  trigger_type text not null default 'scheduled',
  github_run_id text,
  status text not null default 'completed',
  total_raw integer not null default 0,
  total_relevant integer not null default 0,
  total_new integer not null default 0,
  total_generated_cvs integer not null default 0,
  source_stats jsonb not null default '{}'::jsonb,
  summary jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  constraint runs_trigger_type_check check (trigger_type in ('scheduled', 'manual', 'local')),
  constraint runs_status_check check (status in ('running', 'completed', 'failed')),
  constraint runs_total_raw_check check (total_raw >= 0),
  constraint runs_total_relevant_check check (total_relevant >= 0),
  constraint runs_total_new_check check (total_new >= 0),
  constraint runs_total_generated_cvs_check check (total_generated_cvs >= 0),
  constraint runs_owner_github_run_id_unique unique (owner_id, github_run_id)
);

comment on table public.runs is
  'AutoTache execution history. owner_id isolates private run data per authenticated user.';
comment on column public.runs.owner_id is
  'Owner used by Row Level Security; frontend rows are visible only when owner_id = auth.uid().';

create table if not exists public.offers (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  external_offer_id text not null,
  source text not null,
  title text not null,
  company text not null default '',
  location text not null default '',
  contract_type text not null default '',
  description text not null default '',
  technologies text[] not null default '{}'::text[],
  offer_url text not null default '',
  decision text not null,
  score_total integer not null,
  score_reason text not null default '',
  score_details jsonb not null default '{}'::jsonb,
  first_seen_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint offers_owner_source_external_unique unique (owner_id, source, external_offer_id),
  constraint offers_id_owner_unique unique (id, owner_id),
  constraint offers_decision_check check (decision in ('Pertinent', 'À vérifier', 'Rejeté')),
  constraint offers_score_total_check check (score_total between 0 and 100)
);

comment on table public.offers is
  'Normalized job offers and local scoring. owner_id prevents cross-user data exposure.';
comment on column public.offers.owner_id is
  'Owner used by Row Level Security; frontend rows are visible only when owner_id = auth.uid().';

create index if not exists offers_owner_decision_score_idx
  on public.offers (owner_id, decision, score_total desc);

create index if not exists offers_owner_first_seen_idx
  on public.offers (owner_id, first_seen_at desc);

drop trigger if exists offers_set_updated_at on public.offers;
create trigger offers_set_updated_at
before update on public.offers
for each row
execute function public.set_updated_at();

create table if not exists public.candidate_documents (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  offer_id uuid not null,
  pdf_storage_path text,
  docx_storage_path text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint candidate_documents_offer_owner_fk
    foreign key (offer_id, owner_id)
    references public.offers (id, owner_id)
    on delete cascade,
  constraint candidate_documents_has_document_check
    check (pdf_storage_path is not null or docx_storage_path is not null),
  constraint candidate_documents_offer_unique unique (offer_id)
);

comment on table public.candidate_documents is
  'Private candidate document pointers for one offer. Files live in the private candidate-documents Storage bucket.';
comment on column public.candidate_documents.owner_id is
  'Owner used by Row Level Security and mirrored in Storage paths.';

drop trigger if exists candidate_documents_set_updated_at on public.candidate_documents;
create trigger candidate_documents_set_updated_at
before update on public.candidate_documents
for each row
execute function public.set_updated_at();

create table if not exists public.applications (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  offer_id uuid not null,
  status text not null default 'new',
  favorite boolean not null default false,
  notes text not null default '',
  applied_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint applications_offer_owner_fk
    foreign key (offer_id, owner_id)
    references public.offers (id, owner_id)
    on delete cascade,
  constraint applications_status_check
    check (status in ('new', 'to_review', 'to_apply', 'applied', 'interview', 'rejected', 'archived')),
  constraint applications_offer_unique unique (offer_id)
);

comment on table public.applications is
  'Personal application tracking rows. The backend creates rows; the frontend may only update its own rows.';
comment on column public.applications.owner_id is
  'Owner used by Row Level Security; frontend rows are visible and editable only when owner_id = auth.uid().';

create index if not exists applications_owner_status_updated_idx
  on public.applications (owner_id, status, updated_at desc);

drop trigger if exists applications_set_updated_at on public.applications;
create trigger applications_set_updated_at
before update on public.applications
for each row
execute function public.set_updated_at();

-- Row Level Security is explicitly enabled on all application tables because the
-- frontend will use Supabase Auth and a publishable key. Anonymous access is not
-- granted, and authenticated access is limited to owner_id = auth.uid().
alter table public.runs enable row level security;
alter table public.offers enable row level security;
alter table public.candidate_documents enable row level security;
alter table public.applications enable row level security;

revoke all on table public.runs from anon;
revoke all on table public.offers from anon;
revoke all on table public.candidate_documents from anon;
revoke all on table public.applications from anon;

revoke all on table public.runs from authenticated;
revoke all on table public.offers from authenticated;
revoke all on table public.candidate_documents from authenticated;
revoke all on table public.applications from authenticated;

grant select on table public.runs to authenticated;
grant select on table public.offers to authenticated;
grant select on table public.candidate_documents to authenticated;
grant select on table public.applications to authenticated;
grant update (status, favorite, notes, applied_at) on table public.applications to authenticated;

grant select, insert, update, delete on table public.runs to service_role;
grant select, insert, update, delete on table public.offers to service_role;
grant select, insert, update, delete on table public.candidate_documents to service_role;
grant select, insert, update, delete on table public.applications to service_role;

drop policy if exists "runs_select_own_rows" on public.runs;
create policy "runs_select_own_rows"
on public.runs
for select
to authenticated
using (auth.uid() is not null and owner_id = (select auth.uid()));

drop policy if exists "offers_select_own_rows" on public.offers;
create policy "offers_select_own_rows"
on public.offers
for select
to authenticated
using (auth.uid() is not null and owner_id = (select auth.uid()));

drop policy if exists "candidate_documents_select_own_rows" on public.candidate_documents;
create policy "candidate_documents_select_own_rows"
on public.candidate_documents
for select
to authenticated
using (auth.uid() is not null and owner_id = (select auth.uid()));

drop policy if exists "applications_select_own_rows" on public.applications;
create policy "applications_select_own_rows"
on public.applications
for select
to authenticated
using (auth.uid() is not null and owner_id = (select auth.uid()));

drop policy if exists "applications_update_own_rows" on public.applications;
create policy "applications_update_own_rows"
on public.applications
for update
to authenticated
using (auth.uid() is not null and owner_id = (select auth.uid()))
with check (auth.uid() is not null and owner_id = (select auth.uid()));

-- Private Storage bucket for generated CV documents.
--
-- The bucket is never public. The frontend can only download files from its own
-- owner UUID folder, for example:
--   <owner_uuid>/offers/<offer_uuid>/CV_Bastien_....pdf
--   <owner_uuid>/offers/<offer_uuid>/CV_Bastien_....docx
--
-- No INSERT/UPDATE/DELETE policy is created for the frontend. Future uploads
-- must be performed by the backend pipeline with the Supabase service key. That
-- backend key must remain a secret and must never be exposed to browser code.
insert into storage.buckets (
  id,
  name,
  public,
  file_size_limit,
  allowed_mime_types
)
values (
  'candidate-documents',
  'candidate-documents',
  false,
  10485760,
  array[
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  ]::text[]
)
on conflict (id) do update
set
  name = excluded.name,
  public = false,
  file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;

drop policy if exists "candidate_documents_storage_select_own_folder" on storage.objects;
create policy "candidate_documents_storage_select_own_folder"
on storage.objects
for select
to authenticated
using (
  auth.uid() is not null
  and bucket_id = 'candidate-documents'
  and (storage.foldername(name))[1] = (select auth.uid())::text
);
