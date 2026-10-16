+++
id = "order-blocks"
title = "L'order block : la bougie d'où part l'impulsion"
summary = "La dernière bougie de sens contraire avant un mouvement qui casse la structure. Une définition précise, ses variantes, et les conditions sans lesquelles elle ne désigne rien de particulier."
duration_minutes = 15
access = "member"
status = "published"
version = 1
objectives = [
  "Repérer un order block haussier ou baissier avec une règle écrite.",
  "Choisir et noter une convention pour les bornes de la zone.",
  "Énoncer les conditions de contexte qui le rendent pertinent, et ce qu'il ne garantit pas.",
]
quiz = "check-order-blocks"
resources = ["fiche-zones"]
+++

## L'idée

Avant une impulsion, le prix hésite souvent, et la dernière bougie avant le départ va fréquemment dans le sens opposé : une bougie baissière juste avant une forte hausse, ou haussière juste avant une forte baisse. Les méthodes ICT appellent cette bougie un **order block** (OB).

L'hypothèse qui l'accompagne : c'est là que de gros intervenants auraient accumulé leurs positions, et le prix reviendrait souvent tester cette zone avant de poursuivre.

## La règle

::: callout definition "Order block, convention de ce parcours"
Un **order block haussier** est la **dernière bougie baissière** (clôture sous l'ouverture) avant une impulsion haussière qui **casse la structure** en clôture. Un **order block baissier** est la dernière bougie haussière avant une impulsion baissière qui casse la structure. La zone va du **plus bas au plus haut** de cette bougie.
:::

Certaines méthodes ne retiennent que le **corps** de la bougie (de l'ouverture à la clôture), d'autres de l'ouverture au plus bas. Les trois se défendent ; ce qui compte est d'en choisir une et de ne plus en changer.

::: figure order-block.svg
Sur GBPUSD, la deuxième bougie balaie des creux égaux puis l'impulsion casse le sommet de swing en clôture. La dernière bougie baissière avant l'impulsion est l'order block ; l'impulsion laisse aussi un FVG juste au-dessus. Schéma original.
:::

::: callout example "Exemple pédagogique"
La bougie baissière ouvre à 1,2646, monte à 1,2650, descend à 1,2630 et clôture à 1,2634. Les trois bougies suivantes sont haussières et la deuxième clôture à 1,2697, au-dessus du sommet de swing à 1,2685 : la structure est cassée. L'order block va de **1,2630 à 1,2650** selon la convention du parcours, de **1,2634 à 1,2646** si l'on ne garde que le corps.
:::

## Ce qui le rend pertinent

Sans contexte, la règle désigne une bougie à chaque petit mouvement. Les méthodes qui l'utilisent ajoutent presque toujours des conditions :

- l'impulsion **casse la structure** (BOS ou MSS, parcours 2) ;
- elle laisse un **FVG**, signe d'un déplacement rapide ;
- l'order block se trouve près d'une **prise de liquidité** (un sweep, parcours 3) ;
- le prix n'est **pas encore revenu** dans la zone.

::: callout method "Ce qu'il ne garantit pas"
Personne ne voit les ordres qui auraient été accumulés dans la bougie : le nom décrit une hypothèse, pas une observation. Un order block peut être traversé sans réaction. Comme pour le FVG, sa valeur se mesure sur un échantillon, avec les mêmes conditions écrites à chaque fois.
:::

::: callout mistake "Erreur fréquente"
Choisir l'order block après coup, en remontant jusqu'à la bougie qui « a tenu ». La règle désigne une seule bougie, la dernière avant l'impulsion, au moment où la cassure est confirmée.
:::

::: callout recap
- Order block haussier : dernière bougie baissière avant une impulsion qui casse la structure. Baissier : l'inverse.
- Bornes : du plus bas au plus haut dans ce parcours ; une autre convention est possible si elle reste fixe.
- Pertinent avec une cassure de structure, un FVG, un sweep proche et une zone pas encore revisitée.
- Le nom décrit une hypothèse sur des ordres invisibles.
:::
