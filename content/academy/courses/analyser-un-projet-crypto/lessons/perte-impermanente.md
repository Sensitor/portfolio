+++
id = "perte-impermanente"
title = "Fournir de la liquidité : la perte impermanente"
summary = "Celui qui dépose deux actifs dans un pool touche une part des frais, mais le pool lui vend automatiquement l'actif qui monte et lui achète celui qui baisse. La perte impermanente, calculée, et ce que les frais doivent rapporter pour la compenser."
duration_minutes = 14
access = "member"
status = "published"
version = 1
updated = 2026-10-20
objectives = [
  "Expliquer pourquoi un fournisseur de liquidité détient moins de l'actif qui monte.",
  "Calculer la perte impermanente pour une variation de prix donnée.",
  "Comparer la perte impermanente aux frais perçus.",
]
quiz = "check-perte-impermanente"
resources = ["fiche-analyse-crypto"]
sources = [
  "Adams, H., Zinsmeister, N. et Robinson, D. (2020). « Uniswap v2 Core », livre blanc.",
  "Aigner, A. A. et Dhaliwal, G. (2021). « Uniswap: Impermanent Loss and Risk Profile of a Liquidity Provider ». arXiv:2106.14404.",
]
+++

## Ce que fait un pool à ses fournisseurs

Le cours « Utiliser la crypto en sécurité » a montré comment un pool à produit constant fixe son prix. Ceux qui y déposent les deux actifs, les **fournisseurs de liquidité**, reçoivent une part des commissions. En échange, ils subissent les échanges des autres : quand un actif monte, les acheteurs le retirent du pool, et le fournisseur en détient moins.

Comparé à celui qui aurait simplement gardé ses deux actifs, le fournisseur se retrouve avec moins de valeur : c'est la **perte impermanente**. Elle est dite « impermanente » parce qu'elle disparaît si les prix reviennent à leur niveau de départ ; elle devient définitive si l'on retire sa liquidité après la variation.

::: formula
\text{Perte impermanente} = \frac{2\sqrt{r}}{1 + r} - 1
:::

où **r** est le rapport entre le nouveau prix relatif des deux actifs et l'ancien. La perte ne dépend pas du sens : un prix qui double et un prix qui est divisé par deux donnent la même perte.

| Variation du prix relatif | Perte impermanente |
|---|---|
| × 1,25 | −0,6 % |
| × 1,5 | −2,0 % |
| × 2 | −5,7 % |
| × 4 | −20,0 % |
| × 0,5 | −5,7 % |

::: chart perte-impermanente-courbe
La perte d'une position de liquidité par rapport à la simple détention, selon la variation du prix relatif des deux actifs. Elle est nulle sans variation et croît dans les deux sens. Calcul exact, avant commissions.
:::

## À vous

::: exercise perte-impermanente
:::

::: callout note "Ce que doivent rapporter les frais"
Fournir de la liquidité n'est rentable que si les commissions perçues dépassent la perte impermanente. Elles sont plus élevées quand le pool est très utilisé et que les prix bougent peu l'un par rapport à l'autre, comme entre deux stablecoins.
:::

::: callout mistake "Erreur fréquente"
Juger une position de liquidité sur son rendement affiché en frais, sans le comparer à ce qu'aurait donné la simple détention des deux actifs. Un rendement de 10 % en frais peut cacher une perte nette si le prix a doublé.
:::

::: callout recap
- Le pool vend au fournisseur l'actif qui baisse et lui retire celui qui monte.
- Perte impermanente = 2√r ÷ (1 + r) − 1 : −5,7 % si le prix relatif double, −20 % s'il quadruple.
- Les frais doivent dépasser la perte pour que la position vaille mieux que la détention.
:::
