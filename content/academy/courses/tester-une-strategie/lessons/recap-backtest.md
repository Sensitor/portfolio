+++
id = "recap-backtest"
title = "Récapitulatif et quiz de validation"
summary = "Le protocole complet sur une page, ce qu'un backtest peut et ne peut pas dire, la suite du programme, puis un quiz de validation corrigé."
duration_minutes = 15
access = "member"
status = "published"
version = 1
objectives = [
  "Relier règle explicite, protocole, mesure de l'incertitude et validation.",
  "Vérifier vos acquis avec un quiz corrigé.",
  "Savoir quoi étudier ensuite.",
]
quiz = "backtest-validation"
resources = ["fiche-backtest"]
+++

## Le protocole complet

1. **Écrire la règle** en six parties, assez précise pour que deux lecteurs prennent les mêmes trades. Une version par document.
2. **Fixer** l'instrument, la période de construction et la période de test, avant de regarder.
3. **Faire défiler** l'historique bougie par bougie et noter chaque occurrence avant son issue.
4. **Calculer** taux de réussite, espérance brute et nette, profit factor, avec le nombre de trades.
5. **Mesurer l'incertitude** : intervalle de l'espérance nette, intervalle du taux de réussite.
6. **Compter les variantes** essayées, et limiter les paramètres.
7. **Tester une seule fois** hors échantillon, avec la règle figée.
8. **Suivre en temps réel**, en démo ou à très petite taille, avant tout engagement plus important.

::: callout note "Une idée pour tout résumer"
Un backtest ne dit pas si une stratégie va marcher. Il dit si le passé permet d'exclure qu'elle ne marche pas, et avec quelle marge d'erreur.
:::

## Ce qu'un backtest ne dit pas

- Il ne garantit rien pour l'avenir : les marchés changent, et une règle peut cesser de fonctionner.
- Il ne mesure pas votre exécution : spread du moment, glissement, hésitations, ordres manqués.
- Il ne mesure pas votre discipline : c'est le test en temps réel qui la révèle.

## Et ensuite ?

Le parcours **Macroéconomie et actualité** (parcours 8) expliquera ce qui, dans le calendrier économique, change la volatilité et les coûts d'exécution, et donc la validité d'un test réalisé sur des périodes calmes.

## Quiz de validation

Dix questions couvrent l'ensemble du parcours. La correction détaillée s'affiche à la fin, avec un lien vers la leçon à relire pour chaque erreur.

::: callout recap
- Règle écrite, protocole fixé avant, toutes les occurrences, coûts compris.
- Chaque chiffre avec son nombre de trades et son intervalle.
- Validation hors échantillon une seule fois, puis test en temps réel.
:::
