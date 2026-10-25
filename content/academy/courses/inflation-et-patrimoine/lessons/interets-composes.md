+++
id = "interets-composes"
title = "Intérêts composés et coût de la volatilité"
summary = "Les gains produisent eux-mêmes des gains : sur trente ans, l'effet est considérable. Mais une perte se rattrape plus difficilement qu'elle ne se fait, et la volatilité réduit le rendement composé. Deux mécanismes à comprendre avant tout placement risqué."
duration_minutes = 15
access = "member"
status = "published"
version = 1
updated = 2026-10-17
objectives = [
  "Calculer un capital composé et un temps de doublement.",
  "Comparer la règle de 72 au calcul exact.",
  "Expliquer pourquoi la moyenne arithmétique des rendements surestime le rendement composé.",
]
quiz = "check-interets-composes"
resources = ["fiche-patrimoine"]
sources = [
  "Formules des intérêts composés et de la moyenne géométrique ; exemples pédagogiques construits pour la leçon.",
  "Bodie, Z., Kane, A. et Marcus, A. J. Investments. McGraw-Hill, éditions successives, chapitre sur les rendements et leur mesure.",
]
+++

## Les gains produisent des gains

Avec des **intérêts composés**, les intérêts de chaque année s'ajoutent au capital et rapportent à leur tour. 10 000 € placés à 7 % deviennent 19 671,51 € en dix ans, mais **76 122,55 €** en trente : le capital a doublé environ tous les dix ans.

::: formula
\text{Capital final} = \text{Capital} \times (1 + r)^{\text{années}}
:::

::: callout definition "La règle de 72"
Pour estimer de tête le temps de doublement, on divise 72 par le taux en pourcentage : à 7 %, environ 10,3 ans ; le calcul exact, ln 2 ÷ ln 1,07, donne 10,24 ans. La règle est une approximation commode, assez juste entre 2 % et 10 %.
:::

## Le coût de la volatilité

::: figure volatilite-rendement.svg
100 € gagnent 50 % puis perdent 50 % : ils deviennent 150 €, puis 75 €. La moyenne des deux rendements est nulle ; le résultat est une perte de 25 %. Calcul exact.
:::

Une perte de 50 % demande un gain de 100 % pour être effacée. C'est pourquoi la **moyenne arithmétique** des rendements annuels surestime ce que l'on gagne réellement. Le bon chiffre est la **moyenne géométrique**, le taux constant qui donne le même résultat final.

::: callout example "Exemple pédagogique"
Quatre années à +30 %, −20 %, +25 % et −30 %. La moyenne arithmétique est de +1,25 % par an. Pourtant 100 € deviennent 91 € : le rendement composé est de **−2,33 %** par an. Plus les rendements sont dispersés, plus l'écart entre les deux moyennes est grand.
:::

## À vous

::: exercise composes-volatilite
:::

::: callout warning "Pourquoi c'est central pour les actifs volatils"
Un actif très volatil peut afficher une moyenne annuelle élevée et un rendement composé bien plus faible. Pour Bitcoin comme pour une action, la question utile n'est pas « combien gagne-t-il en moyenne ? » mais « combien aurait gagné quelqu'un qui l'a gardé, sur quelle période, en traversant quelles baisses ? ».
:::

::: callout recap
- Les intérêts composés font croître le capital de façon exponentielle : 10 000 € à 7 % deviennent 76 122,55 € en trente ans.
- Temps de doublement : ln 2 ÷ ln(1 + r), environ 72 ÷ taux.
- Une perte de 50 % demande un gain de 100 % pour être effacée.
- La moyenne géométrique, pas l'arithmétique, mesure ce que l'on gagne sur la durée.
:::
