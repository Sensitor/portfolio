+++
id = "confluence"
title = "Confluence : combiner des zones sans se tromper"
summary = "Quand plusieurs zones se recouvrent, l'intervalle commun devient une zone d'entrée précise. Ce que cela apporte, et les erreurs d'analyse qui font paraître une confluence plus solide qu'elle ne l'est."
duration_minutes = 16
access = "member"
status = "published"
version = 1
objectives = [
  "Calculer l'intervalle commun de deux zones de prix.",
  "Reconnaître deux zones qui portent la même information.",
  "Nommer les erreurs d'analyse fréquentes : double compte, critères ajoutés après coup, sélection des exemples.",
]
quiz = "check-confluence"
resources = ["fiche-zones"]
+++

## Ce que l'on appelle confluence

Une **confluence** est un intervalle de prix où plusieurs zones se recouvrent : un FVG à l'intérieur de la zone OTE, un order block sous un niveau de liquidité, et ainsi de suite. Son premier intérêt est pratique : elle **resserre** la zone d'entrée, donc rapproche l'invalidation et améliore le ratio gain / risque.

::: callout definition "Intervalle commun"
Le recouvrement de deux zones va du **plus haut des deux bornes basses** au **plus bas des deux bornes hautes**. Si ce calcul donne une borne basse au-dessus de la borne haute, les zones ne se recouvrent pas.
:::

::: callout example "Exemple pédagogique"
Zone OTE de 1,0821 à 1,0838 ; FVG de 1,0826 à 1,0845. Plus haute des bornes basses : 1,0826. Plus basse des bornes hautes : 1,0838. Intervalle commun : **1,0826 à 1,0838**, soit 12 pips au lieu de 17 pour la zone OTE seule.
:::

::: figure confluence.svg
Quatre zones du cas GBPUSD sur le même axe. Seul le FVG inférieur recoupe la zone OTE ; l'order block reste dessous et le FVG supérieur au-dessus. Schéma original.
:::

## Ce que la confluence n'apporte pas

L'intuition dit : trois raisons valent mieux qu'une. C'est vrai seulement si les trois raisons sont **indépendantes**, et c'est rarement le cas ici.

::: callout warning "Le double compte"
Un FVG et un order block naissent souvent **de la même impulsion** : l'order block est la bougie juste avant, le FVG l'écart que l'impulsion laisse. Les compter comme deux confirmations revient à compter deux fois le même fait. De même, une zone OTE se calcule sur la jambe que cette impulsion a créée.
:::

## Les erreurs d'analyse fréquentes

| Erreur | Ce qui se passe | Le remède |
|---|---|---|
| **Double compte** | deux zones issues du même mouvement comptées comme deux preuves | noter d'où vient chaque zone |
| **Critères ajoutés après coup** | on ajoute un filtre jusqu'à ce que les exemples perdants disparaissent | écrire la liste des critères avant de tester |
| **Sélection des exemples** | on retient les graphiques où la confluence « a marché » | tester toutes les occurrences sur une période fixée |
| **Zone élargie** | on étire une zone pour qu'elle touche la suivante | garder les bornes que la règle donne |

La deuxième erreur a un nom en statistique : le **surajustement**. Avec assez de filtres, n'importe quelle règle paraît excellente sur le passé, et ne vaut plus rien ensuite. Le parcours 7 y reviendra en détail.

::: callout method "Combien de confluences ?"
Ajouter des critères réduit le nombre d'occurrences. Une règle à cinq conditions peut ne se présenter que dix fois par an : trop peu pour la juger, et l'intervalle de confiance du parcours 5 restera très large. Une confluence plus simple, mesurée sur beaucoup d'occurrences, en apprend souvent davantage.
:::

::: callout recap
- Le recouvrement de deux zones va de la plus haute des bornes basses à la plus basse des bornes hautes.
- Une confluence resserre la zone d'entrée ; elle n'additionne pas des preuves indépendantes.
- FVG, order block et zone OTE viennent souvent du même mouvement : attention au double compte.
- Critères écrits avant, toutes les occurrences testées, bornes non étirées.
:::
