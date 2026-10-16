+++
id = "budget-de-risque"
title = "Le budget de risque"
summary = "Décider ce que l'on accepte de perdre avant d'entrer, en déduire la taille de position, et mesurer ce que coûte une série de pertes."
duration_minutes = 18
access = "member"
status = "published"
version = 1
objectives = [
  "Calculer le montant risqué sur une position à partir du capital et d'un pourcentage.",
  "Expliquer pourquoi on place d'abord le stop, puis on calcule la taille de position.",
  "Mesurer l'effet d'une série de pertes sur un compte.",
  "Utiliser un calculateur en connaissant ses hypothèses et ses limites.",
]
quiz = "check-budget-de-risque"
resources = ["checklist-avant-trade"]
+++

## Commencer par ce que l'on accepte de perdre

Le risque d'un trade se décide **avant** l'entrée, et dans cet ordre :

1. **L'invalidation** : le niveau de prix à partir duquel votre scénario est faux. Le stop-loss se place à ce niveau, avec une marge pour le spread et les fluctuations ordinaires.
2. **Le budget de risque** : la somme maximale que vous acceptez de perdre si ce niveau est atteint.
3. **La taille de position** : celle qui fait que, si le stop est touché, la perte est égale à ce budget.

Le budget se fixe le plus souvent en pourcentage du capital :

::: formula
\text{Montant risqué} = \text{Capital} \times \frac{\text{Risque par position (\%)}}{100}
:::

Avec un capital de 10 000 $ et un risque de 1 % par position, le montant risqué est de 100 $.

## De la distance au stop à la taille de position

La taille de position découle du montant risqué et de la distance entre l'entrée et le stop :

::: formula
\text{Taille (lots)} = \frac{\text{Montant risqué}}{\text{Distance au stop} \times \text{Valeur d'un mouvement de 1 par lot}}
:::

::: callout example "Exemple pédagogique : EURUSD, compte en dollars"
Capital de 10 000 $, risque de 1 %, soit 100 $. Achat à 1,0850, stop à 1,0820 : 30 pips. Avec la convention du lot standard (100 000 unités), 1 pip vaut 10 $ par lot : toucher le stop coûte 300 $ par lot.

Taille : 100 ÷ 300 = 0,333 lot, arrondie **vers le bas** à 0,33 lot si le pas de volume est de 0,01. Risque effectif : 0,33 × 300 = 99 $. Ce calcul n'inclut ni le spread, ni la commission, ni le glissement.
:::

::: figure risque-stop-objectif.svg
Entrée, stop et objectif. La distance au stop définit une unité de risque, notée 1R. Un objectif situé à deux fois cette distance correspond à un ratio gain / risque de 2.
:::

::: callout warning "Une formule, plusieurs instruments"
Cette formule ne donne un résultat juste que si la valeur d'un mouvement par lot est correcte pour **votre** instrument chez **votre** courtier : taille de contrat, devise de cotation et conversion vers la devise du compte. Pour l'or, un indice ou une action, lisez la spécification du contrat avant de calculer.
:::

## Le ratio gain / risque

La distance au stop sert d'unité de mesure, notée **R**. Un objectif placé à 60 pips avec un stop à 30 pips représente 2R : si le budget est de 100 $, le gain prévu est de 200 $.

Un ratio élevé ne suffit pas à rendre un trade intéressant : tout dépend de la probabilité d'atteindre l'objectif avant le stop. Un objectif à 5R rarement atteint peut être moins bon qu'un objectif à 1,5R souvent atteint. Cette relation, l'**espérance**, est étudiée dans le parcours consacré à la gestion du risque.

## Les séries de pertes font partie du jeu

Même une approche rigoureuse connaît des séries de pertes. Le tableau ci-dessous montre ce que deviennent 10 000 $ après **dix pertes consécutives**, en risquant chaque fois le même pourcentage du capital restant.

| Risque par position | Capital restant | Baisse | Gain nécessaire pour revenir |
|---|---|---|---|
| 0,5 % | 9 511 $ | −4,9 % | +5,1 % |
| 1 % | 9 044 $ | −9,6 % | +10,6 % |
| 2 % | 8 171 $ | −18,3 % | +22,4 % |
| 5 % | 5 987 $ | −40,1 % | +67,0 % |

La dernière colonne explique pourquoi un drawdown profond est si difficile à effacer : après une baisse de 40 %, il faut gagner 67 % pour retrouver le capital de départ.

Ces séries ne sont pas rares. Avec un taux de réussite de 50 % et des trades indépendants, la probabilité de connaître **au moins une série de 5 pertes consécutives** sur 100 trades est d'environ 81 % ; pour une série de 6 pertes ou plus, d'environ 55 %.

::: callout method "Hypothèse"
Ces probabilités supposent des trades indépendants et un taux de réussite constant. En pratique, les résultats ont tendance à se regrouper (périodes de marché difficiles, erreurs répétées), ce qui rend les longues séries encore plus probables.
:::

## À vous de calculer

Le calculateur ci-dessous applique exactement ces formules. Sans spécification d'instrument, il calcule le montant risqué, la distance au stop et le ratio gain / risque. Avec la spécification de votre courtier, il calcule aussi la taille de position.

::: tool risk-calculator
:::

::: callout mistake "Erreur fréquente"
Éloigner son stop en cours de trade pour « laisser respirer » la position. La perte possible dépasse alors le budget décidé avant l'entrée, au moment précis où l'on est le moins lucide.
:::

::: callout recap
- Ordre des décisions : invalidation, puis budget de risque, puis taille de position.
- Montant risqué = capital × risque % ÷ 100. La taille de position dépend en plus de la distance au stop et de la valeur d'un mouvement par lot.
- Arrondir la taille vers le bas, jamais vers le haut.
- Une série de pertes est normale ; un risque par position élevé la rend difficile à rattraper.
:::
