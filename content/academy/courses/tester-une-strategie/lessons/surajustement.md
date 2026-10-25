+++
id = "surajustement"
title = "Le surajustement"
summary = "En essayant assez de variantes, on finit toujours par en trouver une qui a brillé sur le passé, par hasard. Pourquoi la meilleure variante est presque toujours décevante ensuite, et comment limiter le problème."
duration_minutes = 15
access = "member"
status = "published"
version = 1
objectives = [
  "Définir le surajustement et ses signes.",
  "Calculer la chance qu'au moins une variante sans avantage paraisse significative.",
  "Appliquer des garde-fous : peu de paramètres, choix justifiés avant le test, nombre de variantes noté.",
]
quiz = "check-surajustement"
resources = ["fiche-backtest"]
+++

## Ce que l'on appelle surajustement

Le **surajustement** (*overfitting*) consiste à adapter une règle si finement à un historique qu'elle en décrit le bruit plutôt qu'un comportement durable. Sur la période testée, elle paraît excellente ; sur la suivante, l'avantage disparaît.

Il naît rarement d'une seule décision. Il s'installe par petites touches : un filtre d'horaire ajouté parce que les pertes tombaient le matin, une taille minimale de FVG passée de 5 à 7 pips parce que le résultat est meilleur, un ratio d'objectif ajusté au dixième. Chaque retouche améliore le passé ; ensemble, elles l'apprennent par cœur.

## Le problème des variantes multiples

Supposons qu'aucune des variantes testées n'ait le moindre avantage. Chacune, par hasard, a 5 % de chances de paraître significative au seuil habituel de 5 %. Si l'on en teste plusieurs, la chance qu'**au moins une** paraisse significative grandit vite :

::: formula
P(\text{au moins un faux positif}) = 1 - (1 - 0{,}05)^{k}
:::

::: figure variantes.svg
La chance qu'au moins une variante sans aucun avantage paraisse significative, selon le nombre de variantes testées. Tests supposés indépendants.
:::

Avec 20 variantes, cette chance est de **64 %** ; avec 100, de **99 %**. La « meilleure variante » d'une longue recherche a donc de fortes chances de devoir son résultat au hasard, et de décevoir ensuite.

::: callout example "Exemple pédagogique"
Un trader teste sa stratégie avec 4 tailles minimales de FVG, 5 marges d'invalidation et 5 objectifs : 4 × 5 × 5 = 100 combinaisons. Il retient la meilleure, à +0,40R. Même si aucune combinaison n'avait d'avantage réel, il était presque certain d'en trouver une qui paraisse bonne. Le +0,40R mesure surtout l'ampleur de la recherche.
:::

## Les garde-fous

- **Peu de paramètres** : chaque seuil ajouté est une occasion de s'ajuster au bruit.
- **Des choix justifiés avant le test** : une taille minimale de FVG fixée parce qu'elle dépasse le spread de façon nette, pas parce qu'elle donne le meilleur chiffre.
- **Compter les variantes** : noter combien on en a essayé, et le dire avec le résultat.
- **Préférer la robustesse** : une règle dont le résultat change peu quand on déplace un seuil est plus crédible qu'une règle qui ne fonctionne qu'à une valeur précise.
- **Garder des données de côté** : c'est l'objet de la leçon suivante.

::: callout mistake "Erreur fréquente"
Ajouter un filtre à chaque série de pertes du backtest. On finit par avoir une règle qui évite toutes les pertes passées, et qui n'a jamais été testée sur des données qu'elle n'a pas déjà vues.
:::

::: callout recap
- Le surajustement apprend le bruit du passé ; l'avantage disparaît ensuite.
- Avec k variantes sans avantage, la chance d'un faux positif au seuil de 5 % vaut 1 − 0,95^k : 64 % pour 20.
- Peu de paramètres, choix justifiés avant, variantes comptées, robustesse vérifiée.
:::
