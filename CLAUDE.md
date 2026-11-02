# CLAUDE.md: guide for AI assistants working on Sensitor

## What the project is

Sensitor is a French trading and investment education platform with two
universes that complete each other: **Trading**, and **Monnaie et crypto**
(money, inflation, Bitcoin, crypto, investing). It runs on Streamlit, over one
account and one database, next to the original portfolio and trading
analytics application.

| Entry point | What it is |
|---|---|
| `sensitor_app.py` | the education platform: Academy, Library, Psychology, Progress, Trading Lab |
| `portfolio_optimizer_saas.py` | the portfolio and trading analytics application |
| `sensitor/api` | the HTTP API (FastAPI), optional |
| `mobile/` | the Expo app over the API |

## Where things are

```
content/academy/          the courses, as files: the source of truth
  curriculum.toml         tracks (with their universe), then paths, in order
  courses/<id>/           course.toml and lessons/*.md (TOML front matter between +++)
  quizzes/ exercises/     TOML
  figures/                original SVG diagrams
  data/                   sourced CSV datasets, declared in datasets.toml
  charts.toml             interactive charts over those datasets
  resources/              revision sheets (Markdown) and their PDFs
content/media/articles/   the public site's articles (same front matter, same rules)
content/legal/            the legal pages and the publisher's details (editeur.toml)
sensitor/academy/         domain: content loading and validation, quiz, exercises,
                          and one pure, tested module per subject (risk, structure,
                          zones, backtest, macro, discipline, money, inflation,
                          savings, bitcoin, hashing, crypto, invest)
sensitor/academy/ui/      Academy pages (presentation only)
sensitor/platform/        spaces registry, shell, theme, components, newsletter, legal
sensitor/core/permissions.py  every access decision: levels, roles, capabilities, limits
sensitor/site/            the public site: articles loader and static generator
docs/                     ACADEMY.md, PLATFORM.md, PLAN_BITCOIN_CRYPTO.md, and more
tests/                    one script per area
```

## Running and testing

```bash
pip install -r requirements.txt
streamlit run sensitor_app.py
python -m sensitor.academy.validate       # validates the content tree
python tests/test_academy.py              # and every other tests/test_*.py
python scripts/build_resource_pdfs.py     # after changing a revision sheet
python scripts/build_site.py --base-url … --app-url …   # the public site, into site/
python -m sensitor.core.admin check       # what a deployment still lacks
```

Each test file is a plain script that prints its checks and returns a non-zero
status on failure. Run the whole `tests/` folder before committing.

## Rules of the house

- **Content in French, without long dashes.** No em dash (U+2014) or en dash (U+2013) in lessons,
  quizzes, the interface or replies; tests enforce it. The minus sign « − » is fine.
- **Every number is sourced or computed.** A figure in a lesson comes from a
  dataset in `content/academy/data` (with its source, licence and date) or from
  a pure module in `sensitor/academy`, and a test recomputes it. Constructed
  examples say so.
- **No data without a licence that allows it.** Free sources reviewed on
  19 October 2026 do not allow commercial reuse of Bitcoin's price history; see
  `docs/PLAN_BITCOIN_CRYPTO.md`. Price-free on-chain metrics are computed from
  the chain.
- **Facts, opinions and debates are separated**: the founder's opinion goes in a
  `callout opinion`, open questions in a `callout debate`. Bitcoin is never
  presented as a guaranteed hedge, no indicator as an infallible signal.
- **Never ask for a seed phrase or a private key**, and never build a feature
  that would. A test checks that no input field is labelled as one.
- **No personalised advice, order execution or payment flow** without a
  regulatory review first; access levels exist (public, member, premium), billing
  does not.
- **Every access check asks `core.permissions`** (`can`, `limit`): no page
  compares a level string, and every protected write checks the role in the
  `Store`'s own SQL. Premium comes from an entitlement (`entitlements` table),
  granted by an administrator with a reason; `users.tier` is a cache.
- **A new table holding a member's data** enters the export, the deletion and the
  privacy policy (`content/legal/confidentialite.md`); the tests compare them.
- **Accompaniment answers and trading-room sessions stay pedagogical**: never a
  recommendation on an asset, an amount or a moment (`platform/support.py`).
- **The community follows its charter** (`platform/community.py`): no signals,
  never a secret (a message that looks like a recovery phrase or a private key
  is refused), no advertising; authors show by name or pseudonym, never by
  address; every message can be reported and an administrator decides.
- **Videos load on request** and always carry a transcript (`academy/videos.py`).
- **Statistics are counts**: visits are counted without cookie or identifier,
  and no address appears on the statistics page.
- **Logs carry no personal data**: use `core.logs`, which scrubs addresses,
  tokens and database URLs.
- **Members' data is scoped by the verified email**; nothing user-specific is
  cached across users. The SQLite database stays out of git.
- **The Telegram bot is out of scope**: do not modify it, its configuration,
  database or server, and do not make the Academy depend on it.
- Keep the design system (navy, ivory, tabular figures; blue for Trading, copper
  for Monnaie et crypto). Extend it; do not redo validated components.

## Git

Work on the `claude/` branch you are given, never on `main`. Add files by
explicit path, write a commit message that says what changed and why, and run
the tests before pushing. No pull request unless asked.
