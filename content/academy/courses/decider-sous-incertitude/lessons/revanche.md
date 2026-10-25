+++
id = "revanche"
title = "Le trade pour se refaire"
summary = "Après des pertes, l'envie de récupérer vite pousse à augmenter le risque. Ce que cela fait au compte, chiffré, et les règles d'arrêt qui coupent l'enchaînement avant qu'il commence."
duration_minutes = 15
access = "member"
status = "published"
version = 1
objectives = [
  "Décrire le trade de revanche et ce qui le déclenche.",
  "Calculer l'effet d'une hausse du risque après une série de pertes.",
  "Écrire des règles d'arrêt qui s'appliquent sans décision à prendre sur le moment.",
]
quiz = "check-revanche"
resources = ["routine-de-seance"]
+++

## Ce que l'on appelle trade de revanche

Le **trade de revanche** (*revenge trading*) est un trade pris pour récupérer une perte, plus que parce qu'il répond aux règles. Il se reconnaît à trois signes : il suit de près une ou plusieurs pertes, il est souvent plus gros que d'habitude, et sa justification est le montant à récupérer plutôt que le scénario.

La logique paraît raisonnable sur le moment : « avec un risque de 3 %, un seul gain efface les trois pertes ». Elle oublie que le trade suivant a les mêmes chances de perdre que les précédents.

## Ce que cela fait au compte

::: figure revanche.svg
Après trois pertes à 1 %, la quatrième perte à 1 % mène à 9 605,96 $ ; la même perte à 3 % mène à 9 411,90 $. Calcul exact, risque recalculé sur le capital courant.
:::

::: exercise revanche-serie
:::

La différence entre les deux chemins n'est pas la perte elle-même, qui peut arriver dans les deux cas. C'est que le trade de revanche **change la taille au moment où le jugement est le moins fiable**, et que le chemin du retour s'allonge d'autant.

## Couper l'enchaînement

Une règle d'arrêt ne sert que si elle s'applique **sans décision à prendre** sur le moment. Quelques exemples, à écrire avant la séance :

| Règle | Exemple |
|---|---|
| **Limite de pertes consécutives** | après 2 pertes de suite, fin de la séance |
| **Limite journalière** | à −2 % sur la journée, fin de la séance (parcours 5) |
| **Taille fixe** | le risque par trade ne change qu'après une revue écrite, jamais pendant la séance |
| **Pause** | après chaque perte, 15 minutes sans graphique avant le trade suivant |

::: callout method "Pourquoi écrire la règle à l'avance"
Après une perte, la question « dois-je m'arrêter ? » se pose au pire moment pour y répondre. Une règle écrite déplace la décision vers un moment calme, avant la séance, et ne laisse plus qu'à l'appliquer.
:::

::: callout note "Quand ce n'est plus une question de méthode"
Si vous constatez que vous ne parvenez plus à vous arrêter malgré vos règles, que vous augmentez les montants pour vous refaire ou que le trading pèse sur votre sommeil, vos finances ou vos proches, ce n'est plus un sujet de technique. Parlez-en à un professionnel de santé. En France, **Joueurs Info Service** répond au **09 74 75 13 13**, de façon anonyme et gratuite.
:::

::: callout recap
- Le trade de revanche est pris pour récupérer une perte, souvent plus gros que d'habitude.
- Tripler le risque après trois pertes fait passer le drawdown de 2,97 % à 5,88 % si le trade est perdu.
- Les règles d'arrêt (pertes consécutives, limite du jour, taille fixe, pause) s'écrivent avant la séance.
:::
