+++
id = "blocs-et-chaine"
title = "Les blocs et la chaîne"
summary = "Les transactions sont regroupées en blocs, et chaque bloc contient l'empreinte du précédent. Ce qu'est une empreinte, pourquoi modifier une transaction ancienne casse toute la suite, et ce que contient l'en-tête d'un bloc."
duration_minutes = 14
access = "member"
status = "published"
version = 1
updated = 2026-10-19
objectives = [
  "Expliquer ce qu'est une fonction de hachage et ses propriétés utiles.",
  "Décrire comment les blocs sont chaînés par leurs empreintes.",
  "Expliquer pourquoi modifier un bloc ancien oblige à refaire tous les suivants.",
]
quiz = "check-blocs-et-chaine"
resources = ["fiche-bitcoin-fonctionnement"]
sources = [
  "Nakamoto, S. (2008). « Bitcoin: A Peer-to-Peer Electronic Cash System », sections 3, 4 et 7.",
  "National Institute of Standards and Technology (2015). FIPS 180-4, Secure Hash Standard : définition de SHA-256.",
  "Haber, S. et Stornetta, W. S. (1991). « How to Time-Stamp a Digital Document ». Journal of Cryptology, 3(2), 99-111.",
  "Merkle, R. C. (1980). « Protocols for Public Key Cryptosystems ». Proceedings of the 1980 IEEE Symposium on Security and Privacy, 122-134.",
]
+++

## Une empreinte

Une **fonction de hachage** transforme n'importe quelle donnée, une phrase ou un fichier entier, en une **empreinte** de taille fixe. Bitcoin utilise SHA-256, qui produit 256 bits, écrits en 64 caractères hexadécimaux. Trois propriétés la rendent utile :

- **La même donnée donne toujours la même empreinte**, et chacun peut la recalculer.
- **Un changement minime change tout** : modifier une seule lettre donne une empreinte sans rapport avec la précédente.
- **On ne peut pas revenir en arrière** : connaître l'empreinte ne permet pas de retrouver la donnée, ni d'en fabriquer une autre qui donne la même.

La démonstration de la leçon suivante permet de le vérifier sur vos propres phrases.

## La chaîne

Un **bloc** regroupe quelques milliers de transactions. Son **en-tête** contient notamment :

| Champ | Rôle |
|---|---|
| empreinte du bloc précédent | relie le bloc à toute l'histoire qui le précède |
| racine de Merkle | une empreinte unique qui résume toutes les transactions du bloc |
| horodatage | l'heure approximative du bloc |
| cible | le niveau de difficulté à atteindre |
| nonce | le nombre que les mineurs font varier, objet de la leçon suivante |

::: figure chaine-blocs.svg
Trois blocs chaînés par leurs empreintes. Modifier une transaction du bloc 2 change son empreinte : le bloc 3, qui contenait l'ancienne, ne s'y rattache plus. Schéma original.
:::

Comme chaque bloc contient l'empreinte du précédent, l'empreinte du dernier bloc dépend de **toute** l'histoire. Modifier une transaction ancienne change l'empreinte de son bloc, donc celle de tous les blocs suivants : la falsification se voit immédiatement. Cette idée de chaîne horodatée vient des travaux de Haber et Stornetta (1991), que le livre blanc cite.

::: callout definition "Racine de Merkle"
Une empreinte calculée en hachant les transactions deux à deux, puis les résultats deux à deux, jusqu'à une seule. Elle permet de prouver qu'une transaction figure dans un bloc sans télécharger tout le bloc.
:::

::: callout note "Une chaîne ne suffit pas"
Le chaînage rend la falsification visible, pas impossible : un fraudeur pourrait recalculer toutes les empreintes suivantes en quelques secondes. Ce qui l'en empêche, c'est la preuve de travail, qui rend chaque bloc coûteux à produire.
:::

::: callout mistake "Erreur fréquente"
Croire que l'empreinte chiffre les données. Une empreinte ne cache rien et ne se déchiffre pas : les transactions de Bitcoin sont publiques, l'empreinte sert seulement à les sceller.
:::

::: callout recap
- SHA-256 donne une empreinte fixe, qui change entièrement au moindre changement de la donnée.
- Chaque bloc contient l'empreinte du précédent : modifier le passé change toute la suite.
- Le chaînage rend la falsification visible ; la preuve de travail la rend coûteuse.
:::
