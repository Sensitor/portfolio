+++
id = "ote-retracements"
title = "Retracements et zone OTE"
summary = "Mesurer la profondeur d'un retour en pourcentage de la jambe précédente, calculer la zone OTE de 62 à 79 %, et ne pas prêter aux ratios de Fibonacci des pouvoirs qu'ils n'ont pas."
duration_minutes = 16
access = "member"
status = "published"
version = 1
objectives = [
  "Calculer un niveau de retracement sur une jambe haussière ou baissière.",
  "Calculer les bornes de la zone OTE.",
  "Présenter les ratios comme une convention de mesure, pas comme une prédiction.",
]
quiz = "check-ote"
resources = ["fiche-zones"]
+++

## Mesurer un retour

Après une impulsion, le prix revient souvent en arrière avant de repartir. Pour parler de la **profondeur** de ce retour indépendamment de l'instrument, on l'exprime en **pourcentage de la jambe** : 50 % signifie que le prix a rendu la moitié du mouvement.

Une **jambe** va d'un swing à l'autre : du creux de départ au sommet pour une jambe haussière, du sommet au creux pour une jambe baissière.

::: formula
\text{Niveau}(r) = \text{Fin de la jambe} - r \times (\text{Fin} - \text{Départ})
:::

La même formule sert dans les deux sens : pour une jambe baissière, la fin est sous le départ et le niveau se trouve au-dessus de la fin.

## La zone OTE

Les méthodes ICT appellent **Optimal Trade Entry** (OTE) la bande comprise entre **62 % et 79 %** de retracement, avec **70,5 %** pour milieu. Ces valeurs sont proches des ratios de Fibonacci (61,8 % et 78,6 %), arrondis.

::: figure ote.svg
Une jambe de 2 380 à 2 420 puis un retour. Les niveaux de 0, 50, 62, 70,5, 79 et 100 % sont tracés depuis le sommet ; la bande de 62 à 79 % est la zone OTE. Schéma original.
:::

::: callout example "Exemple pédagogique"
Jambe haussière sur EURUSD de **1,0800** à **1,0900**, soit 100 pips. Le niveau de 62 % est à 1,0900 − 0,62 × 0,0100 = **1,0838** ; celui de 79 % à **1,0821**. La zone OTE va donc de 1,0821 à 1,0838, et son milieu de 70,5 % est à 1,08295.
:::

::: callout method "Une convention de mesure"
Il n'existe aucune raison démontrée pour que le prix respecte 61,8 % plutôt que 60 % ou 65 %. Ces ratios sont utiles parce qu'ils donnent à chacun la même règle de mesure, et parce qu'une zone écrite à l'avance évite d'entrer n'importe où. Sur un échantillon, la question à se poser n'est pas « le prix a-t-il touché 62 % ? » mais « mes entrées dans cette zone ont-elles une espérance positive, coûts compris ? ».
:::

## À vous

::: exercise ote-calcul
:::

::: callout mistake "Erreur fréquente"
Tracer la jambe depuis des points choisis pour que le prix tombe pile sur un niveau. Le départ et la fin sont des swings définis par la règle du parcours 2, pas les points qui arrangent le graphique.
:::

::: callout recap
- Un retracement s'exprime en pourcentage de la jambe, mesuré depuis sa fin.
- La zone OTE va de 62 à 79 % de retracement, avec 70,5 % pour milieu.
- Pour une jambe baissière, la zone se trouve au-dessus du creux.
- Les ratios sont une convention de mesure ; leur intérêt se mesure sur un échantillon.
:::
