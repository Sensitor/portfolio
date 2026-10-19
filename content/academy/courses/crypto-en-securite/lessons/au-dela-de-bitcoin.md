+++
id = "au-dela-de-bitcoin"
title = "Au-delà de Bitcoin : réseaux, jetons et preuve d'enjeu"
summary = "Bitcoin n'est pas le seul registre public. Les réseaux programmables comme Ethereum portent des milliers de jetons, et un même actif peut circuler sur plusieurs réseaux. Ce qu'il faut savoir avant d'en utiliser un."
duration_minutes = 14
access = "public"
status = "published"
version = 1
updated = 2026-10-19
objectives = [
  "Distinguer la cryptomonnaie native d'un réseau et un jeton émis sur ce réseau.",
  "Expliquer ce qu'apporte un réseau programmable, et la différence entre preuve de travail et preuve d'enjeu.",
  "Comprendre pourquoi le choix du réseau compte autant que l'adresse, lors d'un envoi.",
]
quiz = "check-au-dela-de-bitcoin"
resources = ["fiche-crypto-securite"]
sources = [
  "Buterin, V. (2014). « Ethereum: A Next-Generation Smart Contract and Decentralized Application Platform », livre blanc.",
  "Vogelsteller, F. et Buterin, V. (2015). EIP-20 : Token Standard.",
  "Ethereum Foundation : lancement du réseau le 30 juillet 2015 ; passage à la preuve d'enjeu (« The Merge ») le 15 septembre 2022.",
  "Banque des règlements internationaux (2023). « The crypto ecosystem: key elements and risks », rapport au G20, juillet 2023.",
]
+++

## D'autres registres

Le cours sur Bitcoin a montré comment un registre public peut tenir sans tiers de confiance. D'autres réseaux ont repris l'idée, avec d'autres choix. Le plus connu, **Ethereum**, lancé le 30 juillet 2015, ajoute une possibilité que Bitcoin limite volontairement : exécuter des programmes, appelés **contrats intelligents**, directement sur le registre.

Un contrat intelligent est un programme public, que personne ne peut modifier une fois déployé s'il n'a pas été conçu pour l'être. Il permet de créer des jetons, des plateformes d'échange automatiques ou des prêts sans intermédiaire, que la leçon sur les plateformes décrit.

## Monnaie native et jetons

Chaque réseau a sa **cryptomonnaie native**, qui paie les frais : le bitcoin sur Bitcoin, l'ether sur Ethereum. Sur un réseau programmable, n'importe qui peut aussi émettre un **jeton** : une ligne de compte tenue par un contrat. La norme ERC-20, proposée en 2015, fixe la manière de le faire sur Ethereum.

| | Monnaie native | Jeton |
|---|---|---|
| Exemple | ether (ETH) sur Ethereum | un stablecoin, le jeton d'un projet |
| Émis par | les règles du réseau | le contrat écrit par son émetteur |
| Sert à payer les frais | oui | non : il faut de la monnaie native pour le déplacer |
| Ce qu'il faut vérifier | le réseau lui-même | qui contrôle le contrat, et ce qu'il permet |

::: callout warning "Un même nom, plusieurs réseaux"
Beaucoup de jetons existent sur plusieurs réseaux à la fois : un stablecoin peut circuler sur Ethereum et sur d'autres réseaux, sous des versions qui ne sont pas interchangeables. Envoyer un actif sur le mauvais réseau peut le rendre inaccessible. La leçon sur l'envoi y revient.
:::

## Travail ou enjeu

Bitcoin protège son registre par la **preuve de travail**. Ethereum a abandonné ce mécanisme le 15 septembre 2022 pour la **preuve d'enjeu** : les validateurs immobilisent de l'ether en garantie, et en perdent une partie s'ils trichent. Le mécanisme consomme beaucoup moins d'électricité.

::: callout debate "Travail ou enjeu ?"
Pour ses partisans, la preuve d'enjeu offre une sécurité comparable pour une fraction de l'énergie. Pour ses critiques, elle donne plus de poids à ceux qui détiennent déjà beaucoup de jetons, et son modèle de sécurité est plus récent et moins éprouvé que celui de la preuve de travail. Les deux mécanismes coexistent, et le débat porte autant sur des valeurs que sur des faits.
:::

::: callout note "Des milliers de jetons, très peu de réseaux"
La Banque des règlements internationaux rappelait en 2023 que la plupart des jetons n'ont ni revenus ni usage établi, et que leur valeur repose sur la spéculation. Comprendre comment un réseau fonctionne ne dit rien de la valeur d'un jeton : c'est l'objet du parcours suivant de la filière Crypto.
:::

::: callout mistake "Erreur fréquente"
Croire qu'un jeton est « sur la blockchain » au même titre que la monnaie du réseau. Un jeton dépend aussi de son contrat, et de ceux qui peuvent le modifier ou geler les soldes.
:::

::: callout recap
- Ethereum ajoute des programmes publics au registre : les contrats intelligents.
- Monnaie native pour les frais ; jetons émis par des contrats, sur un ou plusieurs réseaux.
- Preuve de travail pour Bitcoin, preuve d'enjeu pour Ethereum depuis septembre 2022.
:::
