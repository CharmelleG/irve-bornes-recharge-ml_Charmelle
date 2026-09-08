# Analyses & questions de cadrage — IRVE

## Semaine 1 — Cadrage & premières données

### Question d'analyse
> *En quoi ce dataset permet-il de répondre à une problématique métier réaliste ? Quelles limites identifies-tu déjà à ce stade ?*

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