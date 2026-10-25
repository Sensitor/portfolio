+++
id = "pouvoir-achat"
title = "Le pouvoir d'achat sur des décennies"
summary = "Une inflation modeste paraît anodine sur un an et considérable sur trente. Ce que sont devenus 100 € de 1996 en France, combien de temps il faut pour diviser le pouvoir d'achat par deux, et pourquoi l'épargne en monnaie pose une question de long terme."
duration_minutes = 14
access = "member"
status = "published"
version = 1
updated = 2026-10-17
objectives = [
  "Calculer une inflation cumulée et la valeur réelle d'une somme.",
  "Estimer le temps nécessaire pour diviser le pouvoir d'achat par deux.",
  "Formuler la question de l'épargne de long terme face à l'inflation.",
]
quiz = "check-pouvoir-achat"
resources = ["fiche-inflation"]
sources = [
  "Eurostat, jeu de données prc_hicp_minr (IPCH, indice base 2025 = 100, France), consulté le 17 octobre 2026.",
  "Banque centrale européenne, stratégie de politique monétaire, 2021 : objectif d'inflation de 2 % à moyen terme.",
]
+++

## Les intérêts composés, à l'envers

L'inflation se **compose** comme des intérêts : chaque année, les prix montent sur une base déjà plus haute. Deux pour cent par an ne font pas 60 % en trente ans, mais **81 %**.

::: formula
\text{Valeur réelle} = \frac{\text{Somme}}{(1 + \text{inflation})^{\text{années}}}
:::

## Ce que sont devenus 100 € de 1996

::: chart pouvoir-achat-100-euros
Le pouvoir d'achat, en euros de janvier 1996, de 100 € conservés en billets en France, chaque mois de janvier depuis. Calculé à partir de l'indice des prix d'Eurostat.
:::

Entre janvier 1996 et janvier 2026, l'indice des prix français a progressé de **67,2 %**. Les 100 € gardés en billets n'achètent plus que ce que **59,82 €** achetaient en 1996. Sur trente ans, cela représente **1,73 %** d'inflation par an en moyenne, en dessous de l'objectif de 2 % de la BCE, et pourtant plus de 40 % de pouvoir d'achat perdu.

## Le temps de division par deux

::: formula
\text{Années pour diviser le pouvoir d'achat par deux} = \frac{\ln 2}{\ln (1 + \text{inflation})}
:::

| Inflation annuelle | Pouvoir d'achat divisé par deux en |
|---|---|
| 2 % | 35 ans |
| 3 % | 23,4 ans |
| 5 % | 14,2 ans |
| 10 % | 7,3 ans |

## À vous

::: exercise pouvoir-achat-long
:::

## La question de l'épargne

L'inflation ne touche pas tout le monde de la même manière. Elle allège la dette de ceux qui doivent à taux fixe, et érode l'épargne de ceux qui gardent leur argent en billets ou sur des comptes peu rémunérés. Sur un an, la différence est faible ; sur une carrière, elle est considérable.

::: callout warning "Une perte nominale et une perte réelle"
Un compte courant ne perd jamais en euros : 1 000 € restent 1 000 €. C'est une protection contre la perte **nominale**. Il perd en revanche en **réel** chaque année où les prix montent. Un placement qui varie peut perdre en euros certaines années et protéger mieux du réel sur longue période, ou l'inverse. Le cours suivant, « Inflation et patrimoine », compare ces deux risques avec un simulateur.
:::

C'est le point de départ de la thèse qui fera l'objet du parcours Bitcoin : une monnaie dont l'émission est programmée et limitée peut-elle mieux conserver le pouvoir d'achat sur longue période ? Le parcours examinera les arguments, mais aussi les objections : volatilité, historique court, et le fait qu'une offre limitée ne garantit pas une demande stable.

::: callout mistake "Erreur fréquente"
Additionner les taux d'inflation annuels. Cinq années à 4 % ne font pas 20 % mais 21,7 % : les hausses se composent.
:::

::: callout recap
- L'inflation se compose : 2 % par an font 81 % en trente ans.
- 100 € de janvier 1996 valaient 59,82 € de pouvoir d'achat en janvier 2026, en France.
- Années pour diviser le pouvoir d'achat par deux = ln 2 ÷ ln(1 + inflation).
- Garder sa monnaie protège de la perte nominale, pas de la perte réelle.
:::
