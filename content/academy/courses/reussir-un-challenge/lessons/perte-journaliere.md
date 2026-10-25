+++
id = "perte-journaliere"
title = "La perte journalière, calculée comme la société la calcule"
summary = "Une limite qui repart chaque jour d'un solde différent. Comment FTMO et Topstep la calculent, combien de pertes elle laisse selon le risque par trade, et pourquoi elle se rapproche après une bonne journée."
duration_minutes = 14
access = "member"
status = "published"
version = 1
updated = 2026-10-25
objectives = [
  "Calculer la limite journalière d'un jour donné.",
  "Traduire cette limite en nombre de pertes selon le risque par trade.",
  "Distinguer une limite qui élimine d'une limite qui arrête la séance.",
]
quiz = "check-perte-journaliere"
resources = ["fiche-prop-firm"]
sources = [
  "FTMO, Trading Objectives, https://ftmo.com/en/trading-objectives/, page mise à jour le 20 octobre 2026, consultée le 25 octobre 2026.",
  "Topstep Help Center, Daily Loss Limit in the Trading Combine and Express Funded Account, https://help.topstep.com/en/articles/10490293, mis à jour le 30 juin 2026.",
]
+++

## Une limite qui repart chaque jour

Chez FTMO, la limite journalière est recalculée à minuit, heure d'Europe centrale : c'est le **solde de minuit** moins un pourcentage du **solde initial**. Le jour 1, la référence est le solde initial.

::: formula
\text{Limite du jour} = \text{Solde à minuit} - \text{Pourcentage} \times \text{Solde initial}
:::

FTMO donne l'exemple d'un compte de 100 000 $ dont le solde est de 102 000 $ à minuit :

| | FTMO 2-Step (5 %) | FTMO 1-Step (3 %) |
|---|---|---|
| Limite du jour | 102 000 − 5 000 = **97 000 $** | 102 000 − 3 000 = **99 000 $** |
| Marge depuis l'ouverture | 5 000 $ | 3 000 $ |

C'est l'**équité** qui ne doit pas passer sous cette limite : une position ouverte en perte compte, avant même d'être fermée.

## Combien de pertes dans une journée

Avec un risque fixe par trade, la limite se traduit en nombre de pertes, comme dans le parcours sur le risque. Sur 100 000 $ avec 1 % par trade, soit 1 000 $ :

- FTMO 2-Step : 5 000 $ de marge, **5 pertes** pour atteindre la limite ;
- FTMO 1-Step : 3 000 $ de marge, **3 pertes**.

À 2 % par trade (2 000 $), deux pertes font 4 000 $ : sous la règle de 3 % du 1-Step, deux pertes le même jour suffisent à perdre le compte.

::: callout definition "Atteindre ou franchir"
Chez FTMO, l'équité ne doit pas **passer sous** la limite. Chez Topstep, le compte ne doit ni **toucher** ni passer sous ses seuils. Dans les deux cas, trader au ras de la limite est un pari sur le glissement de l'exécution : la règle personnelle s'arrête avant.
:::

## Éliminer ou arrêter la séance

Les deux sociétés ne donnent pas la même conséquence à la même idée :

- chez FTMO, franchir la perte journalière **élimine le compte** ;
- chez Topstep, la limite journalière est **optionnelle**, choisie à l'achat (1 000 $ sur un 50K, 2 000 $ sur un 100K, 3 000 $ sur un 150K) : l'atteindre ferme les positions jusqu'à 17 h, heure de Chicago, sans que ce soit une violation de règle.

::: callout method "Sa propre limite, plus serrée"
Écrire une limite personnelle sous celle de la société, par exemple deux pertes par jour, et s'arrêter quand elle est atteinte. La limite de la société devient un filet que l'on ne touche pas.
:::

::: callout mistake "Erreur fréquente"
Croire qu'une bonne journée donne de la marge pour le lendemain. La limite repart du solde de minuit : après un gain, le seuil du jour remonte d'autant.
:::

::: callout recap
- Limite du jour = solde à minuit moins un pourcentage du solde initial (FTMO).
- Avec un risque fixe, elle se traduit en nombre de pertes : 5 à 1 % sous 5 %, 3 à 1 % sous 3 %.
- FTMO élimine, Topstep arrête la séance : lire la conséquence autant que le montant.
:::
