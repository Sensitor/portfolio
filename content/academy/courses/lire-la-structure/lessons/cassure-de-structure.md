+++
id = "cassure-de-structure"
title = "La cassure de structure (BOS)"
summary = "Ce qui confirme qu'une tendance continue : une clôture au-delà du dernier swing. Pourquoi la clôture compte plus que la mèche, et ce qu'une cassure ne promet pas."
duration_minutes = 14
access = "member"
status = "published"
version = 1
objectives = [
  "Reconnaître une cassure de structure dans une tendance haussière ou baissière.",
  "Appliquer la convention de clôture et l'expliquer.",
  "Séparer le constat de cassure de l'hypothèse qui en découle.",
]
quiz = "check-bos"
+++

## La définition

Dans une tendance haussière, chaque nouveau sommet dépasse le précédent. La **cassure de structure** (*break of structure*, BOS) est le moment où le prix franchit le dernier sommet de swing : la séquence de sommets plus hauts se prolonge.

Dans une tendance baissière, c'est l'inverse : une cassure de structure est le franchissement du dernier creux de swing, vers le bas.

::: callout definition "Cassure de structure, convention de ce parcours"
Dans une tendance haussière, une **cassure de structure** est une **clôture** au-dessus du dernier sommet de swing confirmé. Dans une tendance baissière, une clôture en dessous du dernier creux de swing confirmé.
:::

## Clôture ou mèche

Une mèche qui dépasse le niveau puis une clôture qui revient en deçà décrivent une tentative rejetée : le prix est allé voir au-delà et n'y est pas resté. Ce parcours ne la compte pas comme une cassure.

::: figure cassure-bos.svg
Une mèche dépasse le dernier sommet de swing mais la bougie clôture en dessous : pas de cassure. Une bougie suivante clôture au-dessus : cassure de structure. Schéma original.
:::

D'autres méthodes acceptent une mèche. La convention de clôture a un coût : elle confirme plus tard. Elle a un avantage : elle écarte une partie des dépassements qui ne tiennent pas, ces « fausses cassures » que le parcours 3 étudie sous l'angle de la liquidité.

::: callout example "Exemple pédagogique"
EURUSD en H1. Le dernier sommet de swing confirmé est à 1,0890.

Une bougie monte à 1,0895 puis clôture à 1,0884 : la mèche a dépassé le niveau, pas la clôture. **Pas de cassure.**

Deux bougies plus tard, une bougie clôture à 1,0897 : **cassure de structure**, 7 pips au-dessus du sommet.
:::

## Ce qu'une cassure ne promet pas

La cassure est un **constat** : la séquence haussière s'est prolongée d'un cran. L'**hypothèse** qui en découle, « la tendance continue », peut se révéler fausse dès la bougie suivante. Une analyse complète écrit donc aussi ce qui invaliderait cette hypothèse. C'est l'objet de la leçon suivante.

Une cassure se lit aussi dans son unité de temps. Une cassure en M15 décrit le mouvement des dernières heures ; elle ne dit rien de la tendance journalière.

::: callout mistake "Erreur fréquente"
Compter comme cassure une mèche qui dépasse le niveau, puis conclure à une « fausse cassure » quand la bougie clôture en deçà. Avec la convention de clôture, il n'y a pas eu de cassure : il y a eu une tentative rejetée.
:::

::: callout recap
- Une cassure de structure prolonge la tendance : clôture au-delà du dernier sommet (hausse) ou du dernier creux (baisse) de swing confirmé.
- Une mèche seule est une tentative rejetée. La convention de clôture confirme plus tard, mais écarte une partie des dépassements qui ne tiennent pas.
- La cassure est un constat ; « la tendance continue » est une hypothèse, qui a besoin d'une invalidation.
- Une cassure appartient à son unité de temps.
:::
