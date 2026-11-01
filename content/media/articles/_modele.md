+++
# Modèle d'article. Un fichier dont le nom commence par « _ » n'est jamais publié :
# copiez-le sous un nom en minuscules et tirets (par exemple « lire-un-spread.md »).
title = "Titre de l'article"
summary = "Une ou deux phrases, 200 caractères au plus : c'est la description que montrent les moteurs de recherche."
date = 2026-11-01            # date de publication
updated = 2026-11-01         # date de la dernière relecture (obligatoire pour publier)
universe = "trading"         # « trading » ou « crypto »
author = "Sensitor"
status = "draft"             # « draft » tant que l'article n'est pas prêt, puis « published »
tags = ["méthode"]
sources = [
  "Nom de la source, titre du document, date de consultation",
]
+++

Le corps de l'article est en Markdown, comme une leçon : titres « ## », listes,
**gras**, *italique*, tableaux et liens [vers une page](https://exemple.fr).

Chaque chiffre vient d'une source citée plus haut, ou d'un calcul que le texte
explique. Un exemple construit le dit.

::: callout note "À retenir"
Un encadré, comme dans les leçons. L'opinion du fondateur va dans un
« callout opinion », une question ouverte dans un « callout debate ».
:::
