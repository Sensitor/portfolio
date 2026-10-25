+++
id = "taux-interet"
title = "Le taux d'intérêt, prix du temps"
summary = "Emprunter, c'est disposer aujourd'hui d'une somme que l'on rendra plus tard, avec un supplément : l'intérêt. Ce que coûte un crédit immobilier, pourquoi deux points de taux changent tout sur vingt ans, et comment se répartissent intérêts et capital."
duration_minutes = 16
access = "member"
status = "published"
version = 1
updated = 2026-10-17
objectives = [
  "Définir le taux d'intérêt comme le prix du temps et du risque.",
  "Calculer la mensualité et le coût total d'un crédit amortissable.",
  "Expliquer pourquoi les premières années d'un crédit remboursent surtout des intérêts.",
]
quiz = "check-taux-interet"
resources = ["fiche-la-monnaie"]
sources = [
  "Fisher, I. (1930). The Theory of Interest. New York : Macmillan.",
  "Mishkin, F. S. The Economics of Money, Banking and Financial Markets. Pearson, éditions successives, chapitre « The Meaning of Interest Rates ».",
  "Formule de l'annuité constante : mensualité = capital × r ÷ (1 − (1 + r)^−n), r taux mensuel, n nombre de mensualités.",
]
+++

## Le prix du temps

Un **taux d'intérêt** est le prix payé pour disposer d'argent avant de l'avoir gagné. Il rémunère trois choses :

- le **temps** : le prêteur renonce à utiliser son argent pendant la durée du prêt ;
- le **risque** : l'emprunteur peut ne pas rembourser ;
- la **perte de pouvoir d'achat** attendue : si les prix montent, l'argent rendu vaudra moins. Le cours suivant distinguera, pour cette raison, le taux **nominal** du taux **réel**.

Le taux d'un crédit part du taux directeur de la banque centrale, auquel la banque ajoute une **marge** : son coût de financement, le risque de l'emprunteur, ses frais et son profit.

## Ce que coûte un crédit

Un crédit immobilier classique se rembourse par **mensualités constantes**. Chaque mensualité paie les intérêts du mois sur ce qui reste dû, et le reste rembourse une partie du capital.

::: formula
\text{Mensualité} = \text{Capital} \times \frac{r}{1 - (1 + r)^{-n}}
:::

où *r* est le taux annuel divisé par 12 et *n* le nombre de mensualités.

::: callout example "Exemple pédagogique"
200 000 € empruntés à 4 % sur 20 ans, soit 240 mensualités : la mensualité est de **1 211,96 €**. L'emprunteur rembourse au total 290 870,56 €, dont **90 870,56 €** d'intérêts, hors assurance et frais.
:::

::: chart credit-interets-capital
Le même crédit, année par année : la part des intérêts (en bas) diminue à mesure que le capital restant dû baisse. Calcul exact.
:::

La première année, 7 878,69 € sur les 14 543,53 € versés sont des intérêts, plus de la moitié. La dernière année, il n'en reste que 310,27 €.

## À vous

::: exercise cout-credit
:::

::: callout warning "Petit écart de taux, grande différence de coût"
Sur une longue durée, deux points de taux en plus ne coûtent pas « un peu plus » : ils peuvent doubler le coût total des intérêts. C'est l'effet des intérêts calculés chaque mois sur un capital qui ne baisse que lentement au début.
:::

::: callout mistake "Erreur fréquente"
Comparer deux crédits par leur seule mensualité. Allonger la durée baisse la mensualité mais augmente le coût total. On compare le coût total, à durée égale, assurance et frais compris.
:::

::: callout recap
- Le taux d'intérêt rémunère le temps, le risque et la perte de pouvoir d'achat attendue.
- Le taux d'un crédit = taux de la banque centrale + marge de la banque.
- Mensualité = capital × r ÷ (1 − (1 + r)^−n) ; au début, elle paie surtout des intérêts.
- On compare des crédits par leur coût total, pas par leur mensualité.
:::
