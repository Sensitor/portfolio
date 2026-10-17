+++
id = "dette-obligations"
title = "Dette publique, déficits et obligations"
summary = "Un État qui dépense plus qu'il ne prélève emprunte, en émettant des obligations. Ce qui distingue le déficit de la dette, comment fonctionne une obligation, et pourquoi son prix baisse quand les taux montent."
duration_minutes = 17
access = "member"
status = "published"
version = 1
updated = 2026-10-17
objectives = [
  "Distinguer déficit et dette, dette publique et dette privée.",
  "Décrire une obligation : nominal, coupon, échéance.",
  "Calculer le prix d'une obligation et expliquer sa relation inverse avec les taux.",
]
quiz = "check-dette-obligations"
resources = ["fiche-la-monnaie"]
sources = [
  "Reinhart, C. M. et Rogoff, K. S. (2009). This Time Is Different: Eight Centuries of Financial Folly. Princeton University Press.",
  "Herndon, T., Ash, M. et Pollin, R. (2014). « Does high public debt consistently stifle economic growth? A critique of Reinhart and Rogoff ». Cambridge Journal of Economics, 38(2).",
  "Mishkin, F. S. The Economics of Money, Banking and Financial Markets. Pearson, éditions successives, chapitre sur les taux et le prix des obligations.",
  "Formule du prix d'une obligation à coupon annuel : somme des coupons et du nominal, actualisés au taux du marché.",
]
+++

## Déficit et dette

Le **déficit** budgétaire est l'écart, sur une année, entre ce que l'État dépense et ce qu'il prélève. La **dette** publique est le **stock** accumulé de ce qu'il doit, année après année. Un déficit s'ajoute à la dette ; un excédent la réduit.

On rapporte souvent la dette au **PIB**, la richesse produite en un an. Ce ratio peut baisser même avec un déficit, si l'économie et les prix progressent plus vite que la dette.

La dette **privée**, celle des ménages et des entreprises, compte autant. Les crises financières naissent souvent d'un excès de dette privée, comme les crédits immobiliers américains avant 2008.

## Comment un État emprunte

Un État emprunte surtout en émettant des **obligations**, que des banques, des assureurs, des fonds de pension, des épargnants et des banques centrales achètent.

::: callout definition "Obligation"
Une **obligation** est un titre de dette. Son émetteur s'engage à verser un intérêt fixe chaque année, le **coupon**, et à rembourser le **nominal** à l'**échéance**. Une obligation de nominal 100, coupon 3 %, à 10 ans, verse 3 par an pendant 10 ans, puis rembourse 100.
:::

## Le prix d'une obligation

Une fois émise, une obligation se revend sur le marché. Son prix dépend du **taux du marché** du moment : on actualise chaque coupon et le nominal à ce taux.

::: figure obligation-prix-taux.svg
Le prix de l'obligation de nominal 100, coupon 3 %, 10 ans, selon le taux du marché : 108,98 à 2 %, 100 à 3 %, 91,89 à 4 %. Calcul exact.
:::

Si les taux montent à 4 %, une nouvelle obligation rapporte 4 par an. Personne ne paiera donc 100 pour l'ancienne qui ne rapporte que 3 : son prix baisse jusqu'à ce que son rendement rejoigne 4 %, ici à 91,89. C'est la **relation inverse** entre taux et prix des obligations.

## À vous

::: exercise obligation-taux
:::

::: callout warning "Une obligation n'est pas sans risque de perte"
Celui qui garde l'obligation jusqu'à l'échéance récupère le nominal, si l'émetteur ne fait pas défaut. Celui qui doit la vendre avant, après une hausse des taux, vend à perte. Les hausses de taux de 2022 ont ainsi fait baisser fortement la valeur des obligations détenues par de nombreux épargnants et institutions.
:::

## Dette, croissance et taux

Une dette est soutenable tant que l'emprunteur peut payer ses intérêts et refinancer ce qui arrive à échéance. Trois grandeurs comptent : le **taux** auquel il emprunte, la **croissance** de ses revenus, et le **solde** de son budget hors intérêts. Quand le taux dépasse durablement la croissance, la dette tend à progresser plus vite que l'économie, sauf si l'État dégage des excédents.

::: callout debate "Quel niveau de dette est dangereux ?"
Il n'existe pas de seuil universel. Des pays ont connu des crises avec des dettes modérées, quand les prêteurs ont perdu confiance ou que la dette était libellée dans une monnaie étrangère ; d'autres portent des dettes élevées sans crise, avec une banque centrale et une monnaie à eux. Reinhart et Rogoff ont documenté huit siècles de crises de dette ; un seuil de dette qu'ils avaient avancé dans un autre travail a été contesté par Herndon, Ash et Pollin, qui y ont relevé des erreurs de calcul.
:::

::: callout recap
- Le déficit est un flux annuel ; la dette, le stock accumulé.
- Une obligation verse un coupon et rembourse son nominal à l'échéance.
- Quand les taux montent, le prix des obligations déjà émises baisse, et l'inverse.
- La soutenabilité d'une dette dépend du taux, de la croissance et du solde budgétaire, et de la confiance des prêteurs.
:::
