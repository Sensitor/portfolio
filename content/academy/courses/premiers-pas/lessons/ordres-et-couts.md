+++
id = "ordres-et-couts"
title = "Ordres, spread et coûts de transaction"
summary = "Ordre au marché, limite ou stop : ce que chacun garantit, ce qu'il ne garantit pas, et ce que coûte vraiment un aller-retour."
duration_minutes = 15
access = "public"
status = "published"
version = 1
objectives = [
  "Choisir entre ordre au marché, ordre limite et ordre stop selon l'intention.",
  "Expliquer pourquoi un stop-loss peut être exécuté au-delà de son niveau.",
  "Additionner les coûts d'une transaction : spread, commission, swap et glissement.",
  "Comprendre ce que le levier change, et ce qu'il ne change pas.",
]
quiz = "check-ordres-et-couts"
resources = ["fiche-vocabulaire-execution"]
sources = [
  "Décision (UE) 2018/796 de l'ESMA du 22 mars 2018 restreignant la commercialisation des CFD auprès des clients de détail ; mesures reprises depuis par les régulateurs nationaux, dont l'AMF.",
]
+++

## Trois familles d'ordres

Un ordre est une instruction donnée à votre courtier. Il en existe de nombreuses variantes, mais elles reposent toutes sur trois familles.

| Ordre | Ce qu'il dit | Exécution | Risque principal |
|---|---|---|---|
| **Au marché** | « Maintenant, au meilleur prix disponible. » | Immédiate | Un prix obtenu différent du prix affiché (glissement) |
| **Limite** | « À ce prix, ou mieux. » | Seulement si le prix atteint le niveau | Ne pas être exécuté |
| **Stop** | « Si le prix atteint ce niveau, exécute au marché. » | Déclenché au niveau, puis exécuté au marché | Glissement, surtout en cas de gap |

Un ordre limite d'achat se place **sous** le prix actuel (on veut acheter moins cher), un ordre limite de vente **au-dessus**. Un ordre stop d'achat se place **au-dessus** du prix actuel (on veut acheter si le prix monte jusqu'au niveau), un ordre stop de vente **en dessous**.

::: figure types-ordres.svg
Où se placent les ordres en attente par rapport au prix actuel. Les ordres limites attendent un prix plus favorable ; les ordres stops se déclenchent quand le prix va dans la direction indiquée.
:::

::: callout note "À retenir"
Un ordre limite garantit le prix, pas l'exécution. Un ordre stop garantit le déclenchement, pas le prix.
:::

## Le stop-loss est un ordre stop

Un stop-loss est un ordre stop qui ferme votre position lorsque le prix atteint votre niveau d'invalidation. Une fois déclenché, il est exécuté **au meilleur prix disponible**. Dans un marché rapide, ou si le prix ouvre en *gap* au-delà de votre niveau — après un week-end ou une annonce —, la perte réelle peut dépasser la perte prévue. Certains courtiers proposent des stops garantis, en général contre une prime : renseignez-vous sur leurs conditions avant de compter dessus.

## Pips, lots et valeur d'un mouvement

Sur le Forex, trois conventions reviennent sans cesse :

- un **pip** correspond au quatrième chiffre après la virgule pour la plupart des paires (0,0001), et au deuxième pour les paires cotées contre le yen (0,01) ;
- un **lot standard** représente, par convention, 100 000 unités de la devise de base ; un mini-lot 10 000, un micro-lot 1 000 ;
- sur EURUSD, coté en dollars, 1 pip pour 1 lot standard vaut donc 100 000 × 0,0001 = **10 dollars**.

Pour l'or, les indices ou les actions, la taille d'un contrat et la valeur d'un point dépendent de la **spécification publiée par votre courtier**. Il faut la lire avant tout calcul : deux courtiers peuvent définir différemment le « lot » d'un même instrument.

## Le coût complet d'une transaction

Le spread n'est que la partie visible. Un aller-retour peut comporter :

- **le spread**, payé à l'entrée ;
- **une commission**, souvent facturée par lot sur certains types de comptes ;
- **le swap**, des frais — ou plus rarement un crédit — de financement pour une position gardée d'un jour sur l'autre, liés au différentiel de taux d'intérêt entre les deux devises et à la marge du courtier ;
- **le glissement**, l'écart entre le prix demandé et le prix obtenu.

::: callout example "Exemple pédagogique — le coût d'un aller-retour"
Achat de 1 lot EURUSD avec un spread de 0,8 pip et une commission de 7 $ par lot aller-retour (hypothèse de compte). Le spread coûte 0,8 × 10 $ = 8 $, la commission 7 $ : 15 $ au total, avant swap et glissement. Si le stop est placé à 15 pips, soit 150 $ de risque, les coûts représentent déjà 10 % de la perte prévue.
:::

## Le levier et la marge

Le levier permet d'ouvrir une position dont la valeur dépasse votre dépôt. La **marge** est la somme immobilisée pour la maintenir :

::: formula
\text{Marge} = \frac{\text{Valeur de la position}}{\text{Levier}}
:::

Un lot d'EURUSD à 1,0850 représente 108 500 $ ; avec un levier de 30:1, la marge requise est d'environ 3 617 $.

::: callout warning "Ce que le levier ne change pas"
Le levier modifie la marge immobilisée, pas la valeur d'un pip. Avec 1 lot d'EURUSD, un mouvement défavorable de 15 pips coûte 150 $, que le levier soit de 10:1 ou de 30:1. Ce qui détermine la perte, c'est la taille de la position et la distance au stop.
:::

Dans l'Union européenne, le levier proposé aux clients de détail sur les CFD est plafonné : 30:1 sur les principales paires de devises, 20:1 sur les autres paires, l'or et les principaux indices, 10:1 sur les autres matières premières et indices, 5:1 sur les actions individuelles et 2:1 sur les cryptoactifs.

::: callout mistake "Erreur fréquente"
Choisir sa taille de position d'après la marge disponible (« le compte me permet d'ouvrir 3 lots ») plutôt que d'après la perte acceptée si le stop est touché.
:::

::: callout recap
- Ordre au marché : exécution immédiate, prix non garanti. Ordre limite : prix garanti, exécution non garantie. Ordre stop : déclenchement garanti, prix non garanti.
- Un stop-loss peut être exécuté au-delà de son niveau en cas de gap ou de marché rapide.
- Le coût d'un trade additionne spread, commission, swap et glissement.
- Le levier change la marge immobilisée, pas le risque d'une position de taille donnée.
:::
