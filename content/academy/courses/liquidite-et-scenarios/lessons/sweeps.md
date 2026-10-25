+++
id = "sweeps"
title = "Le sweep : dépasser un niveau puis revenir"
summary = "Le prix franchit un niveau visible par une mèche, déclenche les ordres qui s'y trouvaient, puis clôture de retour en deçà. Le reconnaître en clôture, et savoir ce qu'il ne promet pas."
duration_minutes = 15
access = "member"
status = "published"
version = 1
objectives = [
  "Reconnaître un sweep selon la convention de clôture.",
  "Le distinguer d'une cassure de structure.",
  "Énoncer ce qu'un sweep rend plausible et ce qu'il ne prouve pas.",
]
quiz = "check-sweeps"
+++

## La définition

Le parcours 2 a qualifié de **tentative rejetée** une bougie dont la mèche dépasse un niveau mais dont la clôture revient en deçà. Lorsque ce niveau est un sommet ou un creux visible, et qu'on y suppose des ordres accumulés, les méthodes fondées sur la liquidité parlent de **sweep** (balayage) ou de **prise de liquidité**.

::: callout definition "Sweep, convention de ce parcours"
Un **sweep** au-dessus d'un niveau de sommets est une bougie dont le **plus haut dépasse** le niveau et dont la **clôture revient au niveau ou en dessous**. Sous un niveau de creux, c'est une bougie dont le plus bas passe en dessous et dont la clôture revient au niveau ou au-dessus.
:::

::: figure sweep-cassure.svg
Le même dépassement du niveau, deux clôtures différentes : à gauche, la mèche revient sous le niveau (sweep) ; à droite, la clôture se fait au-delà et la bougie suivante tient (cassure). Schéma original.
:::

## Ce qu'un sweep rend plausible

Selon l'hypothèse de la leçon 1, la mèche a déclenché des ordres stops au-delà du niveau. Si le prix revient aussitôt, c'est que ces ordres ont été absorbés sans entraîner de continuation : des vendeurs ont profité des achats déclenchés pour vendre. Le scénario qui en découle est un **retour dans le range**, voire un mouvement vers l'autre côté.

::: callout example "Exemple pédagogique"
Equal highs sur EURUSD à 1,0944. Une bougie H1 monte à 1,0951 puis clôture à 1,0938. Le plus haut a dépassé le niveau de 7 pips, la clôture est revenue 6 pips en dessous : **sweep** selon la convention. Une bougie qui monterait à 1,0951 et clôturerait à 1,0947 serait au contraire une **cassure**.
:::

## Ce qu'un sweep ne prouve pas

- Il ne prouve pas que des stops se trouvaient là : on ne les voit pas.
- Il ne garantit pas de retournement : le prix peut revenir au-delà du niveau quelques bougies plus tard.
- Il n'a de sens qu'à son unité de temps : un sweep en M5 peut n'être qu'une bougie ordinaire en H4.

::: callout method "Hypothèse de méthode"
Beaucoup de méthodes combinent un sweep sur une unité de temps avec un changement de structure sur une unité plus courte, dans le sens opposé au sweep. C'est une manière d'organiser la décision ; sa valeur se juge sur un échantillon suffisant, avec ses coûts, comme toute règle du parcours 5.
:::

::: callout mistake "Erreur fréquente"
Vendre dès que la mèche dépasse le niveau, avant la clôture. Tant que la bougie n'est pas close, rien ne distingue un sweep d'une cassure.
:::

::: callout recap
- Sweep : mèche au-delà d'un niveau visible, clôture revenue en deçà.
- Cassure : clôture au-delà. Avant la clôture, impossible de les distinguer.
- Un sweep rend plausible un retour dans le range ; il ne le garantit pas et ne prouve pas la présence de stops.
- Un sweep appartient à son unité de temps.
:::
