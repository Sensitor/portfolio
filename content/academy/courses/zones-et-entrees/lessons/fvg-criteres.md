+++
id = "fvg-criteres"
title = "Quels FVG retenir"
summary = "Un graphique en contient des dizaines. Des critères écrits à l'avance (taille, contexte, état) font le tri, et une mesure simple dit ce qu'il reste d'un FVG après un retour du prix."
duration_minutes = 16
access = "member"
status = "published"
version = 1
objectives = [
  "Appliquer des critères de sélection écrits avant de regarder le graphique.",
  "Mesurer la part d'un FVG déjà comblée par un retour du prix.",
  "Distinguer un FVG intact, partiellement comblé, comblé ou invalidé.",
]
quiz = "check-fvg-criteres"
resources = ["fiche-zones"]
+++

## Trop de candidats

Sur une journée en M5, la règle des trois bougies trouve facilement une vingtaine de FVG. Les retenir tous revient à n'en retenir aucun : chaque mouvement finit par toucher l'un d'eux, et le récit d'après coup trouve toujours celui qui « a fonctionné ».

Il faut donc des **critères de sélection**, écrits **avant** de regarder le graphique, comme la tolérance des niveaux égaux au parcours 3.

## Trois critères courants

| Critère | Exemple de règle écrite |
|---|---|
| **Taille** | au moins 5 pips en M15 sur EURUSD, ou une fraction fixe de l'amplitude moyenne des bougies |
| **Contexte** | le FVG naît d'une impulsion qui casse la structure, de préférence après un sweep |
| **État** | le prix n'a pas encore traversé l'écart en entier |

Aucun de ces seuils n'est le bon en soi. Leur valeur tient à deux choses : qu'ils soient fixés avant, et qu'ils restent les mêmes sur tout l'échantillon que vous mesurez.

## Ce qu'il reste d'un FVG

Quand le prix revient dans un FVG haussier, on mesure jusqu'où il est descendu dans l'écart, depuis la borne haute :

::: formula
\text{Part comblée} = \frac{\text{Borne haute} - \text{Plus bas atteint}}{\text{Taille du FVG}}
:::

Pour un FVG baissier, on mesure depuis la borne basse jusqu'au plus haut atteint. Le résultat se lit entre 0 % (intact) et 100 % (comblé).

::: callout definition "Les états d'un FVG, conventions de ce parcours"
- **Intact** : le prix n'est pas revenu dans l'écart.
- **Partiellement comblé** : le prix est entré dans l'écart sans le traverser.
- **Comblé** : le prix a atteint la borne opposée.
- **Invalidé** : une bougie a **clôturé** au-delà de la borne opposée. La zone ne sert plus de support (ou de résistance) dans le sens prévu.
:::

## À vous

::: exercise fvg-reperage
:::

::: callout warning "Le milieu n'est pas une cible magique"
Beaucoup de méthodes accordent une importance particulière au milieu de l'écart. C'est une convention commode pour placer un ordre, pas une propriété du prix. Elle se juge, comme le reste, sur un échantillon.
:::

::: callout mistake "Erreur fréquente"
Changer de FVG en cours de route : quand le prix traverse celui que l'on avait choisi, en désigner un autre un peu plus bas et dire que « c'était celui-là ». Le choix se fait avant ; s'il est invalidé, le scénario l'est aussi.
:::

::: callout recap
- Des critères écrits avant (taille, contexte, état) trient les FVG ; sans eux, tout mouvement en « respecte » un.
- La part comblée se mesure depuis la borne d'entrée, en pourcentage de la taille.
- Intact, partiellement comblé, comblé, invalidé en clôture : quatre états, à noter tels quels.
:::
