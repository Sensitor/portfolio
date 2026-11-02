# Fusion de l'analyseur dans la plateforme (P3.5)

État au 2 novembre 2026. L'analyseur (`portfolio_optimizer_saas.py`) reste en
ligne : aucune page n'en est retirée sans votre accord. Ce document dit, page
par page, où se trouve l'équivalent dans la plateforme et ce qu'il reste à
faire avant de retirer une page.

Quand `SENSITOR_PUBLIC_URL` est réglée, la barre latérale de l'analyseur
indique que ses écrans sont dans la plateforme, avec un bouton pour l'ouvrir.

## Pages déjà dans la plateforme

| Page de l'analyseur | Dans la plateforme | Testée |
|---|---|---|
| `overview`, `performance`, `health`, `xray`, `risk`, `stress`, `optimize`, `simulator`, `copilot`, `reports`, `portfolios` | espace Portefeuille et risque (`pf_*`) : les mêmes fonctions de rendu, en français | `test_portfolio_space.py`, `test_sensitor_pages.py` |
| `trading_overview`, `trading_journal`, `trading_analytics`, `trading_risk`, `trading_psychology` | espace Journal de trading : tableau de bord, performance, analyse, risque, comportement, import MT5 | `test_journal_analytics.py`, `test_trading_pages.py` |
| `account` | page Compte (export, suppression, mot de passe, lettre) | `test_accounts.py`, `test_newsletter.py` |

## Pages historiques, à retirer après votre validation

Elles précèdent la plateforme, ne sont pas couvertes par les tests de rendu et
ont toutes un équivalent :

| Page historique | Équivalent dans la plateforme |
|---|---|
| `dashboard` | `pf_overview` |
| `new_analysis` | page Construire (`portfolio`) |
| `models` | Allocations types (`pf_models`) |
| `real_portfolio` | page Construire, mode portefeuille réel, prix manuels compris |
| `improve` | Optimiser (`pf_optimize`) |
| `library` | Bibliothèque d'actifs (`pf_assets`), avec les fiches réécrites |

Critères avant de retirer une page : ses utilisateurs ont été prévenus, son
équivalent a tourné un mois sans régression, et les liens qui pointent vers elle
sont redirigés (`?page=` de l'analyseur vers la plateforme).

## Page à ne pas reprendre en l'état

| Page | Pourquoi |
|---|---|
| `advisor` | Elle compare les portefeuilles de plusieurs « clients » : c'est un outil de gestion pour le compte de tiers, qui relève de la revue réglementaire (`docs/REVUE_REGLEMENTAIRE.md`). Elle reste dans l'analyseur, sans être reprise dans la plateforme, jusqu'à cette revue. |

## La suite

1. Valider la liste des pages historiques à retirer.
2. Rediriger les adresses de l'analyseur vers la plateforme, page par page.
3. Retirer les pages validées, avec leurs chaînes de traduction devenues
   inutiles, et ne garder de l'analyseur que ce que la plateforme n'a pas.
