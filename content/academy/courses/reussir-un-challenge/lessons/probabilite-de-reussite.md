+++
id = "probabilite-de-reussite"
title = "Ses chances de réussite, calculées"
summary = "La probabilité d'atteindre l'objectif avant les limites, calculée exactement à partir du taux de réussite, du ratio gain / risque et du risque par trade. Ce qu'elle dit des règles, du risque par trade et de la taille de son échantillon."
duration_minutes = 18
access = "member"
status = "published"
version = 1
updated = 2026-10-25
objectives = [
  "Estimer sa probabilité de réussir un challenge à partir de ses propres chiffres.",
  "Choisir un risque par trade qui ne détruit pas ses chances.",
  "Mesurer l'incertitude qu'ajoute un petit échantillon de trades.",
]
quiz = "check-probabilite-de-reussite"
resources = ["fiche-prop-firm"]
sources = [
  "FTMO, Trading Objectives, https://ftmo.com/en/trading-objectives/, page mise à jour le 20 octobre 2026, consultée le 25 octobre 2026.",
  "Topstep Help Center, What is the Maximum Loss Limit?, https://help.topstep.com/en/articles/8284204, mis à jour le 18 septembre 2026.",
]
+++

## Ce que le calcul suppose

Les chances de réussite se calculent comme une course entre deux bords : l'objectif au-dessus, les limites de perte en dessous. Sensitor les calcule **exactement**, en suivant toutes les suites possibles de gains et de pertes, avec ces hypothèses :

- chaque trade risque le même montant, une part du **solde initial** ;
- une perte coûte 1 R, un gain rapporte le ratio gain / risque ;
- les trades sont indépendants, avec un taux de réussite constant ;
- deux trades par jour, 400 trades au plus ;
- le compte est jugé sur les trades fermés : un trade ouvert qui frôle une limite en cours de journée n'est pas compté ;
- la règle de régularité n'entre pas dans le calcul.

::: callout definition "Avantage"
L'**espérance** d'un trade, en R : taux de réussite × gain moyen − taux d'échec × perte moyenne. À 45 % de réussite et 1,5 R par gain : 0,45 × 1,5 − 0,55 = **+0,125 R**. À 40 % : 0,40 × 1,5 − 0,60 = **0 R**, aucun avantage.
:::

## Le risque par trade décide

::: chart prop-chances
Probabilité de réussir la première phase de FTMO 2-Step, selon le risque par trade, pour deux profils de trader. Calcul Sensitor, hypothèses ci-dessus.
:::

Avec un avantage de +0,125 R, la probabilité de réussir la phase 1 de FTMO 2-Step est de **93,4 %** à 0,5 % par trade, **85,5 %** à 1 %, **72,7 %** à 2 % et **35,2 %** à 3 %. À 3 %, deux pertes le même jour font 6 %, au-delà de la limite journalière de 5 %.

Sans avantage, les chances plafonnent autour d'une sur deux : **50,7 %** à 1 %, **51,5 %** à 2 %. À 0,25 %, seulement **10,2 %** des chemins réussissent dans les 400 trades : la plupart n'ont encore ni réussi ni échoué. Un risque plus faible ne crée pas d'avantage, il allonge la course.

## Les règles décident aussi

Le même trader, 45 % de réussite, 1,5 R par gain, 1 % du solde initial par trade :

| Challenge | Réussite | Élimination |
|---|---|---|
| FTMO 2-Step, phase 1 | 85,5 % | 14,4 % |
| FTMO 1-Step | 74,6 % | 25,4 % |
| Topstep, Trading Combine 50K | 45,9 % | 54,1 % |

Sur le Trading Combine 50K, 1 % du solde initial fait 500 $ : la perte maximale de 2 000 $ tient en quatre pertes, et elle suit le solde, alors que l'objectif est de six gains de 1 R. Les règles comptent autant que la méthode.

À 2 % par trade sous la règle de 3 % de FTMO 1-Step, la probabilité de réussir tombe à **23,6 %** : dans **76,4 %** des cas, deux pertes le même jour éliminent le compte.

## Combien de trades

Avec +0,125 R par trade et 1 % de risque, l'objectif de 10 % demande en moyenne 10 ÷ (1 × 0,125) = **80 trades**, d'après l'espérance seule. Les chemins qui réussissent le font en **58 trades** en moyenne : ce sont ceux où les gains arrivent tôt. Les autres sont souvent éliminés avant.

## Un petit échantillon, une grande incertitude

Un taux de réussite de 44 % mesuré sur 50 trades (22 gagnants) se situe, avec 95 % de confiance, entre **31,2 %** et **57,7 %**. Sur FTMO 2-Step à 1 %, cela fait une probabilité de réussite comprise entre **4,0 %** et **99,8 %**. Le chiffre central, **80,7 %**, ne veut pas dire grand-chose tant que l'échantillon est petit.

::: callout warning "Ce que coûte une réussite"
Avec des frais de 500 $ par tentative (montant construit pour l'exemple), une réussite coûte en moyenne 500 ÷ 0,855 = **585 $** au trader qui a 85,5 % de chances, et 500 ÷ 0,459 = **1 089 $** à celui qui en a 45,9 %.
:::

## Avec vos propres chiffres

::: tool prop-simulator
:::

::: callout mistake "Erreur fréquente"
Augmenter le risque pour réussir plus vite. Les chemins rapides existent, mais la probabilité d'être éliminé monte plus vite encore, surtout sous une limite journalière serrée.
:::

::: callout recap
- Les chances se calculent : taux de réussite, ratio gain / risque, risque par trade et règles du challenge.
- Sans avantage, environ une chance sur deux au mieux ; avec un avantage, le risque par trade décide.
- Une limite journalière serrée sanctionne deux pertes le même jour : le risque par trade doit en tenir compte.
- Sur un petit échantillon, la fourchette compte plus que le chiffre central.
:::
