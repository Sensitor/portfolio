+++
id = "fvg-definition"
title = "Le Fair Value Gap : un écart sur trois bougies"
summary = "Quand une bougie se déplace si vite que ses voisines ne se recouvrent pas, elle laisse un intervalle de prix où presque rien ne s'est échangé. Le repérer avec une règle stricte, et savoir ce que l'on en dit."
duration_minutes = 13
access = "public"
status = "published"
version = 1
objectives = [
  "Définir un Fair Value Gap haussier et baissier avec une règle sur trois bougies.",
  "Mesurer ses bornes, sa taille et son milieu.",
  "Séparer la définition, observable, de l'hypothèse de méthode qui l'accompagne.",
]
quiz = "check-fvg"
resources = ["fiche-zones"]
+++

## Ce que l'on regarde

Le parcours 3 s'est intéressé aux niveaux **au-delà** des sommets et des creux. Ce parcours regarde **à l'intérieur** des mouvements : les zones que le prix a traversées trop vite, et celles d'où une impulsion est partie.

La première de ces zones s'appelle le **Fair Value Gap** (FVG), parfois traduit par « déséquilibre » ou « imbalance ». Le terme vient des méthodes de price action dites ICT ; la définition, elle, se vérifie sur n'importe quel graphique.

## La règle sur trois bougies

::: callout definition "Fair Value Gap, convention de ce parcours"
Sur trois bougies consécutives, un **FVG haussier** existe quand le **plus bas de la troisième** est strictement au-dessus du **plus haut de la première**. L'écart entre ces deux prix est le FVG. Un **FVG baissier** existe quand le **plus haut de la troisième** est strictement sous le **plus bas de la première**.
:::

La bougie du milieu est celle qui se déplace : elle va si vite que les mèches de ses deux voisines ne se rejoignent pas. Entre elles reste un intervalle que le prix n'a traversé qu'une fois, dans un seul sens.

::: figure fvg.svg
À gauche, un FVG haussier entre le haut de la bougie 1 et le bas de la bougie 3 ; à droite, le FVG baissier symétrique. Le pointillé marque le milieu de chaque écart. Schéma original.
:::

## Les trois mesures

Un FVG se décrit par trois chiffres :

- ses **bornes** : le plus haut de la bougie 1 et le plus bas de la bougie 3 pour un FVG haussier ;
- sa **taille** : l'écart entre les deux bornes, en pips ou en points ;
- son **milieu**, que les méthodes ICT appellent *consequent encroachment* (CE).

::: formula
\text{Milieu} = \frac{\text{Borne basse} + \text{Borne haute}}{2}
:::

::: callout example "Exemple pédagogique"
Sur EURUSD en M15, la bougie 1 a un plus haut à 1,0832, la bougie 3 un plus bas à 1,0846. Le plus bas de la troisième est au-dessus du plus haut de la première : FVG haussier de **1,0832 à 1,0846**, soit **14 pips**, avec un milieu à **1,0839**. Si le plus bas de la bougie 3 avait été 1,0832 ou moins, il n'y aurait pas de FVG : les mèches se toucheraient.
:::

## Ce que l'on en dit, et ce que l'on n'en sait pas

La définition est une **observation** : on peut la vérifier sur l'historique, sans interprétation. Ce qui suit est une **hypothèse de méthode** : un déplacement aussi rapide traduirait un déséquilibre entre acheteurs et vendeurs, et le prix reviendrait souvent dans l'écart avant de poursuivre.

::: callout method "Hypothèse de méthode, pas loi du marché"
Que le prix « revienne combler » les FVG n'a rien d'obligatoire. Certains ne sont jamais revisités ; d'autres le sont entièrement puis dépassés. La seule manière de savoir ce que vaut cette hypothèse sur votre instrument et votre unité de temps est de la compter, avec des règles écrites et un échantillon suffisant, comme au parcours 5.
:::

::: callout mistake "Erreur fréquente"
Appeler FVG toute grande bougie. Une grande bougie dont les voisines se recouvrent ne laisse aucun écart. La règle porte sur les mèches de la première et de la troisième bougie, pas sur la taille de celle du milieu.
:::

::: callout recap
- Un FVG haussier : plus bas de la bougie 3 au-dessus du plus haut de la bougie 1. Baissier : l'inverse.
- Il se décrit par ses bornes, sa taille et son milieu.
- La définition s'observe ; le retour du prix dans l'écart reste une hypothèse à mesurer.
:::
