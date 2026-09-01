# IRVE France — Cartographie, Clustering & Machine Learning

Un projet d'analyse de données, de modélisation prédictive et de restitution interactive géospatiale axé sur le déploiement des Infrastructures de Recharge pour Véhicules Électriques (IRVE) en France.

---

## Présentation du Projet

Ce projet a pour objectif d'analyser la répartition, la puissance et l'accessibilité des bornes de recharge pour véhicules électriques sur le territoire français à partir des données ouvertes officielles fournies par **data.gouv.fr**.

Le projet se décompose en plusieurs grandes étapes :
1. **Exploration & Nettoyage (EDA) :** analyse descriptive, nettoyage des données géospatiales (coordonnées GPS) et harmonisation des informations d'aménageurs et d'opérateurs.
2. **Base de données relationnelle :** structuration et stockage optimisé des données de recharge sous SQLite pour des requêtes performantes.
3. **Modélisation Machine Learning :**
   * **Clustering (ML non supervisé) :** segmentation des stations de recharge (K-Means / DBSCAN) pour dégager des typologies de réseaux.
   * **Classification (ML supervisé) :** prédiction de la tranche de puissance d'une borne selon son type d'implantation et sa localisation.
4. **API REST :** exposition des données et des prédictions du modèle via FastAPI.
5. **Dashboard Interactif :** cartographie dynamique et visualisation des indicateurs clés du maillage national via Streamlit et Folium.

---

## Arborescence du Projet

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