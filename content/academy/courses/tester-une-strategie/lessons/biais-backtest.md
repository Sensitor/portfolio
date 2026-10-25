+++
id = "biais-backtest"
title = "Les biais qui faussent un backtest"
summary = "Un backtest peut être faux sans aucune erreur de calcul : il suffit qu'une information du futur se glisse dans la décision, que l'on choisisse les exemples ou l'instrument après coup. Quatre biais, et la parade de chacun."
duration_minutes = 15
access = "member"
status = "published"
version = 1
objectives = [
  "Définir le biais d'anticipation, le biais de sélection, le biais du survivant et le biais rétrospectif.",
  "Reconnaître chacun dans un protocole de test.",
  "Appliquer la parade qui correspond.",
]
quiz = "check-biais-backtest"
resources = ["fiche-backtest"]
+++

## Un résultat juste, un test faux

Les biais de cette leçon ne produisent aucune erreur visible. Les calculs sont exacts ; c'est ce que l'on a mis dans le calcul qui ne l'est pas. Ils vont presque toujours dans le même sens : ils rendent la stratégie **meilleure** qu'elle n'est.

## Le biais d'anticipation

::: callout definition "Biais d'anticipation (look-ahead)"
Utiliser, au moment d'une décision simulée, une information qui n'était pas encore disponible à ce moment-là.
:::

Les formes courantes : décider sur la clôture d'une bougie avant qu'elle ne soit close ; identifier un swing avant que ses deux bougies de confirmation n'existent (parcours 2) ; tracer une jambe jusqu'à un sommet que l'on ne connaissait pas encore. Le défilement bougie par bougie de la leçon précédente est la parade principale.

## Le biais de sélection

Il consiste à ne retenir **que certaines occurrences**, celles qui « ressemblent » à de bons exemples, ou à choisir la **période** où la stratégie a bien marché. La parade : une période fixée avant, et toutes les occurrences notées.

## Le biais du survivant

Tester sur les instruments ou les actifs qui sont encore là aujourd'hui, ou que l'on a choisis parce qu'ils ont eu une belle tendance, revient à ignorer ceux qui ont disparu ou déçu. Sur le Forex, il prend surtout la forme du **choix de l'instrument après coup** : on teste sur la paire où la stratégie « se voyait » le mieux. La parade : choisir l'instrument et la période avant de regarder, pour des raisons qui ne dépendent pas du résultat.

## Le biais rétrospectif

Déjà rencontré au parcours 3 : une fois la suite connue, chaque décision paraît évidente. Dans un backtest, il pousse à juger qu'une occurrence « n'aurait pas été prise » ou qu'une sortie « aurait été anticipée ». La parade : la règle écrite décide, pas le souvenir de ce qu'on aurait fait.

::: callout example "Exemple pédagogique"
Un trader teste sa stratégie de sweeps sur six paires, garde celle où elle donne le meilleur résultat, puis ne relève que les sweeps « nets ». Trois biais à la fois : sélection de l'instrument, sélection des occurrences, et rétrospectif dans le jugement de « net ». Le résultat obtenu dit surtout combien de choix il a faits après coup.
:::

| Biais | Signe | Parade |
|---|---|---|
| **Anticipation** | décision prise avec une bougie non close, un swing non confirmé | défilement bougie par bougie |
| **Sélection** | occurrences ou période retenues selon leur aspect | période fixée, toutes les occurrences |
| **Survivant** | instrument choisi pour son historique favorable | choix de l'instrument avant le test |
| **Rétrospectif** | « je ne l'aurais pas prise » | la règle écrite décide |

::: callout recap
- Les biais de backtest ne produisent pas d'erreur visible et embellissent presque toujours le résultat.
- Anticipation, sélection, survivant, rétrospectif : chacun a sa parade, à intégrer au protocole.
- Un résultat obtenu après beaucoup de choix faits en voyant les données mesure surtout ces choix.
:::
