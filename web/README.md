# AutoTache Web

Interface web mobile-first pour consulter les offres AutoTache synchronisées dans Supabase. Cette fondation est volontairement en lecture seule: connexion, session sécurisée, dashboard protégé et affichage des offres/runs visibles par RLS.

## Prérequis

- Node.js 24.16.0 ou compatible
- npm 11.13.0 ou compatible

## Installation

```powershell
npm install
```

## Développement

```powershell
npm run dev
```

## Variables publiques

Créer un fichier local non versionné si nécessaire, à partir de `.env.example`:

```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=sb_publishable_your_public_key
```

N'utilisez jamais `SUPABASE_SECRET_KEY`, une clé `sb_secret_...`, un mot de passe, un UID propriétaire ou un secret GitHub dans `web/`. Le frontend doit uniquement utiliser la clé publique publiable Supabase et laisser RLS filtrer les données.

## Validation locale

Sans vraie valeur Supabase, les commandes peuvent être lancées avec des placeholders:

```powershell
$env:NEXT_PUBLIC_SUPABASE_URL="https://placeholder.supabase.co"
$env:NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY="sb_publishable_placeholder"
npm run lint
npm run build
Remove-Item Env:NEXT_PUBLIC_SUPABASE_URL -ErrorAction SilentlyContinue
Remove-Item Env:NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY -ErrorAction SilentlyContinue
```

## Test manuel ultérieur

1. Renseigner localement les deux variables publiques Supabase.
2. Lancer `npm run dev`.
3. Ouvrir `/login`.
4. Se connecter avec l'utilisateur Supabase Auth existant.
5. Vérifier la redirection vers `/dashboard`, les cartes résumé, la liste des offres et la déconnexion.
