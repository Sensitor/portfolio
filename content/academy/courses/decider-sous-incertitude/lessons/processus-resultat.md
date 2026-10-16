+++
id = "processus-resultat"
title = "Juger la décision, pas le résultat"
summary = "Un trade gagnant peut être une mauvaise décision, et une perte une bonne. Séparer les deux est la base de tout le reste : c'est ce qui permet de rester fidèle à une méthode pendant une série de pertes normale."
duration_minutes = 13
access = "public"
status = "published"
version = 1
objectives = [
  "Distinguer la qualité d'une décision de la qualité de son résultat.",
  "Évaluer la probabilité d'une série de pertes avec une bonne méthode.",
  "Formuler une revue de séance qui porte sur les décisions.",
]
quiz = "check-processus"
resources = ["routine-de-seance"]
+++

## Deux questions différentes

Après un trade, on peut se demander **« ai-je gagné ? »** ou **« ai-je suivi mes règles, avec l'information que j'avais alors ? »**. La première question porte sur le **résultat**, la seconde sur la **décision**. Elles n'ont pas la même réponse aussi souvent qu'on le croit.

Le parcours 5 l'a montré : une approche à espérance positive perd souvent. À 50 % de réussite et 1,5R de gain moyen, son espérance est de +0,25R par trade, et pourtant un trade sur deux est perdant. Juger chacun d'eux sur son résultat reviendrait à condamner la méthode une fois sur deux.

::: figure processus-resultat.svg
Les quatre combinaisons d'une décision et d'un résultat. La case la plus dangereuse est la mauvaise décision récompensée : elle apprend à recommencer. Schéma original.
:::

## La case dangereuse

Une **bonne décision suivie d'une perte** est normale : elle fait partie de l'espérance. Une **mauvaise décision suivie d'un gain** est la plus trompeuse : entrer sans invalidation, doubler la taille, ignorer sa limite du jour, et être récompensé. Le gain renforce exactement le comportement que la méthode voulait écarter.

::: callout example "Exemple pédagogique"
Deux traders prennent le même trade sur EURUSD. Le premier suit son plan : entrée dans sa zone, invalidation écrite, 0,5 % de risque. Le second entre en retard, sans stop, avec 3 % du compte. Le prix va dans leur sens : les deux gagnent. Le résultat est le même ; les décisions n'ont rien en commun, et seule la première peut se répéter cent fois sans ruiner le compte.
:::

## Les séries de pertes sont normales

Une série de pertes ne dit presque rien d'une méthode, parce qu'elle arrive même quand la méthode est bonne.

::: figure series-pertes.svg
La probabilité d'au moins cinq pertes d'affilée, à 50 % de réussite et avec des trades indépendants, en fonction du nombre de trades. Calcul exact.
:::

À 50 % de réussite, cinq pertes de suite ont 3,1 % de chances d'arriver sur les cinq prochains trades, mais **81 %** de chances d'arriver au moins une fois sur cent trades. Celui qui change de méthode à chaque série de cinq pertes en changera presque chaque année, sans jamais en avoir testé une.

::: callout method "Une revue qui porte sur les décisions"
La question de la revue n'est pas « combien ai-je gagné aujourd'hui ? » mais « combien de mes trades respectaient toutes mes règles ? ». Le premier chiffre dépend du marché ; le second dépend de vous. Le journal de l'espace Psychologie et discipline pose cette question après chaque séance.
:::

::: callout mistake "Erreur fréquente"
Modifier sa méthode après trois ou quatre pertes. Un échantillon aussi petit ne permet pas de distinguer une méthode cassée d'une série normale ; le parcours 5 montre combien de trades il faut pour en juger.
:::

::: callout recap
- Le résultat d'un trade et la qualité de la décision sont deux choses différentes.
- La mauvaise décision récompensée est la plus dangereuse : elle renforce l'erreur.
- À 50 % de réussite, une série de cinq pertes survient presque sûrement sur cent trades.
- La revue de séance compte les trades conformes aux règles, pas seulement le résultat.
:::
