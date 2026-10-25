+++
id = "indicateurs-de-prix"
title = "Prix réalisé, MVRV et NUPL : les indicateurs fondés sur le prix"
summary = "Les indicateurs on-chain les plus suivis croisent la chaîne et le prix : à quel prix chaque bitcoin a-t-il bougé pour la dernière fois ? Le prix réalisé, le MVRV et le NUPL, expliqués sur un marché construit, ce qu'ils permettent de lire, et pourquoi aucun n'est un signal infaillible."
duration_minutes = 16
access = "member"
status = "published"
version = 1
updated = 2026-10-20
objectives = [
  "Définir le prix réalisé, le MVRV et le NUPL.",
  "Calculer ces indicateurs sur un exemple.",
  "Expliquer leurs limites, et pourquoi Sensitor ne publie pas encore leurs séries réelles.",
]
quiz = "check-indicateurs-de-prix"
resources = ["fiche-on-chain"]
sources = [
  "Carter, N. et Le Calvez, A. (2018). Définition de la capitalisation réalisée (« realized capitalization »), Coin Metrics.",
  "Mahmudov, M. et Puell, D. (2018). « Bitcoin Market-Value-to-Realized-Value (MVRV) Ratio », octobre 2018.",
  "Définition courante du NUPL (Net Unrealized Profit/Loss) : 1 − capitalisation réalisée ÷ capitalisation de marché.",
]
+++

## Le prix auquel chaque pièce a bougé

La chaîne enregistre quand chaque bitcoin a changé de mains pour la dernière fois. Si l'on connaît le prix de ce jour-là, on peut valoriser chaque pièce non pas au prix d'aujourd'hui, mais au prix auquel son détenteur l'a reçue. La somme s'appelle la **capitalisation réalisée** ; divisée par l'offre, elle donne le **prix réalisé** : le prix d'acquisition moyen de l'ensemble des détenteurs.

::: formula
\text{Prix réalisé} = \frac{\sum \text{unités} \times \text{prix au dernier mouvement}}{\text{offre totale}}
:::

## Un marché construit

*Exemple construit pour la leçon : 1 000 pièces, dont on connaît le prix au dernier mouvement. Chaque mois, 5 % des plus anciennes changent de mains au prix du mois.*

::: chart prix-realise-exemple
Le prix de marché, très volatil, et le prix réalisé, qui bouge lentement parce qu'une petite part des pièces change de mains chaque mois. Exemple synthétique.
:::

Le prix réalisé sert de repère : quand le prix de marché passe dessous, les détenteurs sont en moyenne en perte.

## MVRV et NUPL

::: formula
\text{MVRV} = \frac{\text{prix de marché}}{\text{prix réalisé}} \qquad \text{NUPL} = 1 - \frac{\text{prix réalisé}}{\text{prix de marché}}
:::

::: chart mvrv-exemple
Le MVRV du marché construit : 2,57 au sommet du sixième mois, 0,56 au creux du onzième. Exemple synthétique.
:::

::: chart nupl-exemple
Le NUPL du même marché : la part de la valeur de marché qui serait un gain, ou une perte si elle est négative, si tous les détenteurs vendaient. Exemple synthétique.
:::

Un MVRV élevé signifie que les détenteurs ont en moyenne de fortes plus-values latentes, que certains seront tentés de réaliser ; un MVRV sous 1, qu'ils sont en moyenne en perte. Le NUPL dit la même chose en part de la valeur de marché.

## À vous

::: exercise mvrv-calcul
:::

::: callout debate "Des indicateurs de cycle ?"
Pour leurs utilisateurs, MVRV et NUPL ont marqué les excès des cycles passés : des valeurs extrêmes en haut comme en bas. Pour leurs critiques, ces seuils ont été ajustés après coup sur quelques cycles seulement, les pièces perdues faussent le prix réalisé, et rien ne garantit que les prochains cycles ressembleront aux précédents. Un indicateur décrit un état ; il ne fixe ni un sommet ni un creux.
:::

::: callout note "Pourquoi Sensitor ne publie pas encore les séries réelles"
Calculer le prix réalisé de Bitcoin demande l'historique de toutes ses pièces, que la chaîne fournit, et un historique de prix quotidien. Aucune source gratuite vérifiée ne permet de réutiliser cet historique de prix dans un service commercial. Les séries réelles seront publiées quand Sensitor disposera d'une licence ; d'ici là, les graphiques de cette leçon sont construits, et le disent.
:::

::: callout mistake "Erreur fréquente"
Vendre parce que « le MVRV est élevé ». Il est resté élevé des mois pendant certaines hausses. C'est un thermomètre, pas un signal de vente.
:::

::: callout recap
- Prix réalisé : prix d'acquisition moyen des détenteurs, à partir du dernier mouvement de chaque pièce.
- MVRV = prix ÷ prix réalisé ; NUPL = 1 − prix réalisé ÷ prix.
- Des thermomètres de l'état du marché, pas des signaux infaillibles.
:::
