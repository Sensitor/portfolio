# Sensitor — Architecture Map

Written before the V2 restructure, from an inspection of the repository at
`028633b`. It records what exists, what depends on what, and what would break if
moved — so the refactor can be checked against reality rather than intention.

---

## 1. What exists today

Two layers coexist. Both are live; the first is the process entry point.

### Layer A — the legacy monolith

`portfolio_optimizer_saas.py` — **3,921 lines**. The Streamlit entry point.

| Lines | Section | Nature |
|---|---|---|
| 35–65 | `STRIPE_CONFIG`, `TIER_LIMITS`, `PRO_EMAILS` | configuration |
| 66–76 | `st.set_page_config` | UI |
| 77–601 | CSS block (524 lines) | UI |
| 602–1232 | `ASSET_INFO`, `SECTOR_MAPPING`, `GEOGRAPHY_MAPPING`, `POPULAR_ASSETS`, `MODEL_PORTFOLIOS` | **pure reference data (630 lines)** |
| 1233–1285 | `resolve_tier`, `init_session_state`, `auto_rebalance_weights` | config + session |
| 1286–1431 | `T` dict, `t()` | **second translation system** |
| 1432–2028 | `UltimatePortfolioAnalyzer` (10 methods) | **business logic, partly UI-coupled** |
| 2029–2688 | 12 `render_*` helpers | UI |
| 2689–3922 | `_sidebar`, `SENSITOR_PAGES`, `_sensitor_context`, `main()` | routing + 7 legacy pages |

### Layer B — the `sensitor/` package

**10,253 lines**, 19 modules + 12 pages. Added over the four previous phases.
Dependency graph is strictly layered with **no cycles**:

```
                 analytics.py  (leaf — no internal imports)
                       ▲
     ┌────────┬────────┼────────┬─────────┬──────────┐
  factors   health   signals  montecarlo optimize  stress
                       ▲         ▲          ▲
                    copilot   simulate   context ──► xray
                                              ▲
                                          pages/*
        design.py (leaf) ◄── components.py ◄── charts.py ◄── pages/*
        market.py (leaf) ◄── pages/_shared.py
        storage.py (leaf) ◄── pages/_shared.py
```

---

## 2. Where the two layers meet

The monolith imports from the package — never the reverse:

```python
from sensitor import design as sensitor_design      # theme injection
from sensitor.context import build_context          # analysis context
from sensitor.i18n import tr as s_tr                # navigation labels
from sensitor.pages import render_overview, ...     # 12 page renderers
```

`_sensitor_context()` (line 2850) is the single bridge: it wraps
`UltimatePortfolioAnalyzer` in a `Context` and hands the monolith's data
dictionaries to the package. Every Sensitor page reads through that object and
never touches the analyzer directly — which is why the package can be
restructured without the pages noticing.

---

## 3. Duplicated logic

Both layers compute the same things. The monolith's versions feed the 7 legacy
pages; the package's versions feed the 12 Sensitor pages.

| Concept | Legacy | Package |
|---|---|---|
| Performance metrics | `UltimatePortfolioAnalyzer.calculate_metrics` | `analytics.perf_stats` |
| Health score | `calculate_health_score`, `calculate_robustness_index` | `health.compute_health` |
| Stress scenarios | `stress_test_scenarios` (3 windows) | `stress.run_all_scenarios` (8 windows) |
| Optimisation | `optimize_portfolio` (max Sharpe) | `optimize.efficient_frontier` |
| Translations | `T` / `t()` | `i18n.STRINGS` / `tr()` |
| Charts | `render_enhanced_charts` | `charts.py` (20 factories) |

**This duplication is not removed in Phase 1.** Deleting the legacy versions
would change what the 7 legacy pages render, which the brief forbids. They are
catalogued here so a later phase can converge them deliberately.

---

## 4. Business logic mixed into the UI — resolved in Phase 2

All four targets have been extracted. The entry point went from **3,921 to
2,594 lines**; it is now page config, the stylesheet, session state, the sidebar,
routing and the seven legacy pages, and it computes nothing the package cannot.

| Was in the entry point | Now | Note |
|---|---|---|
| `UltimatePortfolioAnalyzer` (596 lines) | `investment/portfolio.py` | `fetch_data()` takes `progress` and `on_error` callbacks instead of calling `st.progress` / `st.warning`; `_fetch_with_progress()` in the app supplies Streamlit-backed ones, so the bar and the warnings look identical |
| `ASSET_INFO` + 4 mappings (630 lines) | `investment/assets.py` | pure data, re-bound to the original module-level names |
| `STRIPE_CONFIG` / `TIER_LIMITS` / `PRO_EMAILS` / `resolve_tier` | `core/config.py` | `resolve_tier` now delegates |
| `T` dict (142 lines) | `core/i18n.py` as `LEGACY_STRINGS` | kept separate from `STRINGS`; merging them would edit what the legacy pages render |

The calculations were moved unchanged — including their pre-existing lint
warnings, which are left alone on purpose. Tidying code while moving it is how a
move becomes a regression.

---

## 5. What breaks if moved

| Move | Breaks | What was done |
|---|---|---|
| Any `sensitor/*.py` → subpackage | the monolith's 4 imports; 13 page files; `tests/` | every call site updated in the same commit |
| `analytics.py` split | every `A.perf_stats` call site (9 modules) | shared primitives moved to `_base`; `analytics` re-exports the full surface, so no call site changed |
| `storage.py` split | `pages/_shared.get_store` | `database/__init__` re-exports `Store` |
| Deleting legacy analyzer methods | the 7 legacy pages | **not attempted** |
| Moving the CSS block | the entire visual identity | **not attempted** |

### On compatibility shims

The first draft of this plan called for re-export shims at the old flat paths.
They were **not** added, deliberately: eighteen alias modules at the package root
would preserve exactly the flat layout the restructure exists to remove, and
every consumer of these modules lives in this repository and was updated in the
same commit. Section 7's table is the migration reference for any code outside
it.

One cycle was found and removed rather than tolerated. Splitting `analytics`
into `performance` and `risk` while having `analytics` re-export them creates a
circular import that happens to work when `analytics` is imported first and
fails when it is not — a latent break for a future API process. The shared
primitives now live in `investment/_base.py`, which both import, so there is no
cycle in any import order. Verified by importing `performance` before
`analytics`.

---

## 6. Test surface

| Suite | Covers |
|---|---|
| `tests/test_sensitor_pages.py` | 159 render checks — 12 pages × 5 portfolio shapes × 2 languages, plus no portfolio, short history, real-portfolio mode, 3 risk profiles |
| `tests/test_investment_engine.py` | 44 checks with `streamlit` poisoned: layering, reference-data integrity, the analyzer's callback contract and its behaviour on a failed download, core helpers, the analytics facade |
| `tests/visual_preview.py` | renders the real pages against a synthetic market universe for visual inspection |
| ad-hoc | legacy page renders (7 pages × 2 languages) |

`test_investment_engine.py` only became possible in Phase 2. Before the
extraction, testing the analyzer meant standing up a Streamlit app.

The render harness is the safety net for the whole restructure: it exercises
every page through the real Streamlit script, so an import that breaks during a
move fails a check rather than reaching the user.

---

## 7. Target structure and the mapping to it

```
sensitor/
├── core/          config.py · exceptions.py · utils.py · i18n.py
├── investment/    analytics · performance · risk · factors · optimize
│                  montecarlo · stress · xray · health · simulate
│                  context · report
├── trading/       (new)
├── integrations/  market_data.py · mt5.py (new)
├── database/      connection.py · models.py · repositories.py
├── api/           (new)
├── ai/            copilot.py · signals.py
├── ui/            themes.py · components.py · charts.py
└── pages/         (unchanged location)
```

| From | To |
|---|---|
| `analytics.py` | `investment/analytics.py` + `performance.py` + `risk.py` |
| `factors · optimize · montecarlo · stress · xray · health · simulate · context · report` | `investment/` |
| `market.py` | `integrations/market_data.py` |
| `storage.py` | `database/connection.py` + `models.py` + `repositories.py` |
| `copilot.py · signals.py` | `ai/` |
| `design.py` | `ui/themes.py` |
| `components.py · charts.py` | `ui/` |
| `i18n.py` | `core/i18n.py` |

---

## 8. Phase sequence

| Phase | Scope | Behaviour change |
|---|---|---|
| 1 | Restructure the package into the target layout, with shims | none |
| 2 | Extract reference data, config and the analyzer out of the monolith | none |
| 3 | Trading engine | additive |
| 4 | Trading journal | additive |
| 5 | MT5 connector | additive |
| 6 | Database models for trading | additive |
| 7 | Multi-user | additive |
| 8 | FastAPI | additive |
| 9 | Mobile-ready backend | additive |

A phase is not started until the previous one leaves the 159 render checks and
the legacy page renders passing.
