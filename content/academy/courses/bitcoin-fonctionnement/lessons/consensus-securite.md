+++
id = "consensus-securite"
title = "Le consensus et la sécurité"
summary = "Des milliers de nœuds vérifient chacun toutes les règles, et suivent la chaîne qui a demandé le plus de travail. Ce que peut faire, et ne peut pas faire, un attaquant qui contrôle une partie de la puissance, et pourquoi on attend plusieurs confirmations."
duration_minutes = 16
access = "member"
status = "published"
version = 1
updated = 2026-10-19
objectives = [
  "Distinguer le rôle des nœuds et celui des mineurs.",
  "Expliquer la règle de la chaîne la plus travaillée et les confirmations.",
  "Lire la probabilité de succès d'un attaquant minoritaire selon le nombre de confirmations.",
  "Dire ce qu'une attaque majoritaire permet, et ce qu'elle ne permet pas.",
]
quiz = "check-consensus-securite"
resources = ["fiche-bitcoin-fonctionnement"]
sources = [
  "Nakamoto, S. (2008). « Bitcoin: A Peer-to-Peer Electronic Cash System », sections 5, 6 et 11 (calcul de la probabilité de rattrapage).",
  "Narayanan, A., Bonneau, J., Felten, E., Miller, A. et Goldfeder, S. (2016). Bitcoin and Cryptocurrency Technologies. Princeton : Princeton University Press, chapitres 2 et 5.",
]
+++

## Les nœuds vérifient, les mineurs proposent

Deux rôles se partagent le réseau.

- **Les nœuds** sont des ordinateurs qui gardent une copie du registre et **vérifient chaque règle** : signatures, absence de double dépense, montant de la récompense, taille des blocs. Un bloc qui viole une règle est rejeté, quelle que soit la puissance qui l'a produit. N'importe qui peut faire tourner un nœud.
- **Les mineurs** produisent les blocs, et proposent ainsi l'ordre des transactions. Ils sont payés pour ce travail, mais ne décident pas des règles.

## La chaîne la plus travaillée

Il arrive que deux mineurs trouvent un bloc presque en même temps : la chaîne se divise un court instant. Chaque nœud suit la version qui a demandé **le plus de travail cumulé**. Dès qu'un nouveau bloc s'ajoute à l'une des branches, l'autre est abandonnée, et ses transactions retournent en attente.

Une transaction incluse dans un bloc a **une confirmation** ; chaque bloc ajouté après elle en ajoute une. Plus elle en a, plus il faudrait de travail pour la remplacer. À dix minutes par bloc, six confirmations prennent environ une heure.

## Ce que peut un attaquant

Un attaquant qui veut annuler un paiement qu'il a fait doit produire, en secret, une chaîne plus travaillée que la chaîne honnête. Le livre blanc calcule ses chances, en fonction de sa part **q** de la puissance et du nombre **z** de confirmations attendues.

::: chart rattrapage
Les chances qu'un attaquant rattrape la chaîne honnête, selon sa part de la puissance de calcul et le nombre de confirmations. Échelle logarithmique : chaque graduation divise la probabilité par cent.
:::

Avec 10 % de la puissance, l'attaquant a environ 20,5 % de chances après une confirmation, 0,09 % après cinq et 0,024 % après six. Avec 30 %, il en garde encore 13,2 % après six confirmations. Pour descendre sous 0,1 %, il faut 5 confirmations face à un attaquant à 10 %, 24 face à un attaquant à 30 %.

::: callout warning "Une attaque majoritaire"
Avec plus de la moitié de la puissance, un attaquant finit toujours par rattraper la chaîne honnête. Il pourrait alors annuler ses propres paiements récents ou refuser d'inclure certaines transactions. Il **ne pourrait pas** dépenser les bitcoins des autres sans leur clé, ni créer plus de bitcoins que la règle d'émission : les nœuds rejetteraient ces blocs.
:::

## À vous

::: exercise confirmations-attaquant
:::

::: callout mistake "Erreur fréquente"
Considérer qu'une transaction sans confirmation est réglée. Tant qu'elle n'est pas incluse dans un bloc, elle peut être remplacée ou ne jamais être incluse. Pour un montant important, on attend plusieurs confirmations.
:::

::: callout recap
- Les nœuds vérifient toutes les règles ; les mineurs proposent l'ordre des transactions.
- Les nœuds suivent la chaîne qui a demandé le plus de travail cumulé.
- Chaque confirmation réduit fortement les chances d'un attaquant minoritaire ; un attaquant majoritaire peut annuler ses paiements, pas voler ceux des autres.
:::
