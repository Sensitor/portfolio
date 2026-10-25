+++
id = "cles-et-transactions"
title = "Clés, signatures et transactions"
summary = "Posséder des bitcoins, c'est détenir une clé capable de signer. Ce qu'est une transaction : des entrées, des sorties, la monnaie rendue et les frais. Et la seule information qu'il ne faut jamais confier à personne, Sensitor compris."
duration_minutes = 17
access = "member"
status = "published"
version = 1
updated = 2026-10-19
objectives = [
  "Distinguer clé privée, clé publique et adresse, et le rôle de la signature.",
  "Décrire une transaction : entrées, sorties, monnaie rendue et frais.",
  "Calculer les frais d'une transaction et la monnaie à se rendre.",
  "Protéger sa phrase de récupération, et reconnaître une tentative d'escroquerie.",
]
quiz = "check-cles-et-transactions"
resources = ["fiche-bitcoin-fonctionnement"]
sources = [
  "Nakamoto, S. (2008). « Bitcoin: A Peer-to-Peer Electronic Cash System », sections 2 et 9.",
  "Antonopoulos, A. M. et Harding, D. A. (2023). Mastering Bitcoin, 3e édition. Sebastopol : O'Reilly Media, chapitres sur les clés, les portefeuilles et les transactions.",
  "Bitcoin Improvement Proposals : BIP 32 (portefeuilles hiérarchiques déterministes) et BIP 39 (phrase de récupération).",
  "Autorités européennes de surveillance (ABE, AEMF, AEAPP), avertissement conjoint aux consommateurs sur les risques des crypto-actifs, mars 2022.",
]
+++

## Une clé, pas une pièce

Un détenteur de bitcoins ne possède pas de fichier. Il possède une **clé privée** : un très grand nombre secret, qui permet de **signer** des transactions.

- De la clé privée se déduit une **clé publique**, et de celle-ci une **adresse**, que l'on communique pour recevoir des bitcoins. Le calcul ne fonctionne que dans un sens : on ne peut pas retrouver la clé privée à partir de l'adresse.
- Une **signature** prouve que l'auteur d'une transaction détient la clé privée, sans la révéler. Chaque nœud du réseau peut vérifier la signature avec la clé publique.

Un « portefeuille » est donc un logiciel ou un appareil qui garde des clés et signe des transactions. Les bitcoins eux-mêmes restent inscrits dans le registre public.

## Une transaction : entrées et sorties

Bitcoin ne tient pas de soldes. Il enregistre des **sorties non dépensées** : des montants attachés à une adresse, issus de transactions antérieures. Une transaction consomme une ou plusieurs de ces sorties en **entrée**, entièrement, et crée de nouvelles **sorties**.

::: figure transaction-utxo.svg
Alice dépense deux sorties de 0,5 et 0,3 BTC pour payer 0,6 BTC à Bob. La différence revient à Alice sur une sortie de monnaie rendue, moins les frais laissés au mineur. Schéma original.
:::

Comme une entrée se dépense en entier, il faut presque toujours se **rendre la monnaie** : une sortie vers une adresse à soi. Les **frais** sont la différence entre le total des entrées et le total des sorties ; ils reviennent au mineur qui inclut la transaction dans un bloc.

::: formula
\text{Frais} = \text{total des entrées} - \text{total des sorties}
:::

Les frais ne dépendent pas du montant envoyé, mais de la **taille** de la transaction en octets virtuels (vB), multipliée par un prix en satoshis par octet virtuel, fixé par la demande d'espace dans les blocs. Un satoshi vaut un cent-millionième de bitcoin.

## À vous

::: exercise transaction-utxo
:::

## La phrase de récupération

La plupart des portefeuilles dérivent toutes leurs clés d'une seule **phrase de récupération** de 12 ou 24 mots (norme BIP 39). Qui connaît cette phrase peut recréer toutes les clés, et dépenser tous les bitcoins, depuis n'importe quel appareil.

::: callout warning "Ne jamais la communiquer"
Aucun service légitime ne demande une phrase de récupération ou une clé privée : ni un support technique, ni une plateforme, ni un formateur. **Sensitor ne vous la demandera jamais.** Toute demande de ce type est une tentative de vol. Une phrase se note sur papier ou sur métal, se garde hors ligne, et ne se photographie pas.
:::

::: callout note "Garder soi-même ou confier"
Garder soi-même ses clés supprime l'intermédiaire, mais rend responsable de leur sécurité : une phrase perdue signifie des bitcoins perdus, sans recours. Confier ses bitcoins à une plateforme est plus simple, mais refait confiance à un tiers, qui peut faire faillite ou être piraté. Les autorités européennes ont rappelé en 2022 que l'on peut perdre tout ou partie de sa mise. Aucun choix n'est sans risque ; il faut savoir lequel on prend.
:::

::: callout mistake "Erreur fréquente"
Oublier la sortie de monnaie rendue. Si Alice dépense une entrée de 0,8 BTC pour payer 0,6 BTC sans se rendre la monnaie, la différence de 0,2 BTC part entièrement en frais. Les portefeuilles le font automatiquement ; un outil mal utilisé, non.
:::

::: callout recap
- Posséder des bitcoins, c'est détenir une clé privée qui signe ; l'adresse se déduit de la clé, jamais l'inverse.
- Une transaction dépense des sorties entières et crée de nouvelles sorties, dont la monnaie rendue.
- Frais = entrées − sorties, fixés par la taille de la transaction et la demande d'espace.
- La phrase de récupération ne se communique jamais, à personne.
:::
