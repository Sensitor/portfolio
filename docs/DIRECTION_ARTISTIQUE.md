# Sensitor : audit créatif et direction artistique

*21 octobre 2026. Point de restauration avant la refonte : tag `avant-refonte-da` (commit a4a97b9).*

Ce document suit la méthode demandée : audit, deux directions, recommandation,
prototype sur deux écrans, puis validation avant toute généralisation.

---

## 1. Audit de l'identité actuelle

### Ce qui a été examiné

`sensitor/platform/ui/theme.py` (tokens et 840 lignes de styles), `brand.py`,
les deux SVG de `assets/brand`, les composants partagés (`components.py`), le
shell, les pages du journal (`trading_journal.py`, `trade_reviews.py`,
`trade_visuals.py`), et le thème de l'application d'analyse
(`sensitor/ui/themes.py`). Mesures faites sur le code et sur des captures.

### Forces à conserver

1. **Le monogramme.** Le S n'est pas une lettre dessinée : ce sont deux
   crochets imbriqués, tracés sur une grille isométrique à 30°. C'est un vrai
   actif. Il contient déjà un angle (30°), une forme (le crochet) et une
   structure (deux moitiés qui se répondent) réutilisables comme langage.
2. **L'ivoire et l'encre marine.** Rares en fintech, chaleureux, lisibles.
   La base est bonne.
3. **La rigueur de fond.** Chiffres sourcés, échantillon toujours affiché,
   « non vérifiable » distinct de « respecté », exemples synthétiques
   étiquetés. C'est la personnalité la plus singulière de Sensitor, et elle
   n'est presque pas visible.
4. **La densité fonctionnelle** du journal : chaque écran répond à une
   question précise.

### Faiblesses : ce qui fait « fintech générée »

| Constat | Mesure | Effet |
|---|---|---|
| Une seule composition pour toutes les pages | rubrique en capitales espacées, titre Playfair avec un mot en italique bleu, bandeau de trois chiffres, sections « § 01 » titre à gauche et chapeau à droite | la file du coach, le journal, le plan et une leçon ont la même silhouette |
| Le monospace partout | 63 usages de `--mono`, 65 `letter-spacing`, 33 `uppercase` | des phrases entières (la question d'un membre) sont composées en machine à écrire ; tout est « libellé », rien n'est hiérarchisé |
| Les grands chiffres en serif | 36 usages de `--serif`, chiffres de 2 à 3,4 rem | le code « luxe éditorial » le plus répandu des interfaces générées |
| Le quadrillage isométrique | 9 surfaces, dont chaque carte marine | décor sans fonction ; il dilue la seule forme propriétaire (l'isométrie du S) |
| Les cartes marine | 13 conteneurs `navy_` | le moment fort n'est plus fort s'il revient à chaque écran |
| Le doré | 21 références | sert à la fois d'alerte, de priorité, de « bientôt » et de décor |
| Les anneaux de progression | score du plan, score d'un trade | un anneau dit « 80 % » ; il ne dit pas quels trades, ni quand |
| Hexagones numérotés | file du coach : « 05 » = identifiant modulo 100 | un repère qui ne repère rien |
| Chiffres tabulaires annoncés, absents | DM Sans n'a pas de chiffres tabulaires (vérifié : `tabular-nums` sans effet) | d'où le monospace pour chaque nombre |

### Incohérence majeure entre espaces

L'application d'analyse (espace Investissement, `sensitor/ui/themes.py`) a un
autre système : fond noir bleuté `#070B14`, bleu électrique `#3987E5`, halos
(`ACCENT_GLOW`), vert et rouge saturés. C'est exactement le code « tableau de
bord fintech sombre ». Les deux applications partagent un compte et un nom,
pas une identité.

### Ce qui peut devenir propriétaire

1. **Le crochet du S** comme repère : il marque un niveau, une note, un visa.
2. **L'angle de 30°** du monogramme : lignes de rappel des annotations,
   hachures des zones de risque. Un angle, pas un motif de fond.
3. **La rigueur rendue visible** : chaque chiffre accompagné de son sens et de
   son échantillon, écrit comme une note de chercheur.
4. **Le trade comme unité visible** : montrer les trades un par un (relevés,
   empreintes) plutôt que des pourcentages abstraits.

---

## 2. Deux directions

### Direction A · « Le Bulletin »

*Une maison de recherche qui publie.* Sensitor comme une lettre d'analyse
indépendante : on lit un rapport bien composé.

- **Codes** : grille à colonnes stricte, filets fins, figures numérotées
  (« Fig. 2 »), notes de bas de page appelées par ¹ ², tableaux sans cadre,
  chapeaux, un seul encadré « Conclusion » par page.
- **Typographie** : Newsreader pour les titres et le texte long, une
  grotesque de presse pour l'interface, petites capitales pour les rubriques.
- **Palette** : papier, encre, un rouge éditorial pour les corrections.
- **Signature** : l'appel de note. Chaque statistique renvoie à une note qui
  l'explique.
- **Effets** : excellente pour l'Academy et les rapports ; plus lointaine pour
  le journal, où l'on travaille plutôt qu'on ne lit. Risque : un produit qui
  ressemble à un journal en ligne.

### Direction B · « Le Carnet de bord »

*Un carnet de recherche tenu dans un atelier.* Sensitor comme l'outil d'un
trader qui travaille : on relève, on annote, on corrige, on progresse.

- **Codes** :
  - **la marge** : une colonne où Sensitor écrit ce que le chiffre veut
    dire, en italique, reliée à la donnée par un trait à 30° ;
  - **le relevé** : une marque par trade, dans l'ordre, au lieu d'un
    pourcentage seul ; on voit quels trades, et quand ;
  - **l'empreinte des règles** : neuf cases, toujours dans le même ordre,
    pour lire d'un coup d'œil quelle règle un trade a enfreinte ;
  - **le repère** : le crochet du S, qui marque les niveaux d'un trade et
    les notes ;
  - **la hachure à 30°** : réservée aux zones de risque et d'objectif ;
  - **le visa** : la revue du coach se termine par une signature, comme une
    copie corrigée.
- **Typographie** : Newsreader (titres, et italique pour les annotations),
  Schibsted Grotesk (interface et chiffres, tabulaires), monospace réservé aux
  heures et identifiants.
- **Palette** : papier, feuille, marge ; encre ; bleu de Prusse pour le plan ;
  vert sapin et brique pour les résultats ; ocre pour la voix d'annotation.
- **Effets** : naturelle pour le journal et la revue, adaptable à l'Academy
  (la marge devient l'encadré pédagogique) et à l'Investissement (le relevé
  et la règle graduée sont des outils de mesure). Risque : la nostalgie du
  papier ; on l'évite en refusant toute texture, écriture manuscrite ou faux
  grain.

Planches comparatives : `docs/assets/direction-a-bulletin.png` et
`docs/assets/direction-b-carnet.png`.

---

## 3. Recommandation : le Carnet de bord, avec la rigueur du Bulletin

Le Carnet de bord est recommandé, pour quatre raisons :

1. **Il naît du produit.** Sensitor demande au membre de relever, d'annoter et
   de se corriger ; le Carnet donne une forme visible à cette méthode. Le
   Bulletin habillerait le produit ; le Carnet l'explique.
2. **Il naît du logo.** Le crochet et l'angle de 30° viennent du S. Aucun
   motif n'est inventé.
3. **Il crée de l'attachement.** Un carnet est à soi. Le relevé et
   l'empreinte montrent le travail du membre, trade après trade, plutôt qu'un
   score.
4. **Il reste reconnaissable sans logo** : une marge annotée en italique, des
   relevés trade par trade et des hachures à 30° ne ressemblent à aucun autre
   produit.

Du Bulletin, on garde la rigueur : figures numérotées dans l'Academy,
tableaux sans cadre, un seul moment fort par page.

---

## 4. Système proposé

### Rôles des couleurs

| Token | Valeur | Rôle | Contraste |
|---|---|---|---|
| `paper` | #F3F0E8 | fond de page | |
| `sheet` | #FFFDF8 | surface de travail : graphiques, fiches, formulaires | |
| `margin` | #EEE9DD | marge et zones d'annotation | |
| `ink` | #0F1B26 | texte, actions principales | 15,3:1 sur papier, 14,4:1 sur marge |
| `ink-2` | #33414D | texte secondaire | 9,2:1 |
| `graphite` | #59636B | libellés, axes | 5,4:1 (5,1:1 sur marge) |
| `rule` / `rule-strong` | #D8D2C3 / #B7B0A0 | filets | décoratif |
| `plan` | #1F4A72 | le plan, la sélection, les liens | 8,1:1 |
| `up` | #22604A | gain | 6,5:1 |
| `down` | #9A3A2C | perte, écart au plan | 6,1:1 |
| `note` | #855615 | la voix d'annotation, Sensitor et le coach | 5,5:1 (5,2:1 sur marge) |
| `na` | #A2A8AC | non vérifiable (forme seulement, jamais seul) | 2,1:1, jamais pour du texte |
| `cover` | #0F1B26 | la reliure : barre latérale ; un seul bloc fort par page | |

Contrastes calculés sur `paper` (formule WCAG 2.1), voir la section 6. Le vert
et la brique ne portent jamais seuls le sens : signe, mot et position
l'accompagnent, pour les daltonismes.

L'ocre n'est plus un doré de luxe : c'est l'encre de l'annotation. Le
quadrillage isométrique reste sur la reliure seulement.

### Hiérarchie typographique

| Rôle | Police | Corps | Usage |
|---|---|---|---|
| Titre éditorial | Newsreader 600, optique display | 2,9 rem, interlignage 1,05 | une phrase directe par page |
| Titre de section | Newsreader 600 | 1,6 rem | une question à laquelle la section répond |
| Rubrique | Schibsted Grotesk 600, capitales | 11,5 px, +0,08 em | la seule capitale espacée du système |
| Texte courant | Schibsted Grotesk 400 | 16 px / 1,6 | interface et explications |
| Libellé | Schibsted Grotesk 500 | 13 px | champs, colonnes, légendes |
| Donnée | Schibsted Grotesk 600 | 2,1 rem / 1,15 rem | les chiffres en sans, plus en serif ; chiffres tabulaires dans les colonnes de tableaux seulement, car la virgule tabulaire de Schibsted est aussi large qu'un chiffre |
| Annotation | Newsreader italique 400 | 15 px | la marge, les notes de graphique, la voix du coach |
| Technique | DM Mono | 12 px | heures, identifiants, rien d'autre |

### Grammaire des données

- **Courbe réalisée** à l'encre (2,4 px), **courbe du plan** en bleu de Prusse
  fin ; l'écart entre les deux est teinté brique : c'est ce que les écarts ont
  coûté. Étiquettes au bout des lignes, pas de légende séparée.
- **Écarts** marqués par de courts traits brique sur l'axe, sous la courbe.
- **Relevé** : une marque par trade. Encre si le plan est suivi, brique et
  plus haute s'il ne l'est pas, grise si rien n'était vérifiable.
- **Empreinte** : les règles du plan, dans un ordre fixe.
- **Niveaux d'un trade** : repère en crochet, prix et R sur la même ligne,
  zone de risque hachurée brique à 30°, zone d'objectif hachurée vert.
- **Annotations** : appel numéroté en ocre, texte en italique dans la marge.

### Motifs et détails

- Le crochet : repère de niveau, appel de note, visa. Jamais en fond.
- La hachure à 30° : zones de risque et d'objectif seulement.
- Le quadrillage isométrique : la reliure seulement.
- Le bloc marine : un par page au plus, pour un verdict.
- États vides : une page de carnet avec une consigne, pas une illustration.

### Voix

- Titres directs : « Ce que vos écarts vous ont coûté », pas « Analyse des
  écarts ».
- Chaque chiffre a sa phrase : « +0,14 R : en moyenne, un trade vous rend 14 %
  de ce que vous risquez. »
- La progression valorise la discipline : « 6 trades d'affilée dans le plan »
  avant le résultat.

---

## 5. Prototype

Deux écrans existants, sans changement de logique, de calcul ni de route :

1. **Le journal de trading** (`journal`) et son tableau de performance.
2. **La file du coach** (`coach`) et **le rapport de revue** (`journal_reviews`
   et la réponse du coach).

Les nouveaux tokens sont centralisés dans `theme.py` (`CARNET_TOKENS`,
`CARNET_CSS`) et ne s'appliquent qu'aux pages qui portent le marqueur
`sx-da` : le reste de la plateforme est inchangé jusqu'à validation.

### Ce que le prototype change

| Avant | Après |
|---|---|
| Carte marine, quadrillage, anneau « 80 % » | **le relevé** : 66 marques, une par trade, les écarts plus hauts et en brique, sur une feuille ivoire |
| Six grands chiffres serif sur fond marine, libellés en capitales espacées | six chiffres en grotesque, chacun suivi d'une **phrase qui dit ce qu'il signifie** |
| Aucun commentaire de lecture | **la marge** « Lecture » : ce que les écarts ont coûté, l'écart qui pèse le plus, la série dans le plan, la portée de l'échantillon |
| Courbes avec légende et points rouges | zone teintée entre les courbes (le prix des écarts), étiquettes en bout de ligne, traits brique sous l'axe, annotation à 30° |
| Barres rouges par règle | **le registre** : une marque par écart, « tenue » quand la règle a tenu, la priorité en note de marge avec son crochet |
| Anneau par trade | **l'empreinte** des neuf règles, dans un ordre fixe |
| Échelle de prix aux libellés en capitales | niveaux marqués par **le crochet du S**, zones **hachurées à 30°**, sortie annotée en italique |
| File du coach : bandeau de trois chiffres, hexagones « 05 » sans sens, question en monospace | une phrase de synthèse, des dossiers avec la question en italique, le temps d'attente et l'empreinte |
| Revue : bloc marine, barres à cinq segments | **copie corrigée** : la question citée, les règles enfreintes en clair, le plan du membre en marge, des graduations avec le crochet, des points numérotés, **le visa** du coach |

Aucune route, aucun calcul, aucune donnée ni interaction n'a changé. Les
phrases de lecture sont dérivées des chiffres déjà calculés ; seule la série
« dans le plan » est un simple comptage des revues existantes.

## 6. Vérifications

- **Contrastes** : tous les tokens de texte dépassent 4,5:1 sur le papier, la
  feuille et la marge (calcul WCAG 2.1, voir le tableau de la section 4).
- **Chiffres** : Schibsted Grotesk a des chiffres tabulaires, mais sa virgule
  tabulaire est aussi large qu'un chiffre ; ils sont donc réservés aux colonnes
  de tableaux.
- **Tailles d'écran** : bureau 1 440 px et téléphone 390 px, sans débordement
  horizontal.
- **Périmètre** : un test vérifie que le marqueur `sx-da` est sur le journal,
  une fiche trade, les revues et la file du coach, et sur aucune autre page.
- **Tests** : toute la suite passe.

Comparaisons : `docs/assets/prototype-journal-avant-apres.png`,
`prototype-coach-avant-apres.png`, `prototype-revue-avant-apres.png`.

## 7. Si la direction est validée

1. Passer les tokens du Carnet de bord à la racine et retirer le marqueur.
2. Academy : la marge devient l'encadré pédagogique, les figures sont
   numérotées ; Newsreader pour le texte long des leçons.
3. Investissement : l'application d'analyse abandonne son thème sombre « fintech »
   pour la feuille, l'encre et la grammaire des données (relevés, règles
   graduées, annotations).
4. Réduire le monospace aux heures et identifiants dans toute la plateforme.
