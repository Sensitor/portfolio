+++
id = "simulateur-epargne"
title = "Le simulateur : valeur affichée et pouvoir d'achat"
summary = "Capital de départ, versements, durée, rendement, inflation, frais et impôt : le simulateur montre côte à côte ce qu'affiche un compte et ce qu'il permet d'acheter. Trois scénarios guidés, puis à vous de tester les vôtres."
duration_minutes = 16
access = "member"
status = "published"
version = 1
updated = 2026-10-17
objectives = [
  "Utiliser le simulateur pour comparer valeur nominale et valeur réelle.",
  "Mesurer l'effet des versements réguliers sur une longue durée.",
  "Lire les hypothèses et les limites d'une simulation.",
]
quiz = "check-simulateur"
resources = ["fiche-patrimoine"]
sources = [
  "Calcul mensuel des intérêts composés, des versements et des frais ; valeur réelle déflatée par l'inflation cumulée (relation de Fisher).",
  "Banque centrale européenne, stratégie de politique monétaire, 2021 : objectif d'inflation de 2 % à moyen terme, retenu comme hypothèse par défaut.",
]
+++

## Ce que fait le simulateur

Le simulateur calcule, mois par mois, la valeur d'une épargne : le capital croît au rendement choisi, les frais sont prélevés sur le capital, le versement s'ajoute en fin de mois. Il affiche deux courbes : la **valeur affichée** sur le compte, et le **pouvoir d'achat**, cette valeur exprimée en euros d'aujourd'hui.

::: tool savings-simulator
:::

## Trois scénarios guidés

Réglez le simulateur comme indiqué et observez les deux courbes.

| Scénario | Réglages | Valeur affichée après 30 ans | Pouvoir d'achat |
|---|---|---|---|
| **Billets** | 10 000 €, aucun versement, rendement 0 %, inflation 2 % | 10 000 € | 5 521 € |
| **Placement prudent** | 10 000 €, rendement 2 %, inflation 2 % | 18 114 € | 10 000 € |
| **Placement plus risqué** | 10 000 €, rendement 5 %, inflation 2 % | 43 219 € | 23 860 € |

Le placement prudent ne fait que conserver le pouvoir d'achat : son rendement égale l'inflation. Le placement à 5 % le multiplie par 2,4, à condition que ce rendement soit tenu trente ans, ce que rien ne garantit.

::: callout example "Les versements réguliers"
Ajoutez 200 € par mois au scénario à 5 % : vous versez 82 000 € en tout. Le compte affiche 206 295 € ; en pouvoir d'achat d'aujourd'hui, c'est 113 889 €. La différence entre les deux chiffres est le travail de l'inflation sur trente ans.
:::

## Ce que le simulateur ne sait pas

::: callout warning "Des taux constants, une réalité qui ne l'est pas"
Le simulateur suppose un rendement et une inflation constants chaque mois pendant toute la durée. En réalité, les rendements varient fortement d'une année à l'autre, l'inflation aussi, et l'ordre des bonnes et des mauvaises années compte, surtout quand on retire de l'argent. Un résultat de simulation est un ordre de grandeur, pas une promesse.
:::

Pour juger un placement réel, on regarde aussi sa **volatilité**, sa **liquidité** et le **pire** qu'il ait connu, comme le montrent les leçons suivantes.

::: callout recap
- Le simulateur sépare la valeur affichée et le pouvoir d'achat.
- Un rendement égal à l'inflation ne fait que conserver ; il faut faire mieux pour s'enrichir en réel.
- Les versements réguliers et la durée pèsent autant que le rendement.
- Les taux constants sont une hypothèse : le résultat est un ordre de grandeur.
:::
