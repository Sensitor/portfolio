+++
id = "hors-echantillon"
title = "Valider hors échantillon"
summary = "Construire la règle sur une partie de l'historique, la tester une seule fois sur une autre qu'on n'a jamais regardée, puis la suivre en temps réel avec une petite taille. Ce que l'on attend de chaque étape, et ce que signifie une dégradation."
duration_minutes = 15
access = "member"
status = "published"
version = 1
objectives = [
  "Séparer les données qui servent à construire la règle de celles qui servent à la tester.",
  "Calculer la dégradation entre les deux échantillons et la lire avec son intervalle.",
  "Décrire le test en temps réel qui suit le backtest.",
]
quiz = "check-hors-echantillon"
resources = ["fiche-backtest"]
+++

## Deux échantillons, deux rôles

La parade la plus efficace contre le surajustement est de garder une partie de l'historique **de côté**.

- L'**échantillon de construction** (*in sample*) sert à écrire la règle, à choisir ses seuils, à essayer des variantes.
- L'**échantillon de test** (*out of sample*) sert **une seule fois**, à la fin, avec la règle figée.

::: figure hors-echantillon.svg
En haut, une séparation simple : 2019 à 2022 pour construire, 2023 et 2024 pour tester. En bas, des fenêtres glissantes : on construit sur trois ans, on teste sur l'année suivante, puis on avance. Schéma original.
:::

::: callout warning "Un échantillon de test ne sert qu'une fois"
Dès que l'on regarde le résultat hors échantillon et que l'on modifie la règle en conséquence, ces données deviennent des données de construction. Il n'existe plus d'échantillon de test, même si l'on continue à l'appeler ainsi.
:::

## Lire une dégradation

Il est normal que le résultat hors échantillon soit moins bon : une partie du résultat de construction venait du hasard et des choix faits en voyant les données. On mesure l'écart par la **dégradation** :

::: formula
\text{Dégradation} = 1 - \frac{\text{espérance hors échantillon}}{\text{espérance dans l'échantillon}}
:::

::: callout example "Exemple pédagogique"
Dans l'échantillon, 300 trades à +0,35R d'espérance nette, écart type 1,3R : intervalle de +0,20 à +0,50R. Hors échantillon, 100 trades à +0,08R, même écart type : intervalle de −0,17 à +0,33R. Dégradation : 1 − 0,08 ÷ 0,35 = **77 %**. L'intervalle hors échantillon contient zéro : le test ne confirme pas l'avantage, et une grande partie du +0,35R initial était probablement due à l'ajustement.
:::

Une dégradation modérée, avec un intervalle hors échantillon qui reste au-dessus de zéro, est un bon signe. Une dégradation forte ou un intervalle qui contient zéro renvoie la règle à la construction, avec de nouvelles données de test à réserver.

## Le test en temps réel

Après le backtest vient le **test en temps réel** (*forward test*) : suivre la règle sur le marché présent, en compte de démonstration ou avec une très petite taille. Il ajoute ce qu'aucun historique ne donne : l'exécution réelle (spread du moment, glissement, ordres manqués) et vous, qui devez appliquer la règle sans connaître la suite. Les comportements du parcours 6 y apparaissent pour la première fois.

::: callout recap
- Construire sur une partie de l'historique, tester une seule fois sur l'autre, avec la règle figée.
- Une dégradation est normale ; elle se lit avec l'intervalle hors échantillon.
- Le test en temps réel, en démo ou à très petite taille, ajoute l'exécution et la discipline.
:::
