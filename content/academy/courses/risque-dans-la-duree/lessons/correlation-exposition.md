+++
id = "correlation-exposition"
title = "Corrélation : une idée, plusieurs positions"
summary = "Trois positions à 1 % peuvent porter un seul et même risque. Compter son exposition par idée et par devise, plutôt que par trade."
duration_minutes = 13
access = "member"
status = "published"
version = 1
objectives = [
  "Reconnaître des positions qui portent le même risque.",
  "Compter son exposition par devise et par idée.",
  "Fixer une limite d'exposition cumulée.",
]
quiz = "check-correlation"
+++

## Le même pari, plusieurs fois

Un trader achète EURUSD, achète GBPUSD et vend USDCHF, avec 1 % de risque sur chacune. Sur le papier, trois trades indépendants. En réalité, les trois positions sont **vendeuses de dollars** : une même annonce américaine peut les faire perdre ensemble. Le risque réel est plus proche de 3 % sur une seule idée que de trois fois 1 % sur trois idées.

Deux positions sont **corrélées** quand leurs résultats ont tendance à aller dans le même sens. Sur le Forex, les paires qui partagent une devise le sont souvent ; les indices boursiers d'une même région aussi. Le degré de corrélation varie dans le temps et peut changer brusquement, notamment lors des annonces.

## Compter par devise

Une méthode simple consiste à décomposer chaque position en ce qu'elle achète et ce qu'elle vend :

| Position | Achète | Vend |
|---|---|---|
| Achat EURUSD | EUR | USD |
| Achat GBPUSD | GBP | USD |
| Vente USDCHF | CHF | USD |

Le dollar apparaît trois fois du même côté : c'est la vraie exposition du portefeuille.

::: callout definition "Exposition par idée"
L'**exposition par idée** est la somme des risques des positions qui perdraient ensemble si l'idée était fausse. Dans l'exemple, « le dollar baisse » porte 3 % du capital.
:::

## Une limite cumulée

Beaucoup de traders fixent, en plus du risque par trade, une **limite par idée** (par exemple 2 % au total sur une même devise ou un même thème) et une **limite globale** sur l'ensemble des positions ouvertes. Ces chiffres sont des choix personnels, à écrire dans son plan de trading et à respecter même quand trois setups paraissent excellents en même temps.

::: callout method "Hypothèse de méthode"
Diviser le risque d'une idée entre plusieurs paires corrélées ne le réduit pas beaucoup ; cela multiplie surtout les coûts. Choisir la paire qui exprime le mieux l'idée est souvent plus simple.
:::

::: callout mistake "Erreur fréquente"
Respecter scrupuleusement 1 % par trade tout en ouvrant quatre positions sur la même idée. La règle par trade est respectée ; la règle de bon sens, non.
:::

::: callout recap
- Des positions corrélées peuvent perdre ensemble : leur risque s'additionne.
- Décomposer chaque position en devises achetées et vendues révèle l'exposition réelle.
- Compter le risque par idée, pas seulement par trade.
- Une limite par idée et une limite globale s'écrivent dans le plan de trading.
:::
