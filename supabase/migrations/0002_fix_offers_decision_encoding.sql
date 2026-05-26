-- Fix the decision constraint installed with mojibake labels in the hosted database.
-- Unicode escape literals keep this migration ASCII-safe when pasted in SQL Editor.

alter table public.offers
  drop constraint if exists offers_decision_check;

alter table public.offers
  add constraint offers_decision_check
  check (
    decision in (
      'Pertinent',
      U&'\00C0 v\00E9rifier',
      U&'Rejet\00E9'
    )
  );
