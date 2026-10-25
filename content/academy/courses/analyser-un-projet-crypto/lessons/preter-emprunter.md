+++
id = "preter-emprunter"
title = "Prêter et emprunter sans banque"
summary = "Sur un protocole de prêt, on emprunte en déposant une garantie supérieure à la somme empruntée. Si la garantie perd de la valeur, la position est liquidée automatiquement. Le ratio prêt-garantie, le facteur de santé et le prix de liquidation, calculés."
duration_minutes = 15
access = "member"
status = "published"
version = 1
updated = 2026-10-20
objectives = [
  "Expliquer le fonctionnement d'un prêt surcollatéralisé.",
  "Calculer le ratio prêt-garantie, le facteur de santé et le prix de liquidation.",
  "Décrire ce qui se passe lors d'une liquidation, et comment s'en protéger.",
]
quiz = "check-preter-emprunter"
resources = ["fiche-analyse-crypto"]
sources = [
  "Banque des règlements internationaux (2023). « The crypto ecosystem: key elements and risks », rapport au G20, juillet 2023 : prêts surcollatéralisés et liquidations automatiques.",
  "Documentation des principaux protocoles de prêt : seuil de liquidation et facteur de santé.",
]
+++

## Un prêt garanti par plus que son montant

Un protocole de prêt ne connaît pas ses emprunteurs : il ne peut pas vérifier leurs revenus. Il demande donc une **garantie** supérieure à la somme prêtée, déposée dans le contrat. C'est un prêt **surcollatéralisé**.

::: formula
\text{Ratio prêt-garantie} = \frac{\text{dette}}{\text{valeur de la garantie}}
:::

Chaque garantie a un **seuil de liquidation**, par exemple 80 % : tant que la dette reste sous 80 % de la valeur de la garantie, tout va bien.

::: formula
\text{Facteur de santé} = \frac{\text{valeur de la garantie} \times \text{seuil de liquidation}}{\text{dette}}
:::

Au-dessus de 1, la position est saine. À 1, n'importe qui peut la **liquider** : rembourser une partie de la dette et prendre une partie de la garantie, avec une décote. La liquidation est automatique, sans délai ni appel de marge.

## Le prix de liquidation

::: formula
\text{Prix de liquidation} = \frac{\text{dette}}{\text{unités de garantie} \times \text{seuil de liquidation}}
:::

::: chart liquidation-par-ratio
Avec un seuil de liquidation de 80 % : à 25 % de ratio prêt-garantie, la garantie peut perdre près de 69 % avant liquidation ; à 75 %, à peine plus de 6 %. Calcul exact.
:::

## À vous

::: exercise pret-liquidation
:::

::: callout warning "Les liquidations en cascade"
Quand les prix chutent, de nombreuses positions atteignent leur seuil en même temps. Les liquidations vendent des garanties, ce qui fait baisser les prix, ce qui déclenche d'autres liquidations. Ces cascades expliquent une partie des chutes les plus brutales du marché.
:::

::: callout note "Se protéger"
- Emprunter peu par rapport à sa garantie : un ratio de 30 % laisse bien plus de marge qu'un ratio de 70 %.
- Surveiller le facteur de santé, et rembourser ou ajouter de la garantie avant qu'il approche 1.
- Se rappeler que la liquidation intervient au prix du marché, à la minute, même la nuit.
:::

::: callout mistake "Erreur fréquente"
Emprunter un stablecoin contre de l'ether pour racheter de l'ether. On augmente son exposition et on rapproche son prix de liquidation : c'est un effet de levier, avec ses risques.
:::

::: callout recap
- Prêt surcollatéralisé : la garantie dépasse la dette.
- Facteur de santé = garantie × seuil ÷ dette ; à 1, la liquidation est automatique.
- Prix de liquidation = dette ÷ (unités de garantie × seuil).
:::
