+++
id = "revue-amelioration"
title = "La revue et l'amélioration du plan"
summary = "Une revue hebdomadaire corrige l'exécution ; une revue mensuelle peut changer le plan, une règle à la fois, et seulement quand l'échantillon le permet. Le protocole des deux revues, et pourquoi on ne change pas une stratégie après dix trades perdants."
duration_minutes = 15
access = "member"
status = "published"
version = 1
updated = 2026-10-19
objectives = [
  "Mener une revue hebdomadaire de l'exécution et une revue mensuelle du plan.",
  "Ne changer qu'une règle à la fois, et la tester avant de l'adopter.",
  "Estimer le nombre de trades nécessaires avant de juger une règle.",
]
quiz = "check-revue-amelioration"
resources = ["modele-plan-de-trading"]
sources = [
  "Steenbarger, B. N. (2009). The Daily Trading Coach. Hoboken : Wiley.",
  "Ericsson, K. A., Krampe, R. T. et Tesch-Römer, C. (1993). « The Role of Deliberate Practice in the Acquisition of Expert Performance ». Psychological Review, 100(3), 363-406.",
]
+++

## Deux revues, deux questions

| | Revue hebdomadaire | Revue mensuelle |
|---|---|---|
| **La question** | ai-je suivi mon plan ? | mon plan fonctionne-t-il ? |
| **Ce qu'on regarde** | taux de respect, règles enfreintes, préparation, limites | espérance des trades conformes, avec son intervalle, et sa tendance |
| **Ce qui peut changer** | l'exécution : une habitude, la routine | le plan : une seule règle, si l'échantillon le permet |
| **Durée** | 30 minutes | une à deux heures |

La revue hebdomadaire est le lieu de la **pratique délibérée**, au sens d'Ericsson et de ses coauteurs : isoler une faiblesse précise, la travailler, mesurer son évolution. On choisit une seule faiblesse pour la semaine suivante, celle qui coûte le plus en R.

## Changer une règle

Changer une règle après une mauvaise semaine, c'est réagir au bruit. Le parcours 7 a montré qu'une espérance mesurée sur quelques dizaines de trades a un intervalle très large.

::: callout method "Avant de changer une règle"
1. **Un seul changement à la fois**, sinon on ne saura pas lequel a produit l'effet.
2. **Une raison écrite**, fondée sur le journal, pas sur la dernière série.
3. **Un test**, en backtest comme au parcours 7, ou en réel à taille réduite.
4. **Une nouvelle version** du plan, datée, et un journal qui indique sous quelle version chaque trade a été pris.
:::

## À vous

::: exercise revue-echantillon
:::

::: callout example "Ce que dit, et ne dit pas, un mauvais mois"
Une stratégie dont l'espérance réelle est de +0,25R, avec un écart type de 1,2R, aura régulièrement des mois de 20 trades négatifs : c'est la variance, pas une panne. Ce qui doit alerter, c'est un **changement** : une espérance des trades conformes qui reste négative sur plusieurs centaines de trades, ou des conditions de marché qui ne correspondent plus à celles où la stratégie a été testée.
:::

::: callout mistake "Erreur fréquente"
Corriger le plan au lieu de corriger l'exécution. Si le journal montre que les pertes viennent des trades non conformes, le plan n'est pas en cause : c'est le respect du plan qu'il faut travailler.
:::

::: callout recap
- Hebdomadaire : ai-je suivi le plan ? Une faiblesse à travailler. Mensuelle : le plan fonctionne-t-il ?
- Une règle à la fois, avec une raison écrite, un test et une nouvelle version.
- Juger une règle demande des centaines de trades : (1,96 × écart type ÷ précision voulue)².
:::
