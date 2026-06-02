create table public.offer_tracking (
  owner_id uuid not null references auth.users(id) on delete cascade,
  offer_id uuid not null,
  status text not null default 'to_review',
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),

  constraint offer_tracking_pkey primary key (owner_id, offer_id),

  constraint offer_tracking_offer_owner_fk
    foreign key (offer_id, owner_id)
    references public.offers (id, owner_id)
    on delete cascade,

  constraint offer_tracking_status_check
    check (status in ('to_review', 'interested', 'to_apply', 'archived'))
);

comment on table public.offer_tracking is
  'Personal pre-application tracking for job offers. Tracking is independent from favorites, applications, and generated documents.';

comment on column public.offer_tracking.owner_id is
  'Owner used by Row Level Security; frontend rows are visible and editable only when owner_id = auth.uid().';

drop trigger if exists offer_tracking_set_updated_at on public.offer_tracking;
create trigger offer_tracking_set_updated_at
before update on public.offer_tracking
for each row
execute function public.set_updated_at();

alter table public.offer_tracking enable row level security;

revoke all on table public.offer_tracking from anon, authenticated;

grant select on table public.offer_tracking to authenticated;
grant insert (owner_id, offer_id, status, notes) on table public.offer_tracking to authenticated;
grant update (status, notes) on table public.offer_tracking to authenticated;
grant delete on table public.offer_tracking to authenticated;

drop policy if exists "offer_tracking_select_own_rows" on public.offer_tracking;
create policy "offer_tracking_select_own_rows"
on public.offer_tracking
for select
to authenticated
using (
  auth.uid() is not null
  and owner_id = (select auth.uid())
);

drop policy if exists "offer_tracking_insert_own_offers" on public.offer_tracking;
create policy "offer_tracking_insert_own_offers"
on public.offer_tracking
for insert
to authenticated
with check (
  auth.uid() is not null
  and owner_id = (select auth.uid())
  and exists (
    select 1
    from public.offers as offer
    where offer.id = offer_tracking.offer_id
      and offer.owner_id = offer_tracking.owner_id
      and offer.owner_id = (select auth.uid())
  )
);

drop policy if exists "offer_tracking_update_own_rows" on public.offer_tracking;
create policy "offer_tracking_update_own_rows"
on public.offer_tracking
for update
to authenticated
using (
  auth.uid() is not null
  and owner_id = (select auth.uid())
)
with check (
  auth.uid() is not null
  and owner_id = (select auth.uid())
);

drop policy if exists "offer_tracking_delete_own_rows" on public.offer_tracking;
create policy "offer_tracking_delete_own_rows"
on public.offer_tracking
for delete
to authenticated
using (
  auth.uid() is not null
  and owner_id = (select auth.uid())
);
