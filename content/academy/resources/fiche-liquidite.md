# Liquidité et scénarios

*Fiche de révision · Sensitor Academy · Parcours 3, « Liquidité et contexte »*

## L'hypothèse de départ

- La **liquidité**, ce sont les ordres disponibles près du prix ; un gros ordre a besoin d'ordres de sens contraire.
- Stops et ordres d'entrée sur cassure s'accumulent, par hypothèse, au-delà des sommets et des creux visibles.
- Le stop d'un vendeur est un ordre d'achat ; celui d'un acheteur, un ordre de vente.
- On ne voit pas ces ordres. On observe le prix autour des niveaux.

## Les définitions du parcours

| Terme | Règle |
|---|---|
| **Niveaux égaux** | des swings à moins de la tolérance du premier d'entre eux |
| **Niveau de référence** | le plus haut des sommets, ou le plus bas des creux, du groupe |
| **Sweep** | mèche au-delà du niveau, clôture revenue au niveau ou en deçà |
| **Cassure** | clôture au-delà du niveau |
| **Fausse cassure** | cassure, puis clôture revenue en deçà dans un délai écrit |
| **Liquidité externe** | les niveaux qui bornent la structure |
| **Liquidité interne** | les niveaux à l'intérieur de la structure |

## Les conventions à écrire avant de regarder

- [ ] Ma tolérance pour les niveaux égaux, par instrument et unité de temps.
- [ ] Le délai qui transforme une cassure en fausse cassure.
- [ ] Ce qui confirme une cassure, et ce que je fais dans chaque cas.
- [ ] L'unité de temps à laquelle je classe un niveau interne ou externe.

## Le scénario

1. **Niveau** : sommets ou creux égaux, référence chiffrée.
2. **Constat** : sweep ou cassure, en clôture, jamais avant.
3. **Invalidation** : au-delà du plus haut (ou du plus bas) du sweep, avec une marge.
4. **Taille** : budget de risque ÷ (distance × valeur d'un point par lot), arrondie vers le bas.
5. **Ce que je ne contrôle pas** : spread aux annonces, spécification du courtier, suite du mouvement.

## Les pièges

- Raconter chaque mouvement comme une « chasse aux stops » après coup.
- Élargir la tolérance jusqu'à voir des niveaux égaux partout.
- Agir sur une mèche avant la clôture de la bougie.
- Juger une fausse cassure avec le graphique terminé.

---

*Document pédagogique. Ne constitue pas un conseil en investissement.*
