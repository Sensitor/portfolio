+++
id = "cas-backtest"
title = "Cas pratique : 120 trades, puis 50 hors échantillon"
summary = "La stratégie sweep, cassure et FVG des parcours 3 et 4, testée sur deux ans puis sur une année réservée. On calcule tout, coûts compris, et l'on prend la décision que les chiffres permettent, ni plus ni moins."
duration_minutes = 24
access = "member"
status = "published"
version = 1
objectives = [
  "Calculer les chiffres d'un backtest réel : taux de réussite, espérances, profit factor, intervalles.",
  "Comparer le résultat à son seuil de rentabilité et à son intervalle.",
  "Formuler une décision proportionnée aux preuves.",
]
quiz = "check-cas-backtest"
resources = ["fiche-backtest", "routine-de-seance"]
+++

## La stratégie testée

La règle, version 1, reprend les parcours précédents : contexte H4 haussier, sweep de creux égaux en M15, cassure de structure haussière en clôture, entrée limite au milieu du FVG de l'impulsion, invalidation 5 pips sous le sweep, objectif au sommet de la jambe, 0,5 % de risque. Elle a été écrite et figée avant le test.

Le protocole : EURUSD et GBPUSD choisis avant de regarder, 2021 et 2022 pour la construction, 2023 réservée au test. Défilement bougie par bougie, toutes les occurrences notées. Coût moyen estimé : **0,07R par trade**.

Les résultats sont fictifs et construits pour l'exercice.

::: exercise cas-backtest-120
:::

## La décision

Les chiffres disent trois choses :

1. **La moyenne est encourageante** : +0,19R net par trade sur 120 trades, au-dessus de zéro.
2. **La preuve est insuffisante** : l'intervalle de l'espérance nette va de −0,07 à +0,44R. Il contient zéro. Le taux de réussite, de 35 % à 52 %, frôle par le bas le seuil de rentabilité de 34,5 %.
3. **Le test hors échantillon ne tranche pas** : +0,05R net sur 50 trades, une dégradation de 73 %, et un intervalle très large.

La décision proportionnée n'est ni « la stratégie marche » ni « elle ne marche pas ». C'est : **continuer à mesurer**, sans modifier la règle. Concrètement, un test en temps réel en démo ou à très petite taille, jusqu'à au moins 200 occurrences supplémentaires, avec la routine de séance du parcours 6 et le journal.

::: callout warning "Ce qu'il ne faut pas faire maintenant"
Ajuster la règle pour améliorer 2023, puis la retester sur 2023. L'échantillon de test serait consommé, et le chiffre suivant n'aurait plus de valeur de validation.
:::

::: callout recap
- Toujours les mêmes chiffres : n, taux de réussite, espérance brute et nette, profit factor, intervalles.
- Une moyenne positive dont l'intervalle contient zéro n'est pas une preuve d'avantage.
- La décision suit les preuves : ici, continuer à mesurer avec la règle figée et une très petite taille.
:::
