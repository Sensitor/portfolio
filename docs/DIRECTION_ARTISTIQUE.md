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

## 7. Décision du 22 octobre 2026

**Direction retenue : B, le Carnet de bord**, pour toute la plateforme. Les
principes du Bulletin s'appliquent à l'Academy et aux contenus éditoriaux.

## 8. Charte d'usage des signatures

Chaque signature a une fonction. Si la fonction est absente, la signature l'est aussi.

| Signature | Sert à | Jamais |
|---|---|---|
| Le relevé | montrer des trades un par un, dans l'ordre | pour une valeur unique, ou plus d'un par écran |
| L'empreinte | dire quelles règles un trade a tenues, ordre fixe | hors d'un trade ou d'une demande de revue |
| La marge « Lecture » | interpréter des chiffres : ce qu'ils veulent dire, leur portée | pour répéter un chiffre, ou sur une page sans données |
| Le crochet du S | marquer un niveau de prix, une valeur sur une graduation, un renvoi à une leçon, une note qui appelle une action, l'étiquette d'une donnée synthétique | dans un statut, un titre, un bouton, un fond |
| La hachure à 30° | une zone de risque ou d'objectif | toute autre surface |
| Le visa | une revue finalisée par un coach | une revue automatique, une demande en attente |
| L'italique Newsreader | la voix qui interprète : marge, phrases sous les chiffres, annotations, paroles du coach et question du membre | un fait (un détail de règle, une date, un plan) |
| Le monospace | heures, dates d'un trade, identifiants, pseudonymes | une phrase, un libellé, un chiffre de synthèse |
| Le bloc marine | un verdict par page au plus | une section courante, une liste |
| Le quadrillage isométrique | la barre latérale (la reliure) | les pages |

Les écrans de travail (journal, coaching, saisie, plan) n'ont pas de numéros de
chapitre : une section y est une question. Les numéros « § » restent à
l'Academy, où l'on lit.

## 9. Finalisation du journal et du coaching

Vérifié le 22 octobre 2026, en largeur bureau (1 440 px) et téléphone (390 px),
sans débordement horizontal ni erreur sur 28 captures :

| Cas | Ce qui a été corrigé |
|---|---|
| Journal vide | page blanche avec une consigne : un trade, dix, trente, et ce que chacun permet de lire |
| Un seul trade | « Avec 1 trade, ces chiffres ne mesurent encore rien de stable » ; plus de « 1 trades », de série « 1, meilleure : 1 », ni d'étiquettes superposées sur le relevé |
| Aucun stop | la marge le dit en premier ; « Coût des écarts : n.d., leur coût en R est inconnu » au lieu de « 0,00 R » ; le résultat en argent est donné quand le R manque |
| Peu d'écarts ou aucun | « aucun », « Aucun trade hors plan sur la période », « Rien à corriger » sans crochet |
| Textes longs | question longue composée plus petit, notes et symboles longs sans débordement, règles enfreintes écrites sans répétition |
| Revues | quota dit en une phrase selon le cas, plus de « 0 en attente, 0 répondue » |
| File vide | « Aucune demande n'attend de réponse », « La file est vide » |
| Téléphone | dans les listes, ce qui est tradé et le résultat sur la première ligne, puis la question, puis l'empreinte |

Ces cas sont couverts par `test_journal_edge_cases` (tests/test_academy_app.py).

Aperçus : `docs/assets/ecrans-valides-bureau.png`, `ecrans-valides-mobile.png`,
`ecrans-valides-cas-limites.png`.

## 10. Plan de généralisation

Chaque étape : un point de restauration, les tokens d'abord, puis les pages,
puis les captures bureau et téléphone, les contrastes et la suite de tests ;
une validation avant l'étape suivante. Aucune route, aucun calcul, aucune donnée
ne change.

### Étape 1 · Socle commun (faite le 24 octobre 2026)

**Fait.** Les composants partagés (fil d'Ariane, rubrique, titres, chapeau,
sections, notes, encadrés, étiquettes, listes de faits, tableaux, pied de page)
lisent des **rôles** (`--r-title`, `--r-label`, `--r-rubric-color`,
`--r-section-display`, `--r-voice`...) dont la valeur par défaut est l'apparence
actuelle. Le Carnet de bord ne réécrit plus ces composants : il redéfinit les
rôles sous son marqueur. Les tokens `--c-*` sont déclarés à la racine.

**Basculer un espace** se fait à un seul endroit : `carnet=True` sur l'espace
dans `sensitor/platform/spaces.py` (ou le nom de la page dans `CARNET_PAGES`).
Le shell pose le marqueur ; aucune page n'a à l'appeler. (Jusqu'à l'étape 4 :
depuis, toutes les pages sont en Carnet et le marqueur est retiré ; seule
l'édition se choisit par espace, avec `edition="bulletin"`.)

**Vérifié au pixel** : 38 captures pleine page (19 pages, bureau et téléphone),
avant et après. Les 30 captures hors journal sont identiques au pixel près.
Sur les 8 du journal et du coaching, seules diffèrent deux rubriques sur fond
marine, qui reprennent leur couleur claire au lieu du graphite peu contrasté
de la version précédente. Tests : `test_theme_roles` (tests/test_journal.py) et
le registre (tests/test_platform.py).

- Passer `CARNET_TOKENS` et `CARNET_FONTS` à la racine du thème, à côté des
  anciens tokens, sans encore les appliquer ailleurs.
- Remplacer, dans les composants partagés (`page_header`, `section`, `notice`,
  `pill`, `crumbs`), les valeurs codées en dur par les rôles du Carnet, derrière
  le marqueur : un seul endroit à basculer ensuite.
- Fin du monospace pour les libellés dans ces composants.

### Étape 2 · Academy et Bibliothèque, traitement « Bulletin » (faite le 24 octobre 2026)

**Fait.** L'Academy, la Bibliothèque et la Progression passent en Carnet de
bord, **édition Bulletin** (`edition="bulletin"` dans `spaces.py`, bloc
`BULLETIN_CSS` dans `theme.py`) :

- **Polices** : sous l'édition, `--serif`, `--sans` et `--mono` pointent vers
  Newsreader et Schibsted Grotesk ; seuls le code et les empreintes de hachage
  restent en monospace. Les libellés en capitales espacées deviennent des
  rubriques à espacement unique.
- **Leçons et fiches** : feuille avec son filet, texte courant en Newsreader
  (18,5 px), sections numérotées en ocre, intertitres en Newsreader.
- **Figures** : « Figure 1 » en ocre, légende en italique, source en note
  sous la légende ; graduations des graphiques en Schibsted Grotesk.
- **Encadrés** : la marge de la leçon. Définition à l'encre, méthode en bleu
  du plan, exemple, note et avertissement en ocre, erreur fréquente en brique,
  débat en double filet graphite, opinion du fondateur en italique dans un cadre
  ocre ; le récapitulatif est le seul bloc marine, sans quadrillage. La fin de
  leçon devient une feuille avec son filet.
- **Exercices** : boutons sur deux colonnes (ils étaient tronqués).
- **Parcours** : la liste devient un registre à filets au lieu de cartes
  encadrées ; les chiffres romains des chapitres restent, en Newsreader.
- **Progression** : une phrase de synthèse et, pour chaque cours, le
  **relevé** des leçons (une marque pleine par leçon terminée, un contour pour
  les autres).
- **Bibliothèque** : couvertures sans quadrillage, titre de couverture sans
  coupure au milieu d'un mot.
- **Monnaie et crypto** garde Space Grotesk pour ses titres et le cuivre pour
  son accent, avec le texte courant en Newsreader (`MONNAIE_TITLES`,
  comparaison : `docs/assets/monnaie-titres-grotesk-ou-newsreader.png`).
- **Chiffres** : plus de chiffres tabulaires sous la direction (la virgule
  tabulaire ouvrait un blanc : « 12 ,5 BTC »).
- **Téléphone** : un tableau ou une formule large défile dans son cadre.
  Balayage des 138 leçons à 390 px : aucun débordement, aucune erreur. Le
  premier balayage en avait trouvé six (formules et tableaux larges), et la leçon
  « Émission et halvings » débordait déjà avant l'étape ; toutes sont corrigées.

Vérifié : captures avant et après (`docs/assets/academy-*-avant-apres.png`,
`bibliotheque-avant-apres.png`), pages hors périmètre identiques au pixel
près, suite de tests complète.

L'Academy est le seul espace qui se lit. Elle prend le Carnet pour les
couleurs, les polices et la grammaire des données, et le Bulletin pour la
mise en page.

- **Leçons** : Newsreader pour le texte long (le seul espace où le corps est en
  serif), chapeau, figures et graphiques numérotés « Fig. 2 » avec leur
  source en note, tableaux en registre.
- **Encadrés** : la marge devient l'encadré pédagogique (définition, méthode,
  erreur fréquente), avec les mêmes rôles : ocre pour l'annotation, faits
  droits, interprétation en italique. Les encadrés « Opinion » et « Débat »
  gardent leur distinction.
- **Parcours et cours** : les numéros de chapitre en serif restent (c'est un
  repère de lecture ici) ; les hexagones des leçons restent comme état de
  progression, sans numéro décoratif.
- **Progression** : le relevé s'applique aux leçons et aux quiz (une marque
  par leçon), pour valoriser le travail fait plutôt qu'un pourcentage.
- **Bibliothèque** : fiches en registre, couvertures sans quadrillage.
- **Univers Monnaie et crypto** : le cuivre reste son accent ; Space Grotesk
  pour ses titres est réévalué face à Newsreader (proposition à valider sur
  captures).
- Points d'attention : les 138 leçons et leurs graphiques sont rendus par des
  composants communs ; la vérification se fait sur un échantillon par parcours
  et sur la page de chaque type de bloc.

### Étape 3 · Investissement et analyseur de portefeuille (faite le 24 octobre 2026)

**Fait.** L'application d'analyse (`portfolio_optimizer_saas.py`, 23 pages) passe
du thème sombre au Carnet de bord. Aucun calcul, aucune donnée ni aucune route
ne change ; Space Grotesk reste pour les titres Monnaie et crypto (option A).

- **Jetons** (`sensitor/ui/themes.py`) : papier, feuille, encre, filets et rôles
  du Carnet (plan, gain, perte, annotation). Le vert et la brique restent
  distincts. `fade(jeton, alpha)` remplace les teintes `rgba` écrites à la main
  dans les graphiques et les composants.
- **Palette de séries** recalculée pour le fond clair et revalidée avec
  `validate_palette.js` (daltonisme, contraste, plancher en vision normale) ;
  rampe séquentielle bleue validée en ordinal ; échelle divergente brique,
  gris chaud, bleu.
- **Ancienne feuille de style** : le bloc `<style>` de 500 lignes du script est
  remplacé par `inject_legacy()`, qui habille les anciennes classes avec les
  jetons (verdict du score en marine, cartes en feuilles, recommandations en
  notes de marge). Les couleurs écrites en dur dans le script sont ramenées aux
  jetons ; un test vérifie qu'il n'en reste aucune hors du Carnet.
- **Titres** : Newsreader pour les titres de page, de section et les `###` ;
  les titres de section ne sont plus forcés en capitales (63 appels).
- **Barre latérale** : la reliure marine avec son quadrillage ; marque, libellés
  et badge de formule en clair sur marine (la marque était devenue invisible
  au premier passage).
- **Grammaire des données** :
  - performance : un point et la valeur en bout de ligne, avec une pastille de
    la couleur de la série ; les étiquettes proches s'écartent ; au-delà de
    quatre séries, la légende seule ;
  - drawdown : zone de risque hachurée à 30° (motif Plotly tourné en CSS ; un
    navigateur qui l'ignore garde une hachure horizontale) ;
  - vue d'ensemble : marge « Lecture » à côté de l'évolution du capital, trois
    phrases calculées (valeur de départ et d'arrivée, indice de référence, pire
    baisse) et la mention « Données passées ».
- **Barre d'outils des graphiques** : affichée au survol (ou au toucher) ; en
  permanence, elle couvrait la légende sur téléphone.
- **Chiffres** : proportionnels, comme dans l'Academy (la virgule tabulaire de
  Schibsted ouvre un blanc).

Vérifié : 23 pages capturées à 1440 px avant et après, vue d'ensemble, risque,
santé, simulateur et compte à 390 px (aucun défilement horizontal), suite de
tests complète, dont 13 contrôles ajoutés à `test_sensitor_pages`. Les pages
« Améliorer » et « Tableau de bord » échouent avec le portefeuille fictif des
tests avant comme après (limite de ce portefeuille, pas de l'étape). Comparaisons :
`docs/assets/analyseur-vue-ensemble-avant-apres.png`,
`analyseur-risque-avant-apres.png`, `analyseur-compte-avant-apres.png`,
`analyseur-mobile.png`.

Décidé le 25 octobre 2026 : « Lecture partout » et le nom Sensitor.

- **Marque** : la barre latérale de l'analyseur porte le même ensemble que la
  plateforme (le monogramme, SENSITOR, puis « Portefeuille et risque ») ;
  l'onglet du navigateur s'appelle Sensitor, avec le monogramme pour icône.
- **Marge « Lecture »** sur chaque écran de synthèse, à côté de son graphique
  principal, par un composant commun (`chart_with_reading` dans
  `sensitor/pages/_shared.py`). Chaque phrase est construite à partir d'un
  chiffre que la page calcule déjà, et chaque marge dit d'où viennent ses
  chiffres (données passées, estimations, simulation, données de référence,
  petits échantillons) :
  - vue d'ensemble : départ, arrivée, indice de référence, pire baisse ;
  - performance : la position qui apporte le plus, celle qui apporte le moins,
    les positions qui retirent du rendement ;
  - santé : d'où vient le score, la composante la plus faible, le trait le plus
    et le moins marqué ;
  - radiographie : la plus grosse position directe, le premier secteur et la
    première zone une fois les fonds décomposés ;
  - risque : trois marges, contribution au risque, corrélations (paire la plus
    et la moins liée, moyenne), drawdown (pire baisse, rattrapage, temps sous
    le sommet) ;
  - stress tests : la pire et la plus douce des fenêtres, le nombre de crises
    où le portefeuille a fait mieux que l'indice ;
  - optimiseur : le portefeuille actuel, le Sharpe maximal, la volatilité
    minimale, présentés comme des estimations ;
  - simulateur : la comparaison des allocations et le Monte Carlo (médiane,
    une trajectoire sur dix de chaque côté, part des trajectoires sous la
    somme investie) ;
  - trading : vue d'ensemble, analytique, dérive du risque et erreurs, avec le
    seuil d'échantillon rappelé.
- Vérifié : 22 contrôles ajoutés (`test_sensitor_pages`, `test_trading_pages`),
  dont le nombre de marges par page dans les deux langues et la concordance
  entre la phrase et le tableau de la page ; captures à 1440 et 390 px.
  Planche : `docs/assets/analyseur-lecture.png`.

Tirets longs (25 octobre 2026) : retirés de toutes les chaînes que
l'analyseur, l'API et les modules partagés peuvent afficher, environ 340. Une
incise encadrée devient une parenthèse, un tiret seul une virgule ou un
deux-points selon la phrase, un séparateur entre deux libellés « · », une
plage de valeurs « 5-15 % » ou « 2 à 5 $ ». Une valeur absente s'écrit
« n.d. » en français et « n/a » en anglais (`na()` dans `sensitor/core/i18n.py`),
comme dans le journal de la plateforme. Un test parcourt chaque chaîne du code
et chaque page rendue dans les deux langues.

Reste, hors de la direction : l'allocation en registre plutôt qu'en barres
(non demandée).

Plan d'origine :

C'est l'écart le plus grand : l'application d'analyse a un thème sombre
« fintech » (`sensitor/ui/themes.py`, 17 pages).

- Passer au fond ivoire et à l'encre, avec les rôles du Carnet ; supprimer les
  halos et le bleu électrique. La palette de séries validée pour le daltonisme
  est recalculée et revalidée sur le fond clair.
- Grammaire des données : performance avec étiquettes en bout de ligne,
  drawdown hachuré à 30° comme zone de risque, allocation en registre, la
  marge « Lecture » sur les écrans de synthèse (risque, corrélations,
  stress tests).
- L'espace reste dense : tableaux en registre, chiffres tabulaires dans les
  colonnes, pas de marge sur les écrans de saisie.
- Points d'attention : l'application a ses propres tests de rendu
  (`test_sensitor_pages`, `test_trading_pages`) ; la refonte se fait page par
  page, en commençant par la vue d'ensemble.

### Étape 4 · Composants communs et autres espaces (faite le 25 octobre 2026)

**Fait.** Toutes les pages de la plateforme sont en Carnet de bord : accueil
(visiteur et membre), compte, Psychologie et discipline, Trading Lab, espaces
en préparation et application séparée, réinitialisation et vérification.

- **Polices** : sur toutes les pages, les composants qui nommaient une police
  (`--serif`, `--sans`, `--mono`) reçoivent celles de la direction ; le
  monospace ne reste que pour le code, les empreintes, les heures et les
  identifiants. Le dernier titre en Playfair (l'appel à se connecter du
  journal) passe en Newsreader.
- **Barre latérale** : la reliure garde son quadrillage ; ses rubriques et ses
  pastilles passent en grotesque.
- **Un seul bloc fort par page, sans quadrillage** : la présentation de
  l'accueil visiteur et la carte « Reprendre » de l'accueil membre restent
  marine, sans grille ; la tuile Academy n'est plus distinguée en marine.
- **Accueil membre** : « Vos parcours » devient un registre, une ligne par
  cours avec son **relevé** (une marque par leçon terminée) et son compte, au
  lieu de dix-neuf grandes cartes et barres de progression. Les espaces
  deviennent un registre (numéro, nom, résumé, état en toutes lettres dans sa
  couleur de rôle), sur l'accueil visiteur comme membre.
- **Trading Lab** : les chiffres des calculateurs forment une ligne de
  registre ; le résultat principal est marqué par un filet bleu du plan sur
  fond de marge, et non plus par une tuile marine. Le même composant sert dans
  les leçons qui contiennent un calculateur.
- **Psychologie** : chaque note du journal de réflexion est posée dans la
  marge, avec un filet bleu du plan, et le texte du membre est en italique
  Newsreader : c'est sa voix. Pas de relevé, rien n'y est mesuré au trade.
- **Retrait du marqueur** : `sx-da`, `uses_carnet`, `CARNET_PAGES` et le champ
  `carnet` des espaces disparaissent. La direction s'applique par la portée
  `.stApp.stApp [data-testid="stMain"]`, qui pèse exactement ce que pesait
  l'ancienne portée : chaque règle garde la priorité avec laquelle elle a été
  validée. Seule l'édition Bulletin garde un marqueur (`sx-edition bulletin`).
  Vérifié au pixel : avant et après le retrait, les 38 captures de référence
  sont identiques, à un décalage de 16 px près (le conteneur du marqueur
  retiré).

Vérifié : captures avant et après des pages concernées à 1440 et 390 px,
aucun défilement horizontal ; pages déjà passées comparées au pixel (seuls
changent la barre latérale, les numéros des règles du plan, le titre en
Playfair du journal et les coins de la carte « Commencer ») ; suite de tests
complète, dont les contrôles du registre des espaces, de l'édition par page et
du retrait du marqueur. Comparaisons : `docs/assets/accueil-membre-avant-apres.png`,
`accueil-visiteur-avant-apres.png`, `trading-lab-avant-apres.png`,
`psychologie-avant-apres.png`, `etape4-mobile.png`.

La généralisation est terminée : la direction n'est plus un prototype, c'est
l'identité de toute la plateforme et de l'analyseur.
