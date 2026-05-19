# AutoTache

AutoTache est une application Python locale de veille d'offres d'emploi. Elle collecte des offres depuis plusieurs sources, les normalise, applique des filtres metier et un scoring local, puis genere des exports CSV/XLSX et un resume Discord optionnel.

Le projet est prevu pour tourner sur Windows avec VS Code, un environnement virtuel `.venv`, et une tache planifiee Windows.

## Fonctionnalites

- Collecte multi-sources.
- Normalisation des offres vers un format commun.
- Detection salaire, teletravail et technologies.
- Filtrage metier et scoring local avec decisions `Pertinent`, `A verifier` et `Rejete`.
- Exports CSV/XLSX des nouvelles offres a traiter.
- Fichier cumulatif `offres_suivi.xlsx` sans doublons.
- Export debug avec toutes les offres normalisees uniques.
- Resume Discord compact, sans secret ni chemin complet.
- Automatisation Windows via `scripts/run_autotache.ps1`.

## Sources Disponibles

- France Travail : source officielle francaise avec authentification API.
- Adzuna : source internationale configurable par pays, recommandee pour la France.
- Jooble : source configurable par domaine, recommandee avec `https://fr.jooble.org/api` pour les cles francaises.
- The Muse : source publique sans cle, configurable par localisation, utile en complement international.
- Arbeitnow : source sans cle, utile en complement mais moins ciblee France.
- Remotive : source remote internationale, utile en complement mais moins ciblee France.

## Configuration Recommandee France

Pour une recherche d'offres francaises, la configuration recommandee est :

```yaml
sources:
  france_travail:
    enabled: true
  adzuna:
    enabled: true
  jooble:
    enabled: true
    base_url: "https://fr.jooble.org/api"
    max_pages: 1
  themuse:
    enabled: false
    max_pages: 1
  arbeitnow:
    enabled: false
  remotive:
    enabled: false
```

`max_pages: 1` est volontairement prudent pour Jooble afin de limiter les requetes.

## Fichiers De Configuration

- `.env` : fichier local contenant les secrets et identifiants API. Il ne doit jamais etre versionne ni partage.
- `config.yaml` : configuration locale active du projet, avec sources, filtres, exports et notifications.
- `.env.example` : modele public des variables d'environnement attendues, sans valeur secrete.
- `config.example.yaml` : modele public de configuration, a copier vers `config.yaml` puis adapter localement.

Les identifiants API et webhooks doivent rester uniquement dans `.env`.

## Exports

Les nouveaux exports sont ranges dans des sous-dossiers :

```text
exports/
  offres/
    offres_suivi.xlsx
    offres_YYYY-MM-DD_HHMM.xlsx
    offres_YYYY-MM-DD_HHMM.csv
  debug/
    debug_offres_YYYY-MM-DD_HHMM.xlsx
    debug_offres_YYYY-MM-DD_HHMM.csv
```

- `exports/offres/offres_suivi.xlsx` : fichier cumulatif de suivi, sans doublons, contenant uniquement les offres `Pertinent` et `A verifier`.
- `exports/offres/offres_*.xlsx` et `exports/offres/offres_*.csv` : nouvelles offres exportables du run courant.
- `exports/debug/debug_offres_*.xlsx` et `exports/debug/debug_offres_*.csv` : toutes les offres normalisees uniques, y compris les offres rejetees.

Les fichiers generes dans `exports/` ne doivent pas etre versionnes.

## Commandes Utiles

Activer l'environnement si besoin :

```powershell
.venv\Scripts\Activate.ps1
```

Lancer les tests :

```powershell
python -m pytest tests
```

Lancer AutoTache :

```powershell
python -m autotache_jobs
```

Lancer AutoTache avec export debug :

```powershell
python -m autotache_jobs --debug
```

## Automatisation Windows

Le script utilise par la tache planifiee est :

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "D:\devAuto\AutoTache\scripts\run_autotache.ps1"
```

Dans le Planificateur de taches Windows :

- lancer AutoTache tous les jours a 10h si le PC est allume ;
- activer `Executer la tache des que possible apres un demarrage planifie manque` ;
- ne pas activer `Reveiller l'ordinateur pour executer cette tache` ;
- definir le dossier de demarrage sur `D:\devAuto\AutoTache`.

## Securite

- Ne jamais versionner `.env`.
- Ne jamais partager les cles API, tokens, secrets client ou webhook Discord.
- Ne jamais afficher de secret dans les logs, exports, messages Discord ou captures d'ecran.
- Garder `config.yaml` local si sa configuration contient des informations personnelles de recherche.
