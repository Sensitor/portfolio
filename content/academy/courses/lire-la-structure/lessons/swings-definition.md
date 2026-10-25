+++
id = "swings-definition"
title = "Repérer les swings sans les inventer"
summary = "Une règle écrite pour désigner les sommets et les creux de swing, appliquée bougie par bougie, et sa conséquence majeure : un swing ne se confirme qu'après coup."
duration_minutes = 14
access = "public"
status = "published"
version = 1
objectives = [
  "Appliquer une règle de swing à une série de bougies.",
  "Expliquer pourquoi un swing n'est confirmé qu'avec retard.",
  "Éviter de redessiner la structure après coup.",
]
quiz = "check-swings"
resources = ["fiche-lire-la-structure"]
+++

## Pourquoi une règle écrite

Le parcours 1 a défini le sommet et le creux de swing, et prévenu qu'il n'existe pas de nombre de bougies universel pour les reconnaître. Ce parcours va plus loin : il fixe une règle et s'y tient.

Une lecture « à l'œil » change avec l'humeur et avec le résultat que l'on espère. Une règle écrite permet de refaire la même lecture demain, de la comparer à celle d'un autre trader et de la tester sur l'historique. C'est la condition pour que l'analyse de structure devienne une compétence plutôt qu'une impression.

## La règle des deux bougies

::: callout definition "La règle utilisée dans ce parcours"
Une bougie est un **sommet de swing** si son plus haut est strictement supérieur aux plus hauts des **deux bougies qui la précèdent** et des **deux bougies qui la suivent**.

Une bougie est un **creux de swing** si son plus bas est strictement inférieur aux plus bas des deux bougies qui la précèdent et des deux qui la suivent.
:::

::: figure swing-regle.svg
La règle appliquée à six bougies : le plus haut de la quatrième dépasse ceux des deux bougies précédentes et des deux suivantes. Le sommet n'est confirmé qu'à la clôture de la sixième.
:::

Cette règle est une convention répandue (on la retrouve dans les « fractales » de certains indicateurs), pas une loi du marché. Avec trois bougies de chaque côté, on obtient moins de swings, plus espacés ; avec une seule, davantage, plus sensibles au bruit. Aucun réglage n'est le bon en soi. Ce qui compte, c'est de garder le même.

## Un swing se confirme toujours en retard

Avec cette règle, un sommet n'est connu comme sommet qu'à la clôture de la deuxième bougie qui le suit. Pendant ces deux bougies, rien n'empêche le prix de le dépasser, auquel cas il n'aura jamais été un sommet.

Ce retard n'est pas un défaut de la règle : il est inévitable. Un point de retournement ne se reconnaît qu'une fois le retournement entamé. Toute définition plus « rapide » se trompe plus souvent.

::: callout warning "Le piège du graphique terminé"
Sur un graphique passé, tous les swings sont visibles d'un coup et la structure paraît évidente. En temps réel, le dernier swing est toujours provisoire.

Un test historique qui utilise un swing avant sa confirmation se sert d'une information qui n'existait pas encore. C'est un biais d'anticipation (*look-ahead bias*), étudié dans le parcours consacré au backtesting.
:::

## Mèches, clôtures et égalités

Trois précisions, à fixer une fois pour toutes :

- la règle porte sur les **plus hauts et les plus bas**, mèches comprises. Certaines méthodes utilisent les clôtures ; c'est défendable, à condition de le dire ;
- en cas d'**égalité** entre deux plus hauts voisins, la règle « strictement supérieur » ne désigne pas de sommet. On peut adopter une autre convention, par exemple garder le premier des deux, à condition de l'écrire ;
- une bougie au bord du graphique, sans deux bougies de chaque côté, **ne peut pas encore** être un swing.

## À vous

Appliquez la règle à la série ci-dessous, sans regarder le corrigé avant d'avoir répondu.

::: exercise reperer-swings
:::

::: callout mistake "Erreur fréquente"
Choisir la définition après avoir vu le graphique, ou changer le nombre de bougies d'un graphique à l'autre selon ce qui « fonctionne ». La lecture devient alors une façon de confirmer une idée déjà faite.
:::

::: callout recap
- Une règle écrite rend la lecture reproductible : deux bougies de chaque côté, plus hauts ou plus bas stricts.
- Un swing n'est confirmé qu'après les bougies qui le suivent. Le dernier swing d'un graphique est toujours provisoire.
- Utiliser un swing avant sa confirmation, dans un test historique, est un biais d'anticipation.
- Mèches ou clôtures, égalités, bords du graphique : chaque convention se choisit une fois et s'écrit.
:::
