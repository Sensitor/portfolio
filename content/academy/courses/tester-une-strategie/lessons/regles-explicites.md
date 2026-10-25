+++
id = "regles-explicites"
title = "D'une idée à une règle testable"
summary = "« J'achète les sweeps dans une tendance haussière » est une idée. Une stratégie testable dit, sans place pour l'interprétation, quand entrer, où, où sortir et avec quelle taille. Six parties, et un test simple pour savoir si la règle est assez précise."
duration_minutes = 13
access = "public"
status = "published"
version = 1
objectives = [
  "Décomposer une stratégie en six parties explicites.",
  "Reconnaître les mots qui laissent place à l'interprétation.",
  "Appliquer le test des deux lecteurs à une règle écrite.",
]
quiz = "check-regles"
resources = ["fiche-backtest"]
+++

## Pourquoi écrire la règle

On ne peut tester que ce qui est défini. Une idée comme « acheter les sweeps quand la tendance est haussière » laisse ouvertes toutes les questions qui décident du résultat : quelle tendance, sur quelle unité de temps, quel sweep, entrée où, sortie quand. Si la réponse change d'un graphique à l'autre, le test ne mesure plus une stratégie, il mesure la manière dont on a interprété chaque graphique, une fois la suite connue.

Les parcours précédents ont déjà fait ce travail pièce par pièce : la règle des swings (parcours 2), la convention du sweep (parcours 3), celles du FVG et de la zone OTE (parcours 4), le budget de risque (parcours 1 et 5). Une stratégie les assemble.

## Les six parties

::: figure regles.svg
Les six parties d'une règle, avec un exemple tiré des parcours précédents. Schéma original.
:::

| Partie | La question | Exemple |
|---|---|---|
| **Contexte** | dans quelles conditions la stratégie s'applique-t-elle ? | dernière cassure de structure H4 vers le haut |
| **Déclencheur** | quel événement crée une occasion ? | sweep de creux égaux en M15, puis cassure de structure haussière en clôture |
| **Entrée** | à quel prix, avec quel ordre ? | ordre limite au milieu du FVG laissé par l'impulsion |
| **Invalidation** | où le scénario est-il faux ? | 5 pips sous le plus bas du sweep |
| **Sortie** | quand sort-on, hors invalidation ? | au sommet de la jambe ; ordre annulé si non exécuté en 8 bougies |
| **Taille** | combien risque-t-on ? | 0,5 % du capital, taille arrondie vers le bas |

## Le test des deux lecteurs

::: callout definition "Une règle explicite"
Une règle est **explicite** quand deux personnes qui la lisent, devant le même historique, prennent **exactement les mêmes trades**, aux mêmes prix. Si elles peuvent diverger, la règle contient encore une part d'interprétation.
:::

Les mots qui trahissent une règle implicite sont faciles à repérer : *fort*, *propre*, *clair*, *significatif*, *proche*, *en général*, *si le contexte s'y prête*. Chacun doit être remplacé par un seuil ou une condition vérifiable.

::: callout example "Exemple pédagogique"
« Entrer sur un FVG propre après un fort mouvement » devient : « entrer au milieu d'un FVG d'au moins 5 pips en M15, laissé par une impulsion qui a cassé la structure en clôture dans les 10 bougies suivant un sweep ». La seconde version est plus longue ; elle est aussi la seule que l'on peut tester.
:::

::: callout method "Une version par fichier"
Écrivez la règle dans un document daté, avec un numéro de version. Toute modification crée une nouvelle version, testée à part. Mélanger dans un même résultat des trades pris avec deux versions de la règle rend le chiffre ininterprétable.
:::

::: callout mistake "Erreur fréquente"
Garder une part de « feeling » dans la règle en se disant qu'elle fait la différence. Peut-être, mais elle ne peut pas être testée, et l'on ne saura jamais si elle aide ou si elle nuit.
:::

::: callout recap
- On ne teste que ce qui est défini : contexte, déclencheur, entrée, invalidation, sortie, taille.
- Une règle est explicite quand deux lecteurs prennent les mêmes trades sur le même historique.
- Les mots vagues se remplacent par des seuils ; chaque modification crée une nouvelle version.
:::
