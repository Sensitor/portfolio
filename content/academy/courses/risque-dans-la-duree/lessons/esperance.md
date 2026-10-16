+++
id = "esperance"
title = "L'espérance : ce que rapporte un trade en moyenne"
summary = "Le taux de réussite seul ne dit rien. Combiné au ratio gain / risque, il donne l'espérance, le seul chiffre qui dit si une approche gagne en moyenne."
duration_minutes = 15
access = "public"
status = "published"
version = 1
objectives = [
  "Calculer l'espérance d'une approche en R.",
  "Trouver le taux de réussite minimal pour un ratio gain / risque donné.",
  "Lire un profit factor et savoir ce qu'il ne dit pas.",
]
quiz = "check-esperance"
resources = ["fiche-risque-duree"]
+++

## Un taux de réussite ne suffit pas

« Je gagne 60 % de mes trades » ne dit pas si l'on gagne de l'argent. Si chaque gain rapporte 0,5R et chaque perte coûte 1R, dix trades donnent six gains de 0,5R et quatre pertes de 1R : 3R − 4R, soit −1R. Une approche peut gagner souvent et perdre de l'argent ; une autre peut perdre souvent et en gagner.

## L'espérance

L'**espérance** est le résultat moyen d'un trade, exprimé en R (l'unité de risque définie au parcours 1) :

::: formula
E = p \times G \;-\; (1 - p) \times P
:::

où *p* est le taux de réussite, *G* le gain moyen d'un trade gagnant et *P* la perte moyenne d'un trade perdant, tous deux en R. Quand chaque perte touche le stop, *P* vaut 1R.

::: callout example "Exemple pédagogique"
Taux de réussite de 40 %, gains moyens de 2R, pertes de 1R.

E = 0,40 × 2 − 0,60 × 1 = 0,80 − 0,60 = **+0,20R par trade**. Avec un risque de 100 $ par trade, l'approche rapporterait en moyenne 20 $ par trade, sur un grand nombre de trades et avant coûts.
:::

## Le seuil de rentabilité

Pour un ratio gain / risque donné, il existe un taux de réussite sous lequel l'espérance devient négative :

::: formula
p_{\min} = \frac{1}{1 + R}
:::

::: figure seuil-rentabilite.svg
Taux de réussite minimal selon le ratio gain / risque, hors coûts : 50 % à 1R, 40 % à 1,5R, 33 % à 2R, 25 % à 3R. Sous la courbe, l'espérance est négative. Courbe calculée.
:::

Les coûts déplacent ce seuil vers le haut : un spread et une commission qui représentent 0,1R par trade retirent 0,1R à l'espérance, quel que soit le résultat.

## Le profit factor

Le **profit factor** divise la somme des gains par la somme des pertes. Au-dessus de 1, l'approche gagne ; à 1, elle est à l'équilibre. Avec 40 % de réussite et des gains de 2R, il vaut 0,80 ÷ 0,60 = 1,33.

::: callout method "Ce que l'espérance ne dit pas"
L'espérance est une moyenne sur un grand nombre de trades. Elle ne dit rien de l'ordre des résultats, donc rien des séries de pertes ni des baisses de capital en chemin. Et calculée sur trente trades, elle est très incertaine : c'est l'objet de la leçon suivante.
:::

::: callout mistake "Erreur fréquente"
Comparer deux approches sur leur seul taux de réussite. Une approche à 35 % de réussite et 2,5R de gain moyen (+0,225R par trade) fait mieux qu'une approche à 60 % et 0,8R (+0,08R par trade).
:::

::: callout recap
- L'espérance, p × G − (1 − p) × P, est le résultat moyen d'un trade en R.
- Le seuil de rentabilité vaut 1 ÷ (1 + R) ; les coûts le relèvent.
- Le profit factor compare gains et pertes bruts ; au-dessus de 1, l'approche gagne.
- Une moyenne ne dit rien des séries ni de la fiabilité d'un petit échantillon.
:::
