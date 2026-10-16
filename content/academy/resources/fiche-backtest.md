# Tester une stratégie

*Fiche de révision · Sensitor Academy · Parcours 7, « Construction de stratégie et backtesting »*

## La règle, en six parties

| Partie | La question |
|---|---|
| **Contexte** | dans quelles conditions la stratégie s'applique-t-elle ? |
| **Déclencheur** | quel événement crée une occasion ? |
| **Entrée** | à quel prix, avec quel ordre ? |
| **Invalidation** | où le scénario est-il faux ? |
| **Sortie** | quand sort-on, hors invalidation ? |
| **Taille** | combien risque-t-on ? |

Test des deux lecteurs : la même règle, le même historique, les mêmes trades.

## Les formules

- **Espérance nette** : moyenne des résultats en R − coût moyen par trade.
- **Profit factor** : somme des gains ÷ somme des pertes.
- **Erreur type** : écart type des résultats ÷ √n.
- **Intervalle à 95 %** : espérance ± 1,96 × erreur type.
- **Trades nécessaires** : (1,96 × écart type ÷ demi-largeur voulue)².
- **Faux positif sur k variantes** : 1 − 0,95^k (64 % pour 20).
- **Dégradation** : 1 − espérance hors échantillon ÷ espérance dans l'échantillon.

## Les biais et leurs parades

| Biais | Parade |
|---|---|
| **Anticipation** | défilement bougie par bougie |
| **Sélection** | période fixée avant, toutes les occurrences |
| **Survivant** | instrument choisi avant le test |
| **Rétrospectif** | la règle écrite décide |
| **Surajustement** | peu de paramètres, variantes comptées, test hors échantillon |

## Avant d'annoncer un résultat

- [ ] La règle et sa version sont écrites et datées.
- [ ] Instrument, période de construction et période de test ont été fixés avant.
- [ ] Toutes les occurrences sont relevées, y compris les ordres non exécutés.
- [ ] Les coûts sont retranchés de chaque trade.
- [ ] Le résultat est donné avec n, son intervalle et le nombre de variantes essayées.
- [ ] L'échantillon de test n'a servi qu'une fois.

---

*Document pédagogique. Ne constitue pas un conseil en investissement.*
