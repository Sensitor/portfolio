+++
id = "revenus-et-incitations"
title = "Revenus réels et incitations"
summary = "Un protocole peut afficher une activité intense parce qu'il paie ses utilisateurs pour venir. Distinguer les frais que paient vraiment les utilisateurs, la part qui revient aux détenteurs du jeton, et les émissions qui financent l'activité : c'est la différence entre un revenu et une subvention."
duration_minutes = 14
access = "member"
status = "published"
version = 1
updated = 2026-10-20
objectives = [
  "Distinguer les frais payés par les utilisateurs des revenus qui reviennent aux détenteurs du jeton.",
  "Calculer le revenu net d'un protocole, incitations déduites.",
  "Rapporter la capitalisation aux revenus, et dire ce que le rapport signifie.",
]
quiz = "check-revenus-et-incitations"
resources = ["fiche-analyse-crypto"]
sources = [
  "Banque des règlements internationaux (2023). « The crypto ecosystem: key elements and risks », rapport au G20, juillet 2023.",
  "Cong, L. W., Li, X., Tang, K. et Yang, Y. (2023). « Crypto Wash Trading ». Management Science, 69(11), 6427-6454.",
]
+++

## Ce qui peut donner une valeur à un jeton

Un jeton n'a de valeur que si quelqu'un veut le détenir. Les raisons possibles se rangent en quelques familles :

| Source | Exemple | La question à poser |
|---|---|---|
| **Frais** | une plateforme d'échange prélève une commission sur chaque échange | les utilisateurs paient-ils vraiment, et combien ? |
| **Partage des frais** | une partie des frais revient aux détenteurs, ou sert à racheter et détruire des jetons | quelle part revient au jeton, et qui le décide ? |
| **Usage obligatoire** | il faut le jeton pour payer les frais du réseau | existe-t-il une demande hors spéculation ? |
| **Gouvernance** | le jeton donne un droit de vote | ce vote décide-t-il de quelque chose qui a de la valeur ? |

## Revenu ou subvention

Beaucoup de protocoles distribuent des jetons pour attirer des utilisateurs : ce sont des **incitations**. Elles gonflent l'activité affichée, mais elles coûtent : ce sont de nouveaux jetons, qui diluent les détenteurs.

::: formula
\text{Revenu net des détenteurs} = \text{frais qui leur reviennent} - \text{valeur des incitations émises}
:::

Un revenu net négatif signifie que le protocole paie plus pour son activité qu'elle ne lui rapporte. Cela peut se justifier un temps, pour démarrer ; cela ne peut pas durer.

## Rapporter la valeur aux revenus

Le rapport entre la capitalisation et les revenus annuels qui reviennent aux détenteurs se lit comme un nombre d'années : à revenu constant, combien de temps pour « rembourser » le prix payé. Il n'a de sens que si les revenus sont réels, durables, et effectivement captés par le jeton.

## À vous

::: exercise revenus-protocole
:::

::: callout warning "Une activité qui peut être fabriquée"
Des volumes d'échange peuvent être gonflés par des transactions fictives entre comptes liés. Une étude publiée en 2023 dans *Management Science* (Cong et ses coauteurs) estimait que les plateformes non régulées faisaient l'objet d'échanges fictifs à grande échelle. Une activité affichée ne vaut que si l'on peut en vérifier la source.
:::

::: callout mistake "Erreur fréquente"
Confondre les frais payés par les utilisateurs et le revenu du jeton. Des frais élevés qui reviennent tous aux fournisseurs de liquidité, et rien aux détenteurs, ne donnent aucun revenu au jeton.
:::

::: callout recap
- Frais, partage des frais, usage obligatoire, gouvernance : quatre sources de valeur possibles.
- Revenu net = frais qui reviennent aux détenteurs − incitations émises.
- Capitalisation ÷ revenus : un nombre d'années, qui n'a de sens que pour des revenus réels et durables.
:::
