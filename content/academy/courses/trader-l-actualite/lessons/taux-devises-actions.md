+++
id = "taux-devises-actions"
title = "Taux, devises et actions : les canaux"
summary = "Une hausse des taux attendus ne touche pas tous les marchés de la même façon. Les canaux par lesquels elle passe aux devises, aux actions, à l'or et à la crypto, et ce que dit, ou ne dit pas, une courbe des taux inversée."
duration_minutes = 17
access = "member"
status = "published"
version = 1
updated = 2026-10-19
objectives = [
  "Décrire comment les taux se transmettent aux devises, aux actions, à l'or et à la crypto.",
  "Calculer l'écart entre taux longs et taux courts, et reconnaître une courbe inversée.",
  "Situer ce que l'inversion de la courbe a précédé, et ses limites comme indicateur.",
]
quiz = "check-taux-devises-actions"
resources = ["fiche-macro"]
sources = [
  "Estrella, A. et Mishkin, F. S. (1998). « Predicting U.S. Recessions: Financial Variables as Leading Indicators ». Review of Economics and Statistics, 80(1), 45-61.",
  "National Bureau of Economic Research, US Business Cycle Expansions and Contractions : dates des récessions américaines.",
  "Board of Governors of the Federal Reserve System, séries GS10 et GS2 ; U.S. Bureau of Labor Statistics, séries CPIAUCSL et UNRATE ; via FRED, Federal Reserve Bank of St. Louis, consultées le 19 octobre 2026.",
  "mempool.space : prix historique hebdomadaire de Bitcoin en dollars (30 décembre 2021 et 31 décembre 2022), consulté le 17 octobre 2026.",
]
+++

## Quatre canaux

Quand le marché révise ses attentes de taux, l'effet se propage par des canaux différents selon l'actif. Ce sont des **tendances**, pas des règles : un autre facteur peut l'emporter.

| Actif | Le canal | Tendance quand les taux attendus montent |
|---|---|---|
| **Devises** | l'écart de taux entre deux pays attire ou repousse les capitaux | la devise du pays dont les taux montent tend à s'apprécier |
| **Actions** | les bénéfices futurs valent moins aujourd'hui quand on les actualise à un taux plus élevé | pression à la baisse, plus forte sur les valeurs de croissance |
| **Or** | il ne rapporte aucun intérêt ; détenir de l'or coûte le rendement auquel on renonce | pression à la baisse, avec de longues exceptions |
| **Bitcoin et crypto** | actifs sans flux de revenus, sensibles aux conditions de liquidité | pression à la baisse, sur la période récente |

En 2022, année de hausse rapide des taux américains, Bitcoin est passé d'environ 43 400 dollars à la fin de 2021 à environ 16 500 dollars à la fin de 2022. Une période ne fait pas une loi, mais elle montre que la crypto ne vit pas à l'écart du cycle des taux. L'univers Monnaie et crypto examine cette relation sur la durée.

## La courbe des taux

La **courbe des taux** relie le rendement des emprunts d'État à leur durée. D'habitude, prêter dix ans rapporte plus que prêter deux ans : la courbe monte. Quand les taux courts dépassent les taux longs, elle est dite **inversée** : le marché attend des baisses de taux, souvent parce qu'il anticipe un ralentissement.

::: formula
\text{Écart} = \text{rendement à 10 ans} - \text{rendement à 2 ans}
:::

::: chart courbe-us
L'écart entre les rendements du Trésor américain à 10 et à 2 ans, chaque mois depuis 1977. Sous zéro, la courbe est inversée.
:::

Les données montrent douze périodes d'inversion depuis 1977. Les plus longues ont précédé les récessions de 1980, 1981-1982, 1990-1991, 2001 et 2007-2009 ; le creux de la série, **−2,13 points**, date de mars 1980. Une inversion d'un seul mois, en juin 1998, n'a été suivie d'aucune récession dans les deux années suivantes.

La dernière inversion est la plus longue de la série : **26 mois**, de juillet 2022 à août 2024. Elle n'a pas été suivie d'une hausse marquée du chômage : de 2022 à septembre 2026, le taux de chômage américain est resté entre 3,4 % et 4,5 %.

::: callout debate "Un indicateur avancé ?"
Pour certains économistes, l'inversion de la courbe reste l'un des meilleurs indicateurs avancés de récession, au moins pour les États-Unis (Estrella et Mishkin, 1998). Pour d'autres, les achats massifs d'obligations par les banques centrales depuis 2008 ont déformé la courbe et affaibli le signal. L'épisode 2022-2024 nourrit les deux lectures : la récession n'est pas venue, ou pas encore.
:::

## Le taux réel

Le marché regarde aussi le **taux réel** : le taux nominal diminué de l'inflation. En septembre 2026, le rendement à 2 ans était de 4,65 % pour une inflation américaine de 3,7 % sur un an : un taux réel d'environ **0,95 point**. Le cours « Inflation et patrimoine » de l'univers Monnaie et crypto en donne la formule exacte.

## À vous

::: exercise courbe-taux-reel
:::

::: callout mistake "Erreur fréquente"
Vendre un marché parce que « la courbe est inversée ». L'inversion a précédé des récessions, de plusieurs mois à deux ans, et s'est parfois trompée. Ce n'est ni un signal de timing ni un signal infaillible.
:::

::: callout recap
- Les taux attendus passent aux devises par l'écart de taux, aux actions par l'actualisation, à l'or et à la crypto par le coût de détention et la liquidité.
- Écart = 10 ans − 2 ans ; négatif, la courbe est inversée.
- L'inversion de 2022-2024, la plus longue depuis 1977, n'a pas été suivie d'une hausse marquée du chômage à la date des données.
:::
