# Évaluation des risques : IRVE

Ce document recense les risques qui peuvent rendre les résultats du projet faux, trompeurs ou mal utilisés. Il couvre quatre familles :
- la qualité et les biais des données ;
- le risque lié aux modèles ;
- le déploiement ;
- l'éthique.

Pour chaque risque, il indique ce qui a été mesuré, ce qui a été fait pour le limiter, et ce qui reste.

Les chiffres proviennent des notebooks `01` à `05`. Les résultats concernés sont :
- la localisation des déserts de recharge (685 communes, 0,90 % de la population) ;
- la localisation des déserts 150 kW (306 communes, 2,44 % de la population) ;
- le scoring des communes sans borne (557 communes au-dessus d'une probabilité de 0,7) ;
- la typologie des stations (4 types).

**Échelle utilisée.**
- *Probabilité* : le risque est-il présent dans les données ou le traitement ? (faible, moyenne, élevée)
- *Impact* : s'il se réalise, change-t-il une conclusion ? (faible, moyen, élevé)
- *Risque résiduel* : ce qui reste après les mesures prises.

---

## Synthèse

| # | Risque | Famille | Probabilité | Impact | Risque résiduel |
|---|---|---|---|---|---|
| D1 | Couverture incomplète du fichier ouvert | Données | Élevée | Moyen | **Moyen** |
| D2 | Doublons et valeurs contradictoires entre sources | Données | Élevée | Moyen | Faible |
| D3 | Géographie manquante ou fausse | Données | Élevée | Élevé | Faible |
| D4 | Puissances erronées ou estimées | Données | Moyenne | Moyen | Faible |
| D5 | Dates de mise en service manquantes, de façon non aléatoire | Données | Élevée | Moyen | **Moyen** |
| D6 | Mesure de l'offre seulement, pas de l'usage | Données | Certaine | Élevé | **Élevé** |
| D7 | Définition du désert : seuil, centre de la commune, vol d'oiseau | Données | Certaine | Moyen | Moyen |
| M1 | Data leakage | Modèle | Moyenne | Élevé | Faible |
| M2 | Score trop optimiste à cause de la proximité géographique | Modèle | Élevée | Moyen | Faible |
| M3 | Modèle qui reproduit le déploiement passé | Modèle | Certaine | Élevé | **Élevé** |
| M4 | Extrapolation hors du domaine d'entraînement | Modèle | Élevée | Élevé | Faible |
| M5 | Faible apport du modèle au-delà de la population | Modèle | Certaine | Moyen | Moyen |
| M6 | Typologie des stations aux frontières floues | Modèle | Certaine | Faible | Faible |
| P1 | Données vieillissantes | Déploiement | Certaine | Moyen | **Moyen** |
| P2 | Sécurité de l'API | Déploiement | Faible | Élevé | Faible |
| P3 | Reproductibilité | Déploiement | Moyenne | Moyen | Faible |
| P4 | Lecture erronée du tableau de bord | Déploiement | Moyenne | Moyen | Faible |
| E1 | Iniquité territoriale du scoring | Éthique | Élevée | Élevé | Moyen |
| E2 | Invisibilisation de l'outre-mer | Éthique | Élevée | Élevé | Faible |
| E3 | Données personnelles | Éthique | Faible | Moyen | Faible |
| E4 | Décision automatisée et encadrement de l'IA | Éthique | Faible | Élevé | Faible |

Les quatre risques résiduels les plus importants sont **D6** et **M3** (le projet décrit l'offre, pas le besoin), puis **D1** et **D5** (couverture et datation incomplètes). Ils ne remettent pas en cause la localisation des déserts, mais ils limitent ce qu'on peut affirmer sur le besoin et sur le rythme du déploiement.

---

## 1. Qualité et biais des données

### D1. Couverture incomplète du fichier ouvert
- **Constat.** Le fichier consolidé nettoyé compte **166 430 points**. Le baromètre Avere-France, établi avec les données Gireve, en recense **200 045** ouverts au public au 31/07/2026, soit 16,8 % de plus.
- **Cause.** Elle n'est pas établie par les données : certains opérateurs ne publient pas sur data.gouv.fr, et les définitions des deux sources peuvent différer.
- **Effet possible.** Une commune peut apparaître en désert alors qu'elle a une borne non publiée. Les déserts sont donc des **déserts « au regard des données ouvertes »** : c'est un plafond, pas une mesure exacte.
- **Mesures.** L'écart est documenté dans le README et dans la synthèse de veille. La part des points de plus de 150 kW concorde entre les deux sources (13,8 % dans le projet, 13 % selon Avere-France) : la structure du parc est fiable, même si son volume est incomplet.
- **Risque résiduel : moyen.**

### D2. Doublons et valeurs contradictoires entre sources
- **Constat.** 60 105 lignes en excédent : un même point est publié par plusieurs producteurs. Parmi les points publiés plusieurs fois, les sources se contredisent sur la puissance pour 9,3 % d'entre eux, et sur le type d'implantation pour 41,2 %.
- **Mesures.**
  - Dédoublonnage par identifiant. Quand plusieurs sources publient le même point, on retient d'abord celle dont la position concorde avec la commune publiée, puis celle dont la géographie est vérifiée, puis la plus complète et la plus récente.
  - Le type d'implantation, trop contradictoire, ne sert pas à construire la typologie des stations : il sert seulement à la décrire.
- **Risque résiduel : faible** pour la localisation et la puissance ; **élevé pour l'implantation**, qui n'est utilisée qu'à titre descriptif.

### D3. Géographie manquante ou fausse
- **Constat.**
  - 24,9 % des lignes brutes n'ont pas de code INSEE.
  - Ce manque n'est pas aléatoire : deux producteurs (gireve-2, indigo-group) n'en publient aucun, et représentent 75,5 % des absences.
  - Une partie des codes présents sont des codes postaux.
- **Mesures.**
  - Chaque point est rattaché à sa commune par sa **position**, en vérifiant dans quel contour communal (référentiel 2025) il se trouve : 43 636 points géolocalisés, 5 744 codes corrigés.
  - 2 114 coordonnées incohérentes avec la commune publiée sont remplacées par le centre de cette commune.
  - 498 points dont la commune ne peut pas être établie sont supprimés.
- **Effet mesuré.** Une première version, qui supprimait les points incertains au lieu de les corriger, faisait perdre toutes leurs bornes à 518 communes (572 180 habitants) : autant de **faux déserts**. La simulation de la correction n'en laissait plus que 17.
- **Risque résiduel : faible.**

### D4. Puissances erronées ou estimées
- **Constat et mesures.**

  | Cas | Points | Traitement |
  |---|---|---|
  | Puissances saisies en watts | 883 | Converties en kW |
  | Puissances supérieures à 600 kW après conversion | 161 | Considérées comme inconnues |
  | Puissances inconnues au moment de la complétion (absentes, nulles ou supérieures à 600 kW) | 2 526 | Complétées par la médiane des points ayant les mêmes prises |

- **Effet mesuré.** 206 des 30 918 points de 150 kW et plus ont une puissance estimée (0,67 %). Les recalculer sans eux **ne change aucun désert 150 kW** : 306 communes avant comme après.
- **Défaut connu, non corrigé.** 5 points ont une puissance impossible, inférieure à 1,38 kW. C'est le courant minimal de la recharge normale : 6 A × 230 V (norme IEC 61851-1). Leur effet est négligeable.
- **Risque résiduel : faible.**

### D5. Dates de mise en service manquantes, de façon non aléatoire
- **Constat.** 60,8 % des points ont une date. Ce taux dépend du producteur (0 % chez certains, 100 % chez d'autres) et du territoire : 0 % à La Réunion, 4 % en Guadeloupe, 73 % en Normandie.
- **Effet possible.** Les tendances (mises en service doublées entre 2021 et 2025, part des 150 kW passée de 8,8 % à 31,9 %) décrivent les **points datés**, pas le parc entier. Les territoires peu datés pèsent moins dans les tendances.
- **Mesures.**
  - Une date manquante est reprise d'une autre source du même point quand c'est possible (18 639 lignes).
  - La part de points datés est affichée dans le tableau de bord.
  - Les tendances sont présentées comme une direction, pas comme un rythme exact.
- **Risque résiduel : moyen.**

### D6. Mesure de l'offre seulement, pas de l'usage
- **Constat.** Le jeu IRVE décrit les bornes : position, puissance, prises. Il ne contient ni le nombre de sessions, ni le taux d'occupation, ni les pannes, ni la demande des conducteurs.
- **Effet.** Le projet peut dire où il n'y a **pas de borne**. Il ne peut pas dire où il en **faudrait davantage** au regard du besoin. Une commune équipée peut être saturée, et une commune en désert peut ne pas en avoir besoin.
- **Mesures.** La limite est écrite dans la problématique, le README, les notebooks et la veille. Les données dynamiques de QualiCharge et les obligations de l'article 20 du règlement AFIR sont identifiées comme la piste d'amélioration.
- **Risque résiduel : élevé**, propre au jeu de données.

### D7. Définition du désert : seuil, centre de la commune, vol d'oiseau
- **Constat.**
  - La distance part du **centre géographique** de la commune et se mesure **à vol d'oiseau** : elle sous-estime le trajet par la route.
  - Le résultat dépend du seuil : 5,57 % de la population en désert à 5 km, 0,90 % à 10 km, 0,61 % à 15 km.
  - Outre-mer, le point le plus proche peut se trouver sur une autre île.
- **Mesures.**
  - Le seuil de 10 km a été fixé avant les calculs. Celui de 30 km pour le 150 kW découle du règlement AFIR.
  - Une analyse de sensibilité aux seuils est présentée.
  - Une commune qui a au moins un point sur son territoire n'est jamais comptée en désert, même si son centre est éloigné (Arles, Kourou, Laruns).
- **Risque résiduel : moyen.** Les ordres de grandeur sont robustes, mais les effectifs exacts dépendent du seuil.

### Sources externes
- **Population** : « État de la Base Adresse Nationale par commune ». C'est la population légale municipale, mais son millésime n'est pas précisé par la source.
- **Contours communaux** : référentiel 2025. Les fusions de communes de 2025 y sont intégrées : Pierrefitte-sur-Seine est rattachée à Saint-Denis.

Un écart de millésime entre population et contours ne concerne qu'un petit nombre de communes fusionnées.

---

## 2. Risque lié aux modèles

### M1. Data leakage
- **Risque.** Un modèle qui dispose d'une information contenant la réponse obtient un score excellent mais inutilisable.
- **Mesures.**
  - Les features qui contiennent la réponse sont exclues : distance au point le plus proche, nombre de points, nombre de stations.
  - Les étapes qui apprennent des statistiques sur les données (StandardScaler, OneHotEncoder) sont dans le pipeline scikit-learn. Elles sont donc ajustées sur le train seul, à chaque pli de cross-validation.
  - Les transformations faites avec pandas (logarithme, densité) sont calculées commune par commune, sans aucune statistique tirée des autres lignes.
  - La target (commune équipée) n'a jamais été complétée : elle compte des points publiés.
- **Risque résiduel : faible.**

### M2. Score trop optimiste à cause de la proximité géographique
- **Risque.** Deux communes voisines se ressemblent. Les répartir au hasard entre train et test reviendrait à tester le modèle sur des quasi-copies de ce qu'il a appris.
- **Mesures.**
  - Le train / test split et la cross-validation se font par **groupes de départements** (GroupShuffleSplit, GroupKFold).
  - Le test porte sur 20 départements jamais vus.
  - L'écart entre validation (AUC 0,883) et test (AUC 0,871) est faible : pas d'overfitting.
- **Risque résiduel : faible.**

### M3. Modèle qui reproduit le déploiement passé
- **Constat.** La target est l'**équipement actuel**. Le modèle apprend où les bornes ont été installées, pas où elles seraient nécessaires. Les biais du déploiement passé (priorité aux villes, aux axes, aux politiques de certains syndicats d'énergie) sont donc appris.
- **Effet.** Les 557 communes prioritaires sont des communes **sous-équipées par rapport à des communes semblables**. Ce sont surtout des communes de la couronne des villes, à moins de 5 km d'un point dans 79,4 % des cas. Ce ne sont pas des communes dont le besoin serait démontré.
- **Mesures.**
  - Le résultat est présenté comme un **sous-équipement relatif**, pas comme un besoin.
  - Les déserts, définis par la distance, sont présentés séparément du scoring.
- **Risque résiduel : élevé**, inhérent à l'absence de données d'usage (voir D6).

### M4. Extrapolation hors du domaine d'entraînement
- **Constat.**
  - Les 129 communes d'outre-mer ont toutes des coordonnées que le modèle n'a jamais vues.
  - Une première version qui utilisait la superficie donnait une probabilité de 1,00 à Saint-Élie, en Guyane (157 habitants), à cause de sa superficie hors norme.
- **Mesures.**
  - Le modèle est limité à la métropole.
  - Un contrôle automatique du domaine figure dans le notebook.
  - La superficie a été retirée : elle est liée mathématiquement à la population et à la densité.
  - L'outre-mer est traité par l'analyse exploratoire.
- **Risque résiduel : faible.**

### M5. Faible apport du modèle au-delà de la population
- **Constat.**

  | Modèle | AUC test |
  |---|---|
  | Logistic Regression | 0,871 |
  | Random Forest | 0,873 |
  | XGBoost | 0,874 |
  | Baseline : population seule | 0,867 |

  La permutation importance de la population vaut 0,355, contre moins de 0,02 pour chacune des autres features.
- **Effet.** Les autres features (densité, type de commune, relief, région) n'apportent presque rien. Présenter le modèle comme une découverte complexe serait trompeur.
- **Mesures.**
  - La baseline est affichée.
  - Le modèle le plus simple est retenu selon une règle fixée avant les résultats : la Logistic Regression l'emporte si l'écart d'AUC avec le meilleur modèle est inférieur à 0,01.
  - La conclusion est formulée honnêtement : « le déploiement suit la population ».
- **Risque résiduel : moyen**, pour la portée du modèle, pas pour sa validité.

### M6. Typologie des stations aux frontières floues
- **Constat.** La silhouette moyenne du K-Means vaut 0,33 : les groupes existent, mais leurs frontières sont floues. La typologie dépend aussi de l'identifiant de station publié.
- **Mesures.**
  - Le nombre de groupes (k = 4) est choisi sur trois critères : la méthode du coude, la silhouette et la stabilité. Les groupes sont identiques d'une initialisation à l'autre (ARI 0,999).
  - La typologie est présentée comme une simplification descriptive.
- **Risque résiduel : faible.**

---

## 3. Déploiement

### P1. Données vieillissantes
- **Constat.** Les résultats décrivent l'état du fichier au 31/08/2026. Avec environ 20 000 mises en service par an, un désert peut disparaître en quelques mois.
- **Mesures.**
  - Le pipeline est entièrement reproductible : notebooks 01 à 05 exécutés dans l'ordre, sans fichier intermédiaire.
  - La date des données est indiquée dans le README et sur le tableau de bord.
  - Une mise à jour suppose de relancer les notebooks puis d'actualiser Power BI.
- **Point de vigilance.** Une nouvelle version du schéma IRVE, ou un nouveau producteur qui n'aurait pas de code INSEE, imposerait de revoir les règles de nettoyage.
- **Risque résiduel : moyen.**

### P2. Sécurité de l'API
- **Constat.** L'API permet de créer, modifier et supprimer des points de charge.
- **Mesures.**
  - Clé d'API exigée pour toute écriture. Elle est stockée hors du code (`.env`, exclu de Git) et comparée en temps constant.
  - Validation de chaque entrée par Pydantic. Requêtes SQL paramétrées. Clés étrangères et contraintes CHECK actives dans la base.
  - Pagination plafonnée à 500 lignes. Serveur limité à la machine locale.
  - 29 tests automatiques, exécutés sur une copie de la base.
- **Limites.**
  - La clé d'API est unique et commune à tous les utilisateurs, sans gestion des droits par utilisateur.
  - Il n'y a pas de HTTPS. C'est acceptable en local, mais ce serait à ajouter avant toute exposition réseau.
  - SQLite convient à un usage individuel, pas à de nombreux accès concurrents.
- **Risque résiduel : faible** dans le périmètre local du projet.

### P3. Reproductibilité
- **Mesures.**
  - Versions des bibliothèques figées dans `requirements.txt`.
  - Graine aléatoire fixée (42) pour les modèles.
  - Sources de données datées.
  - Journal du nettoyage affiché dans le notebook 01.
- **Limite.** Les fichiers bruts ne sont pas versionnés dans Git en raison de leur taille. Un nouveau téléchargement du fichier consolidé donnera une version plus récente.
- **Risque résiduel : faible.**

### P4. Lecture erronée du tableau de bord
- **Risques.**
  - Confondre les déserts de métropole, nombreux mais peu peuplés, avec ceux d'outre-mer, peu nombreux mais très peuplés.
  - Lire les tendances comme couvrant tout le parc.
  - Comparer deux mesures d'échelles différentes sur un même graphique.
- **Mesures.**
  - Indicateurs pondérés par la population.
  - Carte limitée à la métropole, avec l'outre-mer présenté dans les graphiques par région.
  - Mention « points datés uniquement » sur les tendances.
  - Couleurs à sens fixe. Valeurs contrôlées contre les notebooks.
- **Risque résiduel : faible.**

---

## 4. Éthique

### E1. Iniquité territoriale du scoring
- **Risque.** Un classement fondé sur la probabilité d'équipement favorise mécaniquement les communes peuplées. S'il servait seul à répartir des financements, les déserts ruraux passeraient en dernier : les 636 déserts de métropole ont une population médiane de 153 habitants.
- **Mesures.**
  - Le scoring n'est jamais présenté seul. Les déserts, définis par la distance et pondérés par la population concernée, sont présentés à part, comme premier résultat.
  - La note de lecture du notebook 05 précise que la liste est une aide à la décision, à croiser avec le terrain.
- **Risque résiduel : moyen.** Un utilisateur pressé pourrait ne retenir que le classement.

### E2. Invisibilisation de l'outre-mer
- **Risque.** L'outre-mer est exclu du modèle et de la carte. Or c'est là que vit la majorité de la population en désert : toute la population de Mayotte (256 518 habitants, aucun point publié) et 47 % de celle de la Guyane.
- **Mesures.**
  - Les indicateurs et les graphiques par région couvrent la métropole et les 5 départements d'outre-mer.
  - Un tableau métropole / outre-mer est consacré au 150 kW (73,3 % de la population ultramarine en désert 150 kW).
  - Le cas ultramarin est signalé comme relevant d'un diagnostic distinct.
- **Risque résiduel : faible.**

### E3. Données personnelles
- **Constat.** Le fichier brut contient des coordonnées de contact (`contact_amenageur`, `contact_operateur`, `telephone_operateur`). 740 contacts d'aménageurs sont des adresses de messagerie personnelle (gmail, orange, free…) : ils peuvent désigner des personnes physiques, comme des gîtes ou de petits commerces.
- **Mesures.**
  - Aucune de ces colonnes n'est conservée dans le jeu propre, la base de données, l'API ou le tableau de bord.
  - Les aménageurs et opérateurs ne sont désignés que par leur nom.
  - Les données sources sont publiques, sous Licence Ouverte 2.0, dont la mention de source est respectée.
- **Risque résiduel : faible.**

### E4. Décision automatisée et encadrement de l'IA
- **Constat.** Le règlement européen sur l'intelligence artificielle (UE) 2024/1689 impose des obligations renforcées aux systèmes à haut risque, dont ceux qui gèrent ou exploitent des infrastructures critiques. Le scoring du projet ne pilote ni n'exploite aucune infrastructure : il classe des communes pour éclairer une décision humaine. Il ne relève donc pas de cette catégorie.
- **Mesures.** Les bonnes pratiques exigées pour les systèmes à haut risque sont appliquées volontairement :
  - documentation des données et des règles ;
  - validation honnête ;
  - contrôle du domaine d'application ;
  - supervision humaine.

  Aucune décision n'est automatisée.
- **Risque résiduel : faible.**

---

## Conclusion

Les résultats les plus solides du projet sont **la localisation des déserts de recharge et des déserts 150 kW**. Ils résistent au traitement des puissances estimées, au choix de la source lors du dédoublonnage et à la correction géographique. Leur ampleur dépend seulement du seuil retenu, qui est publié avec une analyse de sensibilité.

Les résultats les plus fragiles sont ceux qui touchent au **besoin** et au **rythme** :
- le scoring mesure un sous-équipement relatif, pas une demande ;
- les tendances ne couvrent que les points datés.

Les deux limites ont la même cause : les données décrivent l'offre, pas l'usage. La piste principale pour les lever est l'intégration des données dynamiques de recharge (disponibilité, occupation), que le règlement AFIR rend progressivement accessibles.
