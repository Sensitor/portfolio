+++
id = "fonctionnement-marche"
title = "Comment se forme un prix"
summary = "Qui achète, qui vend, et pourquoi le prix auquel vous êtes exécuté n'est pas toujours celui que vous voyez."
duration_minutes = 12
access = "public"
status = "published"
version = 1
objectives = [
  "Expliquer ce qu'est un marché et qui y intervient.",
  "Distinguer le prix acheteur (bid), le prix vendeur (ask) et le spread.",
  "Comprendre pourquoi la liquidité influence le prix obtenu.",
]
quiz = "check-fonctionnement-marche"
resources = ["fiche-vocabulaire-execution"]
+++

## Un marché, c'est une rencontre

Un marché financier met en relation des personnes qui veulent acheter un actif et des personnes qui veulent le vendre. Actions, devises, matières premières, indices ou cryptoactifs : le mécanisme de base est le même. **Une transaction n'a lieu que lorsqu'un acheteur et un vendeur s'accordent sur un prix.** Le prix d'un actif n'est rien d'autre que la trace de ces accords successifs.

Les intervenants n'ont pas tous les mêmes raisons d'être là :

- les **teneurs de marché** (*market makers*) affichent en permanence un prix d'achat et un prix de vente et se rémunèrent sur l'écart entre les deux ;
- les **investisseurs institutionnels** (fonds, assureurs, caisses de retraite) déplacent des volumes importants, souvent sur plusieurs jours ;
- les **entreprises** se couvrent : un exportateur européen qui vend des dollars, une compagnie aérienne qui fixe à l'avance le prix de son carburant ;
- les **particuliers** interviennent le plus souvent par l'intermédiaire d'un courtier.

Se couvrir, investir, spéculer, fournir de la liquidité : ces motivations différentes expliquent pourquoi il y a presque toujours quelqu'un en face de votre ordre, mais pas toujours au prix que vous espériez.

## Le carnet d'ordres

Sur un marché organisé, les intentions d'achat et de vente sont rassemblées dans un **carnet d'ordres**. Chaque ligne indique un prix et la quantité disponible à ce prix.

::: figure carnet-ordres.svg
Un carnet d'ordres simplifié. Les acheteurs (en bas) proposent des prix inférieurs à ceux des vendeurs (en haut). L'écart entre le meilleur prix vendeur et le meilleur prix acheteur est le spread. Chiffres illustratifs.
:::

::: callout definition "Bid, ask et spread"
- **Bid (prix acheteur)** : le meilleur prix auquel quelqu'un accepte d'acheter. C'est le prix auquel **vous pouvez vendre** immédiatement.
- **Ask (prix vendeur)** : le meilleur prix auquel quelqu'un accepte de vendre. C'est le prix auquel **vous pouvez acheter** immédiatement.
- **Spread** : l'écart entre les deux, *ask − bid*.
:::

## Le prix affiché n'est pas un prix garanti

Le prix d'un graphique est en général le dernier prix échangé, ou le bid selon la plateforme. Or, si vous achetez au marché, vous payez l'ask ; si vous vendez, vous recevez le bid. **Une position ouverte puis refermée immédiatement est donc en perte du montant du spread**, avant toute commission.

::: callout example "Exemple pédagogique"
EURUSD affiche un bid de 1,08500 et un ask de 1,08508. Le spread vaut 0,00008, soit 0,8 pip (le pip est défini dans la leçon suivante). Acheter puis revendre aussitôt coûte ces 0,8 pip. Les chiffres sont illustratifs : les spreads réels dépendent du courtier, du compte et du moment.
:::

## Liquidité et profondeur

Un marché est **liquide** quand de nombreux ordres attendent près du prix : on peut alors échanger des volumes importants sans le déplacer. Quand le carnet est mince, un ordre important « consomme » plusieurs niveaux de prix successifs, et le prix moyen obtenu s'éloigne du prix affiché. C'est l'une des sources du **glissement** (*slippage*), étudié dans la leçon suivante.

La liquidité n'est pas constante. Elle est en général plus forte lorsque plusieurs grandes places financières sont ouvertes en même temps, et plus faible la nuit, les jours fériés ou juste avant une annonce économique importante, quand de nombreux intervenants retirent leurs ordres. Le spread s'élargit alors souvent.

::: callout warning "Marchés de gré à gré"
Le Forex et les CFD ne passent pas par un carnet central unique : les prix vous sont proposés par votre courtier ou par ses fournisseurs de liquidité. Le principe bid / ask reste le même, mais les prix et les spreads peuvent différer d'un courtier à l'autre.
:::

::: callout mistake "Erreur fréquente"
Croire que le prix du graphique est celui auquel l'ordre sera exécuté. Le graphique affiche souvent le bid ; un achat au marché se fait à l'ask, au-dessus.
:::

::: callout recap
- Un prix naît d'une transaction entre un acheteur et un vendeur.
- Vous achetez à l'ask et vous vendez au bid : l'écart, le spread, est un coût payé à chaque aller-retour.
- La liquidité détermine le volume échangeable près du prix affiché. Elle varie selon les heures et les événements.
:::
