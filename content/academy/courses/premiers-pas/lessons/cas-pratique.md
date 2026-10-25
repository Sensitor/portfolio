+++
id = "cas-pratique"
title = "Cas pratique : préparer un trade sur papier"
summary = "Appliquer les leçons précédentes à un scénario chiffré, étape par étape, puis comparer votre raisonnement au corrigé."
duration_minutes = 20
access = "member"
status = "published"
version = 1
objectives = [
  "Enchaîner budget de risque, distance au stop et taille de position sur un cas concret.",
  "Intégrer les coûts de transaction au plan.",
  "Anticiper ce que le plan ne contrôle pas.",
]
quiz = "check-cas-pratique"
resources = ["checklist-avant-trade"]
+++

## Le principe

Ce cas pratique ne vous demande pas de deviner si le trade sera gagnant. Il vous demande de le **préparer** : traduire un scénario en chiffres, de façon que la perte reste dans votre budget si vous vous trompez. Faites chaque calcul vous-même avant d'ouvrir le corrigé.

Le scénario est fictif et construit pour l'exercice. Il ne s'agit ni d'une recommandation, ni d'une analyse du marché actuel.

::: exercise cas-eurusd
:::

## Ce que le plan ne contrôle pas

Le plan fixe une perte **prévue**. Plusieurs événements peuvent la dépasser :

- un **gap** à l'ouverture au-delà du stop, qui sera exécuté au premier prix disponible ;
- un **élargissement du spread** au moment d'une annonce, qui peut déclencher un stop placé trop près ;
- une **erreur de saisie** : un lot au lieu de 0,15 lot multiplie le risque par près de sept.

Relire ses ordres avant de les envoyer fait partie de la gestion du risque.

::: callout recap
- Un trade se prépare dans l'ordre : invalidation, budget, distance, taille, coûts.
- Arrondir la taille vers le bas garde le risque sous le budget.
- Les coûts se calculent sur la taille réelle et se rapportent au risque.
- Le plan maîtrise la perte prévue, pas les gaps ni les erreurs d'exécution.
:::
