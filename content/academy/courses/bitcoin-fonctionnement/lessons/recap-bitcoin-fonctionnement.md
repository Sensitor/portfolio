+++
id = "recap-bitcoin-fonctionnement"
title = "Récapitulatif du cours et quiz de validation"
summary = "Ce que le cours a établi, du problème de la double dépense à la politique monétaire de Bitcoin, ce qui reste débattu, la suite du parcours, puis un quiz de validation corrigé."
duration_minutes = 13
access = "member"
status = "published"
version = 1
updated = 2026-10-19
objectives = [
  "Relier registre public, transactions, preuve de travail, consensus et émission.",
  "Vérifier vos acquis avec un quiz corrigé.",
  "Savoir quoi étudier ensuite.",
]
quiz = "bitcoin-fonctionnement-validation"
resources = ["fiche-bitcoin-fonctionnement"]
sources = [
  "Nakamoto, S. (2008). « Bitcoin: A Peer-to-Peer Electronic Cash System ».",
  "Narayanan, A., Bonneau, J., Felten, E., Miller, A. et Goldfeder, S. (2016). Bitcoin and Cryptocurrency Technologies. Princeton : Princeton University Press.",
]
+++

## Le fil du cours

1. **Le problème** : une monnaie numérique doit empêcher la double dépense, d'habitude grâce à un tiers qui tient le registre.
2. **Les précurseurs** : signatures aveugles, horodatage, preuve de travail, monnaies sans émetteur ; le livre blanc de 2008 les assemble.
3. **Les transactions** : une clé privée signe ; une transaction dépense des sorties entières, se rend la monnaie et paie des frais.
4. **La chaîne** : chaque bloc contient l'empreinte du précédent ; modifier le passé change toute la suite.
5. **La preuve de travail** : trouver est coûteux, vérifier est immédiat ; la difficulté s'ajuste tous les 2 016 blocs.
6. **Le consensus** : les nœuds vérifient tout et suivent la chaîne la plus travaillée ; les confirmations protègent d'un attaquant minoritaire.
7. **L'émission** : 50 BTC par bloc au départ, divisés par deux tous les 210 000 blocs, 20 999 999,9769 BTC au total.

## Établi et débattu

| Établi | Débattu |
|---|---|
| L'émission suit une règle connue, calculable bloc par bloc | Le rôle de Bitcoin comme réserve de valeur |
| Les nœuds rejettent tout bloc qui viole les règles | Le coût environnemental de la preuve de travail |
| Les chances d'un attaquant minoritaire chutent avec les confirmations | La sécurité du réseau quand la récompense aura presque disparu |
| Celui qui détient la phrase de récupération détient les bitcoins | Le meilleur compromis entre garder soi-même et confier |

::: callout opinion "Opinion du fondateur"
Pour moi, Bitcoin et certaines cryptomonnaies sont une forme de diversification, et une manière de préserver son patrimoine dans le temps. C'est cette conviction que Sensitor veut expliquer, et soumettre à l'examen des faits.
:::

## Et ensuite ?

Le parcours **Bitcoin en profondeur** continuera avec les arguments qui font de Bitcoin une réserve de valeur possible et leurs objections, son rapport à l'inflation sur les données, puis ses cycles et ses indicateurs. Du côté de l'univers Trading, le parcours 8 montre comment les taux et l'actualité économique pèsent aussi sur la crypto.

## Quiz de validation

Dix questions couvrent l'ensemble du cours. La correction détaillée s'affiche à la fin, avec un lien vers la leçon à relire pour chaque erreur.

::: callout recap
- Bitcoin remplace le tiers de confiance par un registre public, ordonné par un travail vérifiable.
- Ses règles, dont l'émission, sont vérifiées par chaque nœud.
- Ce qui reste débattu porte sur sa valeur, son coût et sa sécurité à long terme, pas sur son fonctionnement.
:::
