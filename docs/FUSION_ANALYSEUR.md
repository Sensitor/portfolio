# Fusion de l'analyseur dans la plateforme (P3.5)

État au 2 novembre 2026. L'analyseur (`portfolio_optimizer_saas.py`) reste en
ligne pour ses pages d'analyse et de trading ; ses six pages historiques ont été
retirées le 2 novembre 2026, avec l'accord du fondateur (le fichier est passé
d'environ 2 700 à 950 lignes). Ce document dit, page par page, où se trouve
l'équivalent dans la plateforme.

Quand `SENSITOR_PUBLIC_URL` est réglée, la barre latérale de l'analyseur
indique que ses écrans sont dans la plateforme, avec un bouton pour l'ouvrir.

## Pages déjà dans la plateforme

| Page de l'analyseur | Dans la plateforme | Testée |
|---|---|---|
| `overview`, `performance`, `health`, `xray`, `risk`, `stress`, `optimize`, `simulator`, `copilot`, `reports`, `portfolios` | espace Portefeuille et risque (`pf_*`) : les mêmes fonctions de rendu, en français | `test_portfolio_space.py`, `test_sensitor_pages.py` |
| `trading_overview`, `trading_journal`, `trading_analytics`, `trading_risk`, `trading_psychology` | espace Journal de trading : tableau de bord, performance, analyse, risque, comportement, import MT5 | `test_journal_analytics.py`, `test_trading_pages.py` |
| `account` | page Compte (export, suppression, mot de passe, lettre) | `test_accounts.py`, `test_newsletter.py` |

## Pages historiques, retirées

Elles précédaient la plateforme et n'étaient pas couvertes par les tests de
rendu. Un ancien lien, un état enregistré ou le bouton « Charger » des
portefeuilles enregistrés mène désormais à une carte qui nomme la page de la
plateforme et y renvoie (`MOVED_PAGES`, testé par `tests/test_sensitor_pages.py`) :

| Page historique | Équivalent dans la plateforme |
|---|---|
| `dashboard` | `pf_overview` |
| `new_analysis` | page Construire (`portfolio`) |
| `models` | Allocations types (`pf_models`) |
| `real_portfolio` | page Construire, mode portefeuille réel, prix manuels compris |
| `improve` | Optimiser (`pf_optimize`) |
| `library` | Bibliothèque d'actifs (`pf_assets`), avec les fiches réécrites |

Les fonctions qui ne servaient qu'à ces pages (cartes d'actifs, ancien score de
santé, ancien écran de stress tests, invite d'abonnement, éditeur de prix
manuels de l'ancienne page) ont été supprimées avec elles.

## Page à ne pas reprendre en l'état

| Page | Pourquoi |
|---|---|
| `advisor` | Elle compare les portefeuilles de plusieurs « clients » : c'est un outil de gestion pour le compte de tiers, qui relève de la revue réglementaire (`docs/REVUE_REGLEMENTAIRE.md`). Elle reste dans l'analyseur, sans être reprise dans la plateforme, jusqu'à cette revue. |

## La suite

1. Quand les membres ont pris l'habitude de la plateforme, faire de l'adresse
   de l'analyseur une redirection vers l'espace Portefeuille et risque.
2. Trancher le sort de la page `advisor` après la revue réglementaire.
