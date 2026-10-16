+++
id = "risque-de-ruine"
title = "Le risque de ruine"
summary = "La probabilité de perdre une part donnée de son capital avant que l'avantage d'une approche ait le temps de jouer. Pourquoi elle dépend autant du risque par trade que de la méthode."
duration_minutes = 18
access = "member"
status = "published"
version = 1
objectives = [
  "Définir le risque de ruine avec un seuil et un horizon.",
  "Lire l'effet du risque par trade sur ce risque.",
  "Utiliser le simulateur en connaissant ses hypothèses.",
]
quiz = "check-ruine"
resources = ["fiche-risque-duree"]
+++

## Une définition utilisable

« Ruine » ne veut pas forcément dire perdre tout le compte. Une définition utile fixe deux paramètres :

- un **seuil** : la perte, mesurée depuis le capital de départ, que l'on considère comme inacceptable (par exemple 20 %) ;
- un **horizon** : le nombre de trades sur lequel on regarde (par exemple 200).

Le **risque de ruine** est alors la probabilité de franchir ce seuil au moins une fois sur l'horizon.

## Le risque par trade change tout

Le tableau ci-dessous donne cette probabilité pour un seuil de 20 % et 200 trades, avec des gains de 1,5R et des pertes de 1R, en risquant chaque fois le même pourcentage du capital restant.

| Risque par trade | 45 % de réussite (+0,125R) | 40 % (espérance nulle) | 36 % (−0,1R) |
|---|---|---|---|
| 0,5 % | moins de 0,1 % | 0,9 % | 11,0 % |
| 1 % | 1,9 % | 20,7 % | 60,7 % |
| 2 % | 16,0 % | 55,9 % | 88,1 % |
| 3 % | 31,2 % | 72,0 % | 94,3 % |
| 5 % | 53,0 % | 86,1 % | 98,0 % |

::: figure ruine-risque.svg
Probabilité de perdre 20 % du capital de départ en 200 trades, selon le risque par trade, pour trois taux de réussite. Calcul exact sous l'hypothèse de trades indépendants.
:::

Deux enseignements :

1. **Une approche gagnante peut ruiner un compte.** À 45 % de réussite et 1,5R, l'espérance est positive ; avec 5 % de risque par trade, la probabilité de perdre 20 % du capital en 200 trades dépasse pourtant une chance sur deux.
2. **Un risque modéré ne sauve pas une approche perdante.** À 36 % de réussite, même 0,5 % par trade laisse une probabilité de 11 %, et le temps joue contre elle.

::: callout method "Hypothèses du calcul"
Trades indépendants, taux de réussite et ratio constants, risque en pourcentage du capital restant, seuil mesuré depuis le capital de départ. Mesuré depuis un sommet, le seuil serait atteint plus souvent. Et parce que les résultats réels se regroupent en séries, la réalité est en général moins favorable que ces chiffres.
:::

## À vous de simuler

Le simulateur calcule l'espérance, le seuil de rentabilité, le risque de ruine et la fourchette du capital final pour vos propres hypothèses. Tous les chiffres sont exacts sous les hypothèses ci-dessus ; aucun n'est une prévision.

::: tool ruin-simulator
:::

::: callout mistake "Erreur fréquente"
Augmenter le risque par trade après une série de gains, « puisque l'approche marche ». L'échantillon est encore petit (leçon 2) et le risque de ruine augmente beaucoup plus vite que l'espérance.
:::

::: callout recap
- Le risque de ruine se définit avec un seuil de perte et un horizon.
- Il dépend autant du risque par trade que de l'espérance de l'approche.
- Une approche gagnante peut ruiner un compte trop exposé ; un faible risque ne rend pas gagnante une approche perdante.
- Ces probabilités reposent sur des hypothèses favorables ; la réalité est en général plus dure.
:::
