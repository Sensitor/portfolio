+++
id = "espace-de-bloc"
title = "L'espace de bloc : SegWit, Taproot et les inscriptions"
summary = "La taille des blocs a longtemps plafonné à un mégaoctet. SegWit, en 2017, a remplacé la taille par le poids ; Taproot, en 2021, a ouvert de nouveaux usages ; les inscriptions de 2023 ont rempli les blocs autrement. Trois changements lisibles dans la taille moyenne des blocs."
duration_minutes = 13
access = "member"
status = "published"
version = 1
updated = 2026-10-20
objectives = [
  "Distinguer la taille et le poids d'un bloc.",
  "Situer SegWit, Taproot et les inscriptions dans l'évolution de l'espace de bloc.",
  "Lire la taille moyenne des blocs et ce qu'elle révèle des usages.",
]
quiz = "check-espace-de-bloc"
resources = ["fiche-on-chain"]
sources = [
  "Chaîne Bitcoin : un bloc par jour, du 9 janvier 2009 au 30 septembre 2026, relevé via les API publiques Esplora de blockstream.info et de mempool.space ; calculs Sensitor.",
  "BIP 141 (Segregated Witness), activé au bloc 481 824, le 24 août 2017.",
  "BIP 341 (Taproot), activé au bloc 709 632, le 14 novembre 2021.",
  "Rodarmor, C. (2023). Ordinals : protocole d'inscriptions, lancé en janvier 2023.",
]
+++

## Taille et poids

Jusqu'en 2017, un bloc ne pouvait pas dépasser **un mégaoctet**. **SegWit** a remplacé cette règle par une limite de **poids**, 4 millions d'unités, où les signatures comptent quatre fois moins que le reste. Un bloc rempli de transactions SegWit peut donc dépasser un mégaoctet sans dépasser son poids maximal.

::: chart taille-blocs
La taille moyenne des blocs, en mégaoctets, chaque mois. La ligne de 1 Mo était un plafond avant SegWit ; elle est franchie quand les transactions utilisent la place réservée aux signatures.
:::

Trois étapes se lisent sur la courbe :

- **24 août 2017, SegWit** : les blocs peuvent dépasser 1 Mo ; la taille moyenne mensuelle l'a fait pour la première fois en novembre 2017.
- **14 novembre 2021, Taproot** : de nouveaux types de scripts, plus compacts et plus discrets.
- **Janvier 2023, les inscriptions** : des données, images ou textes, inscrites dans la partie signature des transactions ; la taille moyenne a atteint **1,95 Mo** en février 2023.

::: callout debate "Les inscriptions : un usage ou un abus ?"
Pour leurs partisans, les inscriptions sont un usage légitime de l'espace de bloc, payé par des frais qui renforcent la sécurité du réseau. Pour leurs critiques, elles détournent un registre de paiement pour y stocker des données, et font monter les frais des transactions ordinaires. Le protocole les autorise ; la question porte sur ce que doit être Bitcoin.
:::

::: callout note "Ce que la taille ne dit pas"
Deux blocs de même poids peuvent contenir très peu de grosses transactions ou beaucoup de petites. La taille et le poids disent combien de place est utilisée, pas par qui ni pour quoi.
:::

::: callout recap
- Avant 2017 : 1 Mo maximum ; depuis SegWit : 4 millions d'unités de poids.
- SegWit (2017), Taproot (2021), inscriptions (2023) : trois étapes visibles dans la taille des blocs.
- La taille moyenne a dépassé 1 Mo en novembre 2017 et atteint 1,95 Mo en février 2023.
:::
