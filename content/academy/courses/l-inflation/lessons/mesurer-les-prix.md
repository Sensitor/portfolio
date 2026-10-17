+++
id = "mesurer-les-prix"
title = "Mesurer les prix : indices, paniers et pondérations"
summary = "L'inflation se mesure par un indice : le prix d'un panier de biens et de services, pondéré par ce que les ménages dépensent. Comment il est construit, ce que montrent ses composantes, et pourquoi l'inflation de chacun diffère de l'inflation officielle."
duration_minutes = 16
access = "member"
status = "published"
version = 1
updated = 2026-10-17
objectives = [
  "Expliquer comment un indice des prix est construit.",
  "Calculer un taux d'inflation et une inflation cumulée à partir d'un indice.",
  "Lire l'inflation par composante et expliquer l'inflation sous-jacente.",
]
quiz = "check-mesurer-les-prix"
resources = ["fiche-inflation"]
sources = [
  "Eurostat, Harmonised Index of Consumer Prices (HICP), méthodologie et jeu de données prc_hicp_minr, consulté le 17 octobre 2026.",
  "INSEE, indice des prix à la consommation (IPC) : définitions et méthodologie.",
  "Boskin, M. J. et al. (1996). Toward a More Accurate Measure of the Cost of Living. Rapport final à la commission des finances du Sénat des États-Unis.",
]
+++

## Un panier de biens et de services

Les statisticiens relèvent chaque mois les prix de centaines de milliers de produits : alimentation, énergie, vêtements, loyers, transports, communications, loisirs. Ils les regroupent dans un **panier** qui représente la consommation moyenne des ménages.

Chaque poste reçoit une **pondération** : sa part dans les dépenses. Si les ménages consacrent un dixième de leur budget à l'énergie, une hausse de 10 % de l'énergie fait monter l'indice d'environ 1 point.

::: callout definition "Indice des prix"
Un **indice** exprime le prix du panier par rapport à une année de **base**, fixée à 100. Un indice de 105,1 signifie que le panier coûte 5,1 % de plus que pendant l'année de base. L'inflation sur un an est la variation de l'indice entre un mois et le même mois de l'année précédente.
:::

## IPC et IPCH

En France, l'**INSEE** publie l'**indice des prix à la consommation** (IPC). Pour comparer les pays européens, Eurostat publie l'**indice des prix à la consommation harmonisé** (IPCH), calculé selon les mêmes règles dans chaque pays : c'est celui que suit la BCE. Les deux diffèrent légèrement, notamment par le traitement de certaines dépenses de santé.

## À vous

::: exercise indices-inflation
:::

## Les composantes

L'indice d'ensemble cache des évolutions très différentes selon les postes.

::: chart inflation-composantes
L'inflation de la zone euro par composante, chaque mois depuis 2015 : énergie, alimentation, services, biens industriels hors énergie, et inflation sous-jacente.
:::

L'énergie est de loin la composante la plus volatile : elle a atteint **44,3 %** sur un an en mars 2022. L'alimentation a culminé à 15,5 % en mars 2023, les services à 5,6 % en juillet 2023.

::: callout definition "Inflation sous-jacente"
L'**inflation sous-jacente** retire de l'indice les postes les plus volatils, l'énergie et l'alimentation. Elle donne une idée de la tendance de fond, celle qui persiste quand les chocs passagers sont passés. La BCE la suit de près pour juger si une poussée d'inflation s'installe.
:::

## Les limites de la mesure

- **La qualité** : un ordinateur au même prix qu'il y a cinq ans est plus puissant. Les statisticiens corrigent les prix pour la qualité, et ces corrections sont discutées.
- **La substitution** : quand un produit devient cher, les ménages en achètent un autre. Un panier figé surestimerait l'inflation ; c'est l'une des conclusions du rapport Boskin de 1996 aux États-Unis.
- **Le logement** : l'IPCH compte les loyers, mais pas le coût de l'achat d'un logement par son propriétaire.

::: callout debate "L'inflation officielle sous-estime-t-elle le coût de la vie ?"
Beaucoup de ménages ressentent une inflation supérieure à l'inflation mesurée. Une partie s'explique : chacun a son propre panier (un locataire, un automobiliste, un retraité n'achètent pas les mêmes choses), et l'on remarque davantage les prix achetés souvent, comme l'alimentation et le carburant. D'autres critiques portent sur les corrections de qualité ou l'absence de l'achat immobilier. Les instituts publient leurs méthodes ; le débat porte sur les choix, pas sur une dissimulation.
:::

::: callout recap
- L'inflation se mesure par un indice : le prix d'un panier pondéré par les dépenses.
- IPC pour la France (INSEE), IPCH pour les comparaisons européennes (Eurostat, suivi par la BCE).
- L'énergie est la composante la plus volatile ; l'inflation sous-jacente l'exclut, avec l'alimentation.
- Chaque ménage a son propre panier, donc sa propre inflation.
:::
