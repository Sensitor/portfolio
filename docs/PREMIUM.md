# Le contenu Premium : état actuel et proposition à valider

Document de décision pour le point P1.10 de la feuille de route. **Rien ici
n'est décidé** : c'est au fondateur de trancher, puis le code suit en une ligne
par choix. Aucun paiement n'existe ; l'accès Premium est attribué à la main par
un administrateur (page « Membres et accès »), avec un motif et une date de fin
facultative.

## Où se décide l'accès

Un seul fichier : `sensitor/core/permissions.py`.

- `CAPABILITIES` : ce que chaque niveau ou rôle peut faire.
- `LIMITS` : les quantités par niveau.
- Pour le contenu, le niveau est déclaré dans le fichier de chaque leçon ou
  fiche : `access = "public"`, `"member"` ou `"premium"`.

## Ce qui est Premium aujourd'hui

| Élément | Gratuit | Premium | D'où ça vient |
|---|---|---|---|
| Leçons et quiz | toutes les leçons publiées | les mêmes | aucune leçon n'est déclarée `premium` (0 sur 145) |
| Fiches de la Bibliothèque | toutes | les mêmes | aucune fiche n'est déclarée `premium` |
| Salle des marchés | séances « Accès libre » et « Membres » | plus les séances « Premium » | choix du coach, séance par séance |
| Optimisation de portefeuille | non | oui | `portfolio.optimize`, déjà réservée dans l'analyseur historique, étendue à la plateforme en P1.3 |
| Stress tests | non | oui | `portfolio.stress_test`, même origine |
| Allocations types dans l'analyseur | aperçu | chargement | `portfolio.models` |
| Lignes par portefeuille | 5 | 50 | `portfolio.max_assets` |
| Revues de trade par un coach | 1 par mois | 8 par mois | `review.monthly_quota` |

**Changement à noter (P1.3).** Avant ce lot, la plateforme laissait
l'optimisation et les stress tests à tous les comptes, alors que l'analyseur
historique les réservait (constat A5 de l'audit). Les deux suivent maintenant la
même règle : Premium. Si vous préférez les laisser gratuits, il suffit de passer
leur niveau à `FREE` dans `CAPABILITIES`.

## Proposition à valider

Un principe simple : **apprendre reste gratuit, approfondir et être accompagné
est Premium.** Le compte gratuit doit suffire pour suivre un parcours de bout en
bout.

À cocher ou à barrer :

- [ ] Leçons : toutes les leçons actuelles restent gratuites. Le Premium
  accueillera du contenu nouveau (parcours Investissement 2, études de cas
  détaillées), pas du contenu retiré au gratuit.
- [ ] Fiches : les fiches actuelles restent gratuites ; les modèles avancés
  (plan de trading détaillé, tableur de suivi) pourront être Premium.
- [ ] Outils : optimisation, stress tests, allocations types et 50 lignes en
  Premium (réglage actuel).
- [ ] Revues par un coach : 1 par mois en gratuit, 8 en Premium (réglage actuel).
- [ ] Salle des marchés : le coach choisit, séance par séance (réglage actuel).
- [ ] Accompagné (P2) : ateliers de cohorte et demandes d'accompagnement, en
  plus du Premium.

## Avant tout paiement

La vente d'un accès Premium demande d'abord la revue réglementaire prévue en
P2.0 (statut éducatif, promotion des crypto-actifs, CGV, TVA, droit de
rétractation). Le code n'a ni prix ni bouton de paiement.
