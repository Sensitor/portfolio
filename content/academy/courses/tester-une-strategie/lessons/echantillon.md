+++
id = "echantillon"
title = "Ce que vaut un résultat mesuré"
summary = "Une espérance de +0,20R sur 40 trades et la même sur 400 trades ne disent pas la même chose. L'intervalle autour d'une moyenne, et le nombre de trades qu'il faut pour conclure."
duration_minutes = 17
access = "member"
status = "published"
version = 1
objectives = [
  "Calculer l'erreur type et l'intervalle à 95 % d'une espérance mesurée.",
  "Dire si un résultat permet de conclure à un avantage.",
  "Estimer le nombre de trades nécessaire pour une précision donnée.",
]
quiz = "check-echantillon-backtest"
resources = ["fiche-backtest"]
+++

## Une moyenne a une marge d'erreur

Le parcours 5 a montré qu'un taux de réussite mesuré est une estimation, entourée d'un intervalle. Il en va de même pour l'**espérance** d'une série : la moyenne des résultats en R. Rejouée sur une autre période, la même stratégie donnerait une autre moyenne. La question est de savoir de combien elle pourrait varier.

La réponse dépend de deux choses : la **dispersion** des résultats, mesurée par leur écart type, et le **nombre de trades**.

::: formula
\text{Erreur type} = \frac{\text{écart type des résultats}}{\sqrt{n}}
:::

::: formula
\text{Intervalle à 95 \%} \approx \text{espérance} \pm 1{,}96 \times \text{erreur type}
:::

L'approximation est raisonnable à partir de quelques dizaines de trades. En dessous, elle est trop optimiste : une raison de plus de ne pas conclure sur si peu.

## Le même résultat, quatre échantillons

::: figure intervalles.svg
Une espérance mesurée de +0,20R avec un écart type de 1,2R, sur 40, 100, 400 et 1 000 trades. Sur 40 et 100 trades, l'intervalle contient zéro : on ne peut pas exclure l'absence d'avantage. Calcul exact.
:::

::: callout definition "Conclure à un avantage"
Un backtest permet de parler d'un **avantage probable** quand la borne basse de l'intervalle de l'espérance **nette** reste au-dessus de zéro. Si l'intervalle contient zéro, le résultat est compatible avec une stratégie sans avantage, même si la moyenne mesurée est positive.
:::

Une espérance positive mesurée sur trop peu de trades n'est donc ni une bonne ni une mauvaise nouvelle : c'est une absence de réponse.

## À vous

::: exercise intervalle-esperance
:::

::: callout method "Pourquoi il faut autant de trades"
L'écart type d'une stratégie qui gagne 2R ou perd 1R tourne autour de 1,2 à 1,5R, bien plus que l'espérance que l'on cherche à mesurer, souvent 0,1 à 0,3R. Mesurer un petit écart au milieu d'une grande dispersion demande des centaines d'occurrences. C'est une propriété du problème, pas un défaut du backtest.
:::

::: callout mistake "Erreur fréquente"
Annoncer « +0,25R par trade » sans dire sur combien de trades. Un chiffre d'espérance sans taille d'échantillon ni intervalle ne permet de rien décider.
:::

::: callout recap
- Erreur type = écart type ÷ √n ; l'intervalle à 95 % vaut environ espérance ± 1,96 erreur type.
- Un avantage est probable quand la borne basse de l'espérance nette reste au-dessus de zéro.
- Diviser l'intervalle par deux demande quatre fois plus de trades.
:::
