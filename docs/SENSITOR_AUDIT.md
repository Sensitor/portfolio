# Sensitor · audit technique

Audit du dépôt au 30 octobre 2026, branche `claude/improve-portfolio-ui-WLAR3`
(commit `46ff348`). Lecture seule : aucune fonctionnalité n'a été modifiée pour
le produire. La feuille de route qui en découle est dans
`docs/SENSITOR_PRODUCT_ROADMAP.md`.

Chaque constat porte l'un de ces statuts :

| Statut | Sens |
|---|---|
| **Testé** | existe, et un test de `tests/` l'exerce (le test est cité) |
| **Non testé** | existe, aucun test ne l'exerce |
| **Partiel** | existe en partie, ou avec une lacune décrite |
| **Absent** | n'existe pas dans le code |
| **Prod ?** | dépend du déploiement réel, à vérifier en production |

Les chemins sont relatifs à la racine du dépôt ; `fichier:ligne` renvoie à la
ligne au moment de l'audit.

---

## 0. Résultats des tests

Suite complète lancée le 30 octobre 2026 : **22 fichiers, 3 814 vérifications,
0 échec.**

| Fichier | Vérifications | Durée |
|---|---:|---:|
| `test_academy.py` | 1 380 | 34 s |
| `test_academy_app.py` | 596 | 102 s |
| `test_sensitor_pages.py` | 216 | 193 s |
| `test_trading_engine.py` | 178 | 2 s |
| `test_api.py` | 176 | 5 s |
| `test_database.py` | 148 | < 1 s |
| `test_mt5_connector.py` | 131 | < 1 s |
| `test_journal.py` | 128 | < 1 s |
| `test_currency.py` | 111 | 2 s |
| `test_platform.py` | 105 | < 1 s |
| `test_auth.py` | 95 | 3 s |
| `test_academy_api.py` | 92 | 6 s |
| `test_trading_pages.py` | 90 | 36 s |
| `test_portfolio_space.py` | 85 | 25 s |
| `test_market.py` | 57 | 4 s |
| `test_accounts.py` | 47 | 1 s |
| `test_investment_engine.py` | 47 | 2 s |
| `test_mt5_report.py` | 43 | 4 s |
| `test_journal_analytics.py` | 35 | 7 s |
| `test_workspace.py` | 23 | < 1 s |
| `test_french_numbers.py` | 21 | 8 s |
| `test_db_errors.py` | 10 | 3 s |

`python -m sensitor.academy.validate` : « Contenu valide : 19 cours, 145 leçons
publiées, 145 quiz (563 questions), 60 exercice(s), 20 ressource(s). »

Limites de cette couverture :
- **Aucune intégration continue.** Rien ne lance ces tests à chaque modification
  (pas de dossier `.github/`).
- **PostgreSQL n'est testé qu'à la main.** `SENSITOR_TEST_PG` relance
  `tests/test_database.py` sur Postgres (`tests/test_database.py:71-84`) ; tous
  les autres tests tournent sur SQLite.
- **L'application mobile** a ses propres tests (`mobile/tests/integration.ts`),
  non lancés ici.

---

## 1. Cartographie de l'architecture

### Points d'entrée

| Fichier | Rôle |
|---|---|
| `sensitor_app.py` (36 l.) | la plateforme Streamlit en français. Copie les secrets dans l'environnement (`runtime.mirror_secrets`), puis `sensitor/platform/ui/shell.py:main` |
| `academy_app.py` (12 l.) | ancien point d'entrée, relance `sensitor_app.py` (testé : `test_academy_app.py:624`) |
| `portfolio_optimizer_saas.py` (2 745 l.) | l'application d'analyse séparée, bilingue, avec sa propre barre latérale et sa propre connexion |
| `sensitor/api/app.py` | API FastAPI facultative : 6 routeurs, `/health`, `/meta` ; fastapi et uvicorn sont commentés dans `requirements.txt:20-21` |
| `mobile/` | application Expo (SDK 57) qui parle à l'API |
| `landing_page.html` | ancienne page anglaise « Portfolio Optimizer Pro », reliée à rien (voir §3) |
| `scripts/build_resource_pdfs.py` | outil de développement : PDF de la Bibliothèque (Playwright) |

### Paquets sous `sensitor/` (lignes de Python)

| Paquet | Lignes | Contenu |
|---|---:|---|
| `platform/` | 7 284 | registre des espaces (`spaces.py`), règles de la salle des marchés et du journal de réflexion, fiches d'actifs ; `platform/ui/` : coquille, thème, Journal de trading, Portefeuille et risque, Salle des marchés, revues coach, compte |
| `academy/` | 6 551 | chargement et validation du contenu (`content.py`, 978 l.), accès (`access.py`), un module pur par sujet ; `academy/ui/` : pages Academy, leçon, quiz, Bibliothèque |
| `investment/` | 5 773 | moteur du portefeuille (`portfolio.py`), risque, optimisation, Monte Carlo, stress tests, devises, catalogue d'actifs (`assets.py`, 1 257 l.) |
| `pages/` | 5 757 | les 17 écrans de l'application d'analyse, réutilisés par la plateforme |
| `trading/` | 4 159 | modèle de trade, statistiques, risque, comportement, plan et revue, saisie, coaching, données de démonstration |
| `core/` | 2 842 | authentification, sécurité, configuration, e-mails, CLI d'administration, traductions, chiffres en français |
| `database/` | 2 692 | `Store` (`repositories.py`, 1 212 l.), schéma (`models.py`, version 11), SQLite et PostgreSQL |
| `ui/` | 2 575 | thème, composants et graphiques de l'application d'analyse |
| `api/` | 1 610 | application et routeurs FastAPI |
| `integrations/` | 1 360 | MetaTrader 5 (terminal et rapport), synchronisation, données de marché |
| `ai/` | 1 138 | copilotes à règles fixes, sans modèle de langage |

Au total : 182 fichiers Python, 55 828 lignes, dont 10 895 lignes de tests.

### Fonctionnement de la plateforme
- **Routage.** Chaque page a un rendu dans `shell.py:23-66` ; une page inconnue
  retombe sur l'accueil. La page et ses paramètres vivent dans l'URL
  (`?page=…`) ; les paramètres autorisés sont listés dans
  `runtime.ROUTE_FIELDS` (`runtime.py:48`).
- **Espaces.** `spaces.py` déclare chaque espace avec un statut (`LIVE`,
  `PREPARING`) et ses pages ; la barre latérale en est tirée. Le statut
  `SEPARATE` n'est plus utilisé (code mort : `spaces.py:23`, `theme.py:143-149`).
- **Partage avec l'application d'analyse.** Même base (`SENSITOR_DB_URL` ou
  `SENSITOR_DB_PATH`), même authentification (`core/auth.py`), même jeton de
  session. Les espaces Portefeuille et Journal de la plateforme réutilisent ses
  écrans (`platform/ui/portfolio_space.py`, `platform/ui/journal_analysis.py`).

### Dépendances
`requirements.txt` : streamlit épinglé `>=1.64,<1.65` (le thème dépend de la
structure HTML de Streamlit), puis pandas, numpy, yfinance, plotly, scipy,
python-dateutil, psycopg2-binary, avec une borne basse seulement. Pas de
fichier de verrouillage. Chargées à la demande : `psycopg2`, `MetaTrader5`
(Windows seulement), fastapi. Le code exige Python 3.11 (`tomllib`), mais rien
ne fixe la version au déploiement (seul `.devcontainer/devcontainer.json:4`
indique 3.11). **Prod ?**

---

## 2. Fonctionnalités opérationnelles

### Plateforme (`sensitor_app.py`)

| Espace | Pages | Statut |
|---|---|---|
| Accueil, compte, mot de passe oublié, vérification d'adresse | `home`, `account`, `reset`, `verify` | **Testé** : `test_academy_app.py`, `test_accounts.py`, `test_auth.py`, `test_db_errors.py` |
| I. Academy | `academy`, `course`, `lesson`, `quiz` | **Testé** : `test_academy.py`, `test_academy_app.py` (toutes les leçons et tous les quiz sont rendus), `test_academy_api.py` |
| II. Bibliothèque | `library`, `resource` | **Testé** : `test_academy_app.py`, `test_academy.py` (manifeste des PDF) |
| III. Psychologie et discipline | `psychology` | **Testé** : `test_platform.py:65`, `test_academy_app.py:566` |
| IV. Progression | `progress` | **Testé** : `test_academy_app.py:522` |
| V. Trading Lab | `lab` (simulateurs, prop firm) | **Testé** : `test_academy_app.py:408-423`, `test_academy.py:1564` |
| VI. Journal de trading | tableau de bord, trades, fiche, saisie, plan, revues, Performance, Analyse, Risque, Comportement | **Testé** : `test_journal.py`, `test_academy_app.py:275-353`, `test_journal_analytics.py`, `test_mt5_report.py`, `test_french_numbers.py` |
| Import du rapport MetaTrader 5 | section 1 de « Saisir » | **Testé** : `test_mt5_report.py` (rapport reconstitué sur la structure d'un export réel) |
| Synchronisation du terminal MT5 | section 4 de « Saisir » | **Testé** avec un faux terminal (`test_journal_analytics.py:212`, `test_mt5_connector.py`) ; **Prod ?** n'a de sens que sur un serveur Windows avec MT5 |
| VII. Salle des marchés | `market`, `market_session`, `market_edit` | **Testé** : `test_market.py` |
| VIII. Portefeuille et risque | construction, portefeuille réel, allocations types, actifs, 11 onglets d'analyse | **Testé** : `test_portfolio_space.py` ; les onglets performance, santé, radiographie, stress, optimisation et rapports ne sont vérifiés en profondeur que via l'application d'analyse (`test_sensitor_pages.py`) |
| Revue d'un trade par un coach | `journal_reviews`, `coach` | **Testé** : `test_journal.py`, `test_database.py::test_trade_reviews`, `test_academy_app.py` |
| Export et suppression du compte | page Compte | **Testé** côté base (`test_accounts.py::test_export_and_delete`, `test_database.py::test_user_lifecycle`) ; l'interface n'est testée que pour sa présence |

### Application d'analyse (`portfolio_optimizer_saas.py`)
- **Écrans d'investissement** (12) et **écrans de trading** (5) : **Testé**
  (`test_sensitor_pages.py` : 12 pages × 5 portefeuilles × 2 langues ;
  `test_trading_pages.py`, `test_workspace.py`).
- **Pages historiques** `models`, `improve`, `dashboard`, `library`,
  `real_portfolio`, `account` : **Non testé**. `new_analysis` : **Partiel**
  (`test_sensitor_pages.py:248`).

### API (`sensitor/api`)
Authentification par jeton porteur, sur la même table de sessions. Routes :
`/auth/*`, `/trading/*` (lecture seule), `/mobile/*`, `/portfolios/*`,
`/academy/*`, `/journal/*` (journal de réflexion), `/health`, `/meta`. Pas de
préfixe de version. **Testé** : `test_api.py` (dont
`test_every_protected_route_requires_a_token`, 18 routes) et
`test_academy_api.py`. L'application mobile appelle `/meta`, `/health`,
`/auth/*`, `/mobile/*`, `/trading/*` et `/portfolios*`
(`mobile/src/api/client.ts:189-315`) : **ces routes, leurs paramètres et le
comportement ETag/304 doivent rester stables.**

---

## 3. Présent mais incomplet

| Constat | Référence | Statut |
|---|---|---|
| Deux parcours annoncés sans contenu : méthode Sensitor (Trading 9), méthode du fondateur (Investissement 2) | `content/academy/curriculum.toml`, `test_academy.py:94` | **Absent** (annoncé) |
| Vidéos et ebooks annoncés « bientôt » | `academy/ui/pages.py:28-37` | **Absent** |
| Communauté : page « en préparation » honnête, rien derrière | `spaces.py:117-122` | **Absent** |
| « Captures de graphique jointes à un trade », « être prévenu à la publication d'une séance », « études de cas », « simulations de scénarios » | `spaces.py:86,96,104` | **Absent** (annoncé) |
| L'import du rapport MT5 est encore annoncé comme « à venir » alors qu'il existe | `spaces.py:95` | entrée périmée |
| Résultats d'exercices non enregistrés (seulement en session) | `academy/ui/exercise_view.py:23` | **Partiel** |
| Aucun contenu Premium : 0 leçon, 0 ressource premium ; un test l'affirme | `tests/test_academy.py:1247` | **Absent** par choix |
| Bibliothèque : une ressource premium serait étiquetée « Membres », et l'invite dit « Se connecter » même à un membre connecté | `academy/ui/library.py:27-28` | **Partiel** |
| Quota de revues coach appliqué dans la page, pas dans la base | `trade_reviews.py:76-77`, `repositories.py:376-391` | **Partiel** |
| L'API ne vérifie pas l'accès avant de marquer une leçon terminée | `api/routers/academy.py:125-132` | **Partiel** (impact faible) |
| Données fictives montrées en production : le journal de démonstration (étiqueté « Exemple synthétique ») et 9 jeux de données de leçon marqués `synthetic` (étiquetés) | `trading/demo.py`, `platform/ui/trading_journal.py:72-74`, `academy/ui/chart_view.py:115` | **à décider** (contrainte « pas de données fictives en production ») |
| Application d'analyse : rendements attendus écrits à la main et capitalisations non sourcées | `portfolio_optimizer_saas.py:2344`, `:605-607` | contraire à la règle des chiffres sourcés ; la plateforme les masque déjà |
| Application d'analyse : bouton d'abonnement Stripe à 9,99 $/mois dès que `STRIPE_PAYMENT_LINK` est défini, et texte « Set STRIPE_PAYMENT_LINK env var to activate. » visible sinon | `portfolio_optimizer_saas.py:783-819`, `:1626-1690` | contraire à CLAUDE.md (pas de paiement sans revue réglementaire) |
| `landing_page.html` : chiffres inventés (« 10K+ Portfolios Analyzed », « 4.9/5 »), liens Stripe de test, offre « Business » inexistante, en anglais | `landing_page.html:356-368`, `:408`, `:423` | à retirer ou archiver |
| `DEPLOYMENT_GUIDE.md` : Stripe et un webhook vers Streamlit, impossible | `DEPLOYMENT_GUIDE.md:113` | obsolète |
| Deux interfaces de journal de trading sur la même table (application d'analyse et plateforme), chacune avec son formulaire MT5 | `pages/trading_journal.py`, `platform/ui/trading_journal.py` | doublon |
| Documentation en retard sur le code : `V1.md` (18 cours au lieu de 19, MT5 « dans l'application d'analyse »), `ARCHITECTURE.md` (antérieur à la plateforme), `ACADEMY.md` §1, README (arborescence et tests) | `docs/` | à mettre à jour |

---

## 4. Authentification et rôles

### Ce qui est solide
- **Mots de passe** : scrypt (n = 16 384, r = 8, p = 1, sel de 16 octets),
  paramètres enregistrés avec l'empreinte et relevés à la connexion suivante,
  comparaison à temps constant (`core/security.py:41-101`). **Testé**
  (`test_auth.py::test_password_hashing`, `test_rehash_on_sign_in`).
- **Sessions** : jeton `secrets.token_urlsafe(32)`, seule son empreinte SHA-256
  est stockée ; expiration à 30 jours vérifiée en SQL ; révocation à la
  déconnexion, partout, au changement et à la réinitialisation du mot de passe,
  à la suppression du compte. **Testé** (`test_auth.py::test_tokens`,
  `test_sessions`, `test_password_change`, `test_accounts.py::test_reset`).
- **Verrouillage** : 5 échecs bloquent le compte 15 minutes, compteur en base,
  donc commun aux deux applications et à l'API et conservé au redémarrage.
  **Testé** (`test_auth.py::test_lockout`).
- **Réinitialisation et vérification d'adresse** : liens à usage unique (60 min
  et 48 h), le lien précédent est retiré. **Testé**
  (`test_accounts.py::test_reset`, `test_verification`).
- **Connexion** : adresse inconnue et mauvais mot de passe donnent le même
  message. **Testé** (`test_auth.py::test_sign_up_and_in`).

### Problèmes

| # | Constat | Référence | Gravité | Statut |
|---|---|---|---|---|
| A1 | **Sans `SENSITOR_AUTH=multi`, il n'y a pas d'authentification** : n'importe quelle adresse ouvre le compte correspondant. Mode par défaut : `single` | `core/auth.py:57-67`, `:141-143`, `:173-175` | critique si oublié | **Testé** (le comportement) ; **Prod ?** (vos secrets indiquent `multi`) |
| A2 | **Prise de compte à l'inscription** : en mode multi, l'inscription n'est refusée que si le compte a déjà un mot de passe. Une ligne `users` sans mot de passe (créée en mode single, ou avant le passage à multi) peut être réclamée par quiconque connaît l'adresse ; `change_password` ne demande pas l'ancien mot de passe s'il n'y en a pas | `core/auth.py:145`, `:268-269` | élevée si des comptes sans mot de passe existent | **Absent** (protection) |
| A3 | **Le niveau Premium est écrasé** : `upsert_user` remplace toujours `tier`. La page Portefeuilles de l'application d'analyse l'appelle avec le niveau tiré de `PRO_EMAILS`, donc un membre passé Premium par `set-tier` redevient `free` dès qu'il ouvre cette page ; en mode single, chaque connexion fait de même | `database/repositories.py:83-99`, `pages/portfolios.py:44`, `core/auth.py:174` | élevée dès qu'il y aura des Premium | **Absent** (protection) |
| A4 | **Trois orthographes du niveau payant et deux sources de vérité** : `free/premium` (`core/admin.py:28`), `pro/premium` (`academy/access.py:24`), `free/pro` (`core/config.py:43-48`), quotas `free/member/pro/premium` (`trading/coaching.py:30`). L'application d'analyse lit `PRO_EMAILS` (variable d'environnement) et ignore `users.tier` ; la plateforme lit `users.tier` | `portfolio_optimizer_saas.py:140-142`, `:1464`, `platform/ui/portfolio_space.py:134` | moyenne | **Partiel** |
| A5 | **Optimisation et stress tests ouverts aux comptes gratuits** dans les nouveaux écrans de l'application d'analyse et dans la plateforme ; seuls les écrans historiques les réservent. Seul le nombre de lignes (`max_assets`) est appliqué | `portfolio_optimizer_saas.py:1269-1270`, `pages/stress.py`, `pages/optimize_page.py`, `portfolio_space.py:61-62` | faible tant que rien n'est payant | **Partiel** |
| A6 | **Pas de rôle administrateur** : les rôles sont `''` ou `coach`, attribués uniquement en ligne de commande (`set-role`, `set-tier`) ; aucune page d'administration | `models.py:45-47`, `core/admin.py` | bloquant pour la gestion interne | **Absent** ; `set-role` et `set-tier` **Non testé** |
| A7 | **Un coach peut modifier, publier ou supprimer la séance d'un autre coach, et répondre à n'importe quelle revue** : pas de propriétaire ni d'attribution | `repositories.py:484-561` | faible avec un seul coach | **Partiel** |
| A8 | **L'inscription révèle qu'une adresse a déjà un compte** (« déjà inscrit », 409 dans l'API) ; le verrouillage aussi (429 avec heure de déblocage) | `account.py:27`, `api/routers/auth.py:61-65`, `:94` | faible | **Testé** (comportement voulu) |
| A9 | **Pas de limite par IP ni sur l'inscription, la réinitialisation ou le renvoi de vérification** ; on peut faire envoyer des e-mails en boucle. Après expiration du verrou, `failed_logins` n'est pas remis à zéro : chaque échec suivant reverrouille, ce qui permet de bloquer un compte à distance | `core/auth.py:199-218`, `account.py:134-154` | moyenne | **Absent** |
| A10 | **La vérification d'adresse ne conditionne rien** : on peut s'inscrire avec l'adresse d'un autre ; le lien est consommé par une simple ouverture, que les antivirus de messagerie peuvent déclencher | `models.py:41-42`, `account.py:266-269` | moyenne pour une newsletter | **Partiel** |
| A11 | **Cookie de session non HttpOnly** (écrit en JavaScript, limite de Streamlit reconnue), `Secure` seulement en https, `SameSite=Lax`, 30 jours | `platform/ui/runtime.py:13-23`, `:164-177` | moyenne | **Non testé** ; **Prod ?** |
| A12 | **Sessions expirées jamais purgées** : `purge_expired_sessions` n'est appelée nulle part | `repositories.py:747` | faible | **Non testé** |

---

## 5. Sécurité et confidentialité

### Isolation des données
- Toutes les méthodes du `Store` qui lisent ou écrivent des données de membre
  filtrent sur l'adresse. **Testé** par introspection
  (`test_database.py::test_every_user_method_is_scoped`, liste d'exemptions à
  `:218-232`), `test_isolation`, `test_api.py::test_one_account_cannot_read_another`.
- Exceptions voulues : séances de la salle des marchés (contenu partagé), file
  des coachs (filtrée par rôle), sessions et jetons (clé = empreinte).
- Les caches Streamlit ne contiennent que la connexion à la base, les prix de
  marché par symbole, le catalogue et les fiches d'actifs : aucune donnée de
  membre. **Testé** pour le journal (`pages/_trading_shared.py:14-16`).

### Problèmes

| # | Constat | Référence | Gravité | Statut |
|---|---|---|---|---|
| S1 | **Navigateur partagé** : la déconnexion de la plateforme ne retire que le jeton et l'état des quiz. Le portefeuille en cours (`current_portfolio`, `real_portfolio_holdings`, `manual_prices`…) reste en session, et `_workspace.restore` ne vide rien quand le membre suivant n'a pas de portefeuille enregistré : il voit, et peut enregistrer sous son nom, celui du précédent | `platform/ui/runtime.py:201-209`, `pages/_workspace.py:80-97` | élevée sur un poste partagé | **Partiel** (l'application d'analyse, elle, nettoie : `portfolio_optimizer_saas.py:1457`, testé par `test_workspace.py`) |
| S2 | **Mot de passe de la base affiché** : `describe()` le masque avec `://[^@/]*@` ; avec un « / » dans le mot de passe, rien n'est masqué ; avec deux « @ », une partie reste visible. Affiché sur la page Compte de l'application d'analyse | `database/connection.py:78-84`, `portfolio_optimizer_saas.py:1395` | élevée | **Non testé** |
| S3 | **`.gitignore` incomplet** : ni `.env`, ni `.streamlit/secrets.toml`, ni `*.db` en général, ni `*.db-wal` / `*.db-shm` (seul `sensitor_data.db`). Aucun secret n'est suivi aujourd'hui (vérifié avec `git ls-files`) | `.gitignore:1-12` | moyenne | **Partiel** |
| S4 | **Pseudonyme du coach réversible** : SHA-256 de l'adresse avec un préfixe fixe et public (`sensitor-review:`, dans le code), tronqué à 24 bits ; un coach qui a une liste d'adresses peut retrouver le membre. Un secret côté serveur (HMAC) l'empêcherait | `trading/coaching.py:56-62` | moyenne | **Testé** (stabilité seulement) |
| S5 | **Séance verrouillée de la salle des marchés** : un extrait de 220 caractères et le bilan des séances précédentes s'affichent sans contrôle d'accès | `platform/ui/market_room.py:142`, `:148-157` | faible | **Partiel** |
| S6 | **Export incomplet** : ni sessions, ni jetons, ni contenu écrit en tant que coach (séances, réponses aux revues). La suppression couvre les 14 tables, mais ne demande pas le mot de passe (il suffit de retaper son adresse). Ni export ni suppression dans l'application d'analyse ou l'API | `repositories.py:127-222`, `account.py:209-227` | moyenne (RGPD) | **Testé** pour ce qui existe ; reste **Absent** |
| S7 | **Aucune journalisation** : pas de `logging`, des exceptions avalées (`runtime.py:60,83`, `pages/_shared.py:183`), pas de suivi d'erreurs. Aucune fuite de données sensibles dans des journaux, faute de journaux ; mais aucun moyen de voir une panne | `sensitor/` | moyenne | **Absent** |
| S8 | **API** : `/docs` et `/openapi.json` publics ; `/meta` donne le mode d'authentification ; pas de limitation de débit ; pas de `Cache-Control: private` ni `Vary: Authorization` sur les réponses ETag | `api/app.py:81-151`, `api/routers/mobile.py:88-120` | faible tant que l'API n'est pas déployée | **Prod ?** |
| S9 | **Polices Google** chargées depuis `fonts.googleapis.com` (transmet l'IP des visiteurs) ; statistiques d'usage de Streamlit non désactivées (pas de `.streamlit/config.toml`) | `platform/ui/theme.py:48`, `ui/themes.py:458` | RGPD | **Prod ?** |
| S10 | **XSS sur soi-même** : la barre latérale de l'application d'analyse insère l'adresse brute dans du HTML (seule validation : contient « @ ») | `portfolio_optimizer_saas.py:1246-1250` | faible, mais le cookie n'est pas HttpOnly | **Non testé** |

### Règles déjà tenues
- **Jamais de phrase de récupération ni de clé privée** : trois tests le
  vérifient (`test_academy_app.py::test_no_secret_asked`, `:461-473` ;
  `test_hash_demo` ; `test_academy.py:788-794`). **Testé**
- **Synchronisation MT5** : elle demande le mot de passe *investisseur* (lecture
  seule), le retire de la session à l'envoi et ne le stocke jamais
  (`platform/ui/journal_analysis.py`). **Testé** (`test_journal_analytics.py`)
- **Mot de passe absent des messages d'erreur de la base** (`postgres.explain`).
  **Testé** (`test_db_errors.py`)

---

## 6. Déploiement et persistance

### État constaté
- **Hébergement prévu** : Streamlit Community Cloud pour les deux applications,
  PostgreSQL chez Neon ou Supabase (`docs/DEPLOY.md`). Ni Dockerfile, ni
  Procfile, ni `.streamlit/config.toml`, ni version de Python fixée. **Prod ?**
- **Au 29 octobre, la base de production était injoignable** :
  - l'adresse configurée était l'adresse *directe* Supabase
    (`db.<projet>.supabase.co`), qui n'a pas d'adresse IPv4 (vérifié depuis cet
    environnement) alors que Streamlit Cloud ne joint pas l'IPv6 ;
  - le mot de passe contenait un « @ » non encodé.

  Le code accepte maintenant un mot de passe collé tel quel et explique l'échec
  sur la page Compte (commit `64ba225`, **Testé** : `test_db_errors.py`). Il
  reste à changer l'adresse pour le « Session pooler » dans les secrets. **Prod ?**
- **`main` a 12 commits de retard** sur la branche : la salle des marchés,
  l'analyseur intégré, le portefeuille réel, l'import MT5, le nouveau tableau de
  bord et le correctif de connexion n'y sont pas. **Prod ?** (le déploiement
  semble suivre la branche)
- **Secrets** : chaque application copie `st.secrets` dans l'environnement pour
  une liste de clés, mais les deux listes diffèrent. `SENSITOR_MARKET_CACHE_TTL`
  et `SENSITOR_RISK_FREE_RATE` ne sont copiées par aucune
  (`platform/ui/runtime.py:37-42`, `portfolio_optimizer_saas.py:33-47`). **Non testé**
- **E-mails** : `SENSITOR_PUBLIC_URL` vaut par défaut `http://localhost:8501`.
  Sans elle, les liens de réinitialisation pointent vers localhost
  (`core/mailer.py:30`). **Prod ?**

### Persistance

| # | Constat | Référence | Gravité | Statut |
|---|---|---|---|---|
| D1 | **Aucune reconnexion PostgreSQL** : une seule connexion par processus, mise en cache, partagée par toutes les sessions. Si le serveur la coupe (mise en veille Neon, délai du pooler Supabase), chaque requête échoue jusqu'au redémarrage de l'application | `platform/ui/runtime.py:70-73`, `database/postgres.py:257-362` | **élevée** | **Absent** |
| D2 | **Lectures sans fin de transaction** : en psycopg2 sans autocommit, une lecture laisse la connexion « idle in transaction » ; une lecture en erreur bloque la connexion jusqu'à la prochaine écriture | `repositories.py:64-75` | moyenne | **Prod ?** |
| D3 | **Deux connexions par processus de plateforme**, avec des comportements d'échec différents : `pages/_shared.get_store` met `None` en cache jusqu'au redémarrage | `pages/_shared.py:170-184`, `runtime.py:76-90` | moyenne | **Partiel** |
| D4 | **Toutes les requêtes passent l'une après l'autre** (un verrou global sur le `Store`) : correct, mais le débit dépend de la latence vers la base distante | `repositories.py:55-79` | à mesurer | **Prod ?** |
| D5 | **Aucune sauvegarde ni restauration** documentée ou outillée ; seul l'export JSON par membre existe, sans import | `scripts/`, `repositories.py:190-222` | **élevée** | **Absent** |
| D6 | **Migrations PostgreSQL** : ajout de colonnes seulement, pas de reconstruction de table ; un futur changement de contrainte n'aura pas d'outil | `database/connection.py:124-147` | moyenne | **Partiel** |
| D7 | **Fonction `_has` définie deux fois** dans `models.py` : la seconde gagne et rend un booléen. Un `workspace` ancien dont `manual_prices` vaut NULL fait échouer la lecture, et l'échec est avalé : le portefeuille n'est pas restauré | `database/models.py:474`, `:669`, `:498` | faible | **Non testé** |

Schéma (version 11, `models.py:25`) : `users`, `sessions`, `account_tokens`,
`portfolios`, `workspace`, `snapshots`, `trading_accounts`, `trades`,
`lesson_progress`, `quiz_attempts`, `journal_entries`, `trading_plans`,
`trade_reviews`, `market_sessions` (+ `schema_meta` sous Postgres). Migrations
SQLite **Testé** (`test_database.py::test_migration`,
`test_accounts.py::test_upgrade`).

---

## 7. Academy et contenus publiés

**Le contenu est valide et entièrement publié.**

| Élément | Nombre |
|---|---:|
| Parcours | 15 (13 publiés, 2 annoncés sans contenu) |
| Cours | 19, tous publiés |
| Leçons | 145, 2 177 minutes de lecture |
| Accès des leçons | 20 publiques, 125 réservées aux membres, **0 premium** |
| Quiz | 145 (19 finaux, 126 de contrôle), 563 questions |
| Exercices | 60, 299 étapes |
| Ressources | 20 (17 fiches, 2 listes de contrôle, 1 guide), Markdown et PDF ; 5 publiques, 15 membres |
| Jeux de données | 35, tous avec source, licence et date (16 fichiers d'organismes publics, 10 calculés, 9 synthétiques étiquetés) |
| Graphiques / figures | 46 graphiques interactifs, 49 figures SVG |

### Univers
- **Monnaie et crypto** : 8 cours (la monnaie, l'inflation, inflation et
  patrimoine, Bitcoin fonctionnement, Bitcoin réserve de valeur, crypto en
  sécurité, analyser un projet crypto, métriques on-chain) et 1 cours
  d'investissement (investir avec méthode).
- **Trading** : 10 cours.

C'est un point important pour la nouvelle vision, centrée d'abord sur Bitcoin,
la crypto, l'économie monétaire et l'investissement : **aujourd'hui, plus de la
moitié des cours sont du trading**, et le parcours Investissement 2 (méthode du
fondateur) est vide.

### Contrôle d'accès
- Une seule règle dans `academy/access.py:34-64`.
- Elle est appliquée **côté serveur** :
  - dans Streamlit, le corps d'une leçon verrouillée n'est jamais rendu
    (`academy/ui/pages.py:358-376`) ;
  - dans l'API, 401 ou 403 (`api/routers/academy.py:116-245`).
- **Testé** (`test_academy_app.py:192-200`, `test_academy.py::test_access_levels`).
- Lacune : aucun test de l'API ne couvre le cas 403 Premium.

### Règles de qualité
- **Pas de tirets longs** : vérifié sur tout le contenu et les pages rendues
  (`test_academy.py:143-146`, `test_academy_app.py:480-487`). **Testé**
- **Sources et dates obligatoires** dans les filières Monnaie, Crypto et
  Investissement (`academy/content.py:837-851`). **Testé**
- **Chiffres** : une vingtaine de tests `test_*_figures` recalculent les
  chiffres cités. Mais il n'y a pas de détecteur général : un nouveau chiffre
  sans test passerait. **Partiel**
- **Opinions et débats** : 5 encadrés d'opinion, 24 de débat. **Testé**
  pour leur rendu.

### À faire valider
- **Fiscalité** : la leçon `investir-avec-methode/lessons/fiscalite-crypto.md:38-40`
  et l'exercice `plus-value-150vh.toml` utilisent 31,4 % (« plusieurs sources
  indiquent »). La leçon `inflation-et-patrimoine/lessons/frais-impots.md:37,55`
  utilise 30 %. Les deux ne sont pas réconciliées, et aucune source officielle
  n'est confirmée.

### Média public et référencement
- **Absent.**
  - Pas de type « article » ni de flux RSS.
  - Un seul titre de page (« Sensitor ») pour toutes les routes
    (`sensitor_app.py:23-28`), pas de meta description, d'Open Graph, de
    sitemap ni de `robots.txt`.
  - La navigation se fait par boutons, pas par liens.
- Streamlit envoie une page vide puis le contenu par websocket : **un moteur de
  recherche ne voit pas le contenu.** Un média public demande un front distinct
  (voir la feuille de route).

---

## 8. Newsletter

- **Absent** : aucune table, aucun champ de consentement, aucun formulaire,
  aucun lien de désinscription.
- **L'envoi d'e-mails existe** : SMTP (`core/mailer.py`), deux messages
  transactionnels en texte brut, réinitialisation et vérification. **Testé**
  (`test_accounts.py::test_mailer`, transport simulé).
- Ces messages n'ont pas d'en-têtes `Date`, `Message-ID` ou
  `List-Unsubscribe` (`core/mailer.py:96-102`).
- **Points d'insertion possibles** :
  - l'accueil public, `platform/ui/home.py` (`_landing`, lignes 67-128) ;
  - le formulaire d'inscription, `platform/ui/account.py:107-117` (case non
    cochée) ;
  - la page Compte du membre, `account.py:157-227`.
- **Pour un média public sur un site statique**, le formulaire vivrait sur ce
  site et parlerait au prestataire d'envoi.
- **Prérequis RGPD** :
  - consentement distinct et non pré-coché, avec preuve (date, source, version
    du texte) ;
  - double confirmation ;
  - désinscription en un clic ;
  - prise en compte dans l'export et la suppression ;
  - politique de confidentialité (absente aujourd'hui).

---

## 9. Paiement

- **Absent dans la plateforme**, conformément à CLAUDE.md : aucun SDK, aucune
  table d'abonnement, aucun webhook.
- **Exception à corriger** : le bouton Stripe de l'application d'analyse
  (§3, `portfolio_optimizer_saas.py:783-819`, `:1626-1690`).
- **Stockage du niveau** : la colonne `users.tier` (`models.py:31`), à unifier
  d'abord (§4, A3 et A4).
- **Où brancher un paiement vérifié** :
  - pas dans Streamlit, qui ne reçoit pas de requêtes HTTP arbitraires ;
  - dans l'API FastAPI, comme un nouveau routeur (`api/app.py:80-85`).
- **Ce que cela suppose** :
  - une méthode `Store` dédiée au niveau ;
  - une table d'abonnements (statut, fin de période, identifiant client) ;
  - une table d'événements reçus, pour ignorer les doublons ;
  - le déploiement de l'API sur la même base ;
  - la revue réglementaire exigée par CLAUDE.md, des conditions générales de
    vente et la gestion de la TVA et du droit de rétractation.

---

## 10. Gestion interne

| Besoin | État | Référence |
|---|---|---|
| Liste des membres | méthode `Store.list_users()` sans interface | `repositories.py:105-108` (**Testé** : `test_database.py:293`) |
| Attribuer un niveau ou un rôle | ligne de commande seulement | `core/admin.py` (**Non testé** pour `set-tier`, `set-role`) |
| Coachs : file de revue, réponse, salle des marchés | existe | **Testé** (`test_database.py::test_trade_reviews`, `test_market.py`) |
| Cohortes, ateliers, demandes d'accompagnement | rien | **Absent** |
| Statistiques d'acquisition et de conversion | seulement `users.created_at` et `last_login_at`, ni source d'inscription ni UTM | **Absent** |

---

## 11. Risques de régression

| Zone | Pourquoi | Garde-fous existants |
|---|---|---|
| `sensitor/pages/*` | écrans partagés par l'application d'analyse et deux espaces de la plateforme ; la plateforme écrit les clés de session de l'analyseur (`portfolio_space.py:117-141`) et traduit sa navigation (`_hop`) | `test_portfolio_space.py`, `test_journal_analytics.py`, `test_sensitor_pages.py` |
| `core/numbers.py` | réécrit en français tout le HTML de l'analyseur (`ui/themes.py:198-214`) et chaque graphique (`ui/charts.py:1246-1257`) dès que la langue est le français | `test_french_numbers.py`, `test_sensitor_pages.py` |
| Niveau d'accès | trois vocabulaires et deux sources ; toute centralisation touche l'Academy, la salle des marchés, l'analyseur, les quotas de revue et l'API | `test_academy.py::test_access_levels`, `test_academy_api.py`, `test_portfolio_space.py` |
| Base de données | un seul `Store` pour deux moteurs ; un changement de requête doit passer sur SQLite et sur Postgres, or Postgres n'est testé qu'à la main | `test_database.py` (+ `SENSITOR_TEST_PG`) |
| Thème | Streamlit épinglé `<1.65` : le CSS vise des attributs internes (`data-testid`, `st-key-*`) | captures manuelles, pas de test visuel |
| Routage | tout nouveau paramètre d'URL doit entrer dans `ROUTE_FIELDS` ; toute page doit avoir un rendu | `test_platform.py:134-139` |
| Pages historiques de l'analyseur | non testées | aucun |
| API | routes utilisées par l'application mobile | `test_api.py`, `mobile/tests/integration.ts` |
