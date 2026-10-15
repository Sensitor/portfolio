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
| `sensitor/database` (SQLite / PostgreSQL) | the single database; Academy tables since schema v6 |
| `sensitor/academy/*` domain | unchanged: content, quiz, risk, progress, access |
| `/academy/*` API routes | unchanged; the shell does not add a second backend |
| Academy Streamlit UI | split: the generic parts became the platform shell, the Academy pages became the first space |
| `portfolio_optimizer_saas.py` | untouched; linked as the « Outils et portefeuille » space |

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

| | Space | Status | Pages |
|---|---|---|---|
| I | Academy | live | `academy`, `course`, `lesson`, `quiz` |
| II | Bibliothèque | live | `library`, `resource` |
| III | Psychologie et discipline | preparing | `psychology` |
| IV | Trading Lab | live | `lab` (risk calculator, exercises) |
| V | Salle des marchés | preparing | `market` |
| VI | Communauté | preparing | `community` |
| VII | Progression | live | `progress` |
| VIII | Outils et portefeuille | separate | `tools` (link to the analytics app) |

**A preparing space** has exactly one page, rendered by one template
(`spaces_view.preparing`): its status, what is planned, what already exists
that is related, and the sentence « Aucune de ses fonctionnalités n'est
active ». It has no inputs, no sample posts, no fake members. A test checks it.

**The separate space** links to the portfolio app when `SENSITOR_TOOLS_URL` is
set, and says the link is not configured otherwise.

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
`academy_app.py` deployment), with the same secrets as the portfolio app:
`SENSITOR_DB_URL`, `SENSITOR_AUTH = "multi"`, and optionally
`SENSITOR_TOOLS_URL` for the link to the analytics app.

---

## 7. Known limitations

* A browser reload signs the member out (session token in Streamlit session
  state). Fix: cookie-backed session or `st.login` with an identity provider.
* No password reset or email verification yet.
* The portfolio app keeps its own look and sign-in screen until it is brought
  into the shell; the account itself is already shared.
* Fonts load from Google Fonts; offline, system fonts are used.
