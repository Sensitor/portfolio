+++
id = "reequilibrer"
title = "Rééquilibrer son allocation"
summary = "Quand la crypto double, elle pèse bientôt bien plus que prévu dans le patrimoine, et le risque avec elle. Rééquilibrer, c'est revenir à la part choisie : vendre ce qui a monté, racheter ce qui a baissé. Quand le faire, combien, et ce que cela coûte."
duration_minutes = 13
access = "member"
status = "published"
version = 1
updated = 2026-10-20
objectives = [
  "Calculer la part d'un actif après une variation de prix.",
  "Calculer le montant à vendre ou à acheter pour revenir à la cible.",
  "Choisir une règle de rééquilibrage : calendrier ou seuil.",
]
quiz = "check-reequilibrer"
resources = ["fiche-investir"]
sources = [
  "Markowitz, H. (1952). « Portfolio Selection ». The Journal of Finance, 7(1), 77-91.",
  "Jaconetti, C. M., Kinniry, F. M. et Zilbering, Y. (2010). « Best practices for portfolio rebalancing ». Vanguard Research.",
]
+++

## La part dérive

Une allocation décidée à 10 % de crypto ne le reste pas. Si la crypto double et que le reste ne bouge pas, elle pèse soudain 18 % du patrimoine : le risque a presque doublé sans que l'on ait rien décidé.

::: formula
\text{Nouvelle part} = \frac{\text{part} \times (1 + \text{variation})}{\text{part} \times (1 + \text{variation}) + \text{reste}}
:::

## Revenir à la cible

Rééquilibrer, c'est vendre l'actif qui a dépassé sa part et racheter celui qui est en dessous. On vend donc ce qui a monté et on rachète ce qui a baissé : une discipline à rebours de l'instinct.

::: formula
\text{Montant à vendre} = \text{patrimoine} \times (\text{part actuelle} - \text{part cible})
:::

## À vous

::: exercise reequilibrage
:::

## Quand rééquilibrer

| Règle | Comment | Avantage | Inconvénient |
|---|---|---|---|
| **Calendrier** | une fois par an, à date fixe | simple, sans décision | peut laisser dériver longtemps |
| **Seuil** | dès que la part s'écarte de la cible de plus d'un seuil, par exemple 5 points | suit le risque | demande une surveillance |
| **Par les versements** | orienter les nouveaux versements vers ce qui est en dessous | aucune vente, donc aucun impôt | lent si les versements sont petits |

::: callout note "Ce que coûte un rééquilibrage"
Chaque vente a des frais, et une vente en euros d'actifs numériques peut être imposable, comme le montre la leçon sur la fiscalité. Le rééquilibrage par les versements évite ces coûts quand l'écart est modéré.
:::

::: callout mistake "Erreur fréquente"
Ne jamais rééquilibrer après une forte hausse, « parce que ça monte ». La part qui grandit, c'est le risque qui grandit ; la baisse suivante frappe alors un patrimoine bien plus exposé que prévu.
:::

::: callout recap
- Une hausse fait dériver la part, et le risque avec elle.
- Montant à vendre = patrimoine × (part actuelle − part cible).
- Calendrier, seuil ou versements : une règle écrite, appliquée sans débat.
:::
