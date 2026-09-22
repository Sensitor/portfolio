# Sensitor

Investment and trading analytics over one engine. A Streamlit application, an
HTTP API and an iOS app — all reading the same calculations, so no two
surfaces can disagree about what a number means.

---

## What it does

**Investment.** Twelve pages over a portfolio: performance against a benchmark,
risk decomposed by holding, a fund look-through X-ray, eight historical stress
windows, mean-variance optimisation, Monte Carlo, and a Copilot that pairs an
observation with a change you can simulate.

**Trading.** Five pages over a journal: what the book made, where it came from,
how it was risked, and what the behaviour lines up with. Imports from
MetaTrader 5, or entered by hand.

**Documents.** A client portfolio report and a weekly trading review, each one
self-contained HTML you print or send.

**On a phone.** The five trading pages again, as an Expo app over the same
endpoints.

---

## Installing

Python 3.11 or later.

```bash
git clone https://github.com/Sensitor/portfolio.git
cd portfolio
pip install -r requirements.txt
streamlit run portfolio_optimizer_saas.py
```

Optional extras, each independent:

```bash
pip install fastapi uvicorn     # the HTTP API
pip install MetaTrader5         # the broker connector — Windows only
cd mobile && npm install        # the mobile app and its client
```

None of these is needed by the app, and the API process needs no Streamlit.

---

## Configuration

| Variable | Default | |
|---|---|---|
| `SENSITOR_DB_PATH` | `sensitor_data.db` | where the SQLite file lives |
| `SENSITOR_AUTH` | `single` | `multi` for real accounts |
| `SENSITOR_API_TOKEN` | *(unset)* | single-user API key; without it the API issues no sessions |
| `SENSITOR_CORS_ORIGINS` | *(unset)* | comma-separated; never defaults to `*` |
| `PRO_EMAILS` | *(unset)* | comma-separated addresses on the Pro tier |
| `STRIPE_PAYMENT_LINK` | *(unset)* | the upgrade link |

### The two authentication modes

**single** — the app is one person's, on their own machine. The email is a
filing label; there is nobody to verify against, and demanding a password to
open your own spreadsheet is theatre. The Account page says so plainly.

**multi** — accounts have passwords (scrypt), sign-in verifies, repeated
failures throttle, sessions expire, and no account can reach another's data.

An unrecognised value falls back to **single**, not multi: a typo must not
silently claim protection the deployment does not have.

> Before putting this anywhere other people can reach: set `SENSITOR_AUTH=multi`,
> put TLS in front of it, and point `SENSITOR_DB_PATH` at a persistent volume.

---

## The database

SQLite, created and migrated on first open. Nothing to set up.

The file holds personal financial data. It stays on whatever machine runs the
app, it is gitignored, and nothing in this codebase sends it anywhere.

**Streamlit Cloud's filesystem is ephemeral** — the database is wiped on every
restart, redeploy and sleep. Point `SENSITOR_DB_PATH` at a persistent volume
before treating saved data as safe.

Migrations run automatically and are versioned by `PRAGMA user_version`. Added
columns are applied in place; changed constraints rebuild the table, inside a
transaction, copying only columns both shapes share, and the migration refuses
to finish if `foreign_key_check` or `integrity_check` reports a problem. The
rebuild is tested against a populated database built from the previous schema.

```python
from sensitor.database import Store
store = Store()
store.export_user("you@example.com")   # everything, as JSON-able data
store.delete_user("you@example.com")   # and it is gone, counted and reported
```

---

## MetaTrader 5

Journal → **Import from MetaTrader 5**. Requires the terminal running on the
same machine and `pip install MetaTrader5`, which MetaQuotes publishes for
Windows only.

**Set the server UTC offset.** MetaTrader timestamps are the broker's server
clock, and most brokers run on UTC+2 or UTC+3. Left at zero, every trade lands
hours late and a third of them are attributed to the wrong session.

Re-syncing is safe. Trades are matched on the broker's own position number, and
everything you have written — setups, notes, emotions, ratings — is kept.

Full detail, including why deposits are filtered out and how R is calibrated
without a contract-size table: **[docs/MT5_SYNC.md](docs/MT5_SYNC.md)**.

---

## The API

```bash
pip install fastapi uvicorn
SENSITOR_AUTH=multi uvicorn sensitor.api.app:app --port 8000
```

Interactive documentation at `/docs`. Every endpoint that touches your data
needs `Authorization: Bearer <token>` from `POST /auth/sign-in` — the same
session the desktop app issues.

**It computes nothing.** Every number comes from `sensitor.trading` and
`sensitor.investment`. The test suite parses every module under `sensitor/api/`
for arithmetic and for imports of numpy, pandas and scipy, and compares twelve
served figures against the engine called directly.

**The caller comes from the token and nowhere else.** No endpoint takes a user
as a parameter, so none can be asked for someone else's data.

**[docs/API.md](docs/API.md)** — every endpoint, how to read the responses, and
deployment.

---

## Mobile

An Expo app — five screens over the same engine, mirroring the five desktop
trading pages.

```bash
cd mobile
npm install
npx expo start                 # then scan the QR code with Expo Go
npm run typecheck
SENSITOR_API_URL=http://localhost:8000 npm run test:integration
```

`mobile/src/api/` is a dependency-free TypeScript client: ETag caching, typed
errors that distinguish offline from refused, and `| null` on every figure the
engine can leave undefined — so `metrics.profit_factor.toFixed(2)` does not
compile.

Three endpoints are shaped for a handset. On 900 trades, a home screen goes
from 60 KB over six requests to 24 KB over one, and an unchanged reopen
transfers nothing.

On the phone, put the machine's LAN address in the app's Server field —
`localhost` there means the phone. **[docs/MOBILE.md](docs/MOBILE.md)** — the
screens, the client, and the three stages from Expo Go to the App Store.

---

## Architecture

```
portfolio_optimizer_saas.py     Streamlit entry point — routing and the legacy pages
sensitor/
├── core/          config · exceptions · i18n · security · auth · document
├── investment/    analytics · performance · risk · factors · optimize · montecarlo
│                  stress · xray · health · simulate · context · report
├── trading/       models · setups · analytics · performance · risk · psychology
│                  journal · context · report
├── integrations/  market_data · mt5 · sync
├── database/      connection · models · repositories
├── ai/            copilot · signals · trading_copilot
├── api/           app · deps · schemas · routers/
├── ui/            themes · components · charts
└── pages/         17 page renderers
mobile/
├── src/api/       the TypeScript client
├── src/components/ primitives · charts · the screen frame
├── src/state/     session · the fetch hooks
└── app/           expo-router: sign-in and the five tabs
docs/              ARCHITECTURE · API · MOBILE · MT5_SYNC
```

**The rule the layout enforces: business logic never imports Streamlit.**
`core`, `investment`, `trading`, `database`, `integrations` and `ai` are
importable from a script, a test or an API process with no UI runtime present.
Only `ui` and `pages` touch it, and every engine test suite asserts it by
setting `sys.modules["streamlit"] = None` before importing.

**[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** — the full map, the phase
history, and the decisions behind each boundary.

---

## The discipline the code is built around

These are not style preferences. Each one exists because the alternative
produces a confident, wrong number that a person would act on.

**Undefined is never zero.** A profit factor with no losing trades has no
denominator; an R multiple on a trade with no stop has no amount risked; a
percentage drawdown from a peak at zero is a percentage of nothing. All three
come back `null` and render as a dash. Rendering them as `0` tells a trader
their system loses money when it does not.

**Sample size travels with every grouped figure.** A table sorted by win rate
always puts a two-trade bucket on top. Every bucket carries `n` and a
`reliable` flag, and `performance.best()` refuses to promote one below the
threshold — calling that "your best setup" is how a journal teaches someone the
wrong lesson and then watches them size up on it.

**Correlation is never called cause.** The psychology module phrases its own
findings, in both languages, each naming itself a correlation and carrying its
sample size. The wording is fixed in the engine so no page, document or client
can shorten it into a verdict — and the test suite asserts it, including the
absence of causal verbs.

**Thresholds are stated.** Every alert says the number that triggered it and
the line it crossed.

**One user's data is unreachable by another.** Every `Store` method leads with
the owner and none defaults it — a test derives that list from the class rather
than a list maintained by hand.

---

## Testing

```bash
python tests/test_investment_engine.py    #  44 checks — engine, no Streamlit
python tests/test_trading_engine.py       # 173 checks — engine, review, copilot
python tests/test_mt5_connector.py        # 131 checks — mocked terminal
python tests/test_database.py             #  89 checks — isolation, migrations
python tests/test_auth.py                 #  95 checks — crypto, sessions, lockout
python tests/test_api.py                  # 170 checks — HTTP, isolation, no maths
python tests/test_sensitor_pages.py       # 164 render checks
python tests/test_trading_pages.py        #  82 render checks
cd mobile && npm run test:integration     #  38 checks against a live server
```

No pytest and no test framework: each file runs standalone, prints one line per
check, and exits non-zero on failure. That keeps them runnable anywhere and
readable as documentation of what is guaranteed.

The render harnesses drive the real Streamlit script through `AppTest` and
assert that a page renders *content* rather than merely not raising — a page
that quietly refuses to show anything raises nothing at all.

---

## Deploying

**Streamlit Cloud.** Point it at `portfolio_optimizer_saas.py`. Set the
environment variables above; remember the filesystem is ephemeral.

**A server.** Run the Streamlit app and, if you want the API, a separate
uvicorn process against the same `SENSITOR_DB_PATH`. Put TLS in front of both.
Set `SENSITOR_AUTH=multi`.

---

## Licence and scope

Personal project. Nothing in this repository is investment advice, a
recommendation, or a forecast. Every figure describes how something behaved
over the window analysed; past performance does not predict future returns.
