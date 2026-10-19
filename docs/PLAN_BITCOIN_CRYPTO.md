# Sensitor : Bitcoin, Crypto & Trading Intelligence

Plan de mise en œuvre de la vision produit. Rédigé le 17 octobre 2026 après audit du dépôt.
Les lots A, B1, B2, C1, C2 et C3 sont terminés ; les suivants sont construits un par un, chacun vérifié avant le suivant.

## 1. État réel du dépôt (phase A)

### Git

- Branche de travail : `claude/improve-portfolio-ui-WLAR3`, à jour avec `origin`.
- Aucune modification non commitée, aucun stash.
- La branche a 12 commits d'avance sur `main`. **Aucun travail de l'Academy n'est encore en production** : `main` s'arrête à la fusion de la PR #20.
- Point de sauvegarde : le tag `sauvegarde-avant-academy-crypto`, posé sur le commit qui accompagne ce document.

### Ce qui fonctionne, vérifié

| Brique | Vérification |
|---|---|
| Plateforme (Academy, Bibliothèque, Psychologie, Trading Lab, Progression, Compte) | 221 vérifications headless, parcours navigateur en mode clair et sombre |
| Academy : 7 parcours trading publiés, 50 leçons, 50 quiz, 15 exercices, 8 ressources | `python -m sensitor.academy.validate`, 612 vérifications qui recalculent chaque chiffre cité |
| Comptes, sessions, réinitialisation, vérification, export, suppression | 95 + 42 vérifications |
| Base de données SQLite et PostgreSQL, schéma v9 | 119 vérifications, dont l'isolation entre utilisateurs |
| API HTTP | 176 + 86 vérifications |
| Application portefeuille et journal de trading (`portfolio_optimizer_saas.py`) | 180 + 82 vérifications de rendu, démarrage vérifié dans un navigateur |
| Moteurs : investissement, trading, devises, connecteur MT5 simulé | fichiers de test dédiés, tous à zéro échec |
| Client mobile | vérification TypeScript (`tsc --noEmit`) réussie |

Les 15 fichiers de test Python passent (exécutés le 17 octobre 2026).

**Non exécuté :** le test d'intégration mobile (`npm run test:integration`), qui demande un serveur API lancé avec des comptes de test.

### Corrigé pendant la phase A

- **Le bouton « Analyse Portfolio » plantait en mode simulation.** Il levait une `NameError` à chaque analyse réussie : une correction destinée à la page « portefeuille réel » avait aussi été collée dans la branche simulation, où ses variables n'existent pas. Ce bug est en production depuis la PR #20. Le comportement d'origine est rétabli, et un test qui clique réellement sur le bouton le couvre maintenant : il échoue sur l'ancien code et passe sur le nouveau.

### Problèmes connus, non corrigés (relevés par l'audit)

Ceux marqués ✔ ont été vérifiés dans le code ; les autres sont rapportés par l'audit et restent à confirmer avant toute correction.

- ✔ Les volatilités annualisées utilisent 252 jours par an, y compris pour la crypto. C'est documenté dans le code et sous-estime la volatilité crypto par rapport à une base de 365 jours.
- ✔ Aucun indice de référence crypto : les références proposées sont SPY, QQQ, URTH, VT, AGG et GLD.
- ✔ L'accès « pro » ne vient que de la variable `PRO_EMAILS`. La colonne `users.tier` est écrite mais jamais lue par l'application portefeuille.
- ✔ Le Stress Lab récupère les prix sans conversion de devise.
- Les paywalls sont incohérents : seules les anciennes pages sont verrouillées, les nouvelles ne le sont pas.
- Deux moteurs coexistent pour le score de santé, l'optimisation et les stress tests (ancien `PortfolioAnalyzer` et nouveaux modules).
- Plusieurs modules quantitatifs (Monte Carlo, stress, score de santé, optimisation, VaR) ne sont couverts que par des tests de rendu, sans test de leurs calculs.
- L'import CSV du journal n'existe pas, alors que l'interface y fait allusion.
- L'application portefeuille a sa propre charte sombre et ses propres styles, différents du design system validé de la plateforme.
- Les tests s'exécutent avec `python tests/x.py`. Lancés sous pytest, leurs vérifications n'échouent jamais.

## 2. Principes retenus

1. **Rien n'est supprimé.** Les sept parcours trading, le journal, le portefeuille, l'API et le client mobile restent tels quels. Les nouveaux contenus s'ajoutent à côté.
2. **Le système de contenu existant est le bon.** Programme en TOML, cours en TOML, leçons en Markdown, quiz, exercices, figures et ressources séparés, validateur. Il suffit de l'étendre ; il n'y a rien à réécrire.
3. **Les calculs restent à part.** Chaque simulateur a son module Python pur et testé, comme `risk.py`, `expectancy.py`, `zones.py` ou `backtest.py`. La page ne fait qu'afficher.
4. **Aucune donnée inventée.** Une donnée historique a une source, une date de récupération et une licence. Sans donnée fiable, la page affiche un exemple synthétique, signalé comme tel.
5. **Faits, hypothèses et opinions sont séparés visuellement.** Il ne faut jamais présenter Bitcoin comme une protection garantie, ni un indicateur comme un signal infaillible.
6. **Aucune nouvelle pile technique.** Plotly est déjà une dépendance du projet : il suffit pour les graphiques interactifs.

## 3. Organisation proposée de l'Academy

### Quatre filières, le trading en tête

Le programme actuel numérote dix parcours de trading de 1 à 10. Je propose de le regrouper en **filières**, sans toucher aux contenus :

| Filière | Parcours | État |
|---|---|---|
| **Monnaie et Bitcoin** (le complément du trading) | M1 Monnaie, inflation et théorie monétaire · M2 Bitcoin en profondeur | à créer |
| **Crypto** | C1 Blockchain, wallets et sécurité · C2 Altcoins et analyse crypto | à créer |
| **Investissement** | I1 Stratégies d'investissement crypto · I2 La méthode du fondateur | à créer |
| **Trading** | T1 à T8, les huit parcours publiés · T9 La méthode Sensitor · T10 Processus discipliné | conservés tels quels |

Changement technique : un champ `track` dans `curriculum.toml` et une numérotation affichée par filière (« Bitcoin · M2 », « Trading · T4 »).

**Ce changement ne touche pas la progression des membres.** Elle est enregistrée par identifiant de cours et de leçon, pas par numéro de parcours : je l'ai vérifié dans le schéma.

### M1 · Monnaie, inflation et théorie monétaire (trois cours)

1. **La monnaie.** Modules 1 et 4 de la vision :
   - fonctions de la monnaie, histoire, monnaie fiduciaire et bancaire ;
   - création monétaire par le crédit, bilans simplifiés, banque centrale, taux ;
   - dette publique et privée, déficits, obligations, politique monétaire, monétisation et ses limites.

   **Schémas :** les circuits entre ménages, entreprises, banques commerciales et banque centrale, et un bilan bancaire qui s'équilibre quand un crédit est accordé.
2. **L'inflation.** Modules 2 et 5 :
   - mesure, indices, inflation par catégorie ;
   - demande, coûts, énergie, crédit, anticipations, boucles prix-salaires ;
   - épisodes historiques distingués les uns des autres ;
   - les écoles de pensée (monétarisme, approches keynésiennes, école autrichienne, approches institutionnelles, monnaie endogène), chacune avec ses hypothèses, ses désaccords et ses limites.
3. **Inflation et patrimoine.** Modules 3 et 6 :
   - rendement nominal et réel, intérêts composés, frais, fiscalité ;
   - liquidité, concentration, horizon.

   **Simulateur :** capital, durée, rendement nominal, inflation, versements et frais, avec la valeur nominale et la valeur réelle côte à côte. La leçon sur Bitcoin y présente son offre programmée, les arguments en faveur de la réserve de valeur, sa volatilité et son historique court.

### M2 · Bitcoin en profondeur (trois cours)

1. **Origines et fonctionnement.** Le livre blanc de 2008, le lancement de 2009, les clés, l'offre limitée, la vérification indépendante. La politique monétaire : récompense, halvings, frais, mineurs, difficulté, et la question ouverte de la sécurité à très long terme.
   - **Visualisation :** l'émission, **calculée exactement à partir des règles du protocole**. Il y a 50 BTC par bloc à l'origine, divisés par deux tous les 210 000 blocs, avec un arrondi au satoshi, soit un total de 20 999 999,9769 BTC. Cette courbe ne dépend d'aucun fournisseur de données. Les dates futures sont des estimations à 10 minutes par bloc, signalées comme telles.
2. **Réserve de valeur et inflation.**
   - Les propriétés (rareté, durabilité, portabilité, divisibilité, vérifiabilité, prévisibilité), comparées à l'or et à la monnaie fiduciaire, sans conclusion automatique.
   - La différence entre inflation des prix et dilution monétaire.
   - Pourquoi le prix peut baisser pendant une inflation élevée : sensibilité aux taux et à la liquidité, corrélations variables.
   - La différence entre la thèse de long terme et le comportement de court terme, et les scénarios où Bitcoin sous-performe.
3. **Cycles et indicateurs.**
   - Halvings et cycles, drawdowns, volatilité réalisée, limites des analogies.
   - Une fiche par indicateur (MVRV, SOPR, NUPL, capitalisation et prix réalisés, HODL Waves, flux des exchanges, hash rate, frais) : définition, calcul, interprétation, exemple historique, limites, source, cas où il trompe.

### C1 · Blockchain, wallets et sécurité

- **Démonstrations :** une chaîne de blocs où modifier une transaction casse les hash suivants, et une preuve de travail jouet à difficulté réglable. Elles utilisent le SHA-256 réel de Python, sans dépendance.
- **Explorateur pédagogique :** une transaction fictive avec ses entrées, ses sorties, ses frais et ses confirmations.
- **Sécurité :** wallets custodial et non custodial, seed phrase, vérification d'adresse, hameçonnage et faux supports, erreurs de réseau.
- **Exchanges :** centralisés et décentralisés, ordres, spread, stablecoins, risque de contrepartie.
- **Garde-fou :** la plateforme ne demande jamais de clé ni de seed, et aucun exercice ne nécessite de connecter un vrai portefeuille. Un test vérifiera qu'aucun champ de saisie ne porte ces noms.

### C2 · Altcoins et analyse crypto

Tokenomics, dilution et unlocks, revenus, gouvernance, DeFi (prêt, DEX, staking, bridges, exploits), TVL et ses limites, open interest, funding, liquidations, corrélation avec Bitcoin. Les études de cas comparent des actifs **sans jamais formuler de recommandation**.

### I1 · Stratégies d'investissement crypto

DCA, VCA, investissement en une fois ou progressif, rééquilibrage, allocation entre Bitcoin, altcoins et liquidités, drawdowns, frais et fiscalité. Simulateurs dans l'ordre de la vision : comparateur DCA et VCA, versements périodiques, drawdown et récupération, rééquilibrage, comparaison d'allocations, concentration, corrélations, scénarios de volatilité. Chacun affiche ses hypothèses et ses limites, et réutilise les moteurs existants quand ils sont validés.

### I2 · La méthode du fondateur

Un espace éditorial : convictions, indicateurs suivis, critères, règles de risque, conditions d'invalidation, erreurs et limites. Deux nouveaux encadrés, **« Opinion du fondateur »** et **« Débat »**, distinguent visuellement les opinions et les controverses des faits.

**Ce contenu doit venir de vous :** je fournirai la structure et la mise en forme, mais je n'écrirai pas vos convictions à votre place.

## 4. Données, sources et licences

| Donnée | Source envisagée | Point à régler |
|---|---|---|
| Émission de Bitcoin, halvings | règles du protocole, calcul exact ; dates passées des halvings | aucun |
| Inflation France, zone euro, États-Unis | INSEE (IPC), Eurostat (IPCH), BLS (CPI) : données publiques réutilisables avec attribution | accès réseau ouvert le 17 octobre 2026 (sauf api.insee.fr) |
| Taux directeurs | BCE, Réserve fédérale | même point réseau |
| Prix historique de Bitcoin | à choisir | **licence à vérifier** : plusieurs jeux gratuits (dont Coin Metrics Community) sont, à ma connaissance, sous licence non commerciale |
| Indicateurs on-chain (MVRV, SOPR, NUPL…) | fournisseur spécialisé, généralement payant | **décision d'achat ou de licence** avant toute courbe historique |

Chaque jeu de données vivra dans un dossier dédié, avec un manifeste (source, URL, licence, date de récupération, unités) contrôlé par le validateur. Un graphique dont la donnée n'a pas de source ne pourra pas être publié, et chaque graphique affichera automatiquement sa source et sa date.

## 5. Navigation et positionnement

- **Sous-titre de la marque :** « Trading · Éducation » est devenu « Trading · Bitcoin · Crypto », puis « Trading · Monnaie · Crypto » le 18 octobre 2026. Le logo et la charte ne changent pas.
- **Décision du 17 octobre 2026 :** le trading reste la porte d'entrée ; la monnaie, Bitcoin et la crypto viennent le compléter. Filière Trading en tête du programme, groupe « Trader » avant « Investir ».
- **Décision du 18 octobre 2026, qui précise la précédente :** Sensitor se présente comme un seul écosystème en deux univers complémentaires, sans que l'un passe avant l'autre : apprendre le trading, comprendre la monnaie, diversifier ses investissements avec la crypto. L'accueil et l'Academy présentent les deux univers côte à côte.
- **Identité de chaque univers dans l'Academy :** chaque filière déclare son univers dans `curriculum.toml` (`universe = "trading"` ou `"monnaie"`). L'univers Trading garde l'accent bleu et les titres en Playfair Display ; l'univers Monnaie et crypto (filières Monnaie et Bitcoin, Crypto, Investissement) prend un accent cuivre et des titres en Space Grotesk. Les pages d'un cours, de ses leçons et de son quiz portent un badge d'univers et changent d'accent dans toute la colonne principale ; les cartes de cours, le programme et les graphiques suivent la même règle.
- **Barre latérale en trois piliers :** Apprendre (Academy, Bibliothèque, Psychologie, Progression), Investir (le portefeuille), Trader (Trading Lab et journal).
- **Le portefeuille et le journal restent dans leur application** jusqu'à la phase F. Les intégrer directement dans la plateforme est un chantier à part : deux chartes graphiques coexistent, et l'audit a relevé des dépendances entre leurs pages. Je ne le lancerai qu'après validation.

## 6. Accès gratuit et premium, sans facturation

- Ajouter un niveau `premium` à côté de `public` et `member` dans `academy/access.py`, lu depuis `users.tier`, sans dupliquer de contenu. Une leçon déclare simplement `access = "premium"`.
- Aucun système de paiement. L'attribution du niveau reste manuelle tant que la demande n'est pas validée.
- Plus tard, faire lire ce même niveau par l'application portefeuille, à la place de la variable `PRO_EMAILS`.

## 7. Feuille de route par lots

Chaque lot se termine par les tests, une vérification dans le navigateur, un commit et un compte rendu.

| Lot | Contenu | Nature |
|---|---|---|
| **A** ✔ | Stabilisation, correctif « Analyse », audit, ce document, point de sauvegarde | terminé |
| **B1** ✔ | Filières et numérotation par filière, champ `updated` (« Mis à jour le ») et sources obligatoires pour les nouvelles filières, encadrés « Opinion » et « Débat », registre de données sourcées, composant de graphique interactif aux couleurs de la charte, niveau d'accès Premium sans facturation | terminé |
| **B2** ✔ | Sous-titre de marque, accueil et barre latérale en quatre groupes (Apprendre, Investir, Trader, Échanger) | terminé |
| **C1** ✔ | M1, cours « La monnaie » : 9 leçons sourcées, 5 schémas, données de taux BCE et Fed, 3 exercices | terminé |
| **C2** ✔ | M1, cours « L'inflation » : 9 leçons sourcées, données Eurostat, BCE et américaines, écoles de pensée, 3 exercices | terminé |
| **C3** ✔ | M1, cours « Inflation et patrimoine » : 8 leçons, simulateur d'épargne nominal et réel, taux réel BCE, diversification, Bitcoin avec ses objections | terminé |
| **B3** ✔ | Écosystème en deux univers : accueil et Academy recadrés, couleur et typographie propres à l'univers Monnaie et crypto | terminé |
| **T8** ✔ | Trading, parcours 8 « Macroéconomie et actualité » : 9 leçons, données d'emploi, de taux et de courbe américaines (BLS et Réserve fédérale, via FRED), 5 exercices, fiche de révision | terminé |
| **C4** ✔ | M2, cours « Bitcoin : origines et fonctionnement » : 8 leçons sourcées, émission calculée, probabilité de rattrapage du livre blanc recalculée, démonstration d'empreinte et de preuve de travail jouet, 4 exercices | terminé |
| **C5** | M2, cours « Réserve de valeur et inflation » | dépend des données d'inflation |
| **C6** | M2, cours « Cycles et indicateurs » | dépend de la licence on-chain |
| **D** | C1 : chaîne de hash, preuve de travail jouet, explorateur, sécurité | contenu et démonstrations |
| **E** | C2 et I1 : altcoins, DeFi, DCA et VCA, simulateurs | contenu et simulateurs |
| **F** | Portefeuille et trading : référence Bitcoin, option 365 jours pour la crypto (avec tests et justification), liens Academy vers les outils, niveaux d'accès unifiés, rapprochement des chartes | modifications d'outils existants, une par une |
| **G** | Tests avec des utilisateurs, retours, priorisation | validation |

## 8. Décisions attendues

1. **Filières :** l'organisation en quatre filières, Monnaie et Bitcoin en tête, avec une numérotation par filière (lot B1).
2. **Positionnement visible :** le sous-titre « Bitcoin · Crypto · Trading » et la barre latérale en trois piliers (lot B2).
3. **Données :** autoriser l'accès réseau à l'INSEE, Eurostat, au BLS, à la BCE et à la Fed, ou me fournir les fichiers ; choisir une source de prix Bitcoin et, plus tard, un fournisseur on-chain, en connaissant leur licence.
4. **Méthode du fondateur :** me transmettre vos notes, convictions, règles et indicateurs suivis, pour le parcours I2.
5. **Premium :** quels contenus réserver, si vous souhaitez déjà en réserver. Par défaut, tout reste accessible aux membres gratuits.
6. **Mise en production :** la branche contient tout le travail de l'Academy, absent de `main`. Une pull request peut être préparée quand vous le souhaitez ; je ne déploie rien sans votre accord.
