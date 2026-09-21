# The mobile client

What exists, what it is for, and what is deliberately not built yet.

---

## 1. What is here

| | |
|---|---|
| `mobile/src/api/types.ts` | the response shapes, with every undefinable figure typed `\| null` |
| `mobile/src/api/client.ts` | the client: ETag caching, timeouts, typed errors |
| `mobile/src/api/format.ts` | the one place an undefined figure becomes a dash |
| `mobile/tests/integration.ts` | 38 checks against a live server |
| `sensitor/api/routers/mobile.py` | the three endpoints shaped for a handset |

**The React Native screens are not built.** That is a deliberate limit, not an
oversight: there is no simulator or device in the environment this was written
in, so a UI written here could be typechecked and never *seen*. Every visual
decision in this project so far was made by rendering the thing and looking at
it — ten bugs in the trading pages were found that way and none of them by a
test. Shipping a few thousand lines of unlooked-at screens would break the one
practice that has been working.

What is built is everything below the screens, and it is verified end to end:
the client runs against a real uvicorn process, not a mock.

---

## 2. Why the mobile endpoints exist

The `/trading/*` routes serve one thing each. That is right for a browser on a
desk and wrong for a phone, in three ways.

### Round trips cost more than bytes

On a mobile network each request costs a hundred milliseconds or more before a
byte arrives, and each one wakes the radio. A home screen assembled from six
requests is slow *and* a battery cost. `/mobile/overview` returns the whole
screen in one.

It also returns a *consistent* screen. Six requests can each land on a different
moment; one `TradingContext` cannot, so every figure on the page describes the
same set of trades.

### Curves must be thinned without losing their shape

A nine-hundred-trade equity curve is more points than a handset has pixels
across. But *how* it is thinned decides whether the picture stays true, and the
obvious method is wrong: sampling at a stride skips whatever falls between the
samples, and on an equity curve the thing most likely to fall between them is
the single deepest trough. The drawdown would render shallower on the phone than
on the desktop — one figure disagreeing with itself across two screens.

`trading.analytics.downsample` buckets the curve and keeps each bucket's first,
lowest, highest and last point. Extremes survive by construction; only the
uneventful stretches are thinned. The test asserts that the minimum, the maximum
and both endpoints of a 900-point curve survive a thinning to 200.

### Most openings of an app find nothing changed

Every mobile response carries an `ETag` derived from the journal's row count and
newest `updated_at`. A client that sends it back in `If-None-Match` gets a
**304 with no body**. `/mobile/version` is a smaller poll still, for deciding
whether to fetch at all.

### Measured, on 900 trades

| | bytes | gzipped | round trips |
|---|---:|---:|---:|
| six separate requests | 60,119 | 12,283 | 6 |
| `/mobile/overview` | 24,535 | 6,029 | 1 |
| unchanged reopen (304) | 0 | 0 | 1 |

51% fewer bytes on the wire, five fewer round trips, and nothing at all when
nothing has changed.

---

## 3. Incremental sync

```
GET /mobile/trades?since=<server_time>
```

Returns only trades whose `updated_at` is later — **not** `closed_at`, because a
trade annotated today is a change the client needs even though it closed in
March.

**Pass back the `server_time` from the previous response, never a locally
generated timestamp.** A phone whose clock runs fast would ask for changes since
a moment that has not happened and silently miss everything written in between.

**URL-encode it.** A `+` in a query string decodes to a space, so an ISO
timestamp with a UTC offset arrives mangled. The server repairs that case and
rejects anything it cannot parse with a 422 — because the alternative failure is
silent and severe: a string comparison against a mangled cursor matches *every*
row, so the endpoint returns the entire journal and looks like it worked. That
bug was in this code and was found by running the client against a live server.
`URLSearchParams`, which `client.ts` uses, encodes it correctly.

---

## 4. Using the client

```ts
import { SensitorClient, ApiError } from './src/api';
import { money, percent, profitFactor, rCoverageNote } from './src/api/format';

const client = new SensitorClient({
  baseUrl: 'https://your-server',
  onUnauthenticated: () => store.signOut(),
});

await client.signIn('you@example.com', password);

const overview = await client.overview({ period: '30D' });

money(overview.metrics.net_pnl, overview.currency);   // "$4,208.10"
percent(overview.metrics.win_rate);                   // "57.2%"
profitFactor(overview.metrics.profit_factor);         // "1.93" or "undefined"
rCoverageNote(overview.metrics);                      // the caveat, or null
```

### What the client does beyond wrapping fetch

**It caches by ETag.** `overview()` sends the previous tag and returns the copy
it already holds on a 304.

**It clears that cache on sign-out.** A cached overview belongs to whoever was
signed in when it was fetched; keeping it across a sign-out would show one
person's journal to the next. The server is built to make that impossible — the
client is the other half of it.

**It distinguishes offline from refused.** Everything rejects with an `ApiError`
carrying a status. `error.unauthenticated` means send the person to sign in;
`error.offline` (status 0) means show the cached data and a retry. A screen that
cannot tell those apart shows the wrong thing in both cases.

**It times out.** A request with no deadline on a flaky connection is a spinner
that never stops.

---

## 5. The rule the screens must follow

`strictNullChecks` is on, and `types.ts` marks every figure the engine can leave
undefined as `| null`. That is not pedantry — it is the compiler enforcing the
product's central discipline.

```ts
metrics.profit_factor.toFixed(2)        // does not compile
(metrics.profit_factor ?? 0).toFixed(2) // compiles, and is a lie
profitFactor(metrics.profit_factor)     // "undefined" when there are no losses
```

The middle line is the dangerous one. It prints `0.00` when the truth is "there
were no losing trades", and a trader reading that concludes their system loses
money. `format.ts` exists so no screen has to make that choice itself.

Three more the screens inherit from the server:

* **Sample sizes are shown, never hidden.** Every breakdown row carries `n` and
  `reliable`. A table sorted by win rate always puts a two-trade bucket on top;
  `isProvisional(row)` is how a screen marks it instead of ranking it.
* **Findings are rendered verbatim.** `finding.en` / `finding.fr` are written by
  the engine, each stating that it is a correlation and carrying its sample
  size. Paraphrasing one into a verdict removes the only safeguard on the most
  easily misread screen in the product.
* **R has coverage.** `rCoverageNote()` returns the sentence when R describes
  less than the whole book, and null when there is nothing to say.

---

## 6. Running it

```bash
# The API
export SENSITOR_AUTH=multi
uvicorn sensitor.api.app:app --host 0.0.0.0 --port 8000

# The client
cd mobile
npm install
npm run typecheck
SENSITOR_API_URL=http://localhost:8000 npm run test:integration
```

For a phone on the same network, point `baseUrl` at the machine's LAN address
rather than `localhost`. **Put TLS in front of it before it leaves that
network** — a bearer token over plain HTTP is a bearer token anyone on the path
can take.

A single-user deployment issues no session to the API without
`SENSITOR_API_TOKEN` set; pass it as `apiKey` to `signIn`. `client.meta()`
reports `issues_sessions` so the app can say why sign-in is unavailable rather
than showing a failure it cannot account for.

---

## 7. Building the screens

When there is a device to look at, the shape is:

```
mobile/
├── src/api/          ← done, and typechecked
├── src/screens/      Overview · Journal · Analytics · Risk · Psychology
├── src/components/   MetricCard · Meter · Sparkline · FindingCard · SampleBadge
└── app/              expo-router routes
```

Five screens mirroring the five Streamlit pages, because the analytics are the
same analytics — the server already returns exactly what each one needs, in one
request per screen.

Two things to carry over from the desktop work rather than rediscover:

**Every metric is a visual component.** A number alone is a failure; a figure
gets a fill meter positioning it in its range, a benchmark delta, and a
sparkline. `MetricCard` is the atom.

**Look at it.** Ten bugs in the trading pages were found by rendering them and
looking — a −703% drawdown, a full meter on an equal comparison, an amber card
for a judgement the data did not carry. No test found any of them.
