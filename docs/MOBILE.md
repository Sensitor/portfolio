# The mobile app

An Expo app over the same engine as the desktop: five tabs, five Streamlit
trading pages, one set of calculations.

---

## 1. What is here

| | |
|---|---|
| `mobile/app/` | expo-router: `sign-in` and the five tabs |
| `mobile/src/components/primitives.tsx` | Card · Meter · Sparkline · MetricCard · Alert · Note · Pill |
| `mobile/src/components/charts.tsx` | equity curve · daily bars · breakdown bars, in `react-native-svg` |
| `mobile/src/state/` | the session provider and the two fetch hooks |
| `mobile/src/theme.ts` | the same tokens as `sensitor/ui/themes.py` |
| `mobile/src/api/types.ts` | the response shapes, with every undefinable figure typed `\| null` |
| `mobile/src/api/client.ts` | the client: ETag caching, timeouts, typed errors |
| `mobile/src/api/format.ts` | the one place an undefined figure becomes a dash |
| `mobile/tests/integration.ts` | 38 checks against a live server |
| `sensitor/api/routers/mobile.py` | the three endpoints shaped for a handset |

### The five tabs

| | |
|---|---|
| **Overview** | six metric cards, the findings verbatim, equity curve, daily P&L, by instrument |
| **Journal** | the trades themselves, newest close first, filtered by instrument on the server |
| **Analytics** | any of eight dimensions, each group with its sample size and `reliable` flag |
| **Risk** | sizing, drift, stop discipline, concurrent exposure, activity, losing runs |
| **Behaviour** | the findings, after-a-run comparisons, mistakes, discipline, emotions |

Every screen was rendered in a browser against a live API on a 900-trade book
and looked at. That found six things no test did:

* money printed as `USD158,777.59`, because the API sends a currency **code**
  and `money()` was concatenating it;
* a Daily P&L caption reading "90 trading days" on a book with 151 — the
  endpoint returns the most recent 90, and the caption called that the window;
* "over the 0 and 0 trades" beneath two medians plainly computed from
  something: the after-wins comparison carries no per-group stop counts, and a
  `?? 0` filled them in;
* a discipline table reading "low / medium / high" instead of "Low discipline
  (1-2)", losing the scale the rating is on;
* two cards whose fill meter drew a different quantity from the number above
  it — 39% over a bar filled to 61%;
* a red SHORT label beside a green P&L, asking one colour to mean direction in
  one column and outcome in the next.

`tsconfig.json` did not include `app/` at first, so `npm run typecheck` passed
green while no screen was checked at all. It does now, and that is worth
remembering: a typecheck only covers what `include` lists.

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

# The app
cd mobile
npm install
npm run typecheck
npx expo start                 # QR code for Expo Go
npx expo start --web           # the same screens in a browser

# The client, against a live server
SENSITOR_API_URL=http://localhost:8000 \
SENSITOR_TEST_EMAIL=you@example.com \
SENSITOR_TEST_PASSWORD=… \
  npm run test:integration
```

**Dependency versions come from the SDK, not from npm.** `package.json` pins
what `expo/bundledNativeModules.json` lists, exactly. Caret ranges installed
React Native 0.87 against an SDK built for 0.86 here, and the web bundle failed
on a subpath 0.87 had stopped exporting. `npx expo install --check` reconciles
them when the SDK moves.

For a phone on the same network, point `baseUrl` at the machine's LAN address
rather than `localhost`. **Put TLS in front of it before it leaves that
network** — a bearer token over plain HTTP is a bearer token anyone on the path
can take.

A single-user deployment issues no session to the API without
`SENSITOR_API_TOKEN` set; pass it as `apiKey` to `signIn`. `client.meta()`
reports `issues_sessions` so the app can say why sign-in is unavailable rather
than showing a failure it cannot account for.

---

## 7. How the screens are built

**Every metric is a visual component.** A number alone asks the reader to
supply a scale they do not have — is 1.93 a good profit factor? `MetricCard` is
the atom: the figure, a fill meter placing it in its range, a caption saying
what it is measured against, and where there is history, a sparkline.

**The meter shows the same quantity as the number above it.** Two cards shipped
briefly with a bar drawing `1 - x` under a headline of `x`. It reads as two
answers to one question, and it is the kind of thing only looking finds.

**Colour means outcome, and nothing else.** Green is "made money", red is "lost
money", amber is "below the sample threshold". The journal's LONG/SHORT label
is grey with an arrow, because a red SHORT beside a green P&L asks the reader
to hold two meanings for one colour in one row.

**Charts are `react-native-svg`**, so one implementation runs on the device and
in the browser preview — which is what makes looking at them possible at all
without a simulator.

---

## 8. Getting it onto an iPhone

Three stages, in increasing order of commitment. Nothing below is required to
use the app on a desk.

### Expo Go — minutes, free

```bash
uvicorn sensitor.api.app:app --host 0.0.0.0 --port 8000   # not 127.0.0.1
cd mobile && npx expo start
```

Install **Expo Go** from the App Store, scan the QR code. In the app's Server
field put the machine's LAN address — `http://192.168.x.x:8000`. Not
`localhost`: on the phone, that is the phone.

This runs the JavaScript inside Expo's own container. It is not a build of your
app, it cannot be handed to anyone as one, and it stops working when the dev
server does.

### A real build — EAS

```bash
npm install -g eas-cli
eas login
eas device:create                                  # register your iPhone
eas build --platform ios --profile preview
```

Produces a signed `.ipa` in Expo's cloud and a link to install it. Anything
installable on a physical iPhone needs an **Apple Developer account, $99 a
year** — that is Apple's rule, not Expo's. The `preview` profile is internal
distribution: no App Store, no review.

### TestFlight, and the App Store

```bash
eas build --platform ios --profile production
eas submit --platform ios
```

TestFlight review is light, usually a day. App Store review is not, and two
guidelines will come up for this app in particular:

* **3.1.1 — in-app purchase.** If the app unlocks paid features, the payment
  must go through Apple, which takes its cut. Reading a server the person
  already pays for elsewhere is generally accepted; putting the upgrade link
  *in the app* is what changes that.
* **4.2 / 2.1 — what the reviewer sees.** A "bring your own server" app opens
  to a sign-in form pointing at nothing. Supply a demo account against a seeded
  server in the review notes, or it will be rejected for having no content.

The bundle identifier is `com.sensitor.app` in `app.json`, and it has to be
unique across the App Store — change it before submitting.

**Before any of this leaves your own network: TLS.** The app sends a bearer
token on every request. Over plain HTTP, anyone on the path has your journal.
