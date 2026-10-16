+++
id = "fomo"
title = "La peur de rater le mouvement"
summary = "Le prix part sans vous, et l'envie d'entrer quand même devient pressante. Ce que coûte une entrée poursuivie, en chiffres, et la règle qui permet de laisser passer un trade."
duration_minutes = 14
access = "member"
status = "published"
version = 1
objectives = [
  "Décrire la peur de rater un mouvement (FOMO) comme un comportement de décision.",
  "Calculer ce que coûte une entrée poursuivie en ratio gain / risque et en seuil de rentabilité.",
  "Écrire une règle qui définit à l'avance un trade manqué.",
]
quiz = "check-fomo"
resources = ["routine-de-seance"]
+++

## Ce que l'on appelle FOMO

**FOMO** vient de l'anglais *fear of missing out*, la peur de passer à côté. En trading, c'est l'envie d'entrer **après** qu'un mouvement a commencé, parce qu'on le voit partir sans soi. L'entrée n'était pas prévue à ce prix ; elle est décidée par le mouvement lui-même.

Ce n'est pas un défaut de caractère : c'est une réaction ordinaire devant une occasion qui semble s'échapper. Elle a simplement un coût, que l'on peut calculer.

## Le coût d'une entrée poursuivie

Reprenons le cas GBPUSD du parcours 4. Le plan prévoyait un ordre limite à 1,2657, une invalidation à 1,2625 et un objectif à 1,2730. Le prix ne revient pas dans la zone et monte directement à 1,2700. L'envie : acheter maintenant.

::: figure fomo.svg
Même invalidation, même objectif. L'entrée prévue risque 32 pips pour en gagner 73 ; l'entrée poursuivie risque 75 pips pour en gagner 30. Schéma original.
:::

| | Entrée prévue | Entrée poursuivie |
|---|---|---|
| Prix d'entrée | 1,2657 | 1,2700 |
| Distance à l'invalidation | 32 pips | 75 pips |
| Gain possible | 73 pips | 30 pips |
| Ratio gain / risque | 2,28R | 0,40R |
| Taux de réussite minimal pour ne pas perdre | 30 % | 71 % |
| Taille pour 50 $ de risque | 0,15 lot | 0,06 lot |

Le scénario est le même, le marché est le même. Seul le prix d'entrée a changé, et il transforme un trade qui demande d'avoir raison 3 fois sur 10 en un trade qui demande d'avoir raison 7 fois sur 10.

::: callout warning "Déplacer l'invalidation pour « arranger » le ratio"
La tentation suivante est de rapprocher l'invalidation à 1,2685 pour retrouver un bon ratio. Mais cette invalidation ne correspond plus à rien dans la structure : le scénario n'est pas faux à 1,2685. On a gardé l'apparence du plan en retirant ce qui le rendait cohérent.
:::

## La règle du trade manqué

La parade est de décider **avant** ce qui fait qu'un trade est manqué :

- l'entrée se fait dans la zone écrite, ou pas du tout ;
- si le prix atteint la moitié du chemin vers l'objectif sans avoir touché la zone, le trade est noté « manqué » dans le journal, et l'on passe au suivant ;
- un trade manqué n'est ni une perte ni une erreur : c'est une issue normale d'un ordre limite.

::: callout method "Compter les trades manqués"
Notez-les. Sur cinquante scénarios, combien ont été manqués, et combien d'entre eux auraient été gagnants ? Ce chiffre, mesuré, remplace l'impression que « les meilleurs trades partent toujours sans moi ».
:::

::: callout recap
- Le FOMO est l'envie d'entrer après le début d'un mouvement, sans que ce prix ait été prévu.
- Une entrée poursuivie dégrade le ratio et relève le seuil de rentabilité : de 30 % à 71 % dans le cas GBPUSD.
- Rapprocher l'invalidation pour compenser retire sa cohérence au plan.
- Un trade manqué se définit à l'avance et se note ; ce n'est pas une perte.
:::
