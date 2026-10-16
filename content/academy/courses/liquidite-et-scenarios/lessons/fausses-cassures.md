+++
id = "fausses-cassures"
title = "Fausse cassure ou vraie cassure"
summary = "Une cassure peut tenir ou échouer. On ne le sait qu'après coup ; ce que l'on peut décider à l'avance, c'est ce qui confirmera l'une et ce qui invalidera l'autre."
duration_minutes = 14
access = "member"
status = "published"
version = 1
objectives = [
  "Décrire une fausse cassure avec des règles de clôture.",
  "Écrire à l'avance ce qui confirme une cassure et ce qui l'invalide.",
  "Reconnaître le biais rétrospectif dans les récits de « fausses cassures ».",
]
quiz = "check-fausses-cassures"
+++

## La définition

Une **fausse cassure** est une cassure de structure, donc une **clôture** au-delà d'un niveau, suivie d'un retour du prix en deçà, en clôture, peu de temps après. Elle diffère du sweep : dans un sweep, la clôture n'a jamais franchi le niveau ; dans une fausse cassure, elle l'a franchi, puis le prix est revenu.

Combien de temps compte « peu de temps après » ? Encore une convention : par exemple, dans les trois bougies qui suivent la cassure. Elle s'écrit à l'avance.

## On ne le sait qu'après coup

Au moment de la cassure, rien ne dit si elle tiendra. Les deux suites ont la même première bougie. C'est pour cela que les récits de « fausses cassures évidentes » sont trompeurs : ils sont écrits une fois la suite connue.

::: callout warning "Le biais rétrospectif"
Une fois le graphique terminé, chaque fausse cassure paraît annoncée et chaque vraie cassure paraît évidente. Le **biais rétrospectif** consiste à juger une décision passée avec une information qui n'existait pas au moment de la prendre. Il fait surestimer ce que l'on aurait « dû voir ».
:::

## Ce que l'on décide à l'avance

À défaut de savoir, on peut écrire avant la cassure :

| | Exemple de règle |
|---|---|
| **Ce qui confirme** | la bougie suivant la cassure clôture elle aussi au-delà du niveau |
| **Ce qui invalide** | une clôture revient en deçà du niveau dans les trois bougies |
| **Ce que l'on fait** | entrer après confirmation, ou attendre un retour sur le niveau |
| **Ce que cela coûte** | une entrée plus tardive, donc un ratio gain / risque moins bon |

Aucune de ces règles n'est la bonne en soi. Chacune échange de la précision contre du retard ; leur valeur se mesure sur votre historique, avec la taille d'échantillon du parcours 5.

::: callout example "Exemple pédagogique"
Niveau de sommets égaux à 1,0944. Une bougie clôture à 1,0947 : cassure. Les deux bougies suivantes clôturent à 1,0943 puis 1,0936 : retour en deçà dans les trois bougies, la cassure est **fausse** selon la règle écrite. Si elles avaient clôturé à 1,0949 puis 1,0956, elle aurait été **confirmée**.
:::

::: callout mistake "Erreur fréquente"
Changer de lecture en cours de route : appeler « cassure » le mouvement tant qu'il monte, puis « fausse cassure » quand il redescend. Une lecture qui s'adapte à chaque bougie ne décrit plus rien.
:::

::: callout recap
- Fausse cassure : une clôture au-delà du niveau, puis une clôture revenue en deçà dans un délai écrit à l'avance.
- Au moment de la cassure, les deux suites sont indiscernables.
- Le biais rétrospectif fait paraître évident ce qui ne l'était pas.
- Écrire à l'avance ce qui confirme, ce qui invalide et ce que l'on fait ; mesurer ces règles sur un échantillon.
:::
