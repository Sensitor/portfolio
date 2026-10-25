+++
id = "activite-reseau"
title = "L'activité du réseau : transactions et remplissage des blocs"
summary = "Combien de transactions Bitcoin traite chaque jour, et à quel point ses blocs sont pleins : deux mesures de l'usage du réseau, calculées sur la chaîne depuis 2009. Ce qu'elles montrent, et ce qu'elles ne disent pas de l'adoption."
duration_minutes = 14
access = "member"
status = "published"
version = 1
updated = 2026-10-20
objectives = [
  "Lire l'évolution du nombre de transactions par jour.",
  "Lire le remplissage des blocs et comprendre sa limite.",
  "Distinguer activité du réseau et adoption.",
]
quiz = "check-activite-reseau"
resources = ["fiche-on-chain"]
sources = [
  "Chaîne Bitcoin : un bloc par jour, du 9 janvier 2009 au 30 septembre 2026, relevé via les API publiques Esplora de blockstream.info et de mempool.space ; calculs Sensitor.",
  "BIP 141 (Segregated Witness) : poids d'un bloc limité à 4 millions d'unités.",
]
+++

## Les transactions par jour

Chaque bloc contient un certain nombre de transactions. En multipliant la moyenne mensuelle par le nombre de blocs produits chaque jour, on obtient une estimation des **transactions par jour**.

::: chart transactions-jour
Les transactions par jour, en moyenne mensuelle, estimées à partir d'un bloc par jour et du rythme réel des blocs. Les premiers mois de 2009 comptent presque uniquement la transaction de récompense de chaque bloc.
:::

Ce que montrent les données :

- en juin 2012, environ **51 600** transactions par jour ;
- un premier pic en **décembre 2017**, avec environ **388 000** transactions par jour ;
- le plus haut de l'échantillon en **juin 2026**, environ **764 000** par jour ;
- environ **688 000** par jour en septembre 2026.

## Des blocs pleins

Un bloc ne peut pas dépasser un certain **poids** : 4 millions d'unités depuis SegWit, l'équivalent de l'ancienne limite d'un mégaoctet. Le **remplissage** mesure la part de cette capacité utilisée.

::: chart remplissage-blocs
Le remplissage moyen des blocs, en part du poids maximal, chaque mois. Quand il approche 100 %, la place devient rare et les frais montent.
:::

Le remplissage moyen a dépassé **90 %** pour la première fois en avril 2016 ; il était de **99,9 %** en septembre 2026.

## À vous

::: exercise activite-calcul
:::

::: callout warning "Activité n'est pas adoption"
Une transaction peut regrouper des centaines de paiements, ou à l'inverse servir à déplacer des fonds entre deux adresses du même propriétaire. Une partie des paiements se fait aussi hors de la chaîne, sur des plateformes ou sur le réseau Lightning. Le nombre de transactions mesure l'usage de l'espace de bloc, pas le nombre d'utilisateurs.
:::

::: callout mistake "Erreur fréquente"
Conclure d'une baisse du nombre de transactions que le réseau « meurt ». Des transactions plus grosses, regroupant plus de paiements, peuvent remplir les blocs avec moins de transactions.
:::

::: callout recap
- Transactions par jour : environ 688 000 en septembre 2026, contre 51 600 en juin 2012.
- Remplissage : la part du poids maximal utilisée ; proche de 100 %, l'espace devient rare.
- Le nombre de transactions mesure l'usage de l'espace, pas le nombre d'utilisateurs.
:::
