+++
id = "backtest-manuel"
title = "Le backtest manuel, pas à pas"
summary = "Faire défiler l'historique bougie par bougie, noter chaque occurrence sans exception, puis calculer ce que la série dit vraiment, coûts compris. Un protocole simple et une première série à chiffrer."
duration_minutes = 17
access = "member"
status = "published"
version = 1
objectives = [
  "Suivre un protocole de backtest manuel qui exclut l'anticipation.",
  "Tenir une feuille de relevé complète.",
  "Calculer taux de réussite, espérance brute et nette, et profit factor d'une série.",
]
quiz = "check-backtest-manuel"
resources = ["fiche-backtest"]
+++

## Le protocole

Un **backtest** applique une règle écrite à un historique pour mesurer ce qu'elle aurait donné. Un backtest **manuel** le fait à la main, en faisant défiler le graphique. Il est lent, et c'est une qualité : il oblige à regarder chaque occurrence.

1. **Fixer la période avant de regarder** : par exemple, du 1er janvier 2022 au 31 décembre 2023, sur EURUSD M15. La période ne change plus ensuite.
2. **Masquer la suite** : faire avancer le graphique **une bougie à la fois**, sans jamais regarder à droite. La plupart des plateformes ont un mode de relecture pour cela.
3. **Noter chaque occurrence**, gagnante, perdante ou non exécutée, dès que la règle la désigne, et avant de connaître son issue.
4. **Appliquer les coûts** : spread, commission et glissement moyens de l'instrument, exprimés en R.
5. **Calculer** une fois la période terminée, pas en cours de route.

::: callout definition "La feuille de relevé"
Une ligne par occurrence : date et heure, version de la règle, prix d'entrée, invalidation, objectif, exécuté ou non, résultat en R, remarque éventuelle. Les occurrences non exécutées (ordre limite jamais atteint) se notent aussi : elles font partie de ce que la règle produit.
:::

## Ce que l'on calcule

Sur une série de résultats exprimés en R :

- le **taux de réussite** : la part des trades gagnants ;
- l'**espérance brute** : la moyenne des résultats ;
- l'**espérance nette** : l'espérance brute moins le coût moyen par trade ;
- le **profit factor** : la somme des gains divisée par la somme des pertes.

::: formula
\text{Espérance nette} = \frac{\sum \text{résultats}}{n} - \text{coût moyen par trade}
:::

## À vous

::: exercise backtest-serie
:::

::: callout warning "Vingt trades ne suffisent pas"
L'exercice porte sur vingt trades pour que le calcul reste court. La leçon 4 montrera ce que vaut un résultat mesuré sur si peu d'occurrences : à peu près rien. Un backtest manuel utile compte plusieurs centaines d'occurrences, souvent sur plusieurs années.
:::

::: callout mistake "Erreur fréquente"
Sauter les occurrences « évidemment mauvaises » parce que, en les voyant, on sait qu'on ne les aurait pas prises. Si la règle les désigne, elles font partie du test. Si on ne les aurait vraiment pas prises, c'est que la règle écrite n'est pas celle que l'on suit, et c'est elle qu'il faut réécrire.
:::

::: callout recap
- Période fixée avant, graphique avancé bougie par bougie, chaque occurrence notée avant son issue.
- Les coûts se retranchent de chaque trade ; une espérance brute faible peut devenir négative.
- Taux de réussite, espérance brute et nette, profit factor : quatre chiffres, toujours avec le nombre de trades.
:::
