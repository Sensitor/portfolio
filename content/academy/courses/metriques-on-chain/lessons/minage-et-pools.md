+++
id = "minage-et-pools"
title = "Le minage : puissance, revenu par unité de calcul et pools"
summary = "La puissance de calcul du réseau, ce que rapporte chaque unité de cette puissance, et qui produit les blocs : trois mesures du minage, calculées sur la chaîne. La concentration des pools, lue dans les étiquettes que les mineurs inscrivent dans leurs blocs."
duration_minutes = 16
access = "member"
status = "published"
version = 1
updated = 2026-10-20
objectives = [
  "Lire l'évolution de la puissance de calcul et du revenu par unité de puissance.",
  "Identifier les pools à partir de l'étiquette de la coinbase, et ses limites.",
  "Calculer et interpréter le coefficient de Nakamoto.",
]
quiz = "check-minage-et-pools"
resources = ["fiche-on-chain"]
sources = [
  "Chaîne Bitcoin : en-têtes du premier bloc de chaque période de 2 016 blocs, et un bloc par jour du 9 janvier 2009 au 30 septembre 2026, relevés via les API publiques Esplora de blockstream.info et de mempool.space ; calculs Sensitor.",
  "Srinivasan, B. et Lee, L. (2017). « Quantifying Decentralization », publication du 27 juillet 2017 : le coefficient de Nakamoto.",
]
+++

## La puissance et ce qu'elle rapporte

Le cours sur Bitcoin a montré la puissance de calcul du réseau, déduite de la difficulté. En divisant le revenu quotidien des mineurs, récompense et frais, par cette puissance, on obtient ce que rapporte chaque unité de calcul : c'est la mesure de la **concurrence** entre mineurs.

::: chart puissance-reseau
La puissance de calcul du réseau, période par période, déduite de la difficulté et du temps entre les blocs. Échelle logarithmique.
:::

::: chart revenu-par-eh
Ce que rapporte, chaque jour, un exahash par seconde de puissance, en bitcoins. Échelle logarithmique. La baisse continue traduit l'arrivée de machines toujours plus puissantes ; chaque halving ajoute une marche.
:::

En septembre 2016, un exahash par seconde rapportait environ **1 153 BTC** par jour ; en septembre 2026, environ **0,50 BTC**. Le revenu en bitcoins d'une même puissance a été divisé par plus de 2 300 en dix ans : c'est la course à l'efficacité des machines, et l'effet de trois halvings.

## Qui produit les blocs

La plupart des mineurs se regroupent en **pools**, qui partagent le travail et les récompenses. Beaucoup inscrivent leur nom dans la coinbase de leurs blocs. En lisant ces étiquettes dans l'échantillon, on mesure la part de chaque pool, année après année.

::: chart pools-annee
La part des blocs de l'échantillon par pool, chaque année depuis 2013, selon l'étiquette inscrite dans la coinbase. « Non identifié » regroupe les blocs sans étiquette connue. Environ 365 blocs par an : une estimation, à quelques points près.
:::

::: chart nakamoto
Le coefficient de Nakamoto du minage : le nombre de pools identifiés qu'il faut additionner pour dépasser la moitié des blocs.
:::

En 2026, **Foundry USA** produisait environ **30 %** des blocs de l'échantillon, et **3 pools** suffisaient à dépasser la moitié.

## À vous

::: exercise pools-nakamoto
:::

::: callout warning "Un pool n'est pas un mineur"
Un pool coordonne des milliers de mineurs, qui peuvent le quitter en quelques minutes s'il se comporte mal. La concentration des pools n'est donc pas celle des machines. Mais un pool choisit les transactions qu'il inclut : sa part mesure un pouvoir réel sur la composition des blocs, et le risque d'une attaque majoritaire vu au cours sur Bitcoin.
:::

::: callout mistake "Erreur fréquente"
Lire la carte des pools comme une carte des pays. Un pool déclaré dans un pays rassemble des mineurs du monde entier.
:::

::: callout recap
- Revenu par unité de puissance : environ 0,50 BTC par EH/s et par jour en septembre 2026, en baisse continue.
- Les pools se lisent dans l'étiquette de la coinbase ; une partie des blocs reste non identifiée.
- Coefficient de Nakamoto du minage en 2026 : 3 pools pour dépasser la moitié des blocs.
:::
