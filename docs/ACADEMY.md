# Sensitor Academy

The education product: learning paths, lessons, explained quizzes, a numeric
case study, a risk lab and a resource library. French interface.

```bash
streamlit run sensitor_app.py      # the platform; the Academy is its first space
```

The Academy is one space of the Sensitor platform — shell, navigation, design
system and brand are described in [PLATFORM.md](PLATFORM.md).

This document records what exists, how it is put together, how content is
written and published, and what is not built yet.

---

## 1. What exists today

| Area | State |
|---|---|
| Curriculum | 4 tracks (Monnaie et Bitcoin, Crypto, Investissement, Trading) and 16 paths numbered within their track; **Trading paths 1 to 7 and Monnaie et Bitcoin path 1** (its three courses) **published**, the other 8 marked « en préparation » and not clickable |
| Courses | « La monnaie » (9 lessons, sourced, with ECB and Federal Reserve rate data), « L'inflation » (9 lessons, with Eurostat, ECB and US data), « Inflation et patrimoine » (8 lessons, with a savings simulator), « Premiers pas sur les marchés » (6 lessons), « Lire la structure du marché » (7 lessons), « Liquidité et scénarios » (7 lessons), « Zones d'intérêt et entrées » (7 lessons), « Gérer le risque dans la durée » (7 lessons), « Décider sous incertitude » (8 lessons), « Tester une stratégie » (8 lessons), each in 4 chapters |
| Lessons | Markdown + callouts (definition, example, warning, mistake, method, recap, opinion, debate), sources and review date, interactive charts on sourced data, 39 original SVG diagrams and charts (path 5 charts are computed), KaTeX formulas |
| Quizzes | 66 knowledge checks (immediate feedback) + 10 validation quizzes (10 questions each, deferred correction, pass at 7 / 10) |
| Exercises | 24 numeric exercises (compounding and volatility drag, fees and tax over thirty years, two-asset diversification, a bank balance sheet, the cost of a mortgage, a bond when rates move, reading a price index, contributions to inflation, purchasing power over thirty years, EURUSD sizing, swings, GBPUSD structure case, equal highs, XAUUSD sweep case, FVG, OTE, GBPUSD entry case, drawdown series, prop-firm limits, revenge trade, overtrading costs, a 20-trade backtest, the interval of an expectancy, a 120-trade case) with worked solutions |
| Simulators | savings simulator (nominal and real value, contributions, fees, tax), in the lesson « Le simulateur » of « Inflation et patrimoine » |
| Trading Lab | risk calculator (size only with a contract spec, losing streaks) and expectancy / risk-of-ruin simulator (exact, no random simulation) |
| Library | 11 real resources, each as Markdown and as a typeset PDF |
| Progress | lesson completion, quiz attempt history, mistakes to review, JSON export |
| Accounts | the existing `Auth` and `Store` — one account works in both the Academy and the portfolio app |
| API | `/academy/*` routes on the existing FastAPI app |

Every figure quoted in a lesson (the 10-loss table, the 81 % / 55 % streak
probabilities, the 0.33-lot example, the case-study answers, the swings of the
path 2 exercise) is recomputed in `tests/test_academy.py` from the modules the
app uses: `risk.py` for money, `structure.py` for the swing, break, equal-level and sweep rules.

---

## 2. Architecture

```
content/academy/            version-controlled content (the source of truth)
  curriculum.toml           paths, in order, with status published / planned
  courses/<id>/course.toml  modules and lesson order
  courses/<id>/lessons/*.md one lesson: TOML front matter between +++ lines, then the body
  quizzes/*.toml            questions, options, an explanation per option
  exercises/*.toml          numeric steps with answer, tolerance, solution
  resources/                resources.toml + the real files it lists
  figures/*.svg             original diagrams (no scripts allowed)

sensitor/academy/           the domain — no Streamlit, no FastAPI
  content.py   load + validate the tree; Catalog, Course, Lesson, Quiz…
  markup.py    the lesson body format (::: directives)
  quiz.py      grading, pass mark, public view without the answer key
  exercise.py  French number parsing, step checking
  risk.py      every risk figure
  structure.py the swing and break rules (path 2), equal levels and sweeps (path 3)
  zones.py     FVGs, order blocks, retracements, OTE band, zone overlap (path 4)
  backtest.py  series summary, interval of an expectancy, multiple testing, degradation (path 7)
  macro.py     surprises, release times in Paris, implied rates, curve inversions, expected move, event sizing (path 8)
  discipline.py plan compliance, cost of departures, de-risking after a drawdown, the case month (path 10)
  money.py     bank balance sheets, loan instalments and schedules, bond prices (« La monnaie »)
  inflation.py rates from an index, cumulative and annualised inflation, purchasing power, contributions
  savings.py   real return, monthly savings projection, compounding, volatility drag, two-asset volatility
  bitcoin.py   Bitcoin's issuance from the protocol rules, difficulty retarget, the white paper's
               catch-up probability, fees, estimated block dates
  hashing.py   SHA-256 digests, a toy proof of work and a hash chain (the hash demonstration)
  crypto.py    pools and price impact, gas, BIP 39 entropy, depegs, market cap and dilution, loans, impermanent loss
  invest.py    progressive buying, value averaging, rebalancing, portfolio stress, the French 150 VH bis gain
  expectancy.py expectancy, Wilson interval, drawdown, exact risk of ruin (path 5)
  printable.py resource Markdown → print-ready HTML, and the PDF manifest
  progress.py  course progress and "what next"
  access.py    who may read what (the only place that decides)
  views.py     plain-data shapes served by the API
  validate.py  python -m sensitor.academy.validate
  ui/          the Academy, Library, Lab and Progress pages (presentation only;
               the shell, theme and components are in sensitor/platform/ui)

sensitor/database/          + tables lesson_progress, quiz_attempts (schema v6)
sensitor/api/routers/academy.py
sensitor_app.py             Streamlit entry point (academy_app.py runs it)
```

**Why Streamlit for this milestone.** The repository already deploys a
Streamlit app with working accounts and a PostgreSQL database. A second
Streamlit entry point ships the Academy on the same infrastructure, today, with
no new host, no new auth system and no second backend. The domain layer and the
`/academy` API are frontend-agnostic, so a Next.js client can be added later
without moving any logic — the lesson shape, scoring and risk maths are already
served over HTTP and tested there.

**Why content lives in files.** The first authoring workflow is an editor and a
pull request: every change to a lesson or an answer key is reviewed, versioned
and revertible, and the validator catches mistakes before a member does. The
database stores only what members do with the content.

---

## 3. Writing and publishing content

1. Add or edit a lesson under `content/academy/courses/<course>/lessons/`. The
   file name is the lesson id. Front matter fields: `id`, `title`, `summary`,
   `duration_minutes`, `access` (`public` / `member` / `premium`), `status`
   (`draft` / `published`), `version`, `objectives`, `quiz`, `resources`,
   `sources` (a list of texts), `updated` (the date of the last substantive
   review, `2026-10-17`, shown to readers as « mis à jour le … »).

   In a track declared with `require_sources = true` in `curriculum.toml`
   (Monnaie et Bitcoin, Crypto, Investissement), the validator refuses a
   published lesson without sources or without `updated`.
2. List it in the course's `course.toml`, in the module where it belongs.
3. Body directives:

   ```
   ::: callout definition "Titre"      kinds: note definition example warning mistake recap method
                                       opinion (« Opinion du fondateur ») debate (« Débat »)
   …Markdown…
   :::
   ::: figure mon-schema.svg           file in content/academy/figures/
   Légende.
   :::
   ::: formula                          LaTeX, rendered with KaTeX
   x = y
   :::
   ::: exercise cas-eurusd             id from content/academy/exercises/
   :::
   ::: tool risk-calculator           also ruin-simulator, savings-simulator, hash-demo
   :::
   ::: chart emission-bitcoin          id from content/academy/charts.toml
   Légende.
   :::
   ```

   **Opinions and debates.** A founder's conviction goes in `::: callout opinion`,
   a contested theory in `::: callout debate`; facts stay in the body. The two
   frames look different on purpose, so a reader always knows which is which.

   Write dollar amounts normally (`100 $`): the renderer escapes `$` so it is
   never read as LaTeX. Formulas go in `::: formula`.
4. Run `python -m sensitor.academy.validate`. It refuses: unknown references,
   missing figures or files, a question with no right answer or an option with
   no explanation, a single-choice question with two right answers, a lesson
   file left out of the plan, a figure containing a script — and lists any
   published lesson missing objectives, a summary, a recap or a practice element.
5. Preview drafts locally with `SENSITOR_ACADEMY_PREVIEW=1 streamlit run sensitor_app.py`.
6. Set `status = "published"`, bump `version` for a substantial rewrite, and
   merge. The catalogue reloads when files change.

**Library PDFs.** A resource may declare `pdf = "<name>.pdf"` next to its
Markdown `file`. After editing a sheet, rebuild its PDF:

```bash
PLAYWRIGHT_CHROMIUM=/path/to/chromium python scripts/build_resource_pdfs.py
```

The script (a development tool: Playwright, Chromium, network for the fonts)
writes the PDFs and `pdf-manifest.toml`, the SHA-256 of each source. The
validator and the tests refuse a PDF whose source has changed since it was built.

**Tracks and paths.** `curriculum.toml` starts with the `[[track]]` blocks, in
display order, then the `[[path]]` blocks. Each path names its `track` and its
`number` within it; the label shown everywhere is « Trading · Parcours 04 ».
Progress is stored per course and lesson, never per path number, so moving or
renumbering a path changes nothing for members.

**Data and charts.** Charts never embed numbers: they read a dataset declared
in `content/academy/data/datasets.toml`, either a CSV file of that folder (as
retrieved) or a generator in `sensitor/academy` (computed, tested). Every
dataset carries `source`, `url`, `license` and `retrieved`; the loader refuses
one without them, and the source line under each chart is generated from them.
A constructed example sets `synthetic = true` and is labelled « Exemple
synthétique ». `content/academy/charts.toml` then says what to draw: dataset,
`x`, series, kind (`line`, `area`, `bar`, `step`), axis titles, and an optional
boolean column (`highlight`) whose rows are drawn as estimates. Charts are
Plotly figures in the design system (`sensitor/academy/ui/chart_view.py`).

Datasets so far: the ECB deposit facility rate and the US effective federal
funds rate, monthly since 1999 (`data/taux-directeurs.csv`, built from the ECB
Data Portal and FRED and dated with its retrieval); a 200 000 € mortgage
schedule (computed); euro area, French and US inflation since 1997, euro area
inflation by component since 2015, M3 growth against inflation since 1999, US
inflation and federal funds since 1960, and the purchasing power of 100 € of
1996 in France (Eurostat `prc_hicp_minr`, ECB, FRED). An empty cell in a CSV is
a missing observation, drawn as a gap and never as a zero. Another one is
Bitcoin's issuance, computed from the protocol rules in
`sensitor/academy/bitcoin.py` (20 999 999,9769 BTC in total; past halving dates
recorded, future ones estimated and flagged).

**Not built:** an in-app editor. Until there is one, the workflow above is the
CMS. Nothing in the UI pretends otherwise.

---

## 4. Access and publication

* `status` answers *is it finished?* Drafts are absent from the catalogue.
* `access` answers *who may read it?* `public`: anyone; `member`: any signed-in
  account; `premium`: a signed-in account whose `users.tier` is `pro` or
  `premium`. Enforced server-side in both the Streamlit app and the API through
  `sensitor/academy/access.py` (the API answers 401 without an account, 403
  without the tier). A quiz follows the access of its lesson.
* There is **no payment provider, no VIP rule and no Telegram link**: the tier
  is set by hand until there is demand for an offer, and no content is premium
  today. A premium lesson tells a free member so, and asks for no payment.
* The answer key never leaves the server before a submission: the API's
  `GET /academy/quizzes/{id}` omits `correct` and the explanations.

---

## 5. Deploying on Streamlit Cloud

The Academy is a **second app from the same repository**:

1. share.streamlit.io → *Create app* → same repository and branch →
   main file **`sensitor_app.py`** (an existing `academy_app.py` deployment keeps working).
2. *Advanced settings → Secrets*: paste the same `SENSITOR_DB_URL` and
   `SENSITOR_AUTH = "multi"` as the portfolio app. Both apps then share
   accounts and data, and progress survives restarts.
3. Deploy. The database gains the two Academy tables on first open (schema v6);
   no existing row is modified.

---

## 6. Known limitations

Account limitations (reload sign-out, password reset, verification) are
resolved and described in [PLATFORM.md](PLATFORM.md#7-accounts). Remaining:

* Videos and ebooks are announced in the Academy home as « En préparation ».

---

## 7. Tests

```bash
python tests/test_academy.py       # 886 checks — content, validation, quiz, risk, progress, store
python tests/test_academy_api.py   #  92 checks — HTTP access policy, isolation, no answer key, journal
python tests/test_academy_app.py   # 309 checks — every page and space renders, locking, writes per member
python tests/test_platform.py      #  74 checks — spaces registry, journal rules, renderers, brand asset
python tests/test_accounts.py      #  42 checks — reset, verification, e-mail, export, v8 and v9 upgrades
python -m sensitor.academy.validate
```
