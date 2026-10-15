# Réponses aux questions d'analyse : IRVE

Problématique : *dans le cadre de la transition énergétique, où se situent les déserts de recharge en France et les territoires sous-équipés en bornes de 150 kW et plus, et quelle dynamique de déploiement permet d'orienter les futures installations ?*

Les chiffres cités proviennent des notebooks du projet (`notebooks/01` à `05`).

---

## Semaine 1 : cadrage et premières données

> *En quoi ce dataset permet-il de répondre à une problématique métier réaliste ? Quelles limites identifies-tu déjà à ce stade ?*

### Apport métier

Le fichier consolidé des IRVE (data.gouv.fr) recense les points de recharge ouverts au public en France : 226 963 lignes et 52 colonnes. Il décrit chaque point : position, puissance, prises, aménageur, opérateur, type d'implantation et date de mise en service.

La problématique est réaliste parce qu'elle répond à des besoins publics concrets :

- **Les collectivités** élaborent des schémas directeurs de la recharge (décret n° 2021-565), qui commencent par un diagnostic territorial.
- **Le règlement européen AFIR** (UE) 2023/1804 impose un parc de recharge d'au moins 150 kW tous les 60 km sur le réseau routier central.

Croisé avec la population communale, le jeu permet de mesurer où l'offre manque, en tenant compte du nombre d'habitants concernés.

### Limites identifiées dès le diagnostic

| Limite | Mesure |
|---|---|
| Un même point publié par plusieurs sources | 60 105 lignes en excédent, avec des valeurs parfois contradictoires (puissance différente pour 9,3 % des points publiés plusieurs fois) |
| Géographie incomplète | 24,9 % des lignes sans code INSEE ; une partie des codes présents sont des codes postaux |
| Puissances hétérogènes | valeurs saisies en watts au lieu de kilowatts (jusqu'à 160 000) ; 3 360 puissances nulles |
| Couverture temporelle partielle | date de mise en service renseignée pour environ 60 % des points, selon le producteur |
| Offre uniquement | aucune donnée d'usage (fréquentation, occupation, pannes) : le besoin ne se mesure pas directement |
| Population absente | il faut une source externe pour rapporter l'offre aux habitants |

---

## Semaine 2 : nettoyage et base relationnelle

> *Pourquoi ce schéma relationnel (normalisation, clés, tables) est-il adapté à tes données et à leur usage futur ?*

### Ce que le nettoyage a produit

- `irve_points_clean.csv` : **166 430 points de charge** distincts, 20 colonnes. Aucune valeur manquante, sauf la date de mise en service, que plusieurs producteurs ne publient pas.
- `communes_population_clean.csv` : **34 868 communes**, y compris les 24 038 communes sans aucun point, avec leur population, leur distance au point le plus proche et leurs indicateurs de désert.

Les principales règles de nettoyage :

- dédoublonnage par point, en privilégiant la source dont les coordonnées concordent avec la commune publiée ;
- conversion des puissances saisies en watts ;
- rattachement de chaque point à sa commune par la position (contours communaux 2025) ;
- regroupement des arrondissements de Paris, Lyon et Marseille.

### Le schéma : 6 tables en troisième forme normale

| Table | Contenu | Clé primaire | Clés étrangères |
|---|---|---|---|
| REGION | 18 régions | `code_region` | — |
| DEPARTEMENT | 101 départements | `code_departement` | `code_region` |
| COMMUNE | 34 869 communes, population, distances, indicateurs de désert | `code_insee` | `code_departement` |
| ACTEUR | 4 856 aménageurs et opérateurs | `id_acteur` | — |
| STATION | 49 236 stations : nom, adresse, implantation, accès, position | `id_station` | `code_insee`, `id_amenageur`, `id_operateur` |
| POINT_DE_CHARGE | 166 430 points : puissance, prises, date | `id_pdc` | `id_station` |

Une vue, `v_equipement_commune`, recalcule à partir des tables le nombre de stations, de points et de points de 150 kW ou plus par commune.

### Pourquoi ce schéma

| Choix | Justification |
|---|---|
| Région et département dans des tables séparées | La région dépend du département, pas de la commune. La stocker dans COMMUNE créerait une dépendance transitive, contraire à la 3e forme normale |
| Une seule table ACTEUR, référencée deux fois par STATION | Aménageur (qui finance) et opérateur (qui exploite) sont deux rôles distincts, différents pour 62 % des points. Le nom d'une entreprise n'est stocké qu'une fois, quel que soit son rôle |
| Attributs répartis entre STATION et POINT_DE_CHARGE, selon une mesure | Nom, adresse, implantation et acteurs sont identiques dans 98,4 % à 99,96 % des stations : ils appartiennent à la station. La puissance varie dans 34,9 % des stations : elle appartient au point |
| Cardinalité 0,n entre COMMUNE et STATION | Les communes sans borne restent dans la base : c'est ce qui permet de mesurer les déserts |
| Comptages dans une vue, pas dans une table | Un comptage stocké deviendrait faux à la première insertion ; la vue est toujours à jour |
| Contraintes CHECK, NOT NULL et clés étrangères | La base refuse une puissance nulle ou supérieure à 600 kW, une prise autre que 0 ou 1, un point sans station ou une station sans commune |

### Adaptation à l'usage futur

- **L'API** s'appuie sur ces contraintes : une écriture invalide est refusée par la base même si un contrôle applicatif était oublié.
- **L'analyse et le machine learning** partent de la table communale, qui contient toutes les communes, équipées ou non.
- **La mise à jour** est simple : renommer un opérateur ne modifie qu'une ligne de la table ACTEUR.

---

## Semaine 3 : API sur mesure

> *Quels choix as-tu faits pour organiser et sécuriser cette API, et en quoi une API répond-elle mieux à ce contexte qu'un accès direct à la base ?*

### Organisation

L'API est construite avec FastAPI dans le dossier `api/`, découpé en quatre fichiers :

| Fichier | Rôle |
|---|---|
| `main.py` | les routes |
| `database.py` | la connexion à la base |
| `schemas.py` | la validation des données |
| `security.py` | la clé d'API |

| Ressource | Opérations |
|---|---|
| `/stats` | GET : chiffres clés du réseau et des déserts |
| `/communes`, `/communes/{code_insee}`, `/deserts` | GET, avec filtres (département, région, désert) |
| `/stations`, `/stations/{id_station}` | GET |
| `/points-de-charge` | **GET, POST, PUT, PATCH, DELETE** : le CRUD complet |

Les routes de lecture répondent directement à la problématique : par exemple, `/deserts` renvoie les communes en désert, les plus peuplées d'abord. La documentation interactive est générée automatiquement à l'adresse `/docs`.

### Sécurité

| Mesure | Effet |
|---|---|
| Clé d'API (en-tête `X-API-Key`) exigée pour POST, PUT, PATCH et DELETE | La lecture est publique, l'écriture est réservée. La clé est stockée hors du code (`.env`, exclu de Git) et comparée en temps constant (`secrets.compare_digest`). Sans clé configurée, l'écriture est désactivée (erreur 503) |
| Validation par Pydantic | Puissance entre 0 et 600 kW, prises booléennes, date entre 2000 et aujourd'hui, format des identifiants imposé, champs inconnus refusés (erreur 422) |
| Requêtes SQL paramétrées | Aucune injection SQL possible |
| Clés étrangères activées à chaque connexion | Impossible de créer un point rattaché à une station inexistante (erreur 409) |
| Pagination plafonnée à 500 lignes | Une requête ne peut pas extraire toute la base d'un coup |
| Serveur local uniquement (127.0.0.1) | Aucune exposition sur un réseau, conformément au brief (pas de cloud) |

Les 29 tests automatiques (`pytest`) vérifient chaque opération et chaque refus. Ils s'exécutent sur une copie temporaire de la base : la vraie base n'est jamais modifiée par les tests.

### Pourquoi une API plutôt qu'un accès direct à la base

- **Contrôle** : un utilisateur de l'API ne peut faire que les opérations prévues, jamais `DROP TABLE` ni une modification de schéma.
- **Règles centralisées** : la validation est écrite une fois et s'applique à tous les clients (script, tableau de bord, application).
- **Découplage** : si la base passe de SQLite à PostgreSQL, ou si une colonne est renommée, le contrat JSON reste le même pour les clients.
- **Accès standard** : HTTP et JSON se lisent depuis n'importe quel langage, alors qu'un fichier SQLite doit être copié sur la machine de chaque utilisateur.

---

## Semaine 4 : analyse exploratoire et veille

> *Quelles tendances IA / Big Data ?*

La veille complète est dans `docs/veille_ia_bigdata.md`. Quatre tendances se dégagent :

1. **La planification hybride SIG + machine learning.** La littérature récente (revue de 91 études, 2025) combine filtrage géographique, analyse multicritère et prévision de la demande. Elle relève que les territoires ruraux sont peu étudiés : ce sont précisément ceux où se trouvent les déserts identifiés dans ce projet (629 des 636 déserts de métropole sont hors de toute unité urbaine).
2. **La recharge intelligente et le Vehicle-to-Grid.** Le V2G est commercialisé en France depuis octobre 2024. Le pilotage de la recharge repose sur la prévision (consommation, prix, disponibilité des véhicules), un terrain classique du machine learning.
3. **Le passage des fichiers statiques aux flux de données.** Le règlement AFIR impose de publier des données statiques et dynamiques (disponibilité, tarifs) via une API. QualiCharge les collecte déjà auprès des opérateurs de recharge rapide. Ce passage fait entrer les données de recharge dans le Big Data : volume et vélocité.
4. **L'encadrement de l'IA.** L'AI Act impose documentation, gouvernance des données et supervision humaine aux systèmes à haut risque, avec des obligations reportées au 2 décembre 2027.

**Ce que l'analyse exploratoire du projet confirme :**

- **La couverture** : la moitié de la population vit à moins de 640 m d'un point. 0,90 % de la population vit dans un désert de recharge et 2,44 % dans un désert 150 kW.
- **La dynamique** : la part des points de 150 kW et plus parmi les mises en service est passée de 8,8 % en 2021 à 28,3 % en 2025.
- **La limite principale** : elle tient aux données, pas aux algorithmes. Le fichier ouvert compte 16,8 % de points de moins que le baromètre Avere-France, et il ne décrit pas l'usage.

---

## Semaine 5 : tableau de bord Power BI

> *Pourquoi ces indicateurs et ces visualisations pour la problématique ?*

Le tableau de bord (`dashboard/irve_bi.pbix`) lit les deux jeux propres du projet. Il compte trois pages, une par partie de la problématique.

| Page | Question traitée |
|---|---|
| 1. Couverture et déserts | Où se situent les déserts de recharge ? |
| 2. Recharge 150 kW | Quels territoires sont sous-équipés en bornes de 150 kW et plus ? |
| 3. Acteurs et dynamique | Quelle dynamique de déploiement ? |

### Les indicateurs et leur justification

| Indicateur | Valeur (France entière) | Pourquoi cet indicateur |
|---|---|---|
| Communes en désert de recharge | 685 | Mesure directe de l'axe 1, selon une définition fixée à l'avance (aucun point dans la commune et plus de 10 km jusqu'au point le plus proche) |
| Part de la population en désert | 0,9 % (614 653 habitants) | Une commune de 50 habitants ne pèse pas comme une ville : la population concernée donne la gravité réelle |
| Points pour 10 000 habitants | 24,38 | Mesure du sous-équipement rapportée à la population. Elle est lue par département, car à l'échelle d'une commune les ratios sont instables (une borne dans un village de 100 habitants donne 100 points pour 10 000) |
| Part des points de 150 kW et plus | 18,6 % | Seuil tiré du règlement européen AFIR, qui exige un point de 150 kW tous les 60 km sur le réseau routier central |
| Points de 150 kW pour 100 000 habitants | 45,3 | Densité de recharge ultra-rapide, comparable entre territoires |
| Population en désert 150 kW | 1 664 343 habitants (2,4 %) | Mesure directe de l'axe 2 : habitants à plus de 30 km d'un point de 150 kW, soit la moitié de l'espacement AFIR |
| Nombre d'opérateurs | 343 | Structure du marché : un marché très fragmenté, ou au contraire dominé par un acteur, oriente différemment le déploiement |
| Part des points datés | 60,8 % | Indicateur de fiabilité : il rappelle que les tendances ne portent que sur les points dont la date de mise en service est connue |

Le dernier indicateur ne mesure pas l'équipement : il mesure la **qualité de la donnée**. Il évite de présenter une tendance comme si elle couvrait tout le parc.

### Les visualisations et leur justification

| Visualisation | Pourquoi ce choix |
|---|---|
| **Cartes des communes en désert** (pages 1 et 2), bulles proportionnelles à la population | La problématique est géographique : la carte montre *où* se trouvent les déserts. Elle est limitée à la métropole par un filtre propre au visuel, pour rester lisible |
| **Barres par région** (population en désert, part des 150 kW) | Comparer des territoires entre eux. C'est ici que l'outre-mer reste visible : Mayotte et la Guyane concentrent la majorité de la population en désert |
| **Tableau des départements** avec mise en forme conditionnelle | Passer de la carte au détail : nombre de communes en désert et points pour 10 000 habitants, département par département |
| **Barres par catégorie de puissance AFIR**, dans l'ordre des catégories | Montrer la structure du parc : la recharge de 7,4 à 22 kW domine (55,9 % des points) |
| **Les 15 premiers opérateurs** | Montrer la fragmentation du marché : le premier opérateur exploite environ 9 % des points |
| **Deux graphiques alignés sur les mêmes années** : points mis en service (barres) et part des points de 150 kW (courbe) | Montrer la dynamique : mises en service doublées entre 2021 et 2025, part des 150 kW passée de 8,8 % (2021) à 31,9 % (2024). Ce sont deux graphiques séparés et non un graphique à deux axes verticaux : deux échelles sans rapport (nombre de points et pourcentage) superposées inviteraient à comparer des hauteurs qui ne se comparent pas |
| **Barres empilées à 100 % : implantation × type de courant** | Montrer où se trouve la recharge rapide : 74,6 % en courant continu dans les stations dédiées, 22,0 % sur la voirie |

### Choix de conception

- **Des chiffres France entière, une carte métropolitaine.** Les indicateurs et les graphiques par région couvrent la métropole et les 5 départements d'outre-mer. Seule la carte est limitée à la métropole, sinon la taille relative des bulles écraserait les petites communes rurales.
- **Un titre dynamique**, qui se met à jour selon la région ou le département sélectionné. La phrase clé reste lisible quel que soit le filtre.
- **Des segments synchronisés entre les pages.** Une région choisie sur une page reste sélectionnée sur les autres.
- **Des couleurs qui ont un sens fixe** : bleu pour le volume de points, rouge pour les déserts de recharge, orange pour le 150 kW et le courant continu. La palette est choisie pour rester distinguable par les personnes daltoniennes.
- **Des valeurs contrôlées.** Chaque indicateur a été comparé aux résultats des notebooks d'analyse.

### Limites

- **Opérateurs** : Power BI ne distingue pas les majuscules des minuscules, d'où 343 opérateurs contre 338 dans l'analyse Python. Celle-ci regroupe aussi les variantes d'accents et de ponctuation.
- **Tendances** : les graphiques par année ne portent que sur les points datés (60,8 % du parc), et l'année 2026 s'arrête fin août.

---

## Semaine 6 : machine learning et risques

> *Pourquoi ce modèle ? Quels risques majeurs as-tu identifiés et comment les limiter ?*

### Question posée au modèle

Au vu de son profil, une commune devrait-elle avoir au moins un point de charge ?

Les communes **sans point** dont le profil ressemble à celui des communes équipées forment une liste de territoires prioritaires.

- **Target** : commune équipée (31,0 % des 34 739 communes de métropole).
- **Features** : population et densité (en logarithme), position, type de commune dans l'aire d'attraction des villes, unité urbaine, zone de montagne, région.

### Pourquoi ce modèle

Trois modèles ont été comparés par GridSearchCV. Le test porte sur 20 départements jamais vus pendant l'entraînement.

| Modèle | AUC test | Average precision | F1 (threshold 0,5) |
|---|---|---|---|
| Logistic Regression | 0,871 | 0,819 | 0,708 |
| Random Forest | 0,873 | 0,817 | 0,706 |
| XGBoost | 0,874 | 0,819 | 0,704 |
| Baseline : population seule | 0,867 | 0,814 | 0,703 |

**La Logistic Regression est retenue**, selon une règle fixée avant les résultats : si l'écart d'AUC avec le meilleur modèle est inférieur à 0,01, le modèle le plus simple l'emporte. L'écart avec XGBoost est de 0,003. Trois raisons à ce choix :

- **Lisibilité** : ses coefficients s'expliquent à un public non technique.
- **Stabilité** : elle a moins d'hyperparamètres, donc moins de risque d'overfitting.
- **Coût** : elle s'entraîne en 3 secondes, contre 34 pour la Random Forest.

**Résultat principal.** La population explique presque tout : la permutation importance de la population vaut 0,355, contre moins de 0,02 pour les autres variables. Le déploiement suit la population. Le scoring identifie **557 communes sans point avec une probabilité d'équipement supérieure à 0,7** (1,62 million d'habitants). Ce sont surtout des communes de la couronne des villes, à moins de 5 km d'un point dans 79,4 % des cas : il s'agit d'un sous-équipement relatif, pas d'un éloignement.

### Clustering : typologie des stations

Un K-Means, modèle non supervisé, regroupe les 49 180 stations selon six features :
- le nombre de points ;
- la puissance maximale ;
- la part de points en courant continu ;
- la part de points avec prise domestique ;
- la part de points en accès libre ;
- la population de la commune.

Le type d'implantation déclaré est trop peu fiable pour construire les groupes : il sert seulement à les décrire.

**Choix de k = 4.** Trois critères :
- **Méthode du coude** : l'inertie baisse de 33 750 en passant à 4 clusters, puis de 16 695 seulement en passant à 5.
- **Stabilité** : les groupes sont identiques d'une initialisation à l'autre (ARI 0,999).
- **Lisibilité** : k = 3 obtient une silhouette légèrement meilleure, mais fusionne les deux types de bornes en courant alternatif.

La silhouette, autour de 0,33, indique une structure modérée.

| Type | Part des stations | Profil |
|---|---|---|
| AC de proximité avec prise domestique | 34,0 % | 2 points, 22 kW, voirie, communes plutôt petites |
| AC urbaine | 32,9 % | 2 points, 22 kW, sans prise domestique, communes plus peuplées |
| Recharge rapide DC | 24,3 % | 4 points, 150 kW, 81 % en courant continu |
| Accès réservé | 8,8 % | 1 point, 22 kW, accès réservé |

**La recharge rapide n'est pas réservée aux villes** : elle représente 18,8 % des stations dans les communes de moins de 500 habitants et 25,6 % au-delà de 10 000.

**Les écarts régionaux confirment l'analyse exploratoire** : 38,4 % de stations de recharge rapide en Bourgogne-Franche-Comté, contre 18,1 % en Île-de-France.

### Risques et mesures

L'évaluation complète, avec 21 risques classés par probabilité et impact, est dans `docs/evaluation_risques.md`. Les principaux :

| Risque | Constat | Mesure prise |
|---|---|---|
| Data leakage | La distance au point le plus proche et le nombre de stations contiennent la réponse | Variables exclues ; StandardScaler et OneHotEncoder dans le pipeline scikit-learn, ajustés sur le train seul ; target jamais complétée |
| Leakage spatial | Des communes voisines se ressemblent : un split aléatoire surestimerait le score | Train / test split et cross-validation par groupes de départements |
| Qualité des données | 2 526 puissances estimées ; couverture du fichier inférieure au baromètre national | Effet mesuré : les déserts 150 kW sont inchangés sans les puissances estimées ; écart de couverture documenté |
| Variables liées entre elles | La superficie rendait les coefficients incohérents et faussait les très grandes communes (Guyane) | Superficie retirée |
| Extrapolation | Les 129 communes d'outre-mer sont hors du domaine d'entraînement | Modèle non appliqué à l'outre-mer, contrôle automatique dans le notebook |
| Biais du modèle | Le modèle apprend le déploiement passé : une commune « attendue » équipée n'en a pas forcément besoin | La liste est une aide à la décision, à croiser avec le terrain ; aucune décision automatique |
| Usage et éthique | Un classement peut orienter des investissements publics au détriment des petites communes | Les déserts ruraux sont présentés à part, avec la population concernée ; la méthode et les limites sont documentées |

---

## Semaine 7 : restitution

> *Comment le discours a-t-il été adapté à un public non technique ?*

Le support (`docs/restitution_irve.pptx`) compte 10 diapositives pour un oral de 5 à 10 minutes, démonstration du tableau de bord comprise. Le texte de l'oral figure dans les notes de l'orateur.

### Une histoire plutôt qu'un rapport

Le discours suit un fil narratif, et non l'ordre des étapes techniques du projet :

| Temps du récit | Message | Diapositives |
|---|---|---|
| Accroche | « Si vous achetiez une voiture électrique demain, où la rechargeriez-vous ? » | 1 |
| Situation | La couverture est large : la moitié des habitants vit à moins de 640 m d'une borne | 2-3 |
| Retournement | La moyenne cache des inégalités : 73 % des habitants en désert vivent outre-mer, et Mayotte n'a aucune borne publiée | 4-5 |
| Preuve | Démonstration du tableau de bord : les chiffres se recalculent pour chaque territoire | 6 |
| Dynamique | Le déploiement a doublé et se tourne vers la recharge rapide | 7 |
| Exceptions | Un modèle repère 557 communes sans borne qui devraient en avoir une | 8 |
| Action | Trois priorités : outre-mer, villages isolés, bourgs périurbains | 9 |
| Honnêteté | Ce que les données permettent d'affirmer, et ce qu'elles ne disent pas | 10 |

### Les adaptations

- **Une idée par diapositive**, énoncée dans le titre : le titre est la conclusion (« Les déserts de recharge sont d'abord ultramarins »), pas un thème (« Analyse des déserts »).
- **Aucun vocabulaire technique à l'écran.** Le dédoublonnage, la géolocalisation par contour communal, la cross-validation ou le K-Means restent dans les notebooks, pour les questions. Le modèle est présenté par ce qu'il fait : « il devine si une commune est équipée dans 87 % des comparaisons ».
- **Des chiffres traduits en repères concrets** : « 640 mètres », « 1 borne sur 3 », « une ville de 5 000 habitants a 91 % de chances d'être équipée », plutôt qu'une AUC de 0,871 ou une part de 31,9 %.
- **Des définitions posées avant les résultats**, en une phrase chacune : un désert de recharge, un désert de recharge rapide, avec leur traduction (« la recharge des longs trajets, environ 20 minutes »).
- **Un exemple réel** (Thorigny-sur-Marne : 10 440 habitants, sans borne, la plus proche à 1,3 km) plutôt qu'une liste de communes.
- **Des graphiques réduits à l'essentiel** : une seule série par graphique, valeurs écrites sur les barres, aucun axe secondaire.
- **Les mêmes couleurs que le tableau de bord** : rouge pour les déserts, orange pour la recharge rapide, bleu pour les bornes. Le public les retrouve pendant la démonstration.
- **La démonstration remplace les captures d'écran.** Sélectionner une région devant le public montre que les chiffres ne sont pas figés.
- **Des recommandations**, parce qu'un public non technique attend une conclusion utile : où installer les prochaines bornes.
- **Les limites dites simplement**, à la fin : le projet mesure les bornes, pas leur utilisation ; le fichier public est incomplet ; les distances sont à vol d'oiseau.
