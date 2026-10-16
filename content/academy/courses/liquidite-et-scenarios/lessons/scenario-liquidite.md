+++
id = "scenario-liquidite"
title = "Cas pratique : un scénario autour d'un sweep"
summary = "Sur XAUUSD, des sommets égaux, un sweep, une invalidation et une taille de position : le scénario complet, écrit avant d'agir, avec ce qu'il ne contrôle pas."
duration_minutes = 22
access = "member"
status = "published"
version = 1
objectives = [
  "Chiffrer un sweep sur des sommets égaux.",
  "Placer l'invalidation au-delà du plus haut du sweep.",
  "Calculer une taille de position à partir d'une spécification de contrat donnée.",
]
quiz = "check-scenario-liquidite"
resources = ["fiche-liquidite", "checklist-avant-trade"]
+++

## Le principe

Ce cas reprend la méthode des parcours précédents. La liquidité dit **où** regarder ; la structure et le sweep fournissent le **constat** ; l'invalidation dit **où le scénario est faux** ; le budget de risque dit **combien** on accepte de perdre.

Le scénario est fictif et construit pour l'exercice. La taille de contrat utilisée est une **hypothèse de l'exercice** : vérifiez toujours la spécification de votre courtier avant tout calcul sur l'or.

::: exercise cas-xauusd
:::

## Ce que le scénario ne contrôle pas

- Le sweep rend plausible un retour sous le niveau ; il ne le garantit pas. Le prix peut repasser au-dessus de 2 415,80 et invalider le scénario.
- Sur l'or, le spread s'élargit souvent autour des annonces américaines ; un stop placé trop près peut être déclenché par le seul écart de cotation.
- La taille dépend de la spécification réelle : avec un contrat de 10 onces au lieu de 100, le même calcul donnerait dix fois plus de lots.

::: callout recap
- Les sommets égaux désignent le niveau ; la clôture de la bougie dit s'il y a sweep ou cassure.
- L'invalidation se place au-delà du plus haut du sweep, avec une marge.
- La taille découle de la distance à l'invalidation et de la valeur d'un mouvement par lot, vérifiée chez le courtier.
- Le scénario reste une hypothèse ; son coût, lui, est connu avant d'entrer.
:::
