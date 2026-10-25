+++
id = "cas-entree"
title = "Cas pratique : une entrée sur GBPUSD"
summary = "Un sweep de creux égaux, une cassure de structure, un order block, deux FVG et une zone OTE : on choisit la zone, on place l'entrée et l'invalidation, on calcule la taille, et l'on écrit ce que le plan ne contrôle pas."
duration_minutes = 24
access = "member"
status = "published"
version = 1
objectives = [
  "Identifier les zones d'un même mouvement et leur intervalle commun.",
  "Placer une entrée, une invalidation et un objectif à partir de règles écrites.",
  "Calculer une taille de position et un ratio gain / risque, coûts mis à part.",
]
quiz = "check-cas-entree"
resources = ["fiche-zones", "checklist-avant-trade"]
+++

## La méthode, dans l'ordre

Ce cas réunit les quatre parcours précédents. Chaque étape répond à une question, et chaque réponse s'écrit avant d'entrer.

1. **Contexte** (parcours 2) : dans quel sens va la structure de l'unité supérieure ?
2. **Liquidité** (parcours 3) : quel niveau a été pris ?
3. **Confirmation** (parcours 2) : la structure a-t-elle cassé en clôture dans le sens prévu ?
4. **Zone** (ce parcours) : où se recouvrent les zones issues de l'impulsion ?
5. **Risque** (parcours 1 et 5) : où le scénario est-il faux, et combien coûte l'erreur ?

Le scénario est fictif et construit pour l'exercice.

::: exercise cas-zone-entree
:::

## Ce que le plan ne contrôle pas

- Le prix peut ne jamais revenir dans la zone : l'ordre limite n'est alors pas exécuté, et c'est un résultat normal.
- Il peut aussi la traverser et toucher l'invalidation. La perte est connue, 48 $ avant spread et commission, et elle fait partie de la méthode.
- Le ratio de 2,28 suppose l'objectif atteint. Il ne dit rien de la probabilité de l'atteindre : seule une série de trades mesurés le dira.
- Autour des annonces britanniques et américaines, le spread de GBPUSD s'élargit ; un ordre placé juste avant peut être exécuté à un prix moins bon.

::: callout mistake "Erreur fréquente"
Déplacer l'invalidation sous l'order block « pour lui laisser de la place » une fois en position. La taille a été calculée pour 32 pips ; à 45 pips, le même lot risque 67,50 $ au lieu de 48 $, au-delà du budget écrit.
:::

::: callout recap
- Contexte, liquidité, confirmation, zone, risque : cinq questions dans cet ordre.
- La zone d'entrée est l'intervalle commun de zones issues du même mouvement, sans les compter comme des preuves séparées.
- L'invalidation se place au-delà du sweep ; la taille découle de la distance et du budget.
- Le ratio gain / risque décrit le plan, pas sa probabilité de réussite.
:::
