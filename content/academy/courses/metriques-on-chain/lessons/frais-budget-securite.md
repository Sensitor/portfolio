+++
id = "frais-budget-securite"
title = "Les frais et le budget de sécurité"
summary = "Les mineurs sont payés deux fois : par la récompense de bloc et par les frais des transactions. Les frais, calculés à partir de la coinbase de chaque bloc, leur part dans le revenu des mineurs, et ce que cela dit de la sécurité du réseau quand la récompense diminue."
duration_minutes = 15
access = "member"
status = "published"
version = 1
updated = 2026-10-20
objectives = [
  "Calculer les frais d'un bloc à partir de sa coinbase et de la récompense.",
  "Lire la part des frais dans le revenu des mineurs.",
  "Relier cette part à la question de la sécurité à long terme.",
]
quiz = "check-frais-budget-securite"
resources = ["fiche-on-chain"]
sources = [
  "Chaîne Bitcoin : un bloc par jour, du 9 janvier 2009 au 30 septembre 2026, relevé via les API publiques Esplora de blockstream.info et de mempool.space ; calculs Sensitor.",
  "Règles d'émission du protocole Bitcoin : récompense de bloc par époque.",
  "Budish, E. (2018). « The Economic Limits of Bitcoin and the Blockchain ». NBER Working Paper 24717.",
]
+++

## Les frais, lus dans la coinbase

La première transaction de chaque bloc, la **coinbase**, paie le mineur. Elle peut réclamer la récompense du protocole plus la totalité des frais des transactions incluses. Les frais d'un bloc se calculent donc sans rien demander à personne :

::: formula
\text{Frais du bloc} = \text{montant de la coinbase} - \text{récompense du protocole}
:::

::: chart frais-par-bloc
Les frais par bloc, en bitcoins, en moyenne mensuelle. Les pics correspondent aux périodes où l'espace de bloc était le plus demandé.
:::

Le record de l'échantillon est de **3,89 BTC** par bloc en moyenne en décembre 2017, au plus fort de la hausse de 2017. En dehors de cette période, le plus haut est de **1,99 BTC** en décembre 2023, quand les inscriptions se disputaient l'espace de bloc. En septembre 2026, la moyenne était de **0,018 BTC** par bloc.

## La part des frais

::: chart part-frais
La part des frais dans le revenu des mineurs, chaque mois : le reste est la récompense du protocole, divisée par deux à chaque halving.
:::

La part des frais a atteint **22,2 %** en décembre 2023. En septembre 2026, elle était de **0,6 %** : la récompense paie encore l'essentiel de la sécurité du réseau.

::: chart revenu-mineurs
Le revenu total des mineurs, récompense et frais, en bitcoins par jour. Chaque halving le coupe presque de moitié.
:::

## À vous

::: exercise frais-coinbase
:::

::: callout debate "Qui paiera la sécurité ?"
La récompense sera divisée par deux tous les quatre ans environ ; à terme, les frais devront payer la puissance qui protège le registre. Pour certains économistes, comme Eric Budish (2018), c'est une fragilité : si les frais restent faibles, la sécurité baissera. Pour d'autres, la demande d'espace de bloc et la valeur des bitcoins suffiront. Les données de ce graphique, une part des frais encore faible et irrégulière, nourrissent ce débat sans le trancher.
:::

::: callout mistake "Erreur fréquente"
Lire des frais élevés comme une mauvaise nouvelle seulement. Pour les utilisateurs, c'est un coût ; pour la sécurité du réseau, c'est un revenu qui ne dépend pas de l'émission.
:::

::: callout recap
- Frais d'un bloc = coinbase − récompense du protocole.
- La part des frais dans le revenu des mineurs reste faible et irrégulière : 0,6 % en septembre 2026.
- Quand la récompense aura presque disparu, les frais devront payer la sécurité : un débat ouvert.
:::
