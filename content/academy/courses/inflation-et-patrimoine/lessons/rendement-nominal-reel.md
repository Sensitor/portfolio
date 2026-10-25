+++
id = "rendement-nominal-reel"
title = "Rendement nominal, rendement réel"
summary = "Un placement à 3 % quand les prix montent de 5 % fait perdre du pouvoir d'achat. La différence entre ce qu'affiche un compte et ce qu'il permet d'acheter, la relation de Fisher, et vingt-sept ans de taux réels en zone euro."
duration_minutes = 13
access = "public"
status = "published"
version = 1
updated = 2026-10-17
objectives = [
  "Distinguer rendement nominal et rendement réel.",
  "Calculer un rendement réel exact avec la relation de Fisher.",
  "Lire un historique de taux réels et en tirer une conséquence pour l'épargne.",
]
quiz = "check-rendement-reel"
resources = ["fiche-patrimoine"]
sources = [
  "Fisher, I. (1930). The Theory of Interest. New York : Macmillan.",
  "Banque centrale européenne, Data Portal, série FM.D.U2.EUR.4F.KR.DFR.LEV ; Eurostat, jeu de données prc_hicp_minr ; consultés le 17 octobre 2026.",
]
+++

## Ce qu'affiche un compte, ce qu'il permet d'acheter

Le **rendement nominal** est ce que rapporte un placement en euros : 3 % sur un livret, c'est 30 € de plus pour 1 000 €. Le **rendement réel** est ce qu'il rapporte en **pouvoir d'achat**, une fois la hausse des prix déduite.

::: callout definition "La relation de Fisher"
Le rendement réel exact se calcule ainsi :

(1 + rendement réel) = (1 + rendement nominal) ÷ (1 + inflation)

Pour des taux faibles, on l'approche par une simple différence : rendement réel ≈ rendement nominal − inflation.
:::

::: formula
r_{\text{réel}} = \frac{1 + r_{\text{nominal}}}{1 + \text{inflation}} - 1
:::

::: callout example "Exemple pédagogique"
Un placement à 5 % avec 2 % d'inflation rapporte **2,94 %** en réel (1,05 ÷ 1,02 − 1), un peu moins que la différence de 3 points. Un placement à 3 % avec 5 % d'inflation rapporte **−1,90 %** en réel : le compte affiche un gain, le pouvoir d'achat a baissé.
:::

## Vingt-sept ans de taux réels

::: chart taux-reel
Le taux de la facilité de dépôt de la BCE, l'inflation de la zone euro et leur différence, le taux réel, chaque mois depuis 1999. Survolez les courbes pour lire les valeurs.
:::

Ce que montre la courbe : le taux réel a été **négatif dans 72 % des mois** depuis 1999. Il est tombé à **−9,85 %** en octobre 2022, quand l'inflation a atteint 10,6 % alors que le taux de dépôt était encore à 0,75 %. Il n'a été nettement positif que sur de courtes périodes, comme en 2024, où il a atteint 1,8 %.

::: callout warning "Ce que cela signifie pour l'épargne"
Les placements sans risque, comme les dépôts rémunérés, suivent de près les taux de la banque centrale. Quand le taux réel est négatif, l'épargne la plus sûre perd du pouvoir d'achat, même si elle ne perd jamais en euros. C'est la situation la plus fréquente des vingt-sept dernières années en zone euro.
:::

::: callout mistake "Erreur fréquente"
Juger un placement sur son seul rendement affiché. Un rendement de 4 % est excellent avec 1 % d'inflation et négatif avec 6 %. La première question à poser est toujours : au-dessus ou en dessous de l'inflation ?
:::

::: callout recap
- Rendement nominal : ce que rapporte un placement en euros. Rendement réel : en pouvoir d'achat.
- Relation de Fisher : (1 + réel) = (1 + nominal) ÷ (1 + inflation).
- En zone euro, le taux réel de la BCE a été négatif dans 72 % des mois depuis 1999.
- Une épargne sûre peut perdre en réel sans jamais perdre en euros.
:::
