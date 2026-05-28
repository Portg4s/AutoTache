create table public.offer_favorites (
  owner_id uuid not null references auth.users(id) on delete cascade,
  offer_id uuid not null,
  created_at timestamptz not null default now(),

  constraint offer_favorites_pkey primary key (owner_id, offer_id),

  constraint offer_favorites_offer_owner_fk
    foreign key (offer_id, owner_id)
    references public.offers (id, owner_id)
    on delete cascade
);

comment on table public.offer_favorites is
  'Personal bookmarked job offers. Favorites are independent from generated applications and candidate documents.';

alter table public.offer_favorites enable row level security;

revoke all on table public.offer_favorites from anon, authenticated;

grant select on table public.offer_favorites to authenticated;
grant insert (owner_id, offer_id) on table public.offer_favorites to authenticated;
grant delete on table public.offer_favorites to authenticated;

create policy "offer_favorites_select_own_rows"
on public.offer_favorites
for select
to authenticated
using (
  auth.uid() is not null
  and owner_id = (select auth.uid())
);

create policy "offer_favorites_insert_own_eligible_offers"
on public.offer_favorites
for insert
to authenticated
with check (
  auth.uid() is not null
  and owner_id = (select auth.uid())
  and exists (
    select 1
    from public.offers as offer
    where offer.id = offer_favorites.offer_id
      and offer.owner_id = offer_favorites.owner_id
      and offer.owner_id = (select auth.uid())
      and offer.decision in (
        'Pertinent',
        U&'\00C0 v\00E9rifier'
      )
  )
);

create policy "offer_favorites_delete_own_rows"
on public.offer_favorites
for delete
to authenticated
using (
  auth.uid() is not null
  and owner_id = (select auth.uid())
);

insert into public.offer_favorites (owner_id, offer_id)
select application.owner_id, application.offer_id
from public.applications as application
where application.favorite = true
on conflict (owner_id, offer_id) do nothing;
