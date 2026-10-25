+++
id = "seuil-suiveur"
title = "Le seuil de perte maximale : fixe, suiveur, verrouillé"
summary = "La règle qui élimine le plus de comptes se calcule jour après jour. Un seuil fixe ne bouge pas, un seuil suiveur remonte avec le plus haut solde, un seuil verrouillé s'arrête au solde initial."
duration_minutes = 16
access = "member"
status = "published"
version = 1
updated = 2026-10-25
objectives = [
  "Calculer un seuil fixe, un seuil suiveur et un seuil verrouillé.",
  "Mesurer la marge réelle d'un compte, jour après jour.",
  "Savoir pourquoi une perte en cours de journée peut éliminer un compte qui finit au-dessus du seuil.",
]
quiz = "check-seuil-suiveur"
resources = ["fiche-prop-firm"]
sources = [
  "Topstep Help Center, What is the Maximum Loss Limit?, https://help.topstep.com/en/articles/8284204, mis à jour le 18 septembre 2026, consulté le 25 octobre 2026.",
  "FTMO, Trading Objectives, https://ftmo.com/en/trading-objectives/, page mise à jour le 20 octobre 2026.",
]
+++

## Trois façons de placer le seuil

Sur un compte de 50 000 $ avec une perte maximale de 2 000 $, le seuil d'élimination part de 48 000 $ dans les trois cas. Ce qui change, c'est ce qu'il fait ensuite.

::: formula
\begin{aligned}
\text{Seuil fixe} &= \text{Solde initial} - \text{Perte maximale} \\
\text{Seuil suiveur} &= \text{Plus haut solde de fin de journée} - \text{Perte maximale} \\
\text{Seuil verrouillé} &= \min(\text{Seuil suiveur},\ \text{Solde initial})
\end{aligned}
:::

- **Fixe** (FTMO 2-Step) : le seuil reste à 48 000 $, quoi qu'il arrive.
- **Suiveur** (FTMO 1-Step) : chaque nouveau plus haut de fin de journée relève le seuil, qui ne redescend jamais.
- **Verrouillé** (Topstep) : le seuil suit, puis s'arrête au solde initial, ici 50 000 $, et n'en bouge plus.

## Le même mois, trois seuils

::: chart prop-seuils
Douze journées construites pour l'exemple, jugées par les trois seuils. Le solde finit à 52 700 $ ; la marge qui le sépare du seuil n'est pas la même selon la règle.
:::

Le jour 8, le solde retombe à 51 000 $ après un plus haut de 52 600 $ :

| Seuil | Niveau le jour 8 | Marge restante |
|---|---|---|
| Fixe | 48 000 $ | 3 000 $ |
| Suiveur | 50 600 $ | 400 $ |
| Verrouillé | 50 000 $ | 1 000 $ |

Avec un seuil suiveur, le compte est en gain de 1 000 $ et n'a plus que 400 $ de marge : un seul trade risquant 500 $ peut le perdre. C'est la conséquence la plus contre-intuitive des challenges : **réussir ses premiers jours réduit sa marge**.

## L'exemple de Topstep

Topstep donne lui-même l'exemple d'un compte de 50 000 $ : seuil de départ à 48 000 $. Le jour 1 gagne 500 $ : solde 50 500 $, seuil relevé à 48 500 $. Le jour 2 perd 500 $ : le solde revient à 50 000 $, mais le seuil reste à 48 500 $. Il ne redescend jamais.

::: callout warning "Le seuil se juge en temps réel"
Le seuil suit le solde de **fin de journée**, mais il se franchit **à tout moment**, pertes latentes comprises. Exemple de Topstep : solde de 50 000 $, seuil à 48 000 $, une position ouverte fait descendre le compte à 47 750 $. Le compte est liquidé, même si la position finit fermée à 48 050 $.
:::

## À vous

::: exercise seuil-suiveur
:::

::: callout mistake "Erreur fréquente"
Mesurer sa marge depuis le solde initial alors que le seuil a suivi. Après une bonne semaine, la marge réelle est la distance au seuil du jour, pas la perte maximale affichée.
:::

::: callout recap
- Fixe : le seuil ne bouge pas. Suiveur : il remonte avec le plus haut solde de fin de journée. Verrouillé : il suit puis s'arrête au solde initial.
- La marge réelle est la distance entre le solde et le seuil du jour.
- Le seuil se franchit en cours de journée, pertes latentes comprises.
:::
