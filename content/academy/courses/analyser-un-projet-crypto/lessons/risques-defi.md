+++
id = "risques-defi"
title = "Les risques propres à la finance décentralisée"
summary = "Un contrat mal écrit, un oracle manipulé, un pont piraté, une clé d'administration mal gardée, un vote capturé : la DeFi a ses propres façons de perdre des fonds, qui s'ajoutent au risque de prix. Les reconnaître, avec les épisodes qui les ont rendues célèbres."
duration_minutes = 15
access = "member"
status = "published"
version = 1
updated = 2026-10-20
objectives = [
  "Nommer les risques techniques et de gouvernance de la DeFi.",
  "Situer les épisodes marquants : The DAO, les ponts Wormhole, Ronin et Nomad.",
  "Expliquer pourquoi un audit réduit le risque sans le supprimer.",
]
quiz = "check-risques-defi"
resources = ["fiche-analyse-crypto"]
sources = [
  "Ethereum Foundation : le piratage de The DAO (juin 2016) et le changement de règles du réseau de juillet 2016.",
  "Sky Mavis, communiqué du 29 mars 2022 : piratage du pont Ronin, environ 173 600 ether et 25,5 millions d'USDC.",
  "Wormhole, rapport d'incident de février 2022 : 120 000 wETH créés sans contrepartie.",
  "Nomad, rapport d'incident d'août 2022 : environ 190 millions de dollars retirés du pont.",
  "Banque des règlements internationaux (2023). « The crypto ecosystem: key elements and risks », rapport au G20, juillet 2023.",
]
+++

## Cinq risques

| Risque | Ce qui arrive | La question à poser |
|---|---|---|
| **Contrat** | une erreur de programmation permet de retirer des fonds | le code est-il public, audité, ancien, et a-t-il déjà détenu beaucoup de fonds sans incident ? |
| **Oracle** | le prix qu'utilise le contrat est manipulé, et des positions sont liquidées ou des prêts accordés à tort | d'où vient le prix, et peut-on le déplacer avec un seul gros ordre ? |
| **Pont** | les fonds qui relient deux réseaux sont volés | qui garde les fonds du pont, et avec combien de clés ? |
| **Administration** | une clé permet de modifier le contrat ou de geler les fonds | qui détient cette clé, et avec quel délai avant tout changement ? |
| **Gouvernance** | un acteur achète assez de jetons pour faire voter ce qu'il veut | combien coûterait la majorité des votes ? |

## Des épisodes qui ont marqué

- **The DAO, juin 2016.** Une faille dans un contrat qui rassemblait une grande partie de l'ether de l'époque permet d'en retirer environ 3,6 millions. Le réseau Ethereum change ses règles en juillet 2016 pour annuler le vol ; une partie de la communauté refuse, et continue l'ancienne chaîne, devenue Ethereum Classic.
- **Wormhole, février 2022.** Une faille dans le pont permet de créer 120 000 wETH sans contrepartie, soit plus de 300 millions de dollars à l'époque.
- **Ronin, mars 2022.** Des attaquants obtiennent les clés de cinq des neuf validateurs du pont et retirent environ 173 600 ether et 25,5 millions d'USDC, plus de 600 millions de dollars à l'époque.
- **Nomad, août 2022.** Une erreur de mise à jour permet à n'importe qui de retirer des fonds ; environ 190 millions de dollars sortent en quelques heures, beaucoup par des copieurs du premier attaquant.

Les ponts concentrent des sommes importantes dans un seul contrat ou entre quelques clés : ce sont des cibles de choix.

::: callout warning "Un audit n'est pas une garantie"
Un audit est une revue du code par une société spécialisée, à une date donnée. Il réduit le risque ; il ne le supprime pas. Plusieurs protocoles audités ont été piratés, par une faille non vue ou introduite après l'audit.
:::

::: callout note "Données on-chain et données de marché"
Les données on-chain, lues sur le registre, disent ce qui s'est réellement passé : montants déposés, transactions, flux. Les données de marché, publiées par les plateformes, disent à quel prix et en quel volume on a échangé, avec le risque d'échanges fictifs vu à la leçon sur les revenus. Les premières se vérifient ; les secondes demandent de faire confiance à leur source.
:::

::: callout mistake "Erreur fréquente"
Ne regarder que le rendement proposé. Un rendement élevé rémunère souvent un risque élevé, dont une partie, contrat, pont ou administration, n'apparaît nulle part sur l'écran.
:::

::: callout recap
- Contrat, oracle, pont, administration, gouvernance : cinq risques propres à la DeFi.
- The DAO (2016), Wormhole, Ronin et Nomad (2022) : des centaines de millions perdus sans baisse de prix préalable.
- Un audit réduit le risque sans le supprimer ; les données on-chain se vérifient, celles de marché moins.
:::
