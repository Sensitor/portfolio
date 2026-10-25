+++
id = "diversification"
title = "Diversifier : ce qu'on y gagne, ce qu'on n'y gagne pas"
summary = "Combiner des actifs qui ne bougent pas ensemble réduit la volatilité d'un portefeuille, parfois sans réduire beaucoup son rendement espéré. La formule, ce qu'elle montre pour une petite part d'actif très volatil, et pourquoi les corrélations ne sont pas une garantie."
duration_minutes = 16
access = "member"
status = "published"
version = 1
updated = 2026-10-17
objectives = [
  "Expliquer le rôle de la corrélation dans la diversification.",
  "Calculer la volatilité d'un portefeuille de deux actifs.",
  "Identifier les limites de la diversification, notamment en crise.",
]
quiz = "check-diversification"
resources = ["fiche-patrimoine"]
sources = [
  "Markowitz, H. (1952). « Portfolio Selection ». The Journal of Finance, 7(1), 77-91.",
  "Bodie, Z., Kane, A. et Marcus, A. J. Investments. McGraw-Hill, éditions successives, chapitre sur la diversification et le risque d'un portefeuille.",
]
+++

## L'idée de Markowitz

En 1952, Harry Markowitz montre qu'il ne suffit pas de regarder chaque placement isolément : ce qui compte, c'est la façon dont ils **bougent ensemble**. Deux actifs qui ne baissent pas en même temps se compensent en partie, et leur combinaison est moins volatile que leur moyenne.

::: callout definition "Corrélation"
La **corrélation** mesure à quel point deux actifs varient ensemble, de −1 (toujours en sens inverse) à +1 (toujours dans le même sens). Plus elle est faible, plus la diversification réduit la volatilité.
:::

## La volatilité de deux actifs

::: formula
\sigma_p = \sqrt{w_1^2 \sigma_1^2 + w_2^2 \sigma_2^2 + 2\, w_1 w_2\, \rho\, \sigma_1 \sigma_2}
:::

où *w* sont les parts, σ les volatilités et ρ la corrélation.

::: figure diversification-volatilite.svg
La volatilité d'un portefeuille selon la part d'un actif très volatil (60 %) à côté d'un actif à 15 %, pour deux corrélations. Avec une corrélation faible, 5 % de cet actif ne fait passer la volatilité totale que de 15 % à 15,1 %. Calcul exact.
:::

Ce calcul est à l'origine d'une idée répandue : une **petite part** d'un actif très volatil, mais peu corrélé au reste, change peu le risque d'ensemble, tout en lui donnant une exposition à son potentiel. C'est l'un des arguments avancés pour une petite allocation à Bitcoin dans un patrimoine diversifié.

## À vous

::: exercise diversification-deux-actifs
:::

## Ce que la diversification ne fait pas

::: callout warning "Les corrélations changent, surtout en crise"
Les volatilités et les corrélations sont mesurées sur le passé. Elles changent dans le temps, et elles ont tendance à **monter en période de crise**, quand beaucoup d'actifs baissent ensemble. La diversification réduit le risque propre à chaque actif ; elle ne protège pas d'un choc qui les touche tous.
:::

::: callout debate "Bitcoin diversifie-t-il ?"
Sur certaines périodes, Bitcoin a été peu corrélé aux actions ; sur d'autres, notamment lors des hausses de taux de 2022, il a baissé en même temps qu'elles. Ses partisans y voient un actif à part, à long terme ; ses critiques, un actif de risque qui suit l'appétit des investisseurs. Le parcours Bitcoin examinera ces données ; ce que ce cours retient, c'est que l'argument de diversification dépend d'une corrélation qui n'est pas fixe.
:::

::: callout recap
- Diversifier, c'est combiner des actifs qui ne bougent pas ensemble.
- Volatilité d'un portefeuille de deux actifs : √(w₁²σ₁² + w₂²σ₂² + 2w₁w₂ρσ₁σ₂).
- Une petite part d'un actif très volatil et peu corrélé change peu le risque d'ensemble.
- Les corrélations changent et montent en crise : la diversification réduit le risque, elle ne l'annule pas.
:::
