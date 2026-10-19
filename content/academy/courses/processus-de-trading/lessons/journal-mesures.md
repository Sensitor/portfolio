+++
id = "journal-mesures"
title = "Le journal et ce qu'il mesure"
summary = "Un journal utile ne raconte pas la séance, il la mesure : pour chaque trade, le scénario, le résultat en R, et si toutes les règles ont été respectées. De là sortent les deux chiffres qui comptent le plus : le taux de respect du plan, et ce que coûtent les écarts."
duration_minutes = 16
access = "member"
status = "published"
version = 1
updated = 2026-10-19
objectives = [
  "Noter un trade avec les champs qui permettront de le mesurer.",
  "Calculer le taux de respect du plan et l'espérance de chaque groupe de trades.",
  "Calculer le coût des écarts au plan, en R.",
]
quiz = "check-journal-mesures"
resources = ["modele-plan-de-trading"]
sources = [
  "Steenbarger, B. N. (2009). The Daily Trading Coach. Hoboken : Wiley.",
  "Duke, A. (2018). Thinking in Bets. New York : Portfolio : séparer la qualité d'une décision de son résultat.",
]
+++

## Ce qu'il faut noter

| Champ | Pourquoi |
|---|---|
| date, heure, instrument, sens | retrouver le trade |
| stratégie et version du plan | savoir quelle règle l'a produit |
| scénario écrit avant l'entrée | comparer l'intention et l'exécution |
| risque prévu et résultat, **en R** | comparer des trades de tailles différentes |
| **toutes les règles respectées : oui ou non** | la mesure centrale du processus |
| règle enfreinte, le cas échéant | savoir quelle faiblesse coûte |
| capture du graphique à l'entrée et à la sortie | revoir sans réécrire l'histoire |
| état avant la séance | relier les écarts à la fatigue ou à l'émotion |

Le résultat se note en **R**, le multiple du risque prévu : +2R pour un gain de deux fois le risque, −1R pour un stop complet. Un stop éloigné qui finit touché donne par exemple −1,5R.

## Deux groupes, deux espérances

Une fois les trades marqués, le journal se coupe en deux : les trades qui ont respecté **toutes** les règles, et les autres.

::: formula
\text{Taux de respect} = \frac{\text{trades conformes}}{\text{tous les trades}}
:::

::: formula
\text{Coût des écarts} = \text{somme des résultats des trades non conformes, en R}
:::

L'espérance des trades conformes dit ce que vaut le plan lui-même ; celle des trades non conformes, ce que coûtent les écarts. Le coût des écarts est souvent la découverte la plus utile d'un journal : il chiffre une faiblesse que l'on préférerait ignorer.

## À vous

::: exercise journal-semaine
:::

::: callout warning "Petits échantillons"
Dix trades ne prouvent rien sur l'espérance d'une stratégie, le parcours 7 l'a montré. Mais un écart au plan n'a pas besoin de statistique pour être corrigé : la règle existait, elle n'a pas été suivie. Le taux de respect se travaille dès la première semaine ; l'espérance se juge sur des centaines de trades.
:::

::: callout note "Où le tenir"
L'espace **Journal de trading** importe les trades depuis MetaTrader 5 et calcule les résultats en R ; le journal de réflexion de l'espace **Psychologie** garde l'état et la routine de chaque séance. Il reste à marquer chaque trade : conforme ou non.
:::

::: callout mistake "Erreur fréquente"
Ne noter que les trades perdants, ou que les trades « intéressants ». Un journal incomplet donne des chiffres faux, et c'est souvent sur les trades oubliés que se cachent les écarts.
:::

::: callout recap
- Chaque trade : stratégie et version, scénario, résultat en R, règles respectées ou non, règle enfreinte.
- Taux de respect = trades conformes ÷ tous les trades.
- Coût des écarts = somme des R des trades non conformes : la faiblesse chiffrée.
:::
