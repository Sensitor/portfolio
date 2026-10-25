+++
id = "calendrier-economique"
title = "Lire un calendrier économique"
summary = "Heure, importance, précédent, consensus, publié : chaque ligne d'un calendrier se lit de la même façon. Les heures à retenir à Paris, les semaines où elles changent, et la mesure d'une surprise d'un indicateur à l'autre."
duration_minutes = 15
access = "member"
status = "published"
version = 1
updated = 2026-10-19
objectives = [
  "Lire une ligne de calendrier : heure, importance, précédent, consensus, publié.",
  "Connaître les heures de publication majeures à Paris, et les semaines où elles avancent d'une heure.",
  "Comparer des surprises d'indicateurs différents grâce à la surprise normalisée.",
]
quiz = "check-calendrier-economique"
resources = ["fiche-macro"]
sources = [
  "U.S. Bureau of Labor Statistics, calendrier des publications : Employment Situation et Consumer Price Index à 8 h 30, heure de Washington.",
  "Board of Governors of the Federal Reserve System : déclaration du FOMC à 14 h 00, heure de Washington, conférence de presse à 14 h 30.",
  "Banque centrale européenne : décision à 14 h 15 et conférence de presse à 14 h 45, heure de Francfort ; Eurostat : indicateurs euro publiés à 11 h 00.",
  "Directive 2000/84/CE (heure d'été dans l'Union européenne) et Energy Policy Act of 2005 (heure d'été aux États-Unis).",
]
+++

## Une ligne de calendrier

Un calendrier économique liste les publications à venir. Chaque ligne se lit de la même façon.

| Heure (Paris) | Pays | Indicateur | Importance | Précédent | Consensus | Publié |
|---|---|---|---|---|---|---|
| 14 h 30 | États-Unis | Emplois non agricoles | élevée | +80 000 (révisé de +120 000) | +150 000 | +40 000 |
| 14 h 30 | États-Unis | Taux de chômage | élevée | 4,3 % | 4,3 % | 4,4 % |

*Ligne d'exemple, chiffres construits pour la leçon.*

- **L'importance** est une estimation du fournisseur du calendrier : elle dit quelles publications font habituellement réagir le marché, pas ce qui va se passer.
- **Le précédent** peut être révisé dans la même publication : c'est la révision qu'il faut regarder.
- **Le consensus** est la médiane des prévisions d'économistes interrogés quelques jours avant.

## Les heures à retenir

::: figure heures-publication.svg
Une journée de publications à l'heure de Paris : estimation rapide de l'inflation de la zone euro à 11 h 00, décision de la BCE à 14 h 15, emploi et inflation américains à 14 h 30, conférence de la BCE à 14 h 45, décision de la Réserve fédérale à 20 h 00. Schéma original ; aucun jour ne réunit toutes ces publications.
:::

Les publications américaines sont fixées à l'heure de Washington : **8 h 30** pour l'emploi et l'inflation, **14 h 00** pour la décision du FOMC. À Paris, cela donne en général **14 h 30** et **20 h 00**.

::: callout warning "Les semaines décalées"
Les États-Unis passent à l'heure d'été le deuxième dimanche de mars et reviennent à l'heure d'hiver le premier dimanche de novembre ; l'Union européenne le fait le dernier dimanche de mars et le dernier dimanche d'octobre. Pendant deux à trois semaines au printemps et environ une semaine à l'automne, l'écart n'est plus de six heures mais de cinq : un chiffre attendu à 14 h 30 tombe à **13 h 30**. Ainsi, 8 h 30 à Washington le vendredi 13 mars 2026 correspondait à 13 h 30 à Paris, et le vendredi 30 octobre 2026 aussi.
:::

## Comparer des surprises

Une surprise de −110 000 emplois et une surprise de +0,1 point sur l'inflation ne se comparent pas directement. On divise chacune par l'**écart type** des surprises passées du même indicateur : c'est la **surprise normalisée**.

::: formula
\text{Surprise normalisée} = \frac{\text{publié} - \text{consensus}}{\text{écart type des surprises passées}}
:::

Une surprise normalisée de −1,5 signifie : un écart à la baisse une fois et demie plus grand que l'écart habituel. Au-delà de 2 en valeur absolue, la publication sort nettement de l'ordinaire.

## À vous

::: exercise surprise-emploi
:::

::: callout method "La veille d'une séance"
Pour chaque publication d'importance élevée : notez l'heure à Paris, vérifiée pour la semaine en cours, le consensus, le chiffre précédent, et l'écart type habituel des surprises. Décidez avant la publication de ce que vous ferez, comme le montre la leçon « Trois façons de traiter une publication ».
:::

::: callout mistake "Erreur fréquente"
Se fier à l'heure habituelle pendant les semaines décalées, et se retrouver en position au moment où le chiffre sort, une heure plus tôt que prévu.
:::

::: callout recap
- Une ligne de calendrier : heure, importance, précédent (et sa révision), consensus, publié.
- À Paris, en général : 14 h 30 pour l'emploi et l'inflation américains, 20 h 00 pour la Fed, 14 h 15 et 14 h 45 pour la BCE.
- Surprise normalisée = surprise ÷ écart type des surprises passées.
:::
