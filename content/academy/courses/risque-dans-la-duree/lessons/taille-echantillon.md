+++
id = "taille-echantillon"
title = "Combien de trades pour savoir ?"
summary = "Un taux de réussite mesuré sur vingt trades peut être très loin du vrai. L'intervalle de confiance donne la marge d'erreur, et elle est souvent plus large qu'on ne le croit."
duration_minutes = 14
access = "member"
status = "published"
version = 1
objectives = [
  "Expliquer pourquoi un petit échantillon trompe.",
  "Lire un intervalle de confiance sur un taux de réussite.",
  "Décider à partir de quand une conclusion devient raisonnable.",
]
quiz = "check-echantillon"
+++

## Le hasard des petites séries

Lancez une pièce équilibrée dix fois : obtenir sept piles n'a rien d'exceptionnel. Personne n'en conclurait que la pièce tombe sur pile 70 % du temps. Pourtant, un trader qui gagne sept trades sur dix conclut souvent qu'il « a trouvé quelque chose ».

Un taux de réussite mesuré est une **estimation**. Plus l'échantillon est petit, plus elle peut s'éloigner du vrai taux de l'approche.

## L'intervalle de confiance

L'intervalle de confiance à 95 % donne la plage des taux de réussite compatibles avec ce que l'on a observé. Le tableau suivant part d'un taux observé de **60 %**, sur des échantillons de taille croissante (intervalle de Wilson).

| Trades | Gains | Intervalle à 95 % |
|---|---|---|
| 10 | 6 | de 31,3 % à 83,2 % |
| 20 | 12 | de 38,7 % à 78,1 % |
| 50 | 30 | de 46,2 % à 72,4 % |
| 100 | 60 | de 50,2 % à 69,1 % |
| 400 | 240 | de 55,1 % à 64,7 % |

Après vingt trades à 60 %, le vrai taux pourrait être de 39 % : avec des gains à 1,5R, l'approche serait alors perdante, puisque son seuil de rentabilité est de 40 %. Il faut environ cent trades pour que l'intervalle reste au-dessus de 50 %.

::: callout definition "Ce que mesure l'intervalle"
Si l'on répétait l'expérience un grand nombre de fois, un intervalle construit ainsi contiendrait le vrai taux dans environ 95 % des cas. Ce n'est ni une garantie, ni une prévision du prochain trade.
:::

## Ce que cela change en pratique

- **Juger une méthode** demande des dizaines, idéalement des centaines de trades exécutés selon les **mêmes règles**. Changer les règles en cours de route remet le compteur à zéro.
- **Comparer deux setups** sur trente trades chacun ne permet presque jamais de les départager.
- **Une série de pertes** au début d'une approche n'est pas, à elle seule, une preuve qu'elle ne fonctionne pas, et une série de gains n'est pas une preuve qu'elle fonctionne.

::: callout method "Hypothèse de calcul"
L'intervalle suppose des trades indépendants, au taux de réussite constant. Si le marché change de régime en cours d'échantillon, l'incertitude réelle est plus grande que celle du tableau.
:::

::: callout mistake "Erreur fréquente"
Abandonner une approche après dix trades perdants sur vingt, puis en adopter une autre après six gagnants sur huit. À ces tailles, les deux résultats sont compatibles avec n'importe quel taux de réussite raisonnable.
:::

::: callout recap
- Un taux de réussite mesuré est une estimation ; sur un petit échantillon, elle peut être très éloignée du vrai.
- À 60 % observés, l'intervalle à 95 % va de 39 % à 78 % sur vingt trades, de 50 % à 69 % sur cent.
- Juger une méthode demande beaucoup de trades exécutés selon les mêmes règles.
- L'indépendance des trades est une hypothèse ; la réalité est souvent plus incertaine.
:::
