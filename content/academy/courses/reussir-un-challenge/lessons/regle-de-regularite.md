+++
id = "regle-de-regularite"
title = "La règle de régularité : quand un bon jour pèse trop"
summary = "Une limite à la part du meilleur jour. Elle n'élimine pas, mais elle allonge le challenge : chez FTMO, il faut continuer de trader ; chez Topstep, l'objectif monte."
duration_minutes = 13
access = "member"
status = "published"
version = 1
updated = 2026-10-25
objectives = [
  "Vérifier la règle de régularité de FTMO 1-Step sur une série de jours.",
  "Calculer l'objectif relevé par la règle de Topstep.",
  "Répartir son risque pour ne pas dépendre d'une seule journée.",
]
quiz = "check-regle-de-regularite"
resources = ["fiche-prop-firm"]
sources = [
  "FTMO, Trading Objectives, https://ftmo.com/en/trading-objectives/, page mise à jour le 20 octobre 2026, consultée le 25 octobre 2026.",
  "Topstep Help Center, Consistency at Topstep, https://help.topstep.com/en/articles/8284208, mis à jour le 17 septembre 2026.",
]
+++

## Pourquoi une règle de régularité

Un challenge réussi en un seul grand jour dit peu de choses sur la méthode : il ressemble à un pari gagné. Les sociétés limitent donc la part d'une seule journée dans le résultat. La règle **n'élimine pas** le compte ; elle oblige à continuer.

## FTMO 1-Step : le meilleur jour face au profit total

Pour les comptes commandés depuis le 12 octobre 2026, le meilleur jour ne doit pas dépasser **50 %** du profit total, calculé sur les positions fermées.

::: formula
\text{Profit total nécessaire} = \frac{\text{Meilleur jour}}{50\ \%}
:::

L'exemple de FTMO : un meilleur jour de 6 000 $ sur un profit total de 10 000 $ représente 60 %. La règle n'est pas respectée, et tant que ce jour reste le meilleur, il faut atteindre **12 000 $** de profit total.

## Topstep : le meilleur jour face à l'objectif

Sur le Trading Combine, le meilleur jour doit rester sous **55 %** de l'objectif. Sur un 50K, l'objectif est de 3 000 $ : le meilleur jour doit rester sous **1 650 $**. Au-delà, l'objectif monte.

::: formula
\text{Nouvel objectif} = \max\left(\text{Objectif},\ \frac{\text{Meilleur jour}}{55\ \%}\right)
:::

Les exemples de Topstep : un meilleur jour de 1 600 $ sur 3 000 $ de profit fait 53 %, la règle est respectée. Un meilleur jour de 1 800 $ porte l'objectif à 1 800 ÷ 0,55, soit **3 273 $**. Si le jour suivant gagne 2 200 $, il devient le meilleur jour et l'objectif passe à **4 000 $**. Une journée perdante ne fait pas oublier le meilleur jour.

## À vous

::: exercise regularite-challenge
:::

::: callout method "Répartir plutôt que forcer"
La règle se respecte d'elle-même avec un risque constant et une limite de gain journalière : arrêter la séance quand le jour atteint, par exemple, 40 % de l'objectif. Le plus sûr moyen de la violer est d'augmenter la taille un jour où « tout marche ».
:::

::: callout mistake "Erreur fréquente"
Croire que la règle de régularité fait perdre le compte. Elle allonge le challenge, et c'est en continuant de trader pour la respecter que le compte se rapproche de ses limites de perte.
:::

::: callout recap
- La régularité limite la part du meilleur jour ; elle n'élimine pas.
- FTMO 1-Step : meilleur jour au plus 50 % du profit total, sinon il faut continuer.
- Topstep : meilleur jour sous 55 % de l'objectif, sinon l'objectif devient meilleur jour ÷ 0,55.
:::
