+++
id = "volatilite-evenementielle"
title = "Ce qui change au moment d'une publication"
summary = "Dans les secondes qui entourent un chiffre important, la liquidité se retire, le spread s'élargit et un stop peut être exécuté bien au-delà de son niveau. Mesurer le mouvement attendu, et dimensionner une position en comptant le glissement."
duration_minutes = 17
access = "member"
status = "published"
version = 1
updated = 2026-10-19
objectives = [
  "Décrire ce qui arrive à la liquidité, au spread et à l'exécution autour d'une publication.",
  "Calculer le mouvement attendu à partir d'une volatilité implicite.",
  "Dimensionner une position en comptant le glissement, et mesurer l'erreur de ne pas le faire.",
]
quiz = "check-volatilite-evenementielle"
resources = ["fiche-macro"]
sources = [
  "Andersen, T. G., Bollerslev, T., Diebold, F. X. et Vega, C. (2003). « Micro Effects of Macro Announcements: Real-Time Price Discovery in Foreign Exchange ». American Economic Review, 93(1), 38-62.",
  "Hull, J. C. Options, Futures, and Other Derivatives. Pearson, éditions successives : volatilité implicite et écart type d'un prix sur une période.",
]
+++

## Les secondes qui entourent un chiffre

Le parcours 1 a montré qu'un prix se forme dans un carnet d'ordres. Juste avant une publication importante, beaucoup d'intervenants retirent leurs ordres : personne ne veut être exécuté au mauvais prix au moment où l'information arrive. Le carnet se vide.

Trois conséquences, que tout trader doit connaître avant d'avoir une position ouverte à cette heure-là :

- **Le spread s'élargit**, parfois de plusieurs fois sa taille habituelle, pendant quelques secondes ou quelques minutes.
- **Le prix saute** : entre deux cotations, il peut franchir d'un coup plusieurs dizaines de pips ou de points, sans s'arrêter aux niveaux intermédiaires.
- **Un stop peut glisser** : un ordre stop devient un ordre au marché quand son niveau est touché, et il est exécuté au premier prix disponible, qui peut être loin du niveau prévu.

::: figure volatilite-publication.svg
Ce qui se passe autour d'une publication : le spread s'élargit, le prix saute, un stop placé à 20 pips est exécuté à 32 pips, puis le marché fait un aller-retour. Schéma original, prix construits pour l'illustration.
:::

Après le saut initial, le marché fait souvent un **aller-retour** : la première réaction est corrigée, parfois entièrement, quand les intervenants lisent le détail du rapport et les révisions.

## Le mouvement attendu

Le prix des options révèle l'ampleur du mouvement que le marché attend. La **volatilité implicite** d'une option qui expire juste après la publication est plus élevée que d'habitude : elle contient l'événement.

::: formula
\text{Mouvement attendu} = \text{prix} \times \text{volatilité annuelle} \times \sqrt{\frac{\text{jours}}{365}}
:::

Le résultat est un **écart type** : environ deux fois sur trois, le mouvement reste à l'intérieur ; environ une fois sur vingt, il dépasse le double. Le calcul ne dit rien du sens.

::: callout example "EURUSD, un jour d'emploi américain"
EURUSD cote 1,0850 et la volatilité implicite sur un jour atteint 12 % par an, contre 6 à 8 % en temps normal. Le mouvement attendu sur la journée vaut 1,0850 × 0,12 × √(1/365), soit environ **68 pips**. Un stop habituel de 20 pips se trouve bien à l'intérieur du bruit attendu.
:::

## Dimensionner en comptant le glissement

Le parcours 5 a appris à dimensionner une position à partir de la distance au stop. Autour d'une publication, il faut ajouter le **glissement** possible : sinon la perte réelle au stop dépasse le budget.

::: formula
\text{Taille} = \frac{\text{budget de risque}}{(\text{distance au stop} + \text{glissement}) \times \text{valeur du point}}
:::

## À vous

::: exercise mouvement-attendu
:::

::: callout warning "Les conditions du courtier"
Certains courtiers relèvent les marges exigées ou limitent les ordres autour des publications majeures, et certaines prop firms interdisent d'ouvrir ou de fermer une position dans les minutes qui les entourent. Lisez les conditions de votre compte avant d'être concerné.
:::

::: callout mistake "Erreur fréquente"
Garder sa taille habituelle « parce que le stop protège ». Au moment d'une publication, le stop limite la perte à un niveau que l'on ne choisit plus : celui du premier prix disponible.
:::

::: callout recap
- Autour d'un chiffre important : carnet vide, spread élargi, sauts de prix, stops exécutés au-delà de leur niveau, aller-retour fréquent.
- Mouvement attendu = prix × volatilité implicite × √(jours ÷ 365) : un écart type, sans direction.
- Taille = budget ÷ ((stop + glissement) × valeur du point).
:::
