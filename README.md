# IRVE France — Cartographie, Clustering & Machine Learning

Projet d'analyse de données, de modélisation et de restitution géospatiale portant sur le déploiement des Infrastructures de Recharge pour Véhicules Électriques (IRVE) en France.

---

## Problématique métier

Dans le cadre de la transition énergétique, où se situent les déserts de recharge en France et les territoires sous-équipés en bornes de 150 kW et plus, et quelle dynamique de déploiement permet d'orienter les futures installations ?

* **Désert de recharge :** commune sans aucun point de charge sur son territoire et dont le centre est à plus de 10 km du point le plus proche.
* **Désert 150 kW :** commune sans point de 150 kW ou plus et à plus de 30 km d'un tel point (le règlement européen AFIR impose un parc de recharge d'au moins 150 kW tous les 60 km sur le réseau routier central).
* **Périmètre :** France métropolitaine et 5 départements d'outre-mer (Guadeloupe, Martinique, Guyane, La Réunion, Mayotte).

Le projet s'articule autour de 3 axes d'analyse :
1. **Cartographie & déserts de recharge :** identifier les disparités territoriales et les zones sous-équipées, à l'échelle communale, en rapportant l'offre de bornes à la population.
2. **Analyse de la puissance :** décrire la répartition de l'offre haute puissance sur le territoire.
3. **Modélisation (ML) :** identifier les communes sans borne dont le profil ressemble à celui des communes équipées (scoring) et segmenter les stations selon leurs caractéristiques techniques et leur contexte territorial (clustering).

---

## Données

| Jeu de données | Source | Fichier local | Version utilisée |
|---|---|---|---|
| Fichier consolidé des IRVE | [data.gouv.fr](https://www.data.gouv.fr/fr/datasets/fichier-consolide-des-bornes-de-recharge-pour-vehicules-electriques/) | `data/raw/dataset_irve.csv` (226 963 lignes, 52 colonnes) | Dernière modification : 31/08/2026 |
| Population par commune | État de la Base Adresse Nationale par commune ([adresse.data.gouv.fr](https://adresse.data.gouv.fr)), champ « population légale municipale » | `data/raw/population_communes.csv` | Fichier du 21/09/2026 |
| Référentiel des communes (`georef-france-commune`) | [Opendatasoft](https://public.opendatasoft.com/explore/dataset/georef-france-commune/) | `data/raw/referentiel_communes.csv` | Téléchargé le 04/09/2026 |

Licence des données IRVE et de la Base Adresse Nationale : Licence Ouverte / Etalab 2.0.

Les fichiers de données et la base SQLite sont exclus de Git (voir `.gitignore`) : il faut télécharger les fichiers bruts et les placer dans `data/raw/`.

---

## Démarche & étapes du projet

1. **Exploration & nettoyage (EDA) :** diagnostic qualité (doublons entre sources, puissances en watts, codes INSEE manquants ou non vérifiés, coordonnées erronées), nettoyage et jointure avec la population communale.
2. **Base de données relationnelle :** modélisation MERISE et chargement sous SQLite (tables `REGION`, `DEPARTEMENT`, `COMMUNE`, `ACTEUR`, `STATION`, `POINT_DE_CHARGE` et vue `v_equipement_commune`).
3. **API REST :** exposition des données via FastAPI (opérations CRUD), sans cloud.
4. **Analyse exploratoire & veille :** statistiques, corrélations, visualisations Python ; synthèse de veille IA / Big Data.
5. **Dashboard :** Power BI (au moins 3 axes d'analyse et 4 KPI, dont une carte).
6. **Machine Learning & risques :**
   * **Scoring (supervisé)** : Logistic Regression, Random Forest et XGBoost comparés avec GridSearchCV, validation par groupes de départements ; Logistic Regression retenue (AUC test 0,871) ; 557 communes sans borne au profil de commune équipée.
   * **Clustering (non supervisé)** : typologie des 49 180 stations par K-Means (k = 4) : AC de proximité, AC urbaine, recharge rapide DC, accès réservé.
   * Évaluation des risques : qualité et biais des données, data leakage, extrapolation, usage et éthique.
7. **Restitution :** présentation orientée storytelling pour un public non technique.

---

## Arborescence du projet

```text
irve-bornes-recharge-ml/
├── README.md
├── requirements.txt
├── pytest.ini                    # Configuration des tests de l'API
├── .env.example                  # Modèle du fichier .env (clé d'API)
├── .gitignore
├── data/                         # Exclu de Git
│   ├── raw/                      # dataset_irve.csv, population_communes.csv, referentiel_communes.csv
│   ├── processed/                # irve_points_clean.csv, communes_population_clean.csv
│   └── database/                 # irve_database.db
├── notebooks/
│   ├── 01_eda_cleaning.ipynb     # Diagnostic, nettoyage, jointure population
│   ├── 02_database_setup.ipynb   # Création et chargement de la base SQLite
│   ├── 03_api.ipynb              # Présentation et démonstration de l'API
│   ├── 04_analyse_exploratoire.ipynb # Couverture, déserts, puissance, acteurs, tendances
│   └── 05_machine_learning.ipynb # Clustering et scoring
├── api/
│   ├── main.py                   # Application FastAPI et routes
│   ├── database.py               # Connexion SQLite
│   ├── schemas.py                # Validation des entrées et des sorties
│   ├── security.py               # Clé d'API pour les écritures
│   └── tests/test_api.py         # Tests automatiques (pytest)
├── dashboard/                    # Fichier du dashboard Power BI (.pbix)
└── docs/
    ├── schema_bdd.drawio         # Schéma MERISE (draw.io)
    ├── veille_ia_bigdata.md      # Synthèse de veille IA / Big Data
    └── reponses_questions_analyse.md # Réponses aux questions d'analyse de chaque étape
```

---

## Installation et exécution

Prérequis : Python 3.11 ou plus récent.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows (sous Linux/macOS : source .venv/bin/activate)
pip install -r requirements.txt
```

Ordre d'exécution des notebooks (à lancer depuis le dossier `notebooks/`) :
1. `01_eda_cleaning.ipynb` : produit les fichiers de `data/processed/`.
2. `02_database_setup.ipynb` : crée la base SQLite.
3. `03_api.ipynb` : présentation et démonstration de l'API.
4. `04_analyse_exploratoire.ipynb` : analyse exploratoire (cartes, distributions, corrélations, tendances).
5. `05_machine_learning.ipynb` : scoring des communes et typologie des stations.

---

## API

Lancement depuis la racine du projet, après avoir copié `.env.example` en `.env` et renseigné une clé :

```bash
uvicorn api.main:app --host 127.0.0.1 --port 8003
```

Documentation interactive : `http://127.0.0.1:8003/docs` (bouton **Authorize** pour saisir la clé d'API).

| Méthode | Route | Rôle | Accès |
|---|---|---|---|
| GET | `/stats` | Chiffres clés du réseau et des déserts | Public |
| GET | `/communes`, `/communes/{code_insee}` | Communes filtrées (département, région, désert) ; fiche d'une commune | Public |
| GET | `/deserts` | Communes en désert, les plus peuplées d'abord | Public |
| GET | `/stations`, `/stations/{id_station}` | Stations d'une commune ; fiche d'une station et de ses points | Public |
| GET | `/points-de-charge`, `/points-de-charge/{id_pdc}` | Points de charge filtrés par station ou puissance | Public |
| POST | `/points-de-charge` | Créer un point de charge | Clé d'API |
| PUT | `/points-de-charge/{id_pdc}` | Remplacer un point de charge | Clé d'API |
| PATCH | `/points-de-charge/{id_pdc}` | Modifier une partie d'un point de charge | Clé d'API |
| DELETE | `/points-de-charge/{id_pdc}` | Supprimer un point de charge | Clé d'API |

Sécurité : clé d'API (en-tête `X-API-Key`) pour toute écriture, validation des entrées (puissance, prises, dates, identifiants), requêtes SQL paramétrées, clés étrangères activées, pagination plafonnée à 500 lignes, serveur local uniquement.

Tests (sur une copie temporaire de la base) :

```bash
python -m pytest -v
```

---

## Limites connues

* **Doublons entre sources :** un même point de charge peut être publié par plusieurs producteurs (60 105 lignes en excédent dans le fichier brut), avec des valeurs parfois contradictoires.
* **Géographie incomplète :** 24,9 % des lignes brutes n'ont pas de code INSEE et une partie des codes présents sont des codes postaux ; chaque point a été rattaché à sa commune par sa position (contours communaux 2025).
* **Puissances hétérogènes :** des valeurs sont saisies en watts au lieu de kilowatts (converties) ; 2 526 puissances absentes ont été complétées par la médiane des points ayant les mêmes prises, sans effet sur les déserts 150 kW.
* **Couverture :** le fichier consolidé nettoyé compte 166 430 points, contre 200 045 points ouverts au public au 31/07/2026 selon le baromètre Avere-France.
* **Offre uniquement :** IRVE décrit l'offre de recharge, pas son usage ni la demande ; les besoins en haute puissance ne peuvent pas être mesurés avec ce seul jeu de données.
* **Tendances partielles :** `date_mise_en_service` n'est renseignée que pour 60,8 % des points, inégalement selon les producteurs et les territoires ; les tendances portent sur les points datés.
* **Distances :** mesurées à vol d'oiseau depuis le centre de la commune ; elles sous-estiment le trajet par la route.
* **Petites communes :** les ratios de bornes par habitant sont instables lorsque la population est faible.

---

## Suivi de projet

Tableau Trello : [IRVE – projet Data Analyst](https://trello.com/b/L6Rh5CDX/irve-projet-data-analyst)
