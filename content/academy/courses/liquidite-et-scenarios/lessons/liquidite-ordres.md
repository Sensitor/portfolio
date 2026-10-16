+++
id = "liquidite-ordres"
title = "Où se trouvent les ordres : la liquidité"
summary = "Pourquoi des ordres s'accumulent au-delà des sommets et des creux que tout le monde voit, ce que cela implique pour le prix, et pourquoi personne ne voit réellement ces ordres."
duration_minutes = 14
access = "public"
status = "published"
version = 1
objectives = [
  "Relier la liquidité du parcours 1 aux niveaux de structure du parcours 2.",
  "Expliquer pourquoi des stops s'accumulent au-delà des swings visibles.",
  "Séparer l'idée, plausible, de sa vérification, impossible depuis un graphique.",
]
quiz = "check-liquidite"
resources = ["fiche-liquidite"]
+++

## Un rappel du parcours 1

La **liquidité** est la quantité d'ordres disponibles près du prix. Un ordre au marché important a besoin, en face, d'ordres de sens contraire : un gros acheteur a besoin de vendeurs. Sans eux, son ordre consomme plusieurs niveaux de prix et s'exécute mal.

Ce parcours se demande **où** se trouvent ces ordres en attente, et ce que leur emplacement change à la lecture d'un graphique.

## Les ordres se rangent derrière les niveaux visibles

Reprenez les règles des parcours précédents. Un acheteur qui suit la structure place souvent son stop **sous le dernier creux de swing** : c'est son invalidation. Un vendeur place le sien **au-dessus du dernier sommet**. D'autres attendent une cassure pour entrer, avec un ordre stop placé juste au-delà du même niveau.

Tous ces ordres ont un point commun : ils se trouvent au-delà de niveaux que tout le monde voit.

::: figure liquidite-stops.svg
Au-dessus d'un sommet visible s'accumulent les stops des vendeurs et les ordres d'achat qui attendent une cassure ; sous un creux visible, l'inverse. Schéma original, hypothèse de méthode.
:::

::: callout definition "Ce que deviennent ces ordres"
Le stop d'un vendeur est un **ordre d'achat** qui se déclenche au-dessus du sommet. Le stop d'un acheteur est un **ordre de vente** qui se déclenche sous le creux. Quand le prix atteint ces niveaux, ces ordres deviennent des ordres au marché.
:::

## Pourquoi cela intéresse les gros intervenants

Un intervenant qui veut **vendre** une grande quantité a besoin d'acheteurs. Les stops des vendeurs situés au-dessus d'un sommet sont précisément des ordres d'achat : si le prix les atteint, ils fournissent la contrepartie. C'est l'idée au cœur des méthodes fondées sur la liquidité : le prix va souvent « chercher » ces zones avant de repartir.

::: callout method "Hypothèse de méthode, pas observation"
Personne ne voit les ordres stops des autres sur un graphique, et sur le Forex ou les CFD il n'existe même pas de carnet central. L'idée que des ordres s'accumulent au-delà des niveaux visibles est plausible et largement partagée ; elle reste une hypothèse. On peut la confronter à son historique, pas la constater bougie par bougie.
:::

## Ce que l'on peut observer

Ce qui se vérifie, en revanche, c'est le comportement du prix autour de ces niveaux : il les dépasse, il revient, il clôture d'un côté ou de l'autre. Les leçons suivantes s'en tiennent à ces observations et à des règles écrites.

::: callout mistake "Erreur fréquente"
Raconter après coup chaque mouvement comme une « chasse aux stops ». Une explication qui s'applique à tout ne permet de rien anticiper. Une hypothèse utile dit à l'avance ce qu'elle attend, et ce qui la contredirait.
:::

::: callout recap
- La liquidité, ce sont les ordres disponibles ; un gros ordre a besoin d'ordres de sens contraire.
- Stops et ordres d'entrée s'accumulent au-delà des sommets et des creux visibles.
- Le stop d'un vendeur est un ordre d'achat ; celui d'un acheteur, un ordre de vente.
- Leur emplacement est une hypothèse ; seul le comportement du prix autour des niveaux s'observe.
:::
