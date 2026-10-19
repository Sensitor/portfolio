+++
id = "preuve-de-travail"
title = "La preuve de travail et la difficulté"
summary = "Miner, c'est chercher un nombre au hasard jusqu'à obtenir une empreinte assez petite : un travail coûteux à faire, immédiat à vérifier. Comment la difficulté s'ajuste pour garder un bloc toutes les dix minutes, et le débat sur l'énergie consommée."
duration_minutes = 17
access = "member"
status = "published"
version = 1
updated = 2026-10-19
objectives = [
  "Expliquer le principe de la preuve de travail et l'asymétrie entre trouver et vérifier.",
  "Calculer l'ajustement de difficulté après une période de 2 016 blocs.",
  "Estimer le temps moyen entre deux blocs pour un mineur selon sa part de la puissance.",
]
quiz = "check-preuve-de-travail"
resources = ["fiche-bitcoin-fonctionnement"]
sources = [
  "Nakamoto, S. (2008). « Bitcoin: A Peer-to-Peer Electronic Cash System », sections 4 et 6.",
  "Back, A. (2002). « Hashcash: A Denial of Service Counter-Measure ».",
  "Règles de consensus de Bitcoin Core : ajustement de la difficulté tous les 2 016 blocs, limité à un facteur 4.",
  "mempool.space : difficulté des blocs 0, 840 000 et 971 911, consultée le 19 octobre 2026.",
  "Cambridge Centre for Alternative Finance, Cambridge Bitcoin Electricity Consumption Index : méthode d'estimation de la consommation électrique.",
]
+++

## Chercher un nombre

Pour ajouter un bloc, un mineur doit trouver un en-tête dont l'empreinte est **inférieure à une cible**. Il ne peut pas la calculer à l'avance : il change le **nonce**, recalcule l'empreinte, et recommence, des milliards de fois par seconde. Celui qui trouve le premier publie le bloc et reçoit la récompense.

Le cœur de l'idée est une **asymétrie** : trouver le bon nonce demande en moyenne un nombre immense d'essais ; vérifier qu'il convient n'en demande qu'un. Chaque nœud du réseau peut donc contrôler, en une fraction de seconde, le travail que des machines ont mis dix minutes à produire.

::: tool hash-demo
:::

La démonstration exige quelques zéros en tête de l'empreinte. Le réseau Bitcoin fonctionne sur le même principe, à une autre échelle : au bloc 971 911, miné le 17 octobre 2026, la difficulté atteignait environ **140 580 milliards**, soit environ **6 × 10²³** essais en moyenne par bloc. Au bloc de genèse, elle valait 1.

## Dix minutes, quelle que soit la puissance

Si davantage de machines minent, les blocs sont trouvés plus vite. Pour garder un rythme d'**un bloc toutes les dix minutes** en moyenne, la difficulté s'ajuste tous les **2 016 blocs**, soit environ deux semaines.

::: formula
\text{Nouvelle difficulté} = \text{difficulté} \times \frac{\text{14 jours}}{\text{durée réelle des 2 016 derniers blocs}}
:::

Le changement est limité à un facteur 4 dans un sens comme dans l'autre. Entre le quatrième halving, au bloc 840 000 en avril 2024, et le bloc 971 911, la difficulté est passée d'environ 86 390 milliards à 140 580 milliards, soit une hausse d'environ 63 % : la puissance consacrée au réseau a augmenté dans la même proportion.

::: callout definition "Puissance de calcul"
Le nombre d'empreintes calculées chaque seconde par l'ensemble des mineurs. Un mineur qui en détient 2 % trouve en moyenne 2 % des blocs, soit environ un bloc toutes les 500 minutes.
:::

## À vous

::: exercise ajustement-difficulte
:::

::: callout debate "L'énergie consommée"
La preuve de travail consomme de l'électricité : c'est voulu, puisque le coût du travail protège le registre. Pour ses critiques, cette consommation est un gaspillage au regard d'autres systèmes de paiement, et un coût environnemental. Pour ses défenseurs, c'est le prix d'un registre que personne ne peut réécrire, et les mineurs recherchent l'électricité la moins chère, souvent excédentaire ou isolée. Les estimations de consommation, comme celles de l'université de Cambridge, reposent sur des hypothèses sur le matériel utilisé, et varient en conséquence.
:::

::: callout mistake "Erreur fréquente"
Croire que miner consiste à résoudre un problème mathématique difficile. Il n'y a rien à résoudre : on essaie des nombres au hasard. La difficulté est seulement statistique.
:::

::: callout recap
- Miner, c'est essayer des nonces jusqu'à une empreinte inférieure à la cible ; vérifier ne demande qu'un calcul.
- La difficulté s'ajuste tous les 2 016 blocs pour garder dix minutes par bloc, dans la limite d'un facteur 4.
- Une part de la puissance donne la même part des blocs, en moyenne.
:::
