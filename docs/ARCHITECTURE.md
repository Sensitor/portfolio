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
| `tests/test_database.py` | 86 checks: cross-user isolation on every read, write and delete; a scope check derived from the `Store` class itself; the user lifecycle, export and cascade; the constraints that are there and the ones deliberately absent; and the version 2 migration against a populated database built from the previous schema |
| `tests/test_sensitor_pages.py` | 164 render checks — 12 pages × 5 portfolio shapes × 2 languages, plus no portfolio, short history, real-portfolio mode, 3 risk profiles, and the save / snapshot / history / delete flow driven through its own buttons |
| `tests/test_investment_engine.py` | 44 checks with `streamlit` poisoned: layering, reference-data integrity, the analyzer's callback contract and its behaviour on a failed download, core helpers, the analytics facade |
| `tests/test_trading_engine.py` | 124 checks with `streamlit` poisoned: P&L and R arithmetic on hand-built trades, direction and session parsing, validation, metrics, curves and streaks, stop discipline, risk, breakdowns, the psychology framing, the journal |
| `tests/test_mt5_connector.py` | 128 checks with `streamlit` poisoned and a mocked terminal: balance-operation filtering, the 0.0 stop sentinel, deal folding, scaling in and out, partial closes, the implied point value, stops from orders, server-time conversion, the connector's lifecycle and failure modes, the merge rules, an end-to-end sync against a real store, and id namespacing across accounts |
| `tests/test_trading_pages.py` | 82 render checks — 5 pages across a full book (both languages), every period window, an account filter, a book with no stops, a book with no losses, four trades, open positions only, no self-reported fields, trades with data problems, an empty journal, and no signed-in user; plus cross-user isolation asserted through the store |
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
| 3 | Trading engine — **done** | additive |
| 4 | Trading journal — **done** | additive |
| 5 | MT5 connector — **done** | additive |
| 6 | Database models for multi-user — **done** | **breaking inside the package** |
| 7 | Multi-user | additive |
| 8 | FastAPI | additive |
| 9 | Mobile-ready backend | additive |

A phase is not started until the previous one leaves the 159 render checks and
the legacy page renders passing.


---

## 9. Trading engine (Phase 3)

2,386 lines under `sensitor/trading/`, pure computation, no Streamlit and no
broker SDK.

| Module | Holds |
|---|---|
| `models` | the `Trade` model, `Direction`, `Session`, validation |
| `setups` | setup and mistake taxonomies, tag folding |
| `analytics` | P&L, win rate, profit factor, expectancy, R, drawdown, streaks |
| `performance` | the same metrics by symbol, setup, combination, session, weekday, month, hour, timeframe, regime, risk band |
| `risk` | sizing consistency, drift, stop discipline, concurrent exposure, expected losing runs |
| `psychology` | behavioural comparisons, framed as correlations |
| `journal` | `TradeJournal` and `TradeFilter` — a queryable collection |

### The platform-agnostic boundary

The brief's hardest constraint is that nothing above the connector may depend on
a broker's object format. `Trade` is Sensitor's own shape; a connector normalises
into it and everything above only ever sees `Trade`. `Direction.parse` accepts
the spellings brokers actually use (0/1, BUY/SELL, B/S) and **raises** on an
unknown one rather than defaulting — silently guessing a side would invert a
trade's entire P&L.

### Three decisions that keep the numbers honest

**A missing stop leaves R undefined, not zero.** R is P&L over the amount risked,
and the amount risked comes from the stop. Returning 0R would drag every average
toward zero and make a book with no stops look disciplined. `r_coverage` reports
what share of trades the R statistics actually describe.

**Profit factor with no losses is undefined, not infinite.** It is a division by
zero; reporting "∞" puts a meaningless value in a column of meaningful ones.

**Stop discipline is measured on gross R, everything else on net R.** This one
was found by reading the engine's own output: 92% of losses were being flagged as
"beyond the stop" on a book whose stops all held. Net R includes commission, so a
trade stopped out at exactly -1R gross lands past -1R net on costs alone. Judged
that way, any trader paying commission looks like one whose stops never work.
`Trade.r_multiple_gross` exists solely for this check.

### Sample size is structural, not advisory

Every breakdown bucket carries `n` and a `reliable` flag, and `performance.best()`
refuses to promote a bucket below the threshold. A table sorted by win rate will
always put a two-trade bucket on top; calling that "your best setup" is how a
journal teaches someone the wrong lesson.

### The psychology framing is asserted, not trusted

`psychology.findings()` fixes the wording in the engine rather than the UI, so a
page cannot shorten "your data shows a correlation" into a verdict. The test
suite asserts that every finding names itself a correlation in both languages,
carries its sample size in the sentence, and contains no causal verb.

---

## 10. Trading journal (Phase 4)

Five pages under `sensitor/pages/`, plus `_trading_shared.py`, plus the tables
and repository methods that let a journal survive a restart. Nothing in the
investment half was touched: the 159 investment render checks and the 14 legacy
page renders pass unchanged.

| Piece | Holds |
|---|---|
| `_trading_shared.py` | the journal loader, the three guards, the period / account selectors, the filter panel, and the formatters that decide what an undefined value looks like |
| `trading_overview.py` | eight KPI cards, equity and R curves, daily P&L, R distribution, a breakdown on any dimension, recent trades |
| `trading_journal.py` | the only page that writes — entry form, open positions, data problems, the paged trade list |
| `trading_analytics.py` | Trading DNA, the free-form slicer, and where the result concentrates |
| `trading_risk.py` | sizing, drift, stop discipline, simultaneous exposure, losing runs against expectation |
| `trading_psychology.py` | the findings, the streak comparisons, mistakes, and the self-reported fields |

### Navigation

The sidebar is now **Investment · Trading · Workspace · Build**. The headings are
not decoration: "Risk" means portfolio volatility on one side and position sizing
on the other, and an ungrouped list would put the same word twice with no way to
tell which is which.

`TRADING_PAGES` is a separate map from `SENSITOR_PAGES` in the entry point,
because a trading page takes no investment context. Routing it through the same
map would build a `Context` — and fetch prices — for a page that never reads one.

### Two rules enforced in the shared module, not per page

**Trades are read per user, per rerun, and never cached across users.** The
journal is loaded by the signed-in email at read time. A `@st.cache_data` on the
journal would be keyed by its arguments, and one wrong key would serve one
person's book to another. The composite primary key `(user_email, id)` is what
makes that safe at the database level: two traders whose brokers both number a
deal `t0001` get two rows, and the harness asserts that neither appears in the
other's list.

**The filter vocabulary comes from the unfiltered journal.** `ctx.all_symbols`
and its siblings read `ctx.journal`, not `ctx.scoped`. A dropdown that only
offers what survived the current filter cannot be widened again.

### What the pages refuse to show

The restraint in the engine only matters if the UI honours it, so each of these
is a rendering decision, not a computation:

* **A percentage drawdown.** The trading equity curve is cumulative P&L from
  zero, so "percent of peak" is a percentage of whatever the running total
  happened to be — an early $19 peak followed by a $135 decline reads as −703%.
  Money and R are shown instead; a percentage drawdown needs an account balance,
  which the journal does not hold.
* **A best bucket below the sample threshold.** `P.best()` returns nothing, and
  the card shows a dash and says why rather than promoting a three-trade setup.
* **An infinite profit factor**, or a zero R for a trade that had no stop.
* **A cause.** Every psychology finding is phrased in the engine and rendered
  verbatim; the page has no wording of its own to shorten.

### Found by looking at the rendered pages

The unit tests passed the whole time. These did not survive a screenshot:

| Seen | Was |
|---|---|
| "−703.4% from peak" under the drawdown | a percentage of a near-zero peak — now money and R |
| "Average R −2.66R" on a profitable book | the *harness* priced commission at a flat $0.5–$4 against a $4 median risk; costs were half of R. The engine was right |
| "1 vs 1" with a full meter | an equal comparison drawing a 100% bar — now centred at 0.5 and labelled "no difference" |
| An amber card for sizing up after wins | a judgement the data does not carry; the warning colour is now only for the after-losses comparison |
| A white time input on a dark form | Streamlit's time control nests its surface below `div[role="group"]`, so the theme missed it |
| A scarlet "Save trade" | a form submit is `kind="primaryFormSubmit"`, not `primary`, and fell through to Streamlit's default red |
| Red filter chips, a white dropdown panel, a white expander header | three more controls the theme had never been pointed at — all of them reachable only by opening a panel |
| A breakdown axis spanning −300…+300 for bars of +243 and −51 | a symmetric range; now headroom per side |

The last four are theme gaps that predate this phase and affect the investment
pages too. They were fixed in `ui/themes.py`, which is why the change is not
confined to `pages/`.

---

## 11. Broker connector (Phase 5)

`integrations/mt5.py` and `integrations/sync.py`. The full operating manual is
`docs/MT5_SYNC.md`; what follows is where the boundaries sit and why.

### Three boundaries

**MT5 is known in one file.** `mt5.py` is the only module that has heard of a
deal, a position ticket or a `DEAL_ENTRY_IN`. Everything above it — sync, store,
pages, metrics — sees `trading.models.Trade`.

**`sync.py` does not import `mt5.py`.** It asks a source for `fetch_trades()`.
A second broker is a new connector and no change to the merge rules, the
idempotency or the journal protection.

**The page does not know what a deal is.** The Journal's sync panel collects
settings, calls the connector, and reports the result. The rule about what a
sync may overwrite lives in `sync.py`, so the next broker inherits it.

`MetaTrader5` is imported inside `connect()`, never at module scope: the package
is Windows-only, and a top-level import would make the module — and the whole
normalisation layer — unimportable on the machine this was written on. The test
suite asserts that it is never imported at module scope, and that neither file
imports Streamlit.

### Four decisions that decide whether the numbers are right

**Deposits are filtered out.** Balance operations arrive in the same history
stream carrying a `profit`. A $10,000 deposit imported as a trade becomes the
best trade, the largest win, most of the gross profit, and it moves expectancy,
profit factor, win rate and the equity curve with it. `is_trading_deal()` is the
most consequential line in the connector.

**A stop of 0.0 is not a stop at zero.** MT5 writes `0.0` for "none attached".
Taken literally, `risk_amount` becomes the whole notional and every R collapses
toward zero — a book with no stops would report flawless discipline. `_price()`
maps it to None, and the trade is then excluded from R rather than counted as a
zero.

**R is calibrated from the broker's own arithmetic.** MT5 gives volume in lots
and prices in quote terms, so `abs(entry - stop) * volume` is wrong by the
contract size and wrong again by the quote-to-account rate. Rather than look
either up, the point value is derived as `gross_pnl / (distance * volume)` — the
broker already said what the position made in account currency. `size` is stored
in account currency per price unit, which makes risk money and R dimensionless.
On a USDJPY trade from a USD account it gives 2.00R where the naive version gives
1324.

**Direction comes from the opening deal.** A long is closed by a sell; reading
the side off the exit inverts the entire book.

### Two hazards the tests found

Both were real, and both were found because a test asserted an outcome rather
than a call:

*The sync scoped its lookup of existing trades by account.* Any mismatch — a
trade stored before the account was labelled, a label since changed — made every
incoming trade look new, and the re-sync overwrote the journal with the broker's
bare record. The merge rule was correct; the lookup that fed it was not. It now
reads every trade for the user and merges by id.

*Trade ids were not namespaced by account.* A position ticket is unique within
an account and nothing more, and the primary key is `(user_email, id)` — so two
accounts reaching position 12345 meant the second silently replacing the first.
Ids are now `mt5-<account>-<position>`.

### The schema gained a column, and a migration step

`trades.raw` holds the connector's original payload as JSON. Derived values are
still never stored; the *source record* is, so a corrected normaliser can rebuild
the trades from what the broker actually said instead of re-downloading a history
that may no longer be reachable.

`CREATE TABLE IF NOT EXISTS` leaves an existing database untouched, so a new
column never reaches anyone who has already saved anything — which is every real
user. `connection._migrate()` adds missing columns on open. Verified against a
database built from the previous schema: the legacy rows survive and read back.

---

## 12. Multi-user data model (Phase 6)

The first phase whose changes are **breaking inside the package**. Seven `Store`
methods changed signature and every call site moved with them.

### What was wrong

`get_portfolio(portfolio_id)`, `rename_portfolio`, `delete_portfolio`,
`add_snapshot`, `list_snapshots`, `latest_snapshot` and `delete_snapshot` took an
integer id and no user. An integer primary key is guessable, so each of them
returned, renamed or deleted whatever row held that id — regardless of whose it
was. On a single-user desktop app that is harmless. It is also exactly the hole
the multi-user architecture of Phase 7 and the API of Phase 8 would have been
built on top of, and the brief's hardest constraint is that one user's data is
never reachable by another.

Every one of them now leads with the owner, and the user parameter has no
default — a parameter with a default is how this comes back.

### Snapshots reach their owner through the portfolio

`snapshots` carries no user column. Adding one would create a second place for
ownership to be recorded and therefore a place for the two to disagree. Every
query joins through `portfolios` instead, so a snapshot cannot be read, written
or deleted across the boundary even when its own id is known.

### Schema version 2

| Change | Why |
|---|---|
| `portfolios`, `trading_accounts`, `trades` cascade from `users` | makes `delete_user` a guarantee rather than a list of deletes someone must remember to maintain |
| `trades.direction` gains a CHECK | a third value means a P&L sign nothing downstream can interpret |
| `trading_accounts.last_synced_at` / `last_sync_trades` | recorded by a sync rather than inferred from the newest close, which stalls whenever a sync finds nothing |
| `idx_accounts_user` | the account list is read on every trading page |

The constraints deliberately **not** added are as important. There is no
`CHECK (size > 0)` on `trades`, because the journal accepts a trade whose numbers
are wrong and flags it — a trader importing a messy CSV needs to see the bad rows
rather than have the import refused. A CHECK there would turn the product's
stated behaviour into a hard failure at the worst moment.

### Migrating, and the trap it hit

SQLite cannot add a foreign key or a CHECK in place, so the three user-owned
tables are rebuilt: rename aside, create at the current definition, copy the
columns both shapes share, drop the old. Copying by shared column rather than
`SELECT *` is what lets it run on a database that did or did not receive the
`raw` column from Phase 5.

Two things had to be got right, and one was got wrong first:

**Users are backfilled before the constraint exists.** Older databases wrote
portfolios and trades without ever creating the `users` row, and a foreign key
to a missing parent is unsatisfiable.

**`ALTER TABLE ... RENAME TO` rewrites other tables' foreign keys to follow the
new name.** Renaming `portfolios` aside repointed `snapshots` at the scratch
table; dropping the scratch table then left `snapshots` referencing something
that no longer existed — a database that opens fine and fails on the first
cascade. The test caught it. `PRAGMA legacy_alter_table = ON` during the rebuild
turns that rewriting off, which is what a rebuild wants: a referencing table
should keep pointing at the *name*, because the name is about to hold the new
table.

The migration finishes with `foreign_key_check` and `integrity_check`, and
raises rather than returning a database that opens and is quietly broken.

### The test that will catch the next one

`test_every_user_method_is_scoped` derives its list from the `Store` class
rather than from a list written down beside it, and asserts that every public
method leads with `user_email` or `email` and that neither is optional. The seven
unscoped methods survived four phases of review; a list maintained by hand would
have let the eighth through too.
