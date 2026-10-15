+++
id = "structure-de-marche"
title = "Lire la structure : tendances, ranges et swings"
summary = "Décrire un graphique à partir des points où le prix change de direction, et séparer ce que l'on voit de ce que l'on suppose."
duration_minutes = 14
access = "member"
status = "published"
version = 1
objectives = [
  "Identifier des sommets et des creux de swing sur un graphique.",
  "Décrire une tendance haussière, une tendance baissière ou un range à partir de ces points.",
  "Séparer une observation d'une interprétation.",
]
quiz = "check-structure-de-marche"
+++

## Ce que l'on regarde

Un graphique en chandeliers résume chaque période — une minute, une heure, une journée — par quatre prix : l'ouverture, le plus haut, le plus bas et la clôture. Plutôt que de commenter chaque bougie, l'analyse de structure s'intéresse aux **points où le prix a changé de direction**. Ce sont eux qui donnent la forme du mouvement.

::: callout definition "Sommet et creux de swing"
Un **sommet de swing** est un plus haut encadré, de part et d'autre, par des plus hauts inférieurs. Un **creux de swing** est un plus bas encadré par des plus bas supérieurs.

Combien de bougies faut-il de chaque côté ? Il n'existe pas de réponse universelle : certains en exigent deux, d'autres jugent à l'œil. L'essentiel est de choisir une définition et de l'appliquer de façon constante.
:::

## Tendances et ranges

Une fois les swings repérés, trois situations se décrivent simplement :

- **tendance haussière** : des sommets de plus en plus hauts et des creux de plus en plus hauts ;
- **tendance baissière** : des sommets de plus en plus bas et des creux de plus en plus bas ;
- **range** : le prix oscille entre deux zones à peu près horizontales, sans progression nette dans un sens.

::: figure structure-tendance.svg
Une tendance haussière décrite par ses swings : chaque sommet (S) dépasse le précédent, chaque creux (C) reste au-dessus du précédent. Schéma original, sans échelle de prix.
:::

::: figure structure-range.svg
Un range : les sommets butent sur une même zone haute, les creux sur une même zone basse. Aucune séquence de sommets ou de creux plus hauts ou plus bas ne se dégage.
:::

## Quand la structure change

Dans une tendance haussière, la cassure du dernier creux de swing montre que la séquence de « creux plus hauts » est interrompue. Beaucoup de méthodes parlent alors de changement de structure. Vous rencontrerez les sigles **BOS** (*break of structure*) pour une cassure dans le sens de la tendance, et **MSS** ou **CHOCH** pour une cassure contre la tendance. Ces notions sont approfondies dans le parcours 2.

::: callout method "Observation ou interprétation ?"
« Le prix a cassé le dernier creux de swing » est une **observation** : chacun peut la vérifier sur le graphique. « Le marché va maintenant baisser » est une **interprétation** : une hypothèse, qui peut se révéler fausse.

La structure décrit le passé ; elle ne prédit pas l'avenir. Une analyse solide formule les deux séparément et précise ce qui invaliderait l'hypothèse.
:::

## L'unité de temps change la lecture

Une tendance haussière sur un graphique en 15 minutes peut s'inscrire dans une baisse sur le graphique journalier. Les deux lectures sont exactes : elles décrivent des échelles différentes. Précisez donc toujours l'unité de temps dont vous parlez. L'analyse multi-unités de temps — partir du contexte large avant d'affiner sur une unité plus courte — sera traitée plus loin dans le programme.

::: callout mistake "Erreur fréquente"
Redessiner ses swings après coup pour qu'ils confirment l'idée de départ. Fixez votre définition avant de regarder le graphique, et appliquez-la même quand elle vous contrarie.
:::

::: callout recap
- Les swings sont les points où le prix change de direction ; leur définition est une convention à fixer et à respecter.
- Tendance haussière : sommets et creux plus hauts. Tendance baissière : sommets et creux plus bas. Range : oscillation entre deux zones.
- Une cassure de structure est une observation ; ce que l'on en déduit est une hypothèse, avec une invalidation.
- Toujours préciser l'unité de temps.
:::
