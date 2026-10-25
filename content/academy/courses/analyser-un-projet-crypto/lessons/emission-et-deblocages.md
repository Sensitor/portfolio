+++
id = "emission-et-deblocages"
title = "Émission, déblocages et dilution"
summary = "Les jetons d'un projet arrivent par vagues : déblocages pour l'équipe et les investisseurs, émissions pour les utilisateurs, récompenses de staking. Chaque vague dilue les détenteurs. Lire un calendrier d'émission, et calculer ce qu'il faut de demande en plus pour que le prix tienne."
duration_minutes = 14
access = "member"
status = "published"
version = 1
updated = 2026-10-20
objectives = [
  "Lire un calendrier d'émission : allocation, période de blocage, déblocage progressif.",
  "Calculer la baisse de prix qui garde la capitalisation constante après un déblocage.",
  "Mesurer la dilution d'un détenteur qui ne participe pas au staking.",
]
quiz = "check-emission-et-deblocages"
resources = ["fiche-analyse-crypto"]
sources = [
  "Banque des règlements internationaux (2023). « The crypto ecosystem: key elements and risks », rapport au G20, juillet 2023.",
  "Règlement (UE) 2023/1114 sur les marchés de crypto-actifs (MiCA), titre II : livre blanc obligatoire décrivant les droits attachés au jeton et sa répartition.",
]
+++

## Qui reçoit les jetons, et quand

Le document d'un projet, son **livre blanc**, décrit la répartition des jetons. Dans l'Union européenne, le règlement MiCA en impose un pour la plupart des offres au public. On y lit généralement :

| Part | Bénéficiaires | Ce qu'il faut regarder |
|---|---|---|
| **Équipe et conseillers** | les fondateurs | la durée de blocage et le rythme de déblocage |
| **Investisseurs** | les financeurs des premiers tours, souvent à prix réduit | la date de leurs déblocages |
| **Trésorerie, fondation** | le projet lui-même | qui décide de son usage |
| **Communauté, incitations** | les utilisateurs, distribués dans le temps | le rythme d'émission |

Un **blocage** empêche de vendre pendant une période, souvent d'un an ; ensuite, un **déblocage progressif** libère les jetons mois après mois. Un déblocage important augmente d'un coup l'offre en circulation.

::: chart deblocages-exemple
Un jeton construit pour la leçon : 20 % de l'offre en circulation au lancement, 100 % au bout de quatre ans. À partir du treizième mois, la fin du blocage de l'équipe accélère l'arrivée de nouveaux jetons. Exemple synthétique.
:::

## La dilution, chiffrée

Si l'offre en circulation augmente sans que la demande suive, le prix doit baisser pour que la capitalisation reste la même.

::: formula
\text{Prix inchangé en valeur} = \text{prix} \times \frac{\text{offre avant}}{\text{offre après}}
:::

Le **staking** produit le même effet, de façon plus discrète : les récompenses sont de nouveaux jetons. Celui qui ne participe pas voit sa part de l'offre diminuer au rythme de l'émission.

::: chart dilution-staking
À 8 % d'émission par an, celui qui ne stake pas conserve 46 % de sa part de départ au bout de dix ans. Calcul exact sur l'exemple de la leçon.
:::

## À vous

::: exercise deblocage-jetons
:::

::: callout note "Les jetons qui disparaissent"
Certains projets détruisent une partie des jetons, par exemple avec une partie des frais : c'est un **burn**, l'inverse de l'émission. Ce qui compte est le solde net : jetons créés moins jetons détruits.
:::

::: callout mistake "Erreur fréquente"
Prendre un rendement de staking de 8 % pour un gain. Si l'offre croît aussi de 8 % par an, le détenteur qui stake garde seulement sa part ; celui qui ne stake pas perd environ 7 % de la sienne chaque année.
:::

::: callout recap
- Équipe, investisseurs, trésorerie, communauté : chaque part a son calendrier de déblocage.
- Pour une capitalisation constante, prix × offre avant ÷ offre après.
- Le staking dilue ceux qui n'y participent pas ; seul le solde net d'émission compte.
:::
