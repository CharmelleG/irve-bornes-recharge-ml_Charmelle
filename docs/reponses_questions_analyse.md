# Analyses & questions de cadrage — IRVE

## Semaine 1 — Cadrage & premières données

### Question d'analyse
> * En quoi ce dataset permet-il de répondre à une problématique métier réaliste ? Quelles limites identifies-tu déjà à ce stade ?*

### Apport métier
Le jeu de données IRVE répertorie l'ensemble des bornes publiques en France. Il offre la matière nécessaire pour :
* **Cartographier le maillage territorial** et identifier les zones sous-équipées (*déserts de recharge*).
* **Analyser la répartition de la puissance** (lente, rapide, ultra-rapide) face aux besoins stratégiques des axes de transport.
* **Identifier les acteurs majeurs** (aménageurs/opérateurs) et évaluer la maturité du réseau selon les territoires.

### Limites identifiées
* **Données déclaratives :** hétérogénéité des libellés (noms d'opérateurs non harmonisés, doublons potentiels).
* **Absence de données d'usage :** pas d'information sur la fréquentation réelle, le taux d'occupation ou les pannes des bornes.
* **Retraitements techniques nécessaires :** coordonnées GPS agrégées dans un seul champ texte (`coordonneesXY`) et valeurs de puissance à harmoniser.
* **Périmètre restreint au domaine public :** les bornes privées (entreprises, particuliers) ne figurent pas dans la base, masquant une partie de la capacité globale.

## Semaines 2 - Nettoyage & structuration en base relationnelle (Semaine 2)

### Question d'analyse
> * Pourquoi ce schéma relationnel (normalisation, clés, tables) est-il adapté à tes données et à leur usage futur ?* 

### Justification du Schéma Relationnel
Le passage d'une table plate dénormalisée de plus de 220 000 lignes à une base relationnelle en 3ᵉ forme normale (3NF) répond directement aux contraintes de qualité du jeu de données IRVE et aux besoins d'exploitation futurs.

### Objectif de la normalisation et découpage en 4 tables** : 
Pour éliminer la redondance d'information (répétition systématique des communes, codes postaux et paires aménageur/opérateur) et prévenir les anomalies de mise à jour, la base a été structurée en 4 entités :
  * COMMUNES (Table dimensionnelle géographique) : isole les données territoriales (code_insee, nom_commune, code_postal, code_departement).
  * OPERATEURS (Table dimensionnelle acteurs) : centralise les couples uniques d'acteurs (nom_amenageur, nom_operateur) via une clé auto-incrémentée (id_operateur).
  * STATIONS (Table entité physique) : regroupe les sites géographiques uniques (id_station, latitude, longitude, adresse_station, nbre_pdc).
  * POINTS_DE_CHARGE (Table entité technique) : détaille les équipements électriques rattachés aux stations (id_pdc, puissance_nominale, tranche_puissance, types de prises).
  
  ### Adaptation à la structure des données
   * Élimination de la redondance: la suppression de la duplication massive des données textuelles réduit l'espace de stockage et sécurise l'intégrité de la base.
   * Respect de la hiérarchie métier : le modèle reflète la chaîne physique réelle : Territoire (COMMUNES) --> Gestionnaire (OPERATEURS) --> physique (STATIONS) --> borne technique (POINTS_DE_CHARGE).
   * Garantie d'intégrité relationnelle : le verrouillage par clés primaires (PK) et étrangères (FK) empêche la création de points de charge « orphelins » ou de stations positionnées hors d'une commune référencée.
   
   ### Adaptation aux usages futurs
   **Pour l'API REST FastAPI** : 
     * La séparation en 4 entités correspond exactement à la logique de conception d'une API (ressources /communes, /operateurs, /stations, /points-de-charge).
     * Les requêtes SQL/ORM (SQLAlchemy) associées aux endpoints CRUD seront ultra-rapides, car elles filtreront des tables indexées légères au lieu de scanner une table plate volumineuse.

   **Pour le Machine Learning** 
    * La table POINTS_DE_CHARGE isole proprement la variable cible (tranche_puissance) et ses descripteurs techniques. 
    * Les jointures simples avec STATIONS et COMMUNES permettent d'extraire rapidement des variables explicatives géographiques sans polluer le jeu d'entraînement.

**Maintenabilité et évolutivité** : si un opérateur change de nom ou si une station ajoute de nouvelles bornes, la mise à jour s'effectue sur une seule ligne ciblée sans risquer d'altérer le reste de la base.