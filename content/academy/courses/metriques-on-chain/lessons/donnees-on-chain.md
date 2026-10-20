+++
id = "donnees-on-chain"
title = "Ce que la chaîne dit d'elle-même"
summary = "Chaque bloc de Bitcoin est public : son heure, ses transactions, sa taille, ce que le mineur s'est payé. De ces faits naissent les métriques on-chain. Ce qui se mesure, ce qui s'estime, ce qui dépend du prix, et la méthode qu'utilise Sensitor pour en tirer des graphiques sans aucune donnée sous licence."
duration_minutes = 12
access = "public"
status = "published"
version = 1
updated = 2026-10-20
objectives = [
  "Définir une métrique on-chain et la distinguer d'une donnée de marché.",
  "Classer une métrique : mesurée, estimée, ou dépendante du prix.",
  "Comprendre la méthode d'échantillonnage des graphiques du cours, et ses limites.",
]
quiz = "check-donnees-on-chain"
resources = ["fiche-on-chain"]
sources = [
  "Nakamoto, S. (2008). « Bitcoin: A Peer-to-Peer Electronic Cash System ».",
  "Chaîne Bitcoin : un bloc par jour, du 9 janvier 2009 au 30 septembre 2026, relevé via les API publiques Esplora de blockstream.info et de mempool.space les 20 et 21 octobre 2026 ; calculs Sensitor.",
]
+++

## Un registre que tout le monde peut lire

Le cours sur Bitcoin a montré que le registre est public. Chaque bloc porte des faits que n'importe quel nœud peut vérifier : son **heure**, son **nombre de transactions**, sa **taille** et son **poids**, et la transaction particulière par laquelle le mineur se paie, la **coinbase**. En les additionnant, en les comparant dans le temps, on obtient des **métriques on-chain**.

À la différence des données de marché, publiées par les plateformes d'échange, ces données ne dépendent de la parole de personne : la chaîne fait foi.

## Trois familles

| Famille | Exemples | Ce qu'il faut savoir |
|---|---|---|
| **Mesurée** | transactions par bloc, taille, poids, frais d'un bloc, émission | un fait du registre, identique sur tout nœud |
| **Estimée** | puissance de calcul, part de chaque pool | déduite d'autres faits : la difficulté et le temps entre les blocs, l'étiquette écrite par le mineur |
| **Dépendante du prix** | prix réalisé, MVRV, NUPL, SOPR | croise la chaîne et un historique de prix |

Les deux premières familles se calculent à partir de la chaîne seule. La troisième demande un historique de prix quotidien ; la leçon qui lui est consacrée explique pourquoi Sensitor la montre, pour l'instant, sur un exemple construit.

## La méthode des graphiques de ce cours

Lire chacun des quelque 970 000 blocs demanderait de télécharger toute la chaîne. Sensitor a procédé autrement : **un bloc par jour**, celui qui était produit à midi, heure universelle, du 9 janvier 2009 au 30 septembre 2026, soit **6 474 blocs**. Pour chacun, la taille, le poids, le nombre de transactions et la coinbase ont été relevés, puis moyennés mois par mois, une trentaine de blocs par mois.

::: callout warning "Ce que vaut un échantillon"
Un bloc sur 144 donne une image fidèle des tendances, mois après mois, mais pas d'un jour précis : un bloc isolé peut être exceptionnellement plein ou vide. Les valeurs du cours sont des moyennes mensuelles ; chaque graphique donne l'ordre de grandeur, pas la valeur exacte d'un jour.
:::

::: callout note "Ce que pourra faire un nœud"
Avec un nœud Bitcoin hébergé par Sensitor, les mêmes graphiques pourraient porter sur tous les blocs, et s'enrichir de métriques qui demandent l'historique complet des pièces : l'âge des bitcoins, la part détenue à long terme, les jours-pièces détruits.
:::

::: callout mistake "Erreur fréquente"
Prendre une métrique on-chain pour un signal. Une hausse des transactions ou des frais décrit une activité ; elle ne dit pas, à elle seule, ce que fera le prix.
:::

::: callout recap
- Les métriques on-chain viennent de faits publics : heure, transactions, taille, poids, coinbase.
- Mesurées, estimées, ou dépendantes du prix : trois familles, trois niveaux de certitude.
- Les graphiques du cours : un bloc par jour depuis 2009, moyennés par mois.
:::
