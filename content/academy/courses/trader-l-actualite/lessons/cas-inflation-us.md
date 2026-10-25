+++
id = "cas-inflation-us"
title = "Cas pratique : une journée de publication de l'inflation"
summary = "Un compte de 25 000 dollars, un indice d'actions américain et l'inflation sous-jacente qui sort au-dessus du consensus. La préparation de la veille, la lecture du chiffre, l'attente, puis l'entrée, chiffrées étape par étape."
duration_minutes = 20
access = "member"
status = "published"
version = 1
updated = 2026-10-19
objectives = [
  "Préparer une séance de publication avec une règle écrite.",
  "Chiffrer la surprise, le mouvement attendu et la taille d'une position un jour de publication.",
  "Mesurer ce qu'aurait coûté la taille habituelle.",
]
quiz = "check-cas-inflation-us"
resources = ["fiche-macro"]
+++

## La situation

*Cas construit pour la leçon : les prix et les chiffres sont des exemples.*

Un trader suit un indice d'actions américain, coté en CFD : un contrat vaut **1 dollar par point**, la taille se règle par pas de 0,1 contrat. Son compte est de **25 000 dollars** et sa règle fixe un risque de **0,5 %** par trade, soit **125 dollars**.

Le calendrier annonce pour 14 h 30, heure de Paris, l'inflation américaine du mois. Le chiffre le plus suivi est l'inflation **sous-jacente** sur un mois.

| | Valeur |
|---|---|
| Consensus, inflation sous-jacente sur un mois | +0,3 % |
| Écart type des surprises passées | 0,1 point |
| Volatilité implicite de l'indice, sur un jour | 24 % par an |
| Niveau de l'indice la veille au soir | 6 000 points |
| Stop habituel de la stratégie, un jour ordinaire | 12 points |

## La veille : la règle de la séance

1. **Publication** : inflation américaine, 14 h 30 à Paris, heure vérifiée pour la semaine.
2. **Positions ouvertes** : aucune à 14 h 25.
3. **Fenêtre d'abstention** : de 14 h 25 à 14 h 50.
4. **Délai d'attente** : 20 minutes après le chiffre, puis la méthode habituelle, structure et zone.
5. **Taille** : stop placé selon la nouvelle structure, plus un glissement estimé à 5 points.
6. **Ce qui annule tout** : un mouvement de plus de deux fois le mouvement attendu, ou un marché qui ne forme pas de structure lisible avant 15 h 30.

## 14 h 30 : le chiffre

L'inflation sous-jacente sort à **+0,5 %**. Le marché lit une banque centrale contrainte de garder des taux élevés : les rendements montent, l'indice perd **90 points** en quelques minutes, puis en reprend 40.

## 14 h 50 : la structure

Après le délai d'attente, l'indice a formé un **sommet plus bas** à 5 962 points, sous le sommet de 14 h 35, et casse le dernier creux. Selon la méthode des parcours 2 et 4, le trader prépare une vente à **5 932 points**, avec un stop au-dessus du sommet plus bas : **30 points** de distance, auxquels il ajoute les 5 points de glissement estimés.

## À vous

::: exercise cas-inflation-us
:::

## Ce que le cas montre

- La surprise était forte, deux fois l'écart habituel, et le mouvement de l'indice, 90 points, a dépassé le mouvement attendu de 75 points : une journée réellement inhabituelle, mais à l'intérieur de la limite de deux écarts types que la règle avait fixée.
- Le trader n'a jamais parié sur le chiffre. Il a attendu, puis appliqué sa méthode habituelle à la structure nouvelle.
- La taille a été divisée par trois par rapport à un jour ordinaire. C'est le prix d'un stop plus large et d'un glissement possible, pour un risque inchangé.

::: callout mistake "Erreur fréquente"
Entrer à 14 h 31 « dans le sens du chiffre ». Le prix a fait un aller-retour de 40 points dans les minutes suivantes : une vente au plus bas de la première réaction aurait été arrêtée avant que la vraie structure se forme.
:::

::: callout recap
- La règle est écrite la veille : abstention, délai, taille, conditions d'annulation.
- Surprise normalisée de +2,0, mouvement attendu de 75 points : une séance à traiter à part.
- Taille de 3,5 contrats au lieu de 10,4 : avec la taille habituelle, le stop aurait coûté près de trois fois le budget.
:::
