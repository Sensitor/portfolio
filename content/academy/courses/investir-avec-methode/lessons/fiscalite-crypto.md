+++
id = "fiscalite-crypto"
title = "La fiscalité française des actifs numériques"
summary = "En France, un particulier n'est imposé qu'au moment où il convertit ses cryptoactifs en euros ou s'en sert pour payer. La plus-value se calcule sur l'ensemble du portefeuille, avec une formule propre aux actifs numériques. Les événements imposables, le calcul, et les déclarations à faire."
duration_minutes = 16
access = "member"
status = "published"
version = 1
updated = 2026-10-20
objectives = [
  "Distinguer les opérations imposables de celles qui ne le sont pas.",
  "Calculer une plus-value selon la formule du portefeuille global.",
  "Connaître les déclarations à remplir, dont celle des comptes détenus à l'étranger.",
]
quiz = "check-fiscalite-crypto"
resources = ["fiche-investir"]
sources = [
  "Code général des impôts, article 150 VH bis : plus-values de cession d'actifs numériques réalisées par les particuliers.",
  "Code général des impôts, article 1649 bis C : déclaration des comptes d'actifs numériques ouverts à l'étranger (formulaire 3916-bis).",
  "Direction générale des Finances publiques, formulaire 2086 et notice : déclaration des plus ou moins-values sur actifs numériques.",
]
+++

## Ce qui est imposable

Pour un particulier qui investit de façon occasionnelle, le régime est celui de l'article 150 VH bis du Code général des impôts.

| Opération | Imposable ? |
|---|---|
| Vendre des cryptoactifs contre des euros | oui |
| Payer un bien ou un service en cryptoactifs | oui |
| Échanger un cryptoactif contre un autre, y compris un stablecoin | non, l'impôt est reporté à la conversion en euros |
| Transférer entre ses propres portefeuilles | non |
| Total des cessions de l'année inférieur ou égal à 305 € | exonéré |

L'impôt porte sur la **plus-value**, et seulement au moment de la conversion en monnaie ou du paiement.

::: callout warning "Le taux de l'année"
Le gain est soumis par défaut au prélèvement forfaitaire unique, qui additionne une part d'impôt sur le revenu et les prélèvements sociaux ; on peut opter pour le barème progressif. Ce taux a changé ces dernières années : il était de 30 % jusqu'aux gains de 2024, et plusieurs sources indiquent 31,4 % depuis la hausse des prélèvements sociaux votée pour 2026. **Vérifiez le taux de l'année sur impots.gouv.fr** avant tout calcul. Les exercices utilisent 31,4 % comme hypothèse.
:::

## La formule du portefeuille global

La plus-value ne se calcule pas jeton par jeton, mais sur l'ensemble du portefeuille d'actifs numériques. On retire du prix de cession la part du **prix total d'acquisition** que représente la vente, mesurée sur la **valeur globale du portefeuille** juste avant la vente.

::: formula
\text{Plus-value} = \text{prix de cession} - \text{prix total d'acquisition} \times \frac{\text{prix de cession}}{\text{valeur globale du portefeuille}}
:::

Après la vente, le prix total d'acquisition est diminué de la fraction utilisée : il sert de base aux ventes suivantes.

## À vous

::: exercise plus-value-150vh
:::

## Les déclarations

- **Formulaire 2086** : chaque cession imposable de l'année, avec le calcul de la plus-value.
- **Déclaration de revenus** : le total des plus et moins-values, reporté sur la déclaration complémentaire.
- **Formulaire 3916-bis** : chaque compte d'actifs numériques ouvert auprès d'une plateforme établie à l'étranger, même sans cession, même inactif. L'oubli est sanctionné par une amende par compte.

::: callout note "Ce que ce cours ne couvre pas"
Le minage, le staking, les opérations fréquentes assimilables à une activité professionnelle, l'impôt sur la fortune immobilière ou les successions suivent d'autres règles. Pour une situation précise, un conseiller fiscal ou le service des impôts répond ; ce cours n'est pas un conseil fiscal.
:::

::: callout mistake "Erreur fréquente"
Calculer la plus-value comme le prix de vente moins le prix d'achat du jeton vendu. La règle française raisonne sur tout le portefeuille : le résultat est différent, et c'est lui que l'administration attend.
:::

::: callout recap
- Imposable : la conversion en euros et le paiement ; pas l'échange entre cryptoactifs.
- Plus-value = cession − prix total d'acquisition × cession ÷ valeur globale du portefeuille.
- Formulaires 2086 et 3916-bis ; le taux de l'année se vérifie sur impots.gouv.fr.
:::
