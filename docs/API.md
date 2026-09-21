# The HTTP API

The same engine the desktop app uses, over HTTP. Built for the mobile client of
Phase 9, useful on its own for scripting.

```bash
pip install fastapi uvicorn
uvicorn sensitor.api.app:app --port 8000
```

Interactive documentation at `/docs`, the OpenAPI document at `/openapi.json`.

---

## 1. What this process does not contain

There is no metric in `sensitor/api/`. No P&L arithmetic, no definition of a
profit factor, no drawdown. Every number it serves comes from
`sensitor.trading` and `sensitor.investment` — reached through the same `Store`
and the same `Auth` the Streamlit pages use.

That is not tidiness. A metric implemented twice diverges, and the copy that
diverges is the one with fewer readers: the phone and the app would quietly
disagree about a trader's expectancy, and only one of them would be wrong in a
way anyone noticed.

`tests/test_api.py` asserts it both ways. It parses every module under
`sensitor/api/` for arithmetic and for imports of numpy, pandas, scipy,
statistics and math — the only arithmetic permitted is a list slice for
pagination — and it compares twelve served figures against the engine called
directly.

---

## 2. Authentication

Every endpoint that touches your data needs a bearer token.

```bash
curl -X POST localhost:8000/auth/sign-in \
  -H 'Content-Type: application/json' \
  -d '{"email":"you@example.com","password":"…"}'
# → {"token":"…","email":"you@example.com","expires_days":30}

curl localhost:8000/trading/metrics -H "Authorization: Bearer $TOKEN"
```

It is the **same session** the desktop app issues, in the same table. A token
created by signing in through the UI works here and one issued here works there.
A second authentication mechanism for the API would be a second place to get it
wrong.

### The caller is read from the token and nowhere else

No endpoint takes a user as a path parameter, a query parameter or a body
field — so none can be asked for somebody else's data. A portfolio id in a path
is a *filter*, not an identifier the server trusts: `GET /portfolios/3` becomes
`SELECT … WHERE id = 3 AND user_email = <from your token>`.

Asking for a portfolio that belongs to someone else returns **404 with the same
message** as asking for one that does not exist. Distinguishing them would
confirm that it exists.

`tests/test_api.py` reads the OpenAPI document and fails if any parameter is
named `user`, `email`, `owner` or similar, and calls every protected route with
a second account's valid token.

### Single-user deployments issue no sessions by default

The desktop app in single-user mode treats an email as a filing label: type it,
and your data opens. That is defensible for a text box on your own machine and
indefensible over HTTP, which is reachable by anyone who can route a packet to
it.

So the API does not inherit that behaviour:

| Mode | Sign-in |
|---|---|
| `SENSITOR_AUTH=multi` | email + password |
| single, `SENSITOR_API_TOKEN` set | email + that key |
| single, no key set | **503** — no session is issued at all |

`GET /meta` reports `issues_sessions`, so a client can tell the person why
sign-in is unavailable rather than showing a failure it cannot explain.

```bash
export SENSITOR_API_TOKEN="$(python3 -c 'import secrets;print(secrets.token_urlsafe(32))')"
curl -X POST localhost:8000/auth/sign-in \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"you@example.com\",\"api_key\":\"$SENSITOR_API_TOKEN\"}"
```

---

## 3. Endpoints

### Meta

| | |
|---|---|
| `GET /health` | liveness; no auth, reads nothing |
| `GET /meta` | product, version, schema version, auth mode, whether sessions are available |

### Auth

| | |
|---|---|
| `POST /auth/sign-in` | credentials → token |
| `POST /auth/sign-up` | multi-user mode only; 409 if registered, 400 if weak |
| `POST /auth/sign-out` | revoke this session; idempotent |
| `POST /auth/sign-out-everywhere` | revoke all of the caller's sessions |
| `GET /auth/me` | email, tier, last login |

### Trading

All accept `?period=`, `?account=`, `?symbol=` and `?lang=en|fr`.

| | |
|---|---|
| `GET /trading/metrics` | every headline figure |
| `GET /trading/equity` | cumulative net P&L, one point per closed trade |
| `GET /trading/r-curve` | cumulative R; empty when no trade had a stop |
| `GET /trading/daily` | net P&L per trading day |
| `GET /trading/breakdown/{dimension}` | by symbol, setup, combination, session, weekday, hour, month, timeframe, direction, regime, risk_band |
| `GET /trading/risk` | sizing, drift, stop discipline, exposure, losing runs |
| `GET /trading/psychology` | behavioural comparisons |
| `GET /trading/findings` | the sentences the engine phrases, in both languages |
| `GET /trading/trades` | the journal; `?limit=` `?offset=` `?closed_only=` |
| `GET /trading/accounts` | broker accounts and when each was last synced |
| `GET /trading/periods` | only the windows this history can cover |

### Portfolios

| | |
|---|---|
| `GET /portfolios` | the caller's saved allocations |
| `POST /portfolios` | create or overwrite by name |
| `GET /portfolios/{id}` | one, if it is the caller's |
| `DELETE /portfolios/{id}` | it and its snapshots |
| `GET /portfolios/{id}/snapshots` | recorded history |
| `GET /portfolios/{id}/latest` | the most recent snapshot |

---

## 4. Reading the responses

### `null` is not `0`

A client that renders these as zero will draw a confident wrong number, which
is the failure this whole project is designed against.

| Field | `null` when |
|---|---|
| `profit_factor` | there are no losing trades — a division with no denominator, not an infinity |
| `avg_r`, `total_r`, `expectancy_r` | no trade had a stop, so there is no amount risked |
| `max_drawdown_pct` | the peak was at or below zero |
| `r_multiple` on a trade | that trade had no stop |

`r_coverage` says what share of the book the R figures actually describe. A
0.4R average over a fifth of the trades is not the whole picture, and the field
is how a client can say so.

### Sample sizes travel with every grouped figure

Every row from `/trading/breakdown/{dimension}` carries `n` and `reliable`.
A table sorted by win rate always puts a two-trade bucket on top; `reliable` is
false for those, and a client is expected to mark them rather than rank them
alongside the rest.

### Findings are phrased by the engine

`/trading/findings` returns sentences in `en` and `fr`. Each one states that it
is a correlation and carries its sample size, and the test suite asserts both in
both languages. **Render them verbatim.** Paraphrasing one into a verdict undoes
the only safeguard on the most easily misread page in the product.

### Derived values travel with each trade

`r_multiple`, `r_multiple_gross`, `risk_amount`, `planned_rr`,
`duration_minutes` and `session` are all on the trade. A client never recomputes
them and so never disagrees with the app about what a trade was worth.

`stops.measured_on` in `/trading/risk` is `"gross"`, deliberately: stop
discipline is judged on price movement before costs, because a trade stopped at
exactly −1R lands past −1R net on commission alone.

---

## 5. Deployment

| Variable | |
|---|---|
| `SENSITOR_AUTH` | `multi` for real accounts; anything else is single-user |
| `SENSITOR_API_TOKEN` | single-user only: the pre-shared key that authorises a session |
| `SENSITOR_DB_PATH` | the SQLite file; **point this at a persistent volume** |
| `SENSITOR_CORS_ORIGINS` | comma-separated origins; unset means no cross-origin access |

CORS is **not** defaulted to `*`. Credentials travel on these requests, and a
wildcard that arrived by default rather than by decision is how a browser on any
site ends up able to call this API with a user's token. A native mobile client
sends no `Origin` and needs none of it.

Put TLS in front of it. A bearer token over plain HTTP is a bearer token
anyone on the path can take.

---

## 6. Testing

```
python tests/test_api.py
```

121 checks with `streamlit` poisoned: that the API computes nothing, that its
numbers equal the engine's, that every protected route refuses an absent,
malformed or invented token, that no endpoint names a user, that a second
account reaches none of the first's data, the sign-in and registration flows,
single-user mode's refusal to issue sessions, that undefined survives the wire
as `null`, that sample sizes travel, and pagination.
