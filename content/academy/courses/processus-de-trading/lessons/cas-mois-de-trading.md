+++
id = "cas-mois-de-trading"
title = "Cas pratique : un mois de trading au crible"
summary = "Vingt-quatre trades, un mois légèrement perdant, et un trader tenté de changer de stratégie. Le journal dit autre chose : les dix-huit trades conformes au plan gagnent, les six écarts coûtent davantage. L'analyse complète, et la décision qui en découle."
duration_minutes = 18
access = "member"
status = "published"
version = 1
updated = 2026-10-19
objectives = [
  "Analyser un mois de journal : taux de respect, espérance par groupe, coût des écarts.",
  "Identifier la règle enfreinte qui coûte le plus.",
  "Décider de ce qui change le mois suivant, et de ce qui ne change pas.",
]
quiz = "check-cas-mois-de-trading"
resources = ["modele-plan-de-trading"]
+++

## La situation

*Cas construit pour la leçon : les trades sont des exemples.*

Un trader termine le mois à **−0,6R** sur 24 trades. Sa première réaction : « ma stratégie ne marche plus, il faut en changer ». Son journal, tenu avec soin, marque chaque trade comme conforme ou non au plan, et nomme la règle enfreinte.

| Règle enfreinte | Trades | Résultat |
|---|---|---|
| aucune, trade conforme | 18 | +5,8R |
| trade de revanche après une perte | 2 | −2,0R |
| stop éloigné en cours de trade | 1 | −1,8R |
| entrée hors de la zone écrite | 1 | −1,0R |
| taille doublée « pour se refaire » | 1 | −2,2R |
| sortie anticipée par peur | 1 | +0,6R |

::: chart mois-de-trading
Le mois trade par trade : en bleu, le résultat réalisé ; en or, celui des seuls trades conformes, les écarts comptés pour zéro. Exemple synthétique.
:::

La courbe des trades conformes ne dit pas ce qui se serait passé exactement sans les écarts : le trader aurait peut-être pris d'autres trades. Elle dit ce que les trades conformes ont produit, et ce que les écarts ont coûté.

## À vous

::: exercise cas-mois
:::

## La décision

- **La stratégie ne change pas.** Ses trades conformes ont une espérance positive, et 18 trades ne permettent de toute façon pas de la juger : le parcours 7 en demanderait des centaines.
- **L'exécution change.** Quatre des six écarts suivent une perte : revanche, stop éloigné, taille doublée. La faiblesse de la semaine suivante est donc la règle « après une perte, pause, puis seulement le scénario suivant ».
- **Le plan se renforce sur ce point** : une pause obligatoire de trente minutes après toute perte complète, notée dans la routine. C'est une règle d'exécution, pas une modification de la stratégie.

::: callout note "Ce que le trader aurait fait sans journal"
Il aurait changé de stratégie, perdu les dix-huit trades d'expérience accumulés, et emporté ses écarts dans la stratégie suivante. Le journal a évité de corriger la mauvaise chose.
:::

::: callout recap
- Mois à −0,6R ; trades conformes à +5,8R ; écarts à −6,4R.
- La faiblesse est l'après-perte : quatre écarts sur six suivent une perte.
- On garde la stratégie, on travaille l'exécution, on ajoute une pause après chaque perte complète.
:::
