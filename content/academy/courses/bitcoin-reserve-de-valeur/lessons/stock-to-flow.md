+++
id = "stock-to-flow"
title = "Le stock-to-flow : une mesure, pas une prévision"
summary = "Le rapport entre le stock existant et la production annuelle mesure la rareté d'un actif : environ 58 ans pour l'or, plus de 120 ans pour Bitcoin en 2026, calculé à partir du protocole. Ce que ce ratio mesure, et pourquoi le modèle de prix qui en a été tiré est contesté."
duration_minutes = 14
access = "member"
status = "published"
version = 1
updated = 2026-10-20
objectives = [
  "Calculer le stock-to-flow d'un actif à partir de son stock et de sa production.",
  "Lire le stock-to-flow de Bitcoin, calculé à partir du protocole, et le comparer à celui de l'or.",
  "Distinguer la mesure de rareté du modèle de prix qui en a été tiré, et ses critiques.",
]
quiz = "check-stock-to-flow"
resources = ["fiche-reserve-de-valeur"]
sources = [
  "World Gold Council : stocks d'or extraits (environ 212 582 tonnes à la fin de 2023) et production minière de 2023 (environ 3 644 tonnes).",
  "PlanB (2019). « Modeling Bitcoin Value with Scarcity », publié le 22 mars 2019.",
  "Granger, C. W. J. et Newbold, P. (1974). « Spurious Regressions in Econometrics ». Journal of Econometrics, 2(2), 111-120.",
  "Règles d'émission du protocole Bitcoin ; calcul Sensitor.",
]
+++

## Le rapport entre le stock et le flux

Le **stock-to-flow** divise le stock existant d'un actif par sa production de l'année. Il se lit en années : combien de temps faudrait-il, au rythme actuel, pour produire tout ce qui existe déjà.

::: formula
\text{Stock-to-flow} = \frac{\text{stock existant}}{\text{production annuelle}}
:::

Un stock-to-flow élevé signifie qu'une année de production change peu la quantité totale : la rareté résiste à la demande. Pour l'or, avec environ 212 582 tonnes extraites à la fin de 2023 et une production d'environ 3 644 tonnes cette année-là, le ratio vaut environ **58 ans**.

::: chart stock-flux-bitcoin
Le stock-to-flow de Bitcoin chaque mois depuis 2014 : l'offre en circulation divisée par l'émission des douze mois précédents, calculée à partir des règles du protocole.
:::

Pour Bitcoin, le ratio double à chaque halving, puisque l'émission est divisée par deux. Il dépassait **120 ans** en septembre 2026, et doublera encore après le halving de 2028.

## À vous

::: exercise stock-flux
:::

## Une mesure, pas un modèle de prix

En 2019, un auteur publiant sous le pseudonyme PlanB a proposé un modèle qui relie le prix de Bitcoin à son stock-to-flow, et en tire des prix futurs. Ce modèle a été très diffusé.

::: callout debate "Le modèle stock-to-flow"
Pour ses défenseurs, la rareté croissante de Bitcoin, mesurée par ce ratio, explique la hausse de son prix sur le long terme. Pour ses critiques, le modèle relie deux séries qui montent toutes les deux avec le temps : une corrélation de ce type peut apparaître sans lien de cause, un piège décrit en économétrie dès 1974 par Granger et Newbold. Surtout, le modèle ne tient compte que de l'offre : il suppose que la demande suivra, ce que rien ne garantit.
:::

Le ratio, lui, reste une mesure utile : il dit, de façon exacte et vérifiable, que l'offre de Bitcoin devient plus rare que celle de l'or. Ce qu'un actif rare vaudra demain dépend de ceux qui voudront le détenir.

::: callout mistake "Erreur fréquente"
Utiliser un ratio d'offre pour prédire un prix à une date. Le stock-to-flow se calcule à l'avance avec certitude ; le prix, non.
:::

::: callout recap
- Stock-to-flow = stock ÷ production annuelle ; environ 58 ans pour l'or, plus de 120 ans pour Bitcoin en 2026.
- Le ratio de Bitcoin double à chaque halving.
- Le modèle de prix tiré du ratio est contesté : il ignore la demande, et repose sur une corrélation entre deux tendances.
:::
