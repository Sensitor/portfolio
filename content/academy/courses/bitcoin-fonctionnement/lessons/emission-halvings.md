+++
id = "emission-halvings"
title = "L'émission, les halvings et les frais"
summary = "De nouveaux bitcoins naissent à chaque bloc, selon une règle que personne ne peut changer seul : 50 au départ, divisés par deux tous les 210 000 blocs. L'émission calculée bloc par bloc, les halvings passés et à venir, le rôle des frais, et la question ouverte de la sécurité quand la récompense aura presque disparu."
duration_minutes = 17
access = "member"
status = "published"
version = 1
updated = 2026-10-19
objectives = [
  "Calculer la récompense de bloc d'une époque et l'émission annuelle qui en découle.",
  "Situer les halvings passés et estimer le prochain.",
  "Expliquer le rôle des frais dans la rémunération des mineurs, et le débat sur la sécurité à long terme.",
]
quiz = "check-emission-halvings"
resources = ["fiche-bitcoin-fonctionnement"]
sources = [
  "Nakamoto, S. (2008). « Bitcoin: A Peer-to-Peer Electronic Cash System », section 6.",
  "Règles d'émission du protocole Bitcoin : récompense initiale de 50 BTC, divisée par deux tous les 210 000 blocs, arrondie au satoshi ; calcul Sensitor.",
  "mempool.space : dates des blocs 210 000, 420 000, 630 000 et 840 000, et hauteur de bloc au 17 octobre 2026 (971 911), consultées les 17 et 19 octobre 2026.",
  "Budish, E. (2018). « The Economic Limits of Bitcoin and the Blockchain ». NBER Working Paper 24717.",
]
+++

## Une émission programmée

Chaque bloc contient une transaction particulière, qui crée de nouveaux bitcoins et les attribue au mineur : la **récompense de bloc**. Elle valait **50 BTC** au lancement, et elle est divisée par deux tous les **210 000 blocs**, environ tous les quatre ans : c'est le **halving**.

::: chart recompense-bitcoin
La récompense par bloc, époque par époque. Les points clairs, à partir de 2028, sont des estimations à dix minutes par bloc.
:::

| Halving | Bloc | Date | Récompense après |
|---|---|---|---|
| 1 | 210 000 | 28 novembre 2012 | 25 BTC |
| 2 | 420 000 | 9 juillet 2016 | 12,5 BTC |
| 3 | 630 000 | 11 mai 2020 | 6,25 BTC |
| 4 | 840 000 | 20 avril 2024 | 3,125 BTC |
| 5 | 1 050 000 | vers avril 2028, estimation | 1,5625 BTC |

::: chart emission-bitcoin
L'offre de Bitcoin, époque par époque, calculée à partir des règles du protocole.
:::

En additionnant toutes les récompenses, arrondies au satoshi comme le fait le logiciel, l'offre totale atteint **20 999 999,9769 BTC**, un peu moins que les 21 millions souvent cités. Le 17 octobre 2026, au bloc 971 911, **20 099 725 BTC** avaient été émis, soit **95,7 %** du total. La dernière fraction de bitcoin devrait être créée vers **2140**, au bloc 6 929 999.

## Ce que cela représente chaque année

Au rythme d'un bloc toutes les dix minutes, il se mine **144 blocs par jour**. Avec une récompense de 3,125 BTC, cela fait 450 BTC créés chaque jour, environ 164 000 par an : moins de 1 % de l'offre existante. Après le halving de 2028, ce sera la moitié.

## À vous

::: exercise emission-halving
:::

## Les frais prennent le relais

Le mineur reçoit la récompense **et** les frais de toutes les transactions du bloc. Aujourd'hui, la récompense en représente l'essentiel. À mesure qu'elle diminue, la sécurité du réseau, c'est-à-dire la puissance que les mineurs acceptent d'y consacrer, devra être payée de plus en plus par les frais.

::: callout debate "La sécurité à très long terme"
Pour certains économistes, comme Eric Budish (2018), la sécurité d'une preuve de travail coûte cher en permanence : si les frais ne suffisent pas à remplacer la récompense, la puissance consacrée au réseau baissera, et une attaque deviendra moins coûteuse. Pour d'autres, la hausse de la valeur des bitcoins, la demande d'espace dans les blocs et l'usage de Bitcoin comme couche de règlement suffiront à payer cette sécurité. La question reste ouverte : elle ne se posera pleinement que dans plusieurs décennies.
:::

::: callout mistake "Erreur fréquente"
Penser que le halving fait mécaniquement monter le prix. Il réduit le nombre de bitcoins nouveaux, une donnée connue des années à l'avance. Ce que fait le prix dépend de la demande, que rien ne garantit ; le parcours y reviendra avec les données.
:::

::: callout recap
- 50 BTC par bloc au départ, divisés par deux tous les 210 000 blocs ; 3,125 BTC depuis avril 2024.
- 20 999 999,9769 BTC au total ; 95,7 % émis en octobre 2026 ; la dernière fraction vers 2140.
- La rémunération des mineurs passera peu à peu de la récompense aux frais : la sécurité à long terme reste une question ouverte.
:::
