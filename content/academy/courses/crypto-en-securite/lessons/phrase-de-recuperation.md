+++
id = "phrase-de-recuperation"
title = "Sauvegarder une phrase de récupération"
summary = "Douze ou vingt-quatre mots suffisent à reconstituer un portefeuille entier. Personne ne les devinera ; le risque est de les perdre ou de se les faire voler. Comment les noter, où les garder, et comment vérifier sa sauvegarde sans rien exposer."
duration_minutes = 14
access = "member"
status = "published"
version = 1
updated = 2026-10-19
objectives = [
  "Expliquer pourquoi une phrase de récupération ne peut pas être devinée.",
  "Sauvegarder une phrase correctement, et éviter les sauvegardes dangereuses.",
  "Prévoir la vérification de la sauvegarde et la transmission en cas de décès.",
]
quiz = "check-phrase-de-recuperation"
resources = ["fiche-crypto-securite"]
sources = [
  "Bitcoin Improvement Proposals : BIP 39 (liste de 2 048 mots, somme de contrôle, phrase secondaire facultative).",
  "Antonopoulos, A. M. et Harding, D. A. (2023). Mastering Bitcoin, 3e édition. Sebastopol : O'Reilly Media, chapitre sur la récupération des portefeuilles.",
]
+++

## Personne ne la devinera

Une phrase de récupération de la norme BIP 39 choisit ses mots dans une liste de **2 048**. Douze mots portent un secret de **128 bits** ; vingt-quatre mots, 256 bits. Une partie des mots sert de somme de contrôle, pour détecter une faute de frappe.

::: formula
2^{128} \approx 3{,}4 \times 10^{38} \text{ phrases possibles}
:::

À mille milliards d'essais par seconde, essayer toutes les phrases de douze mots prendrait environ 10¹⁹ ans, des centaines de millions de fois l'âge de l'univers. Le danger n'est donc jamais le hasard. Il est ailleurs : **la perte**, **le vol**, et **la ruse** de quelqu'un qui obtient la phrase de son propriétaire.

::: chart force-phrase
Le temps pour essayer toutes les phrases à mille milliards d'essais par seconde : environ 10¹⁹ ans pour 12 mots, plus de 10⁵⁷ ans pour 24. Échelle logarithmique. Calcul exact.
:::

## À vous

::: exercise securite-phrase
:::

## Noter et garder

::: callout method "Une sauvegarde correcte"
1. **Sur papier ou sur métal**, à la main, dans l'ordre, sans faute. Le métal résiste au feu et à l'eau.
2. **Jamais en numérique** : ni photo, ni capture d'écran, ni fichier, ni gestionnaire de notes, ni messagerie, ni envoi par courriel. Un appareil connecté peut être compromis.
3. **Deux exemplaires**, dans deux lieux sûrs différents, pour survivre à un incendie ou à un cambriolage.
4. **Vérifier la sauvegarde** avant d'y déposer une somme importante : restaurer le portefeuille à partir de la phrase sur un appareil réinitialisé, puis vérifier qu'on retrouve la même adresse.
5. **Prévoir la transmission** : une personne de confiance doit savoir que les fonds existent et comment les retrouver, sans détenir la phrase de son vivant si ce n'est pas voulu.
:::

::: callout definition "Phrase secondaire"
La norme BIP 39 permet d'ajouter une phrase secondaire, choisie par l'utilisateur, à la phrase de récupération. Les deux sont alors nécessaires. C'est une protection de plus contre le vol de la feuille, et un risque de plus d'oubli.
:::

::: callout warning "La règle qui ne souffre aucune exception"
Personne n'a besoin de votre phrase pour vous aider : ni un support technique, ni une plateforme, ni un formateur, ni un « service de récupération ». **Sensitor ne vous la demandera jamais**, et aucun exercice de l'Academy ne demande de connecter un vrai portefeuille. Quiconque la demande cherche à vous voler.
:::

::: callout mistake "Erreur fréquente"
Photographier sa phrase « en attendant ». La photo part dans une sauvegarde en ligne, et un compte piraté suffit à vider le portefeuille.
:::

::: callout recap
- 12 mots = 128 bits : impossible à deviner ; le risque est la perte, le vol ou la ruse.
- Papier ou métal, jamais en numérique, deux exemplaires, deux lieux.
- Vérifier la sauvegarde, prévoir la transmission, ne jamais communiquer la phrase.
:::
