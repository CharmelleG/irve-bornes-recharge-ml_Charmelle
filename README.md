# IRVE France — Cartographie, Clustering & Machine Learning

Un projet d'analyse de données, de modélisation prédictive et de restitution interactive géospatiale axé sur le déploiement des Infrastructures de Recharge pour Véhicules Électriques (IRVE) en France.

---

## Problématique métier

Dans le cadre de la transition énergétique et de l'essor du véhicule électrique en France, **
**

Pour répondre à cette problématique, le projet s'articule autour de 3 axes d'analyse :
1. **Cartographie & Déserts de recharge :** identifier les disparités territoriales et les zones sous-équipées en bornes.
2. **Analyse de la Puissance :** évaluer si l'offre en haute puissance répond aux besoins des axes stratégiques.
3. **Modélisation & Optimisation (ML) :** segmenter les stations (Clustering) pour guider les futurs investissements de déploiement.

---

## Démarche & étapes du projet

Ce projet exploite les données ouvertes officielles fournies par **data.gouv.fr** et se décompose en plusieurs étapes :

1. **Exploration & Nettoyage (EDA) :** analyse descriptive, nettoyage des données géospatiales (coordonnées GPS) et harmonisation des données.
2. **Base de données relationnelle :** structuration et stockage optimisé des données de recharge sous SQLite.
3. **API REST :** exposition des données et des prédictions du modèle via FastAPI (opérations CRUD).
4. **Modélisation Machine Learning :**
   * **Clustering (non supervisé)** : segmentation typologique des stations de recharge (K-Means) pour classifier les réseaux selon leur usage (transit, résidentiel, commercial).
   * **Analyse Prédictive / Scoring (supervisé)** : modèle d'aide à la décision pour identifier les zones territoriales sous-équipées nécessitant en priorité le déploiement de bornes à haute puissance.
5. **Dashboard & Restitution :** cartographie dynamique sous Power BI / Tableau et présentation orientée storytelling.
---

## Arborescence du projet

irve-bornes-recharge-ml/
├── .gitignore               # Fichiers et dossiers ignorés par Git (.venv, data, etc.)
├── README.md                # Documentation principale du projet
├── requirements.txt         # Dépendances Python nécessaires
│
├── data/                    # Stockage local des données (exclu du suivi Git)
│   ├── raw/                 # Fichiers bruts téléchargés depuis Eurostat
│   ├── processed/           # Fichiers nettoyés et transformés (CSV/Parquet)
│   └── database/            # Fichier de base de données SQLite (.db)
│
├── src/               # Carnets d'exploration Jupyter 
src
│   ├── 01_eda_cleaning.ipynb   # Téléchargement, nettoyage et exploration des données
│   ├── 02_database_setup.ipynb # Création et alimentation de la BDD SQLite
│   └── 03_machine_learning.ipynb # Modélisation et évaluation des prédictions ML
│
├── api/                     # Code source de l'API (FastAPI)
│   └── main.py              # Endpoints et logique de l'API
│
└── dashboard/               # Interface utilisateur interactive (Streamlit)
    └── app.py               # Code de l'application web
docs/
│  └── reponses_questions_analyse.md  # Réponses rédigées (S1 à S7)