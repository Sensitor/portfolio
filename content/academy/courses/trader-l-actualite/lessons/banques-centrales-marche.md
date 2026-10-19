+++
id = "banques-centrales-marche"
title = "Les banques centrales et ce que le marché anticipe"
summary = "Une décision de taux attendue ne surprend personne : le marché l'a déjà intégrée, parfois des mois avant. Comment lire ce qu'il anticipe, dans le rendement à 2 ans et dans le prix des contrats à terme."
duration_minutes = 17
access = "member"
status = "published"
version = 1
updated = 2026-10-19
objectives = [
  "Décrire le calendrier et la communication de la Réserve fédérale et de la BCE.",
  "Lire dans le rendement à 2 ans ce que le marché anticipe de la politique monétaire.",
  "Calculer le taux implicite d'un contrat à terme et la probabilité d'une décision qu'il contient.",
]
quiz = "check-banques-centrales-marche"
resources = ["fiche-macro"]
sources = [
  "Board of Governors of the Federal Reserve System : calendrier du FOMC, déclarations et Summary of Economic Projections.",
  "Banque centrale européenne : calendrier des réunions de politique monétaire, communiqué à 14 h 15 et conférence de presse à 14 h 45, heure de Francfort.",
  "Board of Governors of the Federal Reserve System, séries GS2 et FEDFUNDS, via FRED, Federal Reserve Bank of St. Louis, consultées le 19 octobre 2026.",
  "CME Group, contrats 30-Day Federal Funds Futures : cotation en 100 moins le taux moyen attendu du mois.",
]
+++

## Ce que décide une banque centrale

La **Réserve fédérale** américaine se réunit huit fois par an. Son comité, le FOMC, fixe une fourchette pour le taux des fonds fédéraux. Son mandat est double : l'emploi maximal et la stabilité des prix, avec un objectif d'inflation de 2 %. Quatre fois par an, en mars, juin, septembre et décembre, elle publie aussi les projections de ses membres, dont leur prévision de taux.

La **BCE** se réunit aussi huit fois par an. Elle vise une inflation de 2 % à moyen terme dans la zone euro ; son taux de référence est aujourd'hui celui de la facilité de dépôt.

| | Réserve fédérale | BCE |
|---|---|---|
| Réunions par an | 8 | 8 |
| Décision, heure de Paris | 20 h 00 en général | 14 h 15 |
| Conférence de presse | 30 minutes après | 14 h 45 |
| Objectif d'inflation | 2 % (indice PCE) | 2 % à moyen terme (IPCH) |

Le jour d'une décision, trois choses font réagir le marché : la décision elle-même, le **communiqué**, et ce que dit le président ou la présidente en conférence de presse sur la suite. La troisième pèse souvent le plus.

## Le marché anticipe

Une décision attendue ne surprend personne. Le marché l'a intégrée, parfois longtemps avant, dans les taux à court terme. Le rendement du Trésor à **2 ans** en est le meilleur témoin : il reflète, à une prime de risque près, le niveau moyen que le marché attend des taux directeurs sur les deux années à venir.

::: chart deux-ans-fed
Le rendement du Trésor américain à 2 ans et le taux des fonds fédéraux, chaque mois depuis 2015.
:::

Ce que montre la courbe :

- **En 2021-2022**, le rendement à 2 ans passe de 0,20 % en juin 2021 à 1,44 % en février 2022, alors que le taux des fonds fédéraux reste à 0,08 %. La première hausse n'arrive qu'en mars 2022.
- **En 2023-2024**, le rendement à 2 ans culmine à 5,07 % en octobre 2023, puis recule à 3,97 % en août 2024 pendant que le taux directeur reste à 5,33 %. La première baisse est décidée en septembre 2024.
- **En septembre 2026**, le rendement à 2 ans, 4,65 %, dépasse de 0,90 point le taux des fonds fédéraux, 3,75 %. En première lecture, le marché attend des taux plus élevés sur les deux ans qui viennent.

::: callout definition "Taux implicite d'un contrat à terme"
Un contrat à terme sur les fonds fédéraux cote **100 moins le taux moyen attendu** du mois. À 95,80, il contient un taux attendu de 4,20 %.
:::

## Lire une probabilité

Supposons que la fourchette actuelle soit 4,25 à 4,50 %, dont le milieu est 4,375 %, et que le contrat du mois qui suit la réunion cote 95,80. Le taux attendu est de 4,20 %, soit 0,175 point sous le taux actuel : **0,70** baisse d'un quart de point. Si l'on admet que seules deux issues sont possibles, aucune baisse ou une baisse d'un quart de point, le marché donne environ **70 %** de chances à la baisse.

::: formula
\text{Probabilité} \approx \frac{|\text{taux attendu} - \text{taux actuel}|}{0{,}25}
:::

::: callout warning "Une approximation"
Ce calcul suppose deux issues seulement et ignore la prime de risque contenue dans le prix du contrat. Les outils qui publient ces probabilités, comme le FedWatch du CME, raffinent la méthode, mais reposent sur la même idée.
:::

## À vous

::: exercise taux-anticipes
:::

::: callout mistake "Erreur fréquente"
Prendre position sur une décision « que tout le monde attend ». Si elle est déjà dans les prix, la décision elle-même ne fera presque rien bouger ; c'est la conférence de presse, et ce qu'elle dit de la suite, qui décide de la réaction.
:::

::: callout recap
- Fed et BCE se réunissent huit fois par an ; la communication sur la suite pèse souvent plus que la décision.
- Le rendement à 2 ans anticipe la politique monétaire : en 2022 comme en 2024, il a bougé des mois avant la banque centrale.
- Taux implicite = 100 − prix du contrat ; part d'un quart de point déjà intégrée ≈ probabilité.
:::
