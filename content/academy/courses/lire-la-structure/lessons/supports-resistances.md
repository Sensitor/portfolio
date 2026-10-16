+++
id = "supports-resistances"
title = "Supports et résistances : des zones, pas des lignes"
summary = "Construire des zones à partir des swings, comprendre pourquoi le marché ne réagit pas au pip près, et ce qu'une zone dit, ou ne dit pas, de la suite."
duration_minutes = 15
access = "member"
status = "published"
version = 1
objectives = [
  "Construire une zone de support ou de résistance à partir de swings voisins.",
  "Expliquer pourquoi une zone est plus juste qu'une ligne.",
  "Décrire l'inversion de rôle sans la présenter comme une règle.",
]
quiz = "check-zones"
resources = ["fiche-lire-la-structure"]
+++

## Ce qu'est une zone

Un **support** est une zone de prix, située sous le prix actuel, où le marché a déjà cessé de baisser, parfois à plusieurs reprises. Une **résistance** est une zone, au-dessus du prix actuel, où il a déjà cessé de monter.

La définition est volontairement modeste : elle décrit où quelque chose s'est produit. Elle ne dit pas pourquoi, ni que cela se reproduira.

## Pourquoi une zone, et pas une ligne

Les réactions du prix ne se produisent presque jamais deux fois exactement au même niveau. Plusieurs raisons à cela :

- les ordres des intervenants s'étalent sur une plage de prix, ils ne se concentrent pas sur un chiffre ;
- les mèches varient d'une réaction à l'autre, et d'un courtier à l'autre sur le Forex ou les CFD ;
- le spread s'élargit souvent près des niveaux observés par tout le monde.

Une ligne tracée au pip près sera « cassée » par la première mèche venue. Une zone rend compte de l'imprécision réelle du marché.

## Construire la zone

La méthode la plus simple part des swings de la leçon précédente :

1. repérez les **sommets** (pour une résistance) ou les **creux** (pour un support) de swing proches les uns des autres ;
2. tracez la zone de la réaction la plus basse à la plus haute de ce groupe, mèches comprises ;
3. si la zone devient très large, elle regroupe probablement deux niveaux distincts : séparez-les.

::: figure zones-sr.svg
Le prix bute deux fois sous une zone de résistance, la franchit, puis revient sur cette zone, qui joue alors le rôle de support. Schéma original.
:::

::: callout example "Exemple pédagogique"
Sur un graphique H1, trois sommets de swing se situent à 1,0862, 1,0868 et 1,0871. La zone de résistance s'étend de 1,0862 à 1,0871, soit 9 pips. Un prix qui monte à 1,0866 est **dans** la zone : ce n'est ni une cassure, ni un rejet, c'est un test en cours.
:::

## L'inversion de rôle

Une résistance franchie est souvent retestée ensuite comme support, et inversement. On parle d'inversion de rôle (*polarity*). C'est une observation fréquente sur beaucoup de marchés, que les méthodes de trading utilisent largement.

::: callout method "Ce que dit une zone, et ce qu'elle ne dit pas"
Une zone dit où le marché a réagi. Elle ne dit pas qu'il réagira à nouveau, ni dans quel sens. Une idée courante veut qu'une zone testée plusieurs fois « s'use » ; une autre, qu'elle se « renforce ». Les deux sont des hypothèses de méthode, pas des faits établis : elles se vérifient sur votre propre historique.
:::

::: callout mistake "Erreur fréquente"
Multiplier les zones jusqu'à en avoir à tous les prix. Quand chaque niveau est une zone, aucune ne renseigne plus sur rien. Gardez celles qui ont produit des swings nets et récents sur l'unité de temps étudiée.
:::

::: callout recap
- Support et résistance sont des zones où le marché a déjà réagi, construites à partir de swings voisins.
- Une zone rend compte de l'imprécision réelle des réactions ; une ligne au pip près se « casse » à la première mèche.
- Un prix dans la zone est un test en cours, ni une cassure ni un rejet.
- L'inversion de rôle est fréquente, jamais garantie. Toute idée sur la « force » d'une zone est une hypothèse à vérifier.
:::
