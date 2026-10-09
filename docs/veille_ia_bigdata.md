# Veille IA et Big Data : la recharge des véhicules électriques

Veille réalisée en octobre 2026, en lien avec la problématique du projet : localiser les déserts de recharge et les territoires sous-équipés en bornes de 150 kW et plus, pour orienter les futures installations.

**Méthode.** Trois sujets, choisis parce qu'ils prolongent directement le projet :

1. l'IA au service de la planification des bornes ;
2. la recharge intelligente et le Vehicle-to-Grid (V2G) ;
3. le Big Data et les données ouvertes IRVE.

Un quatrième point traite du cadre réglementaire de l'IA (AI Act), qui conditionne tout usage d'un modèle.

Sources privilégiées, dans cet ordre : textes réglementaires et organismes publics (Commission européenne, ministère, data.gouv.fr, Enedis), publications scientifiques à comité de lecture, puis presse spécialisée. Chaque affirmation renvoie à une source listée en fin de document. Les chiffres du projet sont issus des notebooks 01 à 05.

---

## 1. L'IA au service de la planification des bornes

### Le cadre : les schémas directeurs

La loi d'orientation des mobilités (décembre 2019) et le décret n° 2021-565 du 10 mai 2021 permettent aux collectivités d'élaborer un **schéma directeur des infrastructures de recharge (SDIRVE)** [1]. Un SDIRVE comprend :

- un diagnostic ;
- des priorités et des objectifs ;
- un calendrier d'actions ;
- une concertation avec les acteurs de la recharge [1].

C'est le cadre dans lequel une analyse comme celle de ce projet trouve un usage concret : le diagnostic territorial.

Au niveau européen, le règlement AFIR (UE) 2023/1804, applicable depuis le 13 avril 2024, fixe des objectifs chiffrés sur le réseau routier central RTE-T. Un parc de recharge est exigé tous les 60 km dans chaque sens de circulation, selon deux échéances [2][3] :

| Échéance | Puissance du parc | Dont points de 150 kW ou plus |
|---|---|---|
| 31 décembre 2025 | 400 kW au moins | au moins 1 |
| 31 décembre 2027 | 600 kW au moins | au moins 2 |

Ces objectifs sont à l'origine du seuil « désert 150 kW » du projet : 30 km, soit la moitié de l'espacement de 60 km.

### L'état de la recherche

Une revue systématique publiée en 2025 analyse **91 études** parues entre 2011 et 2024 sur la localisation des bornes [4]. Elle classe les méthodes en trois familles :

| Famille | Exemples | Rôle |
|---|---|---|
| Optimisation mathématique | programmation linéaire, couverture maximale | placer N bornes au mieux sous contraintes |
| Systèmes d'information géographique (SIG) | analyse multicritère, superposition de couches | filtrer les sites possibles |
| Machine learning | prévision de la demande, classification de sites | estimer où le besoin apparaîtra |

Les auteurs proposent de combiner les trois : un filtrage spatial, puis une analyse multicritère, puis une prévision de la demande par machine learning. Ils relèvent trois manques dans la littérature [4] :

- les territoires ruraux sont peu étudiés ;
- les données en temps réel sont peu intégrées ;
- le comportement des usagers est traité de façon incohérente.

### Lien avec le projet

- **La démarche du projet suit cette approche hybride.** La partie SIG rattache chaque point à sa commune par son contour géographique et calcule la distance au point le plus proche. La partie machine learning est un modèle de scoring des communes, validé par cross-validation groupée par département.
- **La limite relevée par la revue se vérifie sur nos données.** Le scoring prédit l'équipement actuel, pas la demande : la Logistic Regression retenue atteint une AUC de 0,871, et la population seule en explique déjà l'essentiel (baseline : AUC 0,867). Sans données d'usage, un modèle reproduit la logique du déploiement passé.
- **Le monde rural reste le point aveugle.** Sur les 636 déserts de recharge de métropole (685 avec l'outre-mer), 629 sont hors de toute unité urbaine. La population médiane de ces communes est de 153 habitants, et 127 sont en zone de montagne. Ce sont précisément les territoires que la littérature étudie le moins.

---

## 2. Recharge intelligente et Vehicle-to-Grid

### Définitions

Le règlement AFIR distingue deux notions [2] :

- **La recharge intelligente (smart charging)** : la puissance délivrée à la batterie est ajustée en temps réel.
- **La recharge bidirectionnelle** : recharge intelligente dans laquelle le sens du courant peut s'inverser. Le véhicule peut alors restituer de l'électricité au réseau (Vehicle-to-Grid, V2G), à un bâtiment (V2B) ou à un logement (V2H).

### Ce que montrent les études françaises

Enedis, gestionnaire du réseau de distribution, a étudié le pilotage de la recharge (décembre 2020) [5]. Il distingue trois types de pilotage :

- **temporel** : recharger aux heures creuses, soit une économie de l'ordre de 90 € par an selon certaines offres tarifaires ;
- **en puissance** : ne pas dépasser la puissance souscrite ;
- **pour l'autoconsommation** : recharger avec la production solaire de la journée.

Le V2G est passé au stade commercial en France en octobre 2024. Renault, sa filiale Mobilize et The Mobility House proposent la Renault 5 et l'Alpine A290 avec une borne à courant alternatif bidirectionnelle (PowerBox Verso) et un contrat d'électricité dédié [6]. L'électricité restituée au réseau est vendue de façon agrégée, ce qui réduit le coût de la recharge pour le conducteur.

La France a été le premier pays européen à proposer une offre commerciale de ce type [6]. Le partenaire l'explique par :

- un gestionnaire de réseau de distribution très majoritaire (Enedis) ;
- un déploiement avancé des compteurs communicants.

### Où intervient l'IA

Le pilotage repose sur des prévisions : consommation du réseau, prix de l'électricité, production solaire, heure de départ du conducteur. C'est un terrain classique du machine learning appliqué aux séries temporelles. L'agrégation de milliers de batteries en une réserve de puissance, comme dans l'offre V2G décrite ci-dessus [6], suppose de prévoir la disponibilité des véhicules.

### Lien avec le projet

Le jeu IRVE décrit les bornes (localisation, puissance, prises), pas leur usage : il ne contient ni sessions de recharge, ni taux d'occupation, ni capacité bidirectionnelle. **La question de la recharge intelligente ne peut donc pas être traitée avec ces données.** Elle montre la limite du projet : l'offre est mesurée, la demande ne l'est pas.

Les données dynamiques décrites dans la partie 3 sont un premier pas vers une mesure de l'usage.

---

## 3. Big Data et données ouvertes IRVE

### Un cadre d'ouverture qui s'est construit par étapes

| Date | Étape | Source |
|---|---|---|
| 12 janvier 2017 | Arrêté : obligation d'ouvrir les données de localisation et de caractéristiques techniques des bornes | [7] |
| Septembre 2018 | Consolidation automatique des fichiers publiés sur data.gouv.fr | [8] |
| 4 mai 2021 | Arrêté précisant la publication sur data.gouv.fr, au format du schéma IRVE statique | [7] |
| 17 octobre 2022 | Schéma IRVE statique v2.1.0, qui rend plusieurs champs facultatifs | [8] |
| 13 avril 2024 | Le règlement AFIR (art. 20) impose de rendre gratuites des données statiques et dynamiques, via une API, aux points d'accès nationaux | [2][9] |
| 1er avril 2025 | Connexion à l'API QualiCharge obligatoire pour les opérateurs de bornes en courant continu qui veulent percevoir des certificats d'électricité renouvelable | [10] |

### Du fichier statique au flux de données

Le fichier consolidé utilisé dans ce projet est un **instantané** : une ligne par point de charge et par source de publication, mise à jour périodiquement.

Les données **dynamiques** changent de nature :

- statut de chaque point (libre, occupé, hors service) ;
- disponibilité en temps réel ;
- tarifs.

QualiCharge, porté par la Direction générale de l'énergie et du climat, publie déjà ces deux types de données selon deux schémas ouverts (`schema-irve-statique` et `schema-irve-dynamique`). L'objectif est d'améliorer la qualité de service de la recharge [10].

Avec des centaines de milliers de points qui envoient chacun un statut à intervalle régulier, on passe d'un fichier CSV que pandas lit en quelques secondes à un **flux continu**. C'est le domaine du Big Data : volume, vélocité, stockage en colonnes et traitement distribué.

### Retour d'expérience du projet : la qualité avant le volume

Le nettoyage du fichier consolidé montre que l'ouverture des données ne garantit pas leur qualité. Chiffres vérifiés dans le notebook 01 :

| Constat | Chiffre |
|---|---|
| Lignes brutes | 226 963 |
| Lignes en excédent : un même point publié par plusieurs sources | 60 105 |
| Lignes sans code INSEE | 24,9 % |
| Part des codes INSEE absents dus à deux publieurs qui n'en fournissent aucun (gireve-2, indigo-group) | 75,5 % |
| Puissances saisies en watts au lieu de kilowatts, converties | 883 |
| Puissances absentes, nulles ou aberrantes, estimées | 2 526 |
| Points dont la date de mise en service est connue | 60,8 % |
| Points de charge distincts après nettoyage | 166 430 |

Pour comparaison, le baromètre Avere-France, établi avec les données Gireve, recense **200 045 points ouverts au public au 31 juillet 2026** [11]. Le fichier consolidé nettoyé en compte 166 430, soit 16,8 % de moins. La couverture du fichier ouvert est donc incomplète ; les causes de l'écart (opérateurs qui ne publient pas, définitions différentes) ne sont pas établies par les données.

Sur la puissance, en revanche, les deux sources concordent :

| Source | Points de plus de 150 kW |
|---|---|
| Avere-France [11] | 13 % (courant continu) |
| Fichier consolidé nettoyé (projet) | 13,8 % (strictement plus de 150 kW) |

**Tendance :** la valeur d'un jeu de données ouvert dépend moins de son volume que de son **identifiant unique** et de son **contrôle à la source**. QualiCharge et AFIR vont dans ce sens : API normalisée, schéma imposé, données publiées par l'opérateur lui-même.

---

## 4. Le cadre réglementaire de l'IA : l'AI Act

Le règlement européen sur l'intelligence artificielle (UE) 2024/1689 classe les systèmes d'IA selon leur niveau de risque. Les systèmes à haut risque de son annexe III, qui couvre notamment la gestion et l'exploitation des infrastructures critiques, doivent satisfaire plusieurs exigences [12] :

- un système de gestion des risques ;
- une gouvernance des données d'entraînement ;
- une journalisation des événements ;
- une documentation technique ;
- une supervision humaine.

**Calendrier.** Ces obligations devaient s'appliquer le 2 août 2026. Le « Digital Omnibus » sur l'IA, voté par le Parlement européen le 16 juin 2026 et adopté par le Conseil le 29 juin 2026, les reporte [13] :

- au **2 décembre 2027** pour les systèmes de l'annexe III ;
- au **2 août 2028** pour ceux de l'annexe I.

Les obligations de transparence et celles des fournisseurs de modèles d'IA à usage général restent applicables au 2 août 2026 [13].

**Application au projet.** Le modèle de scoring ne pilote ni n'exploite aucune infrastructure : il classe des communes pour éclairer une décision humaine de déploiement. Il ne relève donc pas des cas de l'annexe III. Les bonnes pratiques que le texte impose aux systèmes à haut risque s'appliquent néanmoins utilement :

| Exigence de l'AI Act | Mise en œuvre dans le projet |
|---|---|
| Documentation des données | règles de nettoyage documentées et chiffrées |
| Absence de data leakage | variables qui contiennent la réponse écartées ; pipeline scikit-learn |
| Validation honnête | départements de test jamais vus par le modèle |
| Contrôle du domaine d'application | modèle non appliqué à l'outre-mer, hors du domaine d'entraînement |
| Supervision humaine | la liste des communes est une aide à la décision, pas une décision |

---

## 5. Synthèse : tendances et conséquences pour le projet

| Tendance | Constat de la veille | Conséquence pour le projet |
|---|---|---|
| Planification hybride SIG + machine learning | Approche recommandée par la littérature récente [4] | Démarche du projet : rattachement géographique, distances, scoring |
| Monde rural sous-étudié | Lacune de la recherche [4] | Les déserts identifiés sont ruraux : c'est l'apport du projet |
| Recharge intelligente et V2G | Offre commerciale en France depuis 2024 [6] ; pilotage étudié par Enedis [5] | Hors de portée : IRVE ne contient pas de données d'usage |
| Données dynamiques et API | Imposées par AFIR [2] ; publiées par QualiCharge [10] | Une prochaine version pourrait mesurer l'occupation et la disponibilité, donc la demande |
| Qualité des données ouvertes | 60 105 lignes en excédent, 24,9 % de codes INSEE manquants, couverture inférieure de 16,8 % au baromètre | Le nettoyage a représenté la plus grande part du travail |
| Encadrement de l'IA | AI Act, obligations à haut risque reportées à fin 2027 [13] | Modèle d'aide à la décision, documenté et supervisé |

**Conclusion.** Les outils d'IA pour planifier les bornes existent. Leur limite n'est pas l'algorithme : c'est la donnée.

- Sur l'offre, les données sont ouvertes mais hétérogènes.
- Sur la demande, elles restent rares.

Le passage annoncé des fichiers statiques aux flux dynamiques normalisés (AFIR, QualiCharge) est la tendance qui ferait le plus progresser une analyse comme celle-ci : il permettrait de passer de « où sont les bornes ? » à « où manquent-elles au regard de l'usage ? ».

---

## Sources

1. Ministère de la Transition écologique, *Schémas directeurs pour les infrastructures de recharge pour véhicules électriques*, guide, mai 2021. [ecologie.gouv.fr](https://www.ecologie.gouv.fr/sites/default/files/2021%20-%20Guide%20sch%C3%A9ma%20directeur%20IRVE.pdf)
2. Commission européenne, *Questions and answers on Regulation (EU) 2023/1804 on the deployment of alternative fuels infrastructure*. [transport.ec.europa.eu](https://transport.ec.europa.eu/transport-themes/clean-transport/alternative-fuels-sustainable-mobility-europe/alternative-fuels-infrastructure/questions-and-answers-regulation-deployment-alternative-fuels-infrastructure-eu-20231804_en). Texte du règlement : [EUR-Lex, règlement (UE) 2023/1804](https://eur-lex.europa.eu/eli/reg/2023/1804/oj)
3. ICCT, *Alternative Fuels Infrastructure Regulation (AFIR)*, EU Policy Update, 2023. [theicct.org](https://theicct.org/wp-content/uploads/2023/04/AFIR-EU-Policy-Update-A4-Final.pdf)
4. Dharangaonkar S. K., Patil S. A., « Planning of Electric Vehicle Charging Infrastructure: A Review and a Conceptual Framework Based on Spatial and Predictive Analysis », *International Journal of Sustainable Development and Planning*, vol. 20, n° 6, 2025, p. 2317-2330. [doi:10.18280/ijsdp.200605](https://doi.org/10.18280/ijsdp.200605)
5. Connaissance des Énergies, « Pilotage de la recharge de véhicules électriques » (étude Enedis, décembre 2020). [connaissancedesenergies.org](https://www.connaissancedesenergies.org/pilotage-de-la-recharge-de-vehicules-electriques-241104)
6. electrive, « Renault and The Mobility House launch V2G project in France », 22 octobre 2024. [electrive.com](https://www.electrive.com/2024/10/22/renault-and-the-mobility-house-launch-v2g-project-in-france)
7. DataSud, *Bornes de recharge pour véhicules électriques en Provence-Alpes-Côte d'Azur (IRVE)*, fiche de métadonnées (arrêtés du 12 janvier 2017 et du 4 mai 2021). [datasud.fr](https://www.datasud.fr/geonetwork/srv/api/records/6f685ba7-5f9e-4f0f-945f-cd7773fa1ab4)
8. data.gouv.fr, *Base nationale des IRVE*. [data.gouv.fr](https://www.data.gouv.fr/datasets/base-nationale-des-irve-infrastructures-de-recharge-pour-vehicules-electriques)
9. Spirii, *AFIR compliance*, documentation technique (article 20 : données statiques et dynamiques, API, points d'accès nationaux). [docs.spirii.com](https://docs.spirii.com/developers/afir-compliance)
10. data.gouv.fr, *Infrastructures de recharge pour véhicules électriques - Données ouvertes* (QualiCharge, DGEC). [data.gouv.fr](https://www.data.gouv.fr/datasets/infrastructures-de-recharge-pour-vehicules-electriques-donnees-ouvertes)
11. Automobile Propre, « C'est fait : la France passe le cap des 200 000 points de recharge ouverts au public » (baromètre Avere-France), 10 août 2026. [automobile-propre.com](https://www.automobile-propre.com/articles/cest-fait-la-france-passe-le-cap-des-200-000-points-de-recharge-ouverts-au-public/)
12. Données Personnelles, *AI Act : calendrier*. [donneespersonnelles.fr](https://donneespersonnelles.fr/ai-act-calendrier)
13. Quantic Avocats, « IA Act : le calendrier des obligations haut risque officiellement reporté », 22 juillet 2026. [quantic-avocats.com](https://www.quantic-avocats.com/2026/07/22/ai-act-digital-omnibus-report-obligations-haut-risque/)
