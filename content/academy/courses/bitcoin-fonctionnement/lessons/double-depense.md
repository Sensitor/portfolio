+++
id = "double-depense"
title = "Payer en ligne sans intermédiaire : le problème"
summary = "Un fichier se copie à l'infini : une monnaie numérique peut-elle exister sans qu'une banque tienne le registre ? Le problème de la double dépense, la solution habituelle, et celle que propose Bitcoin."
duration_minutes = 12
access = "public"
status = "published"
version = 1
updated = 2026-10-19
objectives = [
  "Expliquer le problème de la double dépense d'une monnaie numérique.",
  "Décrire la solution habituelle, un tiers de confiance qui tient le registre.",
  "Résumer la solution de Bitcoin : un registre public tenu par tous, dont l'ordre est fixé par un travail vérifiable.",
]
quiz = "check-double-depense"
resources = ["fiche-bitcoin-fonctionnement"]
sources = [
  "Nakamoto, S. (2008). « Bitcoin: A Peer-to-Peer Electronic Cash System », sections 1 et 2.",
  "Narayanan, A., Bonneau, J., Felten, E., Miller, A. et Goldfeder, S. (2016). Bitcoin and Cryptocurrency Technologies. Princeton : Princeton University Press, chapitre 1.",
]
+++

## Un fichier se copie

Un billet de 10 euros ne peut être donné qu'une fois : une fois remis, on ne l'a plus. Un fichier, lui, se copie à l'infini. Si une monnaie numérique n'était qu'un fichier, rien n'empêcherait de l'envoyer à deux personnes à la fois. C'est le problème de la **double dépense**.

::: figure double-depense.svg
Alice envoie la même pièce numérique à Bob et à Carol. Sans registre commun, chacun croit l'avoir reçue ; avec un registre, seule la première transaction inscrite compte. Schéma original.
:::

## La solution habituelle : un tiers de confiance

Les paiements électroniques que l'on utilise chaque jour résolvent ce problème par un **registre tenu par un tiers** : la banque, le réseau de carte ou le prestataire de paiement. Quand Alice paie, c'est le registre de la banque qui change ; l'argent n'est jamais « envoyé », il est déplacé d'une ligne à l'autre. Le cours « La monnaie » l'a montré : la monnaie bancaire est une écriture dans un bilan.

Cette solution fonctionne bien. Elle demande seulement de faire confiance au tiers : qu'il tienne le registre honnêtement, qu'il ne bloque pas un paiement, qu'il reste solvable et qu'il ne se trompe pas.

::: callout definition "Double dépense"
Le fait de dépenser deux fois la même unité de monnaie numérique. Une monnaie numérique doit l'empêcher, soit par un tiers qui tient le registre, soit par un autre mécanisme.
:::

## La proposition de Bitcoin

En 2008, une personne ou un groupe signant **Satoshi Nakamoto** publie un texte de neuf pages : « Bitcoin: A Peer-to-Peer Electronic Cash System ». Sa proposition tient en trois idées.

1. **Un registre public** : toutes les transactions sont publiées et chacun peut en garder une copie.
2. **Un ordre vérifiable** : les transactions sont regroupées en blocs, et chaque bloc demande un travail de calcul que tout le monde peut vérifier. Pour réécrire le passé, il faudrait refaire ce travail.
3. **Une règle simple** : en cas de désaccord, la version du registre qui a demandé le plus de travail l'emporte.

Plus besoin de tiers pour savoir qui possède quoi : le registre fait foi, et chacun peut le vérifier soi-même. Les leçons suivantes expliquent chaque étape.

::: callout note "Ce que Bitcoin ne promet pas"
Supprimer l'intermédiaire pour tenir le registre ne supprime pas tous les risques. Celui qui détient lui-même ses bitcoins devient responsable de leur sécurité, et celui qui les confie à une plateforme refait confiance à un tiers. La leçon sur les clés y revient.
:::

::: callout mistake "Erreur fréquente"
Croire qu'un bitcoin est un fichier stocké dans un portefeuille. Ce qui existe, c'est une ligne du registre public, que seul le détenteur d'une clé peut dépenser.
:::

::: callout recap
- Une monnaie numérique doit empêcher la double dépense.
- La solution habituelle est un tiers de confiance qui tient le registre.
- Bitcoin propose un registre public, ordonné par un travail vérifiable, sans tiers.
:::
