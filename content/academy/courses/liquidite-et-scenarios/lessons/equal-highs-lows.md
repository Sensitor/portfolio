+++
id = "equal-highs-lows"
title = "Equal highs et equal lows"
summary = "Deux sommets ou deux creux presque au même prix forment un niveau particulièrement visible. Les repérer avec une tolérance écrite, et savoir quel prix retenir."
duration_minutes = 14
access = "member"
status = "published"
version = 1
objectives = [
  "Repérer des sommets ou des creux égaux avec une tolérance écrite.",
  "Choisir le niveau de référence d'un groupe.",
  "Expliquer pourquoi ces niveaux sont particulièrement observés.",
]
quiz = "check-egalites"
resources = ["fiche-liquidite"]
+++

## Pourquoi ces niveaux comptent

Un sommet de swing isolé est un niveau parmi d'autres. Deux ou trois sommets presque au même prix forment une ligne que tout le monde remarque, qui ressemble à une résistance « solide ». C'est précisément ce qui en fait, pour les méthodes fondées sur la liquidité, un endroit où beaucoup d'ordres s'accumulent : les stops des vendeurs juste au-dessus, les ordres d'achat sur cassure aussi.

On parle d'**equal highs** pour des sommets égaux, d'**equal lows** pour des creux égaux.

::: figure egalites.svg
Deux sommets de swing dans la même bande de tolérance : des sommets égaux, un niveau très visible et donc très observé. Schéma original.
:::

## Une tolérance écrite

Deux sommets ne sont presque jamais exactement au même prix. Il faut donc une **tolérance** : l'écart maximal entre deux swings pour les considérer comme égaux. Elle dépend de l'instrument et de l'unité de temps.

::: callout definition "Règle utilisée dans ce parcours"
Des sommets (ou des creux) de swing sont **égaux** quand ils se situent à moins de la tolérance choisie du premier d'entre eux. Le **niveau de référence** du groupe est le plus haut des sommets (ou le plus bas des creux) : c'est au-delà de ce prix que se trouvent les ordres.
:::

Comme pour la règle des swings, il n'existe pas de bonne tolérance universelle. Quelques pips en H1 sur EURUSD, quelques dixièmes de dollar sur l'or : l'important est de la fixer avant de regarder le graphique et de ne plus y toucher.

::: callout example "Exemple pédagogique"
Avec une tolérance de 3 pips, des sommets à 1,0942 et 1,0944 sont égaux ; un sommet à 1,0928, 14 pips plus bas, n'en fait pas partie. Le niveau de référence est 1,0944.
:::

## À vous

::: exercise egalites-tolerance
:::

::: callout mistake "Erreur fréquente"
Élargir la tolérance jusqu'à trouver des « equal highs » partout. Avec une tolérance de 20 pips, presque tous les sommets d'une semaine finissent dans le même groupe, et le niveau ne veut plus rien dire.
:::

::: callout recap
- Des sommets ou des creux presque au même prix forment un niveau très visible.
- Une tolérance écrite décide de ce qui est « égal » ; elle se fixe à l'avance, par instrument et unité de temps.
- Le niveau de référence est le plus haut des sommets, ou le plus bas des creux, du groupe.
- Une tolérance trop large dilue le niveau jusqu'à le rendre inutile.
:::
