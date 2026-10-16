+++
id = "biais-recence"
title = "Le biais de récence"
summary = "Les derniers trades pèsent plus lourd dans la tête que les cent précédents. Ce que vaut vraiment un taux de réussite mesuré sur cinq trades, et comment s'en protéger."
duration_minutes = 13
access = "member"
status = "published"
version = 1
objectives = [
  "Définir le biais de récence et le reconnaître dans ses propres réactions.",
  "Comparer l'incertitude d'un taux de réussite mesuré sur 5 et sur 100 trades.",
  "Fixer à l'avance la taille d'échantillon qui autorise un changement de règle.",
]
quiz = "check-recence"
resources = ["routine-de-seance"]
+++

## Ce que l'on appelle biais de récence

Le **biais de récence** consiste à accorder plus de poids aux événements les plus récents qu'à ceux qui les précèdent, simplement parce qu'ils sont frais en mémoire. En trading, il prend deux formes opposées :

- après quelques gains, la méthode paraît infaillible, et l'on augmente la taille ;
- après quelques pertes, elle paraît cassée, et l'on change de règles.

Dans les deux cas, cinq trades décident de ce que cent trades auraient dû décider.

## Ce que disent cinq trades

Le parcours 5 a introduit l'**intervalle de confiance** d'un taux de réussite. Appliqué aux derniers trades, il montre à quel point ils renseignent peu.

| Mesure | Taux observé | Intervalle à 95 % |
|---|---|---|
| 4 gains sur les 5 derniers trades | 80 % | de 38 % à 96 % |
| 2 gains sur les 5 derniers trades | 40 % | de 12 % à 77 % |
| 52 gains sur 100 trades | 52 % | de 42 % à 62 % |

Quatre gains sur cinq sont compatibles avec un vrai taux de réussite de 40 %. Deux sur cinq le sont avec un vrai taux de 70 %. Les deux séries peuvent venir **de la même méthode**.

::: callout example "Exemple pédagogique"
Une trader suit la même méthode depuis 100 trades, à 52 % de réussite. Ses cinq derniers trades sont quatre gains. Elle envisage de passer de 0,5 % à 1,5 % de risque. Ce que les données disent : son taux de réussite se situe probablement entre 42 % et 62 %, exactement comme avant les quatre gains. Rien n'a changé, sinon son impression.
:::

## Se protéger

La parade la plus simple est d'écrire **avant** la règle qui autorise un changement :

- la taille de risque ne change qu'après une revue sur au moins 50 ou 100 trades ;
- une règle ne se modifie qu'après une revue écrite, jamais pendant la séance ;
- les statistiques se lisent sur l'ensemble de l'échantillon, pas sur la semaine.

::: callout method "Regarder le bon chiffre"
Votre journal de trading peut afficher le taux de réussite des 5 derniers trades ou celui des 200 derniers. Le premier est le plus visible et le moins informatif. Le second, accompagné de sa taille d'échantillon, est celui qui permet de décider.
:::

::: callout mistake "Erreur fréquente"
Augmenter la taille après une série de gains. C'est précisément quand le compte a le plus progressé, et quand l'impression de maîtrise est la plus forte, qu'une série de pertes normale fait le plus de dégâts.
:::

::: callout recap
- Le biais de récence donne aux derniers trades un poids qu'ils n'ont pas.
- Sur cinq trades, un taux de réussite est compatible avec presque n'importe quelle méthode.
- Une taille d'échantillon minimale, écrite à l'avance, décide quand changer de règle.
:::
