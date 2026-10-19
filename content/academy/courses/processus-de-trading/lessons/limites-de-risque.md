+++
id = "limites-de-risque"
title = "Les limites qui protègent le compte"
summary = "Une limite de perte se décide à froid et s'applique à chaud, sans renégociation. Limite journalière, hebdomadaire, réduction du risque après une baisse du compte : comment les fixer, les chiffrer, et pourquoi elles comptent plus que n'importe quel setup."
duration_minutes = 15
access = "member"
status = "published"
version = 1
updated = 2026-10-19
objectives = [
  "Fixer une limite journalière et hebdomadaire cohérentes avec le risque par trade.",
  "Écrire une règle de réduction du risque après une baisse du compte.",
  "Calculer ce que coûte une baisse, et ce qu'il faut pour la rattraper.",
]
quiz = "check-limites-de-risque"
resources = ["modele-plan-de-trading"]
sources = [
  "Vince, R. (1990). Portfolio Management Formulas. New York : Wiley : effet du risque par trade sur les baisses du capital.",
  "Kahneman, D. et Tversky, A. (1979). « Prospect Theory: An Analysis of Decision under Risk ». Econometrica, 47(2), 263-291.",
]
+++

## Trois niveaux de limite

Le parcours 5 a montré qu'une série de pertes arrive à toute stratégie, et qu'une baisse se rattrape plus difficilement qu'elle ne se creuse. Les limites du plan en tirent les conséquences.

| Niveau | Ce qu'il arrête | Exemple avec 1 % de risque par trade |
|---|---|---|
| **Séance** | la séance en cours | 2 pertes complètes, soit −2 % |
| **Semaine** | la semaine de trading | −5 % depuis le début de la semaine |
| **Compte** | le niveau de risque, jusqu'au retour au plus haut | −10 % depuis le plus haut : risque divisé par deux |

Ces niveaux se fixent ensemble. Une limite journalière de −2 % avec un risque de 1 % laisse deux pertes complètes ; avec un risque de 2 %, elle n'en laisserait qu'une.

## Une limite ne se renégocie pas

La théorie des perspectives de Kahneman et Tversky l'a montré : après une perte, on devient plus enclin au risque pour revenir à zéro. C'est exactement le moment où une limite décidée à froid doit s'appliquer. Une limite que l'on discute au moment de l'atteindre n'est pas une limite.

::: callout method "Rendre la limite automatique"
- L'écrire dans le plan, en pourcentage et en montant.
- La noter chaque matin dans la préparation : « limite du jour : 400 € ».
- Quand elle est atteinte : fermer la plateforme, remplir le journal, et s'arrêter là.
- Si la plateforme ou le courtier le permettent, programmer la limite dans l'outil lui-même.
:::

## Réduire le risque pendant une baisse

Une règle courante divise le risque par trade par deux quand le compte a baissé d'un seuil, par exemple 10 % depuis son plus haut, et le rétablit au retour au plus haut. Elle ralentit la baisse quand la stratégie traverse une mauvaise période, ou quand elle a cessé de fonctionner, sans arrêter l'activité.

::: formula
\text{Gain nécessaire} = \frac{1}{1 - \text{baisse}} - 1
:::

## À vous

::: exercise limites-perte
:::

::: callout note "Les règles des prop firms"
Les sociétés qui financent des traders imposent presque toutes une limite journalière et une limite de baisse maximale, souvent mesurées sur le capital en temps réel. Le parcours 5 les a détaillées : un plan personnel peut s'en inspirer, avec des seuils plus prudents.
:::

::: callout mistake "Erreur fréquente"
Fixer la limite journalière en nombre de trades perdants plutôt qu'en perte. Trois petites pertes et une grosse ne pèsent pas la même chose : la limite se mesure en pourcentage du compte.
:::

::: callout recap
- Trois niveaux : séance, semaine, compte ; fixés ensemble, en pourcentage et en montant.
- Une limite se décide à froid et s'applique sans renégociation.
- Réduire le risque après une baisse ralentit la chute ; gain nécessaire = 1 ÷ (1 − baisse) − 1.
:::
