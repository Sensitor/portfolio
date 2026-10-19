+++
id = "plateformes-echange"
title = "Plateformes d'échange et pools automatiques"
summary = "On achète des cryptoactifs sur une plateforme centralisée, avec un carnet d'ordres, ou dans un pool automatique, où une formule fixe le prix. Ce que coûte vraiment un échange : frais, spread, et l'impact d'un ordre sur un pool trop petit."
duration_minutes = 17
access = "member"
status = "published"
version = 1
updated = 2026-10-19
objectives = [
  "Distinguer une plateforme centralisée et une plateforme décentralisée.",
  "Expliquer comment un pool à produit constant fixe son prix.",
  "Calculer ce que reçoit un acheteur et l'impact de son ordre sur le prix.",
]
quiz = "check-plateformes-echange"
resources = ["fiche-crypto-securite"]
sources = [
  "Adams, H., Zinsmeister, N. et Robinson, D. (2020). « Uniswap v2 Core », livre blanc : le produit constant x × y = k et la commission de 0,30 %.",
  "Banque des règlements internationaux (2023). « The crypto ecosystem: key elements and risks », rapport au G20, juillet 2023.",
  "Règlement (UE) 2023/1114 sur les marchés de crypto-actifs (MiCA) : agrément des prestataires de services, applicable depuis le 30 décembre 2024.",
]
+++

## Deux façons d'échanger

| | Plateforme centralisée | Plateforme décentralisée |
|---|---|---|
| Qui tient les fonds | la plateforme, pendant que vous l'utilisez | vous, jusqu'à l'échange |
| Comment le prix se forme | un **carnet d'ordres**, comme sur les marchés du parcours 1 | un **pool** et une formule |
| Ce qu'on paie | frais de transaction, spread, frais de retrait | commission du pool, impact sur le prix, frais du réseau |
| Le risque principal | la contrepartie : faillite, gel, piratage | le contrat : erreur de programmation, faux jeton |

Sur une plateforme centralisée, acheter revient à rencontrer un vendeur dans un carnet d'ordres : les notions de spread, d'ordre au marché et d'ordre limite du parcours Trading s'appliquent telles quelles.

## Le pool à produit constant

Une plateforme décentralisée n'a souvent pas de carnet d'ordres. Elle utilise un **pool** : un contrat qui détient deux actifs, par exemple de l'ether et un stablecoin. Le prix découle d'une règle simple : le produit des deux réserves reste constant.

::: formula
x \times y = k
:::

Pour obtenir de l'ether, l'acheteur dépose des stablecoins. La réserve de stablecoins grossit, celle d'ether doit diminuer pour que le produit reste le même. Chaque unité achetée coûte plus cher que la précédente : c'est l'**impact sur le prix**.

::: figure produit-constant.svg
La courbe d'un pool de 100 ETH et 300 000 USDC. Acheter avec 30 000 USDC déplace le pool le long de la courbe : on reçoit 9,09 ETH, au prix moyen de 3 300 USDC, 10 % au-dessus du prix de départ. Calcul exact, sans la commission du pool.
:::

::: formula
\text{Reçu} = \frac{y \times \text{montant déposé}}{x + \text{montant déposé}}
:::

## À vous

::: exercise pool-automatique
:::

::: callout warning "Les faux jetons"
N'importe qui peut créer un jeton portant le nom d'un projet connu et ouvrir un pool. Sur une plateforme décentralisée, c'est l'adresse du contrat qui identifie un jeton, pas son nom. Elle se vérifie sur le site officiel du projet.
:::

::: callout mistake "Erreur fréquente"
Passer un gros ordre dans un petit pool. L'impact sur le prix croît avec la taille de l'ordre par rapport aux réserves : 1 % du pool coûte environ 1 % de plus que le prix affiché, 10 % du pool environ 10 %.
:::

::: callout recap
- Centralisée : carnet d'ordres et risque de contrepartie ; décentralisée : pool, formule et risque de contrat.
- Pool à produit constant : x × y = k ; chaque unité achetée coûte plus cher.
- L'impact sur le prix dépend de la taille de l'ordre rapportée aux réserves.
:::
