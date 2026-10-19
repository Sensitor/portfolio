+++
id = "executer-seance"
title = "Exécuter et gérer ses trades"
summary = "Pendant la séance, il ne reste qu'à appliquer : entrer là où le plan le dit, gérer la position comme il l'a prévu, réagir à une erreur d'exécution sans l'aggraver, et clore la séance quand une limite ou l'heure est atteinte."
duration_minutes = 14
access = "member"
status = "published"
version = 1
updated = 2026-10-19
objectives = [
  "Appliquer les règles d'entrée et de gestion du plan, sans en ajouter pendant la séance.",
  "Traiter une erreur d'exécution selon une procédure.",
  "Clore une séance et remplir le journal tant que les faits sont frais.",
]
quiz = "check-executer-seance"
resources = ["modele-plan-de-trading", "checklist-avant-trade"]
sources = [
  "Steenbarger, B. N. (2009). The Daily Trading Coach. Hoboken : Wiley.",
  "Shefrin, H. et Statman, M. (1985). « The Disposition to Sell Winners Too Early and Ride Losers Too Long: Theory and Evidence ». The Journal of Finance, 40(3), 777-790.",
]
+++

## Entrer seulement là où le plan le dit

Chaque entrée passe la **checklist avant trade** du parcours 1, en entier : scénario écrit, invalidation, taille calculée, coûts, conditions de marché. Une entrée qui ne la passe pas n'est pas prise, même si le prix part ensuite dans le bon sens.

## Gérer la position comme prévu

La gestion d'un trade ouvert est l'endroit où les règles cèdent le plus souvent. Shefrin et Statman ont décrit dès 1985 l'**effet de disposition** : on vend trop tôt ce qui gagne et on garde trop longtemps ce qui perd. D'où des règles écrites à l'avance.

| Ce qui arrive | La règle habituelle | L'écart fréquent |
|---|---|---|
| le prix approche du stop | le stop reste où il est | éloigner le stop « pour laisser respirer » |
| le trade est en gain | sortie selon la règle écrite : objectif, sortie partielle ou stop suiveur | sortir trop tôt par peur de rendre le gain |
| le scénario est invalidé avant le stop | sortir si le plan le prévoit | rester « au cas où » |
| une perte vient d'arriver | pause, puis seulement le scénario suivant | reprendre tout de suite pour se refaire |

## Une erreur d'exécution

Une taille mal saisie, un ordre en double, un achat à la place d'une vente : cela arrive. La règle est de **ne pas transformer l'erreur en trade**.

::: callout method "Procédure d'erreur"
1. Constater l'écart avec le plan : taille, sens, instrument, prix.
2. Ramener immédiatement la position à ce que le plan prévoit, ou la fermer si elle n'aurait pas dû exister, quel qu'en soit le résultat.
3. Noter l'erreur dans le journal, avec sa cause.
4. Si la cause est la fatigue ou la précipitation, terminer la séance.
:::

## Clore la séance

Une séance se termine à l'heure prévue, ou plus tôt si une limite est atteinte. Avant de quitter l'écran, on remplit le journal : chaque trade, son résultat en R, et s'il a respecté toutes les règles. Le soir, la mémoire a déjà commencé à réécrire l'histoire.

::: callout mistake "Erreur fréquente"
Garder une erreur d'exécution « parce qu'elle gagne ». Un trade hors plan qui gagne apprend à recommencer ; le jour où il perd, il coûte bien plus que prévu.
:::

::: callout recap
- Chaque entrée passe la checklist ; sinon, pas de trade.
- La gestion suit la règle écrite : stop immobile, sortie prévue, pause après une perte.
- Une erreur d'exécution se corrige tout de suite et se note ; le journal se remplit avant de quitter l'écran.
:::
