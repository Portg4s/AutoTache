# AutoTache

Application Python locale pour rechercher des offres France Travail autour du front-end, WordPress, intégration web, UI/UX et graphisme web.

## Sécurité

- Ne jamais écrire de secret dans le code.
- Créer un fichier `.env` local à partir de `.env.example`.
- Le fichier `.env` est ignoré par Git.
- Les anciens secrets, tokens ou webhooks issus d'autres workflows doivent être considérés comme fictifs et non réutilisables.

## Configuration

Copier `config.example.yaml` vers `config.yaml`, puis adapter :

- les mots-clés ;
- les communes ;
- la distance ;
- les types de contrat ;
- le nombre de jours à regarder ;
- les règles de filtrage ;
- l'autorisation ou non des stages et alternances.

## Variables France Travail

Créer un fichier `.env` local avec :

```env
FRANCE_TRAVAIL_CLIENT_ID=...
FRANCE_TRAVAIL_CLIENT_SECRET=...
FRANCE_TRAVAIL_SCOPE=api_offresdemploiv2 o2dsoffre
FRANCE_TRAVAIL_TOKEN_URL=https://entreprise.francetravail.fr/connexion/oauth2/access_token
FRANCE_TRAVAIL_API_BASE_URL=https://api.francetravail.io/partenaire/offresdemploi/v2
```

`FRANCE_TRAVAIL_CLIENT_ID` et `FRANCE_TRAVAIL_CLIENT_SECRET` doivent venir du portail développeur France Travail après habilitation à l'API Offres d'emploi.

## Dépendances prévues

- `httpx`
- `python-dotenv`
- `pydantic`
- `PyYAML`
- `python-dateutil`
- `pytest`

## Lancement prévu

La V1 sera exécutable avec :

```bash
python -m autotache_jobs
```

La logique API complète sera ajoutée par petites étapes vérifiables.
