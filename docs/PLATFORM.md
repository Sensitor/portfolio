# The Sensitor platform

One application, one identity, one navigation and one account for every
Sensitor space. The Academy is the first space and the priority; the others are
declared, visible in the navigation, and opened one at a time when they are
genuinely usable.

```bash
streamlit run sensitor_app.py
```

`academy_app.py` still works — it runs `sensitor_app.py` — so a deployment
created with it keeps its address.

---

## 1. How the existing application was evolved

Nothing was rewritten from scratch. The audit found these pieces already in
place, and each one is reused as it was:

| Existing piece | Role in the platform |
|---|---|
| `sensitor/core/auth.py` + `Store` sessions | the single account system, shared with the portfolio app |
| `sensitor/database` (SQLite / PostgreSQL) | the single database; Academy tables since schema v6, the reflection journal since v8, its routine since v9, the trading plan, coach review requests and `users.role` since v10 |
| `sensitor/academy/*` domain | unchanged: content, quiz, risk, progress, access |
| `/academy/*` API routes | unchanged; the shell does not add a second backend |
| Academy Streamlit UI | split: the generic parts became the platform shell, the Academy pages became the first space |
| `portfolio_optimizer_saas.py` | kept as it is; linked as the « Portefeuille et risque » space, and for MetaTrader 5 synchronisation from the journal |

What moved:

```
sensitor/academy/ui/runtime.py    → sensitor/platform/ui/runtime.py     (identity, routing)
sensitor/academy/ui/components.py → sensitor/platform/ui/components.py  (design primitives)
sensitor/academy/ui/theme.py      → sensitor/platform/ui/theme.py       (design system)
sensitor/academy/ui/app.py        → sensitor/platform/ui/shell.py       (navigation, router)
sensitor/academy/ui/brand.py      → sensitor/platform/brand.py + assets/brand/
```

Old URLs keep working: `?page=paths` opens the Academy home.

---

## 2. Spaces

`sensitor/platform/spaces.py` is the registry — plain data, tested by
`tests/test_platform.py`. The sidebar, the home page's space map and the router
are all built from it.

The sidebar groups them in four pillars, in this order: **Apprendre**, **Trader**,
**Investir**, **Échanger**. The brand reads « Trading · Monnaie · Crypto »: one ecosystem
in two universes that complete each other, neither placed above the other.

**The two universes.** Each Academy track names its universe in `curriculum.toml`
(`universe = "trading"` or `"monnaie"`). Trading keeps the blue accent and Playfair
Display titles; Monnaie et crypto (the Monnaie et Bitcoin, Crypto and Investissement
tracks) takes a copper accent and Space Grotesk titles. `crumbs(..., universe=...)`
marks a course, lesson or quiz page; the stylesheet then swaps the accent tokens of
the main column (`--blue`, `--blue-2`, `--blue-soft`, `--on-navy-accent`, `--serif`),
so numerals, rules, markers, bars and charts follow. A card carries the class
`uni-monnaie` for the same effect in a mixed list. `sx-uni` is the universe badge.

| | Space | Group | Status | Pages |
|---|---|---|---|---|
| I | Academy | Apprendre | live | `academy`, `course`, `lesson`, `quiz` |
| II | Bibliothèque | Apprendre | live | `library`, `resource` |
| III | Psychologie et discipline | Apprendre | live | `psychology` (private reflection journal and session routine) |
| IV | Progression | Apprendre | live | `progress` |
| V | Trading Lab | Trader | live | `lab` (risk calculator, ruin simulator, prop firm challenge simulator, exercises) |
| VI | Journal de trading | Trader | live | `journal`, `journal_trades`, `journal_trade`, `journal_add`, `journal_plan`, `journal_reviews` |
| VII | Salle des marchés | Trader | live | `market`, `market_session`, `market_edit` (coaches) |
| VIII | Portefeuille et risque | Investir | live | `portfolio` (build), `pf_models`, `pf_assets`, `pf_overview`, `pf_performance`, `pf_health`, `pf_xray`, `pf_risk`, `pf_stress`, `pf_optimize`, `pf_simulator`, `pf_copilot`, `pf_reports`, `pf_portfolios`; the old `tools` address opens `portfolio` |
| IX | Communauté | Échanger | preparing | `community` |

The analytics app honours `?page=` only for `overview`, `trading_overview` and
`trading_journal`, and only when a session starts; any other value is ignored.

**A preparing space** has exactly one page, rendered by one template
(`spaces_view.preparing`): its status, what is planned, what already exists
that is related, and the sentence « Aucune de ses fonctionnalités n'est
active ». It has no inputs, no sample posts, no fake members. A test checks it.

**Psychologie et discipline** is live with one feature: a reflection journal
(`platform/journal.py` for the rules, `platform/ui/psychology.py` for the page,
table `journal_entries`, routes under `/journal`). Each note has a moment
(before the session, after it, or free), an optional guided question from a
fixed list, an optional 1 to 5 scale and up to 4 000 characters of text. Notes
before and after a session also carry the « Routine de séance » of path 6 to
tick (column `checks`, a JSON list; NULL when no routine was offered, so notes
written before v9 stay out of the routine counts).

* **Private by construction.** Every store method takes the member's address
  and puts it in the WHERE clause; the API takes the member from the bearer
  token only, and a note that belongs to someone else answers 404, like a
  missing one. Notes are in the account export and are erased with the account.
* **No interpretation.** The page shows counts, the average of the scale the
  member filled in, and how many notes ticked each routine item, each with its
  sample size. It never reads the text, scores
  it, labels the person or suggests a diagnosis.
* The space links to path 6, « Décider sous incertitude », and to its « Routine de séance »
  checklist. Nothing in it is announced as planned any more.

**Journal de trading** is live, in this app and on the same `trades` table as
the analytics app, so trades synchronised from MetaTrader 5 there appear here.

* **The plan and the automatic review** (`trading/review.py`). A member writes
  their rules once (stop, maximum risk, minimum reward-to-risk, sessions,
  setups, trades per day, daily loss limit in R, pause after losses; table
  `trading_plans`). Every closed trade is checked rule by rule: respected,
  broken, or not checkable (never counted as a pass). Mistakes the member
  recorded on a trade count as departures; nothing is inferred from prices.
  Each broken rule points to the Academy lesson that teaches it. The dashboard
  shows the compliance rate, the R of trades inside and outside the plan, the
  curve as traded against the curve with departures set to zero, the cost per
  rule with a priority lesson, a calendar of R per day, and results by setup
  and session with their sample size.
* **Entry and import** (`trading/entry.py`). A trade is entered with the risk
  in money; the size is `risk / |entry − stop|`, so R is exact for any
  instrument. Times are Paris time, stored in UTC. A CSV template imports
  many trades (« ; » or « , », decimal comma), reports each bad row by line,
  and re-importing a file updates rather than duplicates.
* **Coach review** (`trading/coaching.py`, `platform/ui/trade_reviews.py`,
  table `trade_reviews`). A member sends one closed trade with a question: a
  frozen copy of that trade and its notes, its automatic review and the plan.
  Nothing else of the journal leaves the account; the coach sees a pseudonym.
  Quota per calendar month: 1 for a member, 8 for premium (no billing; the tier
  is set by hand). A coach is an account with `users.role = 'coach'`, set with
  `python -m sensitor.core.admin set-role someone@example.com coach`; the
  queue and the answer go through store methods that check the role inside
  their own query, and the page `coach` checks it again. The answer has four
  marks, what is solid, what to work on, a comment and up to four lessons. It
  is about a closed trade only; the form says no recommendation belongs in it.
* **Demonstration.** A visitor, or a member who asks, sees a constructed
  journal (`trading/demo.py`), labelled « Exemple synthétique » on every page.

**Salle des marchés** is live (`platform/market.py` for the rules,
`platform/ui/market_room.py` for the pages, table `market_sessions`, schema v11).
A coach prepares a session before the open: the week's context, the day's
calendar (one line per publication, « 14:30 | Emploi américain | forte », Paris
time), up to four scenarios, each a condition, what to watch and its
**invalidation, which is mandatory**, the lessons it uses, and optionally the
address of a live (https YouTube or Vimeo only). After the close, the review
gives each scenario its outcome (joué, invalidé, non déclenché), what the
session teaches, the replay and further lessons.

* **No signals.** `market.signal_phrases` flags instructions to buy or sell,
  « signal d'achat / de vente », profit targets and promises of results, on
  words, accents and case removed, without catching analysis vocabulary
  (« les vendeurs », « un signal de faiblesse », « rien n'est garanti »). The
  store refuses to publish a session that has any, and a review cannot be saved
  with one. Every session page carries the same pedagogical notice.
* **Who writes, who reads.** Writing, publishing, reviewing and deleting go
  through store methods that check the coach role in their own query; a draft
  and its author are returned to a coach only; a published session cannot be
  deleted, only unpublished. Readers get each session at the access level its
  author chose (public, member, premium), decided by `academy.access` like the
  lessons. A departing coach's sessions stay, without the address.
* **No invented content.** With nothing published, the room says so and shows
  how a session is built; there is no sample session.
* The room lists the latest session, the earlier ones with the print of their
  outcomes, and the record of every reviewed scenario, then the lessons on
  preparing a session, building a liquidity scenario and reading the calendar.

**Portefeuille et risque** is the portfolio analyzer inside the member space
(`platform/ui/portfolio_space.py`). Nothing of the analysis is rewritten: the
eleven pages are the `sensitor.pages` renderers, given the context the separate
app builds (`investment.context.build_context`), in French, and styled by the
analyzer's component stylesheet alone (`ui.themes.components_css`, injected by
`inject_components`: headers, cards, alerts, tables, the « Lecture » margin, the
risk hatch, with no page, sidebar or widget rule; the separate app's own
stylesheet is byte for byte what it was).

* **Building page** (`portfolio`): lines from the asset library, their weights
  (brought back to 100 % in proportion), the currency and the risk profile, then
  « Analyser le portefeuille », which prices the last two years as the separate
  app does. A free account composes five lines, a premium one fifty; an
  allocation built elsewhere with more lines stays whole and can be edited, not
  grown.
* **The real portfolio**, in quantities: lines from the library or outside it
  (a short name, « APPARTEMENT », « ASSURANCE-VIE »), a price typed by hand with
  its currency for whatever no provider covers (used only when no quote exists,
  and marked as the member's estimate with its date), then « Valoriser et
  analyser ». The valuation is `investment.holdings`, the one rule both apps
  use: quantity × today's price in the base currency, a total, weights, and the
  lines without any price named rather than valued at zero. A line priced by
  hand has no history, so the analysis leaves it out with its money; the
  building page shows the whole wealth, line by line with the source of each
  price, and every analysis page says which lines are valued but not analysed.
* **One working portfolio per member.** The allocation is the `workspace` row
  of the verified email, restored and written by `pages._workspace` exactly as
  in the separate app, so a portfolio built in one opens in the other. The
  analyzer itself (the price history) stays in the session. A visitor can
  analyse; nothing is kept.
* **Navigation.** The separate app's page changes (the copilot sending a change
  to the simulator, the portfolios page asking for a new analysis of a saved
  allocation) become the platform's pages.
* **Allocations types** (`pf_models`): the analyzer's eight model portfolios,
  from the most prudent to the most aggressive, framed as compositions to study,
  never as advice. Each shows its lines and weights and its share by kind of
  asset (shares, bonds, gold and commodities, listed real estate, crypto),
  computed from the weights and the library's sectors (`composition`). The
  catalogue's hand-written expected return and volatility are not shown: the
  figures are those the analysis computes once the allocation is loaded. Names
  and descriptions are written for the platform, without a figure or a promise.
  « Étudier cette allocation » analyses it and makes it the working portfolio.
* **Actifs** (`pf_assets`, a sheet with `asset=`): the asset library, searched
  by symbol, name or sector and filtered by class. A sheet gives the asset's
  description, class, sector and geography in French, its risk level and its
  liquidity in words, and the role usually given to it, marked as a reading and
  not a sizing advice; a crypto sheet points to the course « Bitcoin, une
  réserve de valeur ? ». Market cap, dividend yield and allocation ranges are
  left out, and so is any sentence of the catalogue's prose that carries a
  figure (`plain`): none of them is sourced. « Ajouter » puts the asset in the
  working portfolio (an equal share, the other lines keeping their proportions,
  within the free account's five lines) or, in real mode, in the holdings with
  its quantity.
* **Still in the separate app**, and said on the building page with a link when
  `SENSITOR_TOOLS_URL` is set: the MetaTrader 5 analytics.

### Adding a space

1. Declare it in `spaces.SPACES` (id, label, group, status, summary, entry,
   pages, planned, related).
2. Give each of its pages a renderer in `RENDERERS` in `platform/ui/shell.py`.
3. Use the platform components; read the account through `runtime.current_user()`.
4. `tests/test_platform.py` fails until every page has a renderer.

When the space opens, change its status to `live`. The navigation follows.

### The Telegram bot

Completely independent. The platform does not read, call, link to or depend on
the bot, its database, its VPS or its deployment.

---

## 3. Design system

`sensitor/platform/ui/theme.py` holds the tokens and the stylesheet;
`components.py` the primitives. Every space uses them.

**Signature**

* Editorial numerals — chapters I, II, III in a large serif italic; sections
  « § 01 » on a strong ink rule with a short blue lead-in.
* Hexagonal markers from the mark — lesson state at a glance: outlined (to
  read), ink (current), blue with a check (finished), dashed (members only).
* An isometric grid, barely visible, on navy panels — the monogram's 30° geometry.

**Hierarchy** — Playfair Display for titles (display 4.4 rem → page 3.3 rem →
section 2.15 rem → chapter 1.95 rem → lesson 1.32 rem), DM Sans for reading,
DM Mono for every label, duration and figure. A title, a chapter, a lesson and
its metadata never share a treatment.

**Surfaces** — ivory page, white for what is read or filled in (lesson sheet,
quiz, calculator), navy for a starting point, a result or a recap. One blue
accent; green and red only for right and wrong.

**Interaction** — a whole composition is clickable through a stretched button
(`components.tap`): the drawing is `aria-hidden`, the real button carries the
label and the keyboard focus ring. Hover moves arrows and lifts cards by 1–2 px;
`prefers-reduced-motion` disables transitions.

**Responsive** — below 1000 px sections stack, chapters shrink their numeral,
lesson rows wrap their metadata, the lesson outline stops being sticky.

**Light and dark systems** — every widget colour is set explicitly, so the
pages are identical whatever the visitor's system theme.

---

## 4. Brand

`assets/brand/sensitor-mark.svg` is a vector trace of the supplied logo: the two
hooks of the S measured on its isometric grid, the anthracite tile (#262626,
21/128 corner radius) and the silver gradient (#fcfcfc → #9c9c9c) sampled from
the image. `assets/brand/sensitor-monogram.svg` is the S alone, one colour.

**If the official vector file exists**, save it as
`assets/brand/sensitor-mark-official.svg`. `sensitor/platform/brand.py` uses it
in preference everywhere — sidebar, favicon — with no code change.

---

## 5. Real features and demonstration

Everything on screen is real:

* counts on the home page are counted from the published content;
* progress, scores and dates come from the member's rows;
* every library download serves the file it names.

Illustrative figures exist only **inside lessons**, where they are labelled
(« Chiffres illustratifs », « Exemple pédagogique », « compte de démonstration »).
Spaces in preparation say so and offer nothing to click but links to real content.

---

## 6. Deploying

Streamlit Cloud: main file **`sensitor_app.py`** (or keep an existing
`academy_app.py` deployment), with the same secrets as the portfolio app, plus
the optional ones for e-mail:

```toml
SENSITOR_DB_URL = "postgresql://…"
SENSITOR_AUTH = "multi"
SENSITOR_PUBLIC_URL = "https://<your-app>.streamlit.app"   # base of e-mailed links
SENSITOR_TOOLS_URL = "https://<portfolio-app>.streamlit.app" # optional

# E-mail (password reset, address verification). Any SMTP provider works:
SENSITOR_SMTP_HOST = "smtp-relay.brevo.com"
SENSITOR_SMTP_PORT = "587"
SENSITOR_SMTP_USER = "…"
SENSITOR_SMTP_PASSWORD = "…"
SENSITOR_MAIL_FROM = "Sensitor <no-reply@your-domain>"
```

Without the SMTP block the app says that e-mail is not configured, and an
operator can still hand out a reset link:

```bash
python -m sensitor.core.admin reset-link someone@example.com    # valid 1 hour, once
python -m sensitor.core.admin verify-link someone@example.com   # valid 48 hours, once
python -m sensitor.core.admin set-role someone@example.com coach   # or member
python -m sensitor.core.admin set-tier someone@example.com premium # or free; no billing
```

---

## 7. Accounts

* **Staying signed in.** The session token is kept in a `sensitor_session`
  cookie (SameSite=Lax, Secure on HTTPS, 30 days) and read back on reload.
  Sign-out clears it; « Se déconnecter de tous les appareils » revokes every
  session server-side.
* **Password reset** and **address verification** use single-use tokens
  stored as fingerprints (table `account_tokens`, schema v7). Reset links last
  one hour and revoke every session when used; asking twice keeps only the
  latest link; the request page never reveals whether an address has an account.
* **For a member:** password change, full JSON export (credentials excluded),
  and account deletion with confirmation, which removes every row filed under
  the address.

---

## 8. Known limitations

* The session cookie is set from the page, so it cannot be HttpOnly; all
  rendered text is escaped, which is what makes that acceptable.
* Verification is shown, not enforced: an unverified address can still read.
* The portfolio app keeps its own look and sign-in screen until it is brought
  into the shell; the account itself is already shared.
* Fonts load from Google Fonts; offline, system fonts are used.
