+++
id = "drawdown"
title = "Le drawdown et la récupération"
summary = "Mesurer une baisse de capital du plus haut au plus bas, comprendre pourquoi elle se rattrape plus difficilement qu'elle ne se creuse, et la calculer sur une vraie série."
duration_minutes = 16
access = "member"
status = "published"
version = 1
objectives = [
  "Mesurer le drawdown maximal d'une série de résultats.",
  "Calculer le gain nécessaire pour revenir à un sommet.",
  "Distinguer drawdown depuis le départ et drawdown depuis un sommet.",
]
quiz = "check-drawdown"
resources = ["fiche-risque-duree"]
+++

## La définition

Le **drawdown** est la baisse du capital depuis son dernier plus haut. Le **drawdown maximal** est la plus forte de ces baisses sur une période : la distance entre un sommet et le creux le plus bas qui le suit, avant qu'un nouveau sommet ne soit atteint.

::: formula
\text{Drawdown} = 1 - \frac{\text{Creux}}{\text{Sommet}}
:::

::: figure drawdown-courbe.svg
Treize trades risquant chacun 1 % du capital. Le sommet est atteint après le trade 3, le creux après le trade 9 : un drawdown maximal de 3,47 %. Courbe calculée.
:::

## Depuis le départ ou depuis un sommet

Deux mesures coexistent, et il faut savoir laquelle on lit :

- **depuis le capital de départ** : on regarde seulement si l'on est sous le capital initial ;
- **depuis le dernier sommet** : on mesure ce qui a été perdu après un plus haut. C'est la mesure la plus exigeante, et celle qu'utilisent la plupart des rapports de performance.

Un compte qui passe de 10 000 $ à 12 000 $ puis redescend à 10 500 $ est au-dessus de son départ, mais en drawdown de 12,5 % depuis son sommet.

## L'asymétrie de la récupération

Une baisse se rattrape toujours plus difficilement qu'elle ne s'est creusée, parce que le gain s'applique à un capital plus petit :

::: formula
\text{Gain nécessaire} = \frac{1}{1 - \text{Drawdown}} - 1
:::

Une baisse de 10 % demande un gain de 11,1 % ; une baisse de 25 %, un gain de 33,3 % ; une baisse de 50 %, un gain de 100 %. C'est la raison principale pour laquelle un risque par trade modéré protège une approche : il limite la profondeur des baisses ordinaires.

## À vous

::: exercise drawdown-serie
:::

::: callout mistake "Erreur fréquente"
Mesurer le drawdown seulement depuis le capital de départ, et conclure qu'un compte « n'a jamais perdu » parce qu'il n'est jamais passé sous son dépôt initial, alors qu'il a rendu une grande partie de ses gains.
:::

::: callout recap
- Le drawdown se mesure du dernier sommet au creux qui le suit ; le drawdown maximal est le plus profond sur la période.
- Depuis le départ ou depuis un sommet : deux mesures différentes, à ne pas confondre.
- Gain nécessaire pour revenir : 1 ÷ (1 − drawdown) − 1. Il croît plus vite que la baisse.
- Un risque par trade modéré limite la profondeur des baisses ordinaires.
:::
