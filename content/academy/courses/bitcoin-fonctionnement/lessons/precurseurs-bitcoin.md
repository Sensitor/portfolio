+++
id = "precurseurs-bitcoin"
title = "De l'argent électronique au livre blanc : les précurseurs"
summary = "Bitcoin n'est pas sorti de nulle part. Signatures aveugles, preuves de travail, monnaies sans émetteur imaginées par des cryptographes : vingt-cinq ans de travaux, et ce que le livre blanc de 2008 y a ajouté, jusqu'au premier bloc du 3 janvier 2009."
duration_minutes = 15
access = "member"
status = "published"
version = 1
updated = 2026-10-19
objectives = [
  "Situer les principaux précurseurs de Bitcoin et l'idée que chacun apporte.",
  "Dire ce que le livre blanc de 2008 ajoute à ces travaux.",
  "Retracer les premiers mois du réseau, du bloc de genèse à la première transaction.",
]
quiz = "check-precurseurs-bitcoin"
resources = ["fiche-bitcoin-fonctionnement"]
sources = [
  "Chaum, D. (1983). « Blind Signatures for Untraceable Payments ». Advances in Cryptology: Proceedings of Crypto 82. New York : Plenum Press, 199-203.",
  "Haber, S. et Stornetta, W. S. (1991). « How to Time-Stamp a Digital Document ». Journal of Cryptology, 3(2), 99-111.",
  "Back, A. (2002). « Hashcash: A Denial of Service Counter-Measure » ; première annonce en 1997.",
  "Dai, W. (1998). « b-money ».",
  "Szabo, N. (2005). « Bit Gold », Unenumerated.",
  "Nakamoto, S. (2008). « Bitcoin: A Peer-to-Peer Electronic Cash System », publié le 31 octobre 2008 sur la liste de diffusion consacrée à la cryptographie.",
  "Bloc de genèse (3 janvier 2009) et bloc 170 (12 janvier 2009), consultés sur mempool.space le 19 octobre 2026.",
]
+++

## Vingt-cinq ans de travaux

Le livre blanc de Bitcoin cite ses sources, et plusieurs idées qu'il assemble existaient déjà.

::: figure precurseurs.svg
Les principaux précurseurs de Bitcoin, de 1983 à 2008, et le premier bloc de 2009. Schéma original.
:::

| Année | Travail | L'idée apportée |
|---|---|---|
| 1983 | David Chaum, signatures aveugles | une monnaie électronique dont la banque ne voit pas les paiements ; elle reste émise par une banque |
| 1991 | Stuart Haber et W. Scott Stornetta, horodatage | chaîner des documents par leurs empreintes pour qu'on ne puisse pas antidater l'un d'eux |
| 1997 | Adam Back, Hashcash | une **preuve de travail** : un calcul coûteux à produire, immédiat à vérifier, contre le courrier indésirable |
| 1998 | Wei Dai, b-money | une monnaie tenue collectivement, sans émetteur central |
| 2005 | Nick Szabo, bit gold | une monnaie dont la rareté vient d'un travail de calcul, imaginée dès 1998 |
| 2008 | Satoshi Nakamoto, livre blanc | l'assemblage qui fonctionne : preuve de travail, chaîne horodatée, registre public, règle de la chaîne la plus travaillée |

Ce qui manquait aux projets précédents, c'était un moyen pour des inconnus de s'accorder sur un seul registre sans autorité centrale. Le livre blanc le règle en liant l'ordre des transactions à la preuve de travail. Le livre blanc cite b-money, Hashcash et les travaux d'horodatage ; il ne cite pas bit gold.

## Les premiers mois

- **31 octobre 2008** : le livre blanc est publié sur une liste de diffusion consacrée à la cryptographie.
- **3 janvier 2009** : le premier bloc, dit **bloc de genèse**, est miné. Son auteur y a inscrit un titre du quotidien britannique *The Times* du jour : « Chancellor on brink of second bailout for banks », le chancelier au bord d'un second sauvetage des banques.
- **12 janvier 2009** : dans le bloc 170, Satoshi Nakamoto envoie **10 bitcoins** au cryptographe Hal Finney. C'est la première transaction entre deux personnes.
- **22 mai 2010** : un programmeur, Laszlo Hanyecz, paie deux pizzas 10 000 bitcoins. C'est l'un des premiers achats connus d'un bien réel.
- **Fin 2010, début 2011** : Satoshi Nakamoto cesse d'intervenir publiquement. Son identité reste inconnue.

::: callout example "Le message du bloc de genèse"
Le titre de presse inscrit dans le premier bloc a deux fonctions. Il prouve que le bloc n'a pas été miné avant le 3 janvier 2009. Et il rappelle le contexte : la crise financière de 2008 et le sauvetage des banques par les États, que le cours « La monnaie » situe dans l'histoire monétaire.
:::

::: callout debate "Une monnaie politique ?"
Pour une partie de ses défenseurs, ce titre de presse fait de Bitcoin une réponse à la crise de 2008 et aux politiques de sauvetage. Pour d'autres, c'est d'abord un horodatage, et le projet était surtout technique : le livre blanc ne parle ni de banques centrales ni d'inflation. Les deux lectures coexistent, et Satoshi Nakamoto n'a jamais tranché.
:::

::: callout mistake "Erreur fréquente"
Croire que Bitcoin a été inventé d'un coup. La preuve de travail, le chaînage par empreintes et l'idée d'une monnaie sans émetteur existaient avant ; l'apport du livre blanc est de les avoir assemblés en un système qui tient.
:::

::: callout recap
- Chaum (1983), Haber et Stornetta (1991), Back (1997), Dai (1998), Szabo (2005) : les idées étaient là.
- Le livre blanc (2008) les assemble autour de la preuve de travail et de la chaîne la plus travaillée.
- Bloc de genèse le 3 janvier 2009 ; première transaction le 12 janvier 2009, 10 bitcoins à Hal Finney.
:::
