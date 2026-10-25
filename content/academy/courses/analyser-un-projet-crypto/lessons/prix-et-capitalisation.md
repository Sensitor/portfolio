+++
id = "prix-et-capitalisation"
title = "Le prix ne dit rien seul : capitalisation et valorisation diluée"
summary = "Un jeton à 0,50 dollar n'est pas « moins cher » qu'un jeton à 500 dollars. Ce qui compte, c'est la valeur de l'ensemble des jetons en circulation, et celle de tous ceux qui existeront. Deux mesures à calculer avant tout autre chose."
duration_minutes = 12
access = "public"
status = "published"
version = 1
updated = 2026-10-20
objectives = [
  "Calculer la capitalisation et la valorisation totalement diluée d'un jeton.",
  "Expliquer pourquoi le prix unitaire ne dit rien de la cherté d'un jeton.",
  "Lire l'écart entre jetons en circulation et offre maximale.",
]
quiz = "check-prix-et-capitalisation"
resources = ["fiche-analyse-crypto"]
sources = [
  "Banque des règlements internationaux (2023). « The crypto ecosystem: key elements and risks », rapport au G20, juillet 2023.",
  "Autorité des marchés financiers, mises en garde sur les crypto-actifs et les offres de jetons.",
]
+++

## Le piège du prix unitaire

Un jeton qui vaut quelques centimes semble avoir « de la marge ». C'est une illusion : son prix dépend surtout du **nombre de jetons** entre lesquels la valeur se partage. Diviser chaque jeton en dix ne crée aucune valeur ; cela divise le prix par dix.

::: formula
\text{Capitalisation} = \text{prix} \times \text{jetons en circulation}
:::

La **capitalisation** mesure ce que vaut, au prix du jour, l'ensemble des jetons qui circulent. C'est elle qu'il faut comparer d'un projet à l'autre, pas le prix.

## La valorisation totalement diluée

Beaucoup de projets n'ont mis en circulation qu'une partie de leurs jetons : le reste sera distribué plus tard à l'équipe, aux investisseurs, à la trésorerie ou aux utilisateurs.

::: formula
\text{Valorisation diluée} = \text{prix} \times \text{offre maximale}
:::

Un grand écart entre les deux signale une **dilution à venir** : pour que le prix tienne, il faudra que la demande absorbe tous les jetons encore à distribuer. La leçon suivante en mesure l'effet.

## À vous

::: exercise capitalisation-fdv
:::

::: callout note "Des données de marché sous licence"
Ce cours calcule sur des exemples construits. Les capitalisations réelles des projets sont publiées par des agrégateurs de données de marché, dont la réutilisation demande une licence commerciale ; Sensitor ne reproduit pas ces chiffres tant qu'il n'en dispose pas.
:::

::: callout mistake "Erreur fréquente"
Acheter un jeton « parce qu'il pourrait atteindre 1 dollar comme un autre ». Pour qu'un jeton de 100 milliards d'unités vaille 1 dollar, sa capitalisation devrait atteindre 100 milliards : la question est de savoir si le projet peut valoir cela, pas si le prix « peut monter ».
:::

::: callout recap
- Capitalisation = prix × jetons en circulation : c'est elle que l'on compare, pas le prix.
- Valorisation diluée = prix × offre maximale : l'écart annonce la dilution à venir.
- Un prix unitaire bas ne veut pas dire « pas cher ».
:::
