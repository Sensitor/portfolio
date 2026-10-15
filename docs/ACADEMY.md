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
| Curriculum | 10 paths declared; **path 1 published**, 9 marked « en préparation » and not clickable |
| Course | « Premiers pas sur les marchés » — 6 lessons in 4 modules, ~1 h 34 |
| Lessons | Markdown + callouts (definition, example, warning, mistake, method, recap), 5 original SVG diagrams, KaTeX formulas |
| Quizzes | 5 knowledge checks (immediate feedback) + 1 validation quiz (10 questions, deferred correction, pass at 7 / 10) |
| Exercise | « Préparer un achat sur EURUSD » — 6 numeric steps, tolerance per step, worked solution |
| Risk lab | risk amount, stop distance, reward-to-risk, position size (only with a contract spec), losing-streak table, streak probability |
| Library | 2 real Markdown resources (a revision sheet, public; a pre-trade checklist, members) |
| Progress | lesson completion, quiz attempt history, mistakes to review, JSON export |
| Accounts | the existing `Auth` and `Store` — one account works in both the Academy and the portfolio app |
| API | `/academy/*` routes on the existing FastAPI app |

Every figure quoted in a lesson (the 10-loss table, the 81 % / 55 % streak
probabilities, the 0.33-lot example, the case-study answers) is recomputed in
`tests/test_academy.py` from the module the calculator uses.

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
   `duration_minutes`, `access` (`public` / `member`), `status` (`draft` /
   `published`), `version`, `objectives`, `quiz`, `resources`, `sources`.
2. List it in the course's `course.toml`, in the module where it belongs.
3. Body directives:

   ```
   ::: callout definition "Titre"      kinds: note definition example warning mistake recap method
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
   ::: tool risk-calculator
   :::
   ```

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

**Not built:** an in-app editor. Until there is one, the workflow above is the
CMS. Nothing in the UI pretends otherwise.

---

## 4. Access and publication

* `status` answers *is it finished?* Drafts are absent from the catalogue.
* `access` answers *who may read it?* `public` — anyone; `member` — any signed-in
  account. Enforced server-side in both the Streamlit app and the API through
  `sensitor/academy/access.py`.
* There is **no paid tier, no VIP rule, no payment provider and no Telegram
  link**. These are deliberately deferred. When the access model is agreed it
  is added to `access.py`; nothing else decides access.
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

* **A browser reload signs the member out.** The session token lives in
  Streamlit session state, as in the portfolio app. The fix is a cookie-backed
  session or Streamlit's built-in OIDC login (`st.login`), which needs an
  identity provider to be chosen.
* **No password reset or email verification yet** — the existing auth has
  neither; both need an email service.
* The logo is a vector trace of the supplied image; drop the official file in
  `assets/brand/sensitor-mark-official.svg` to replace it everywhere.
* Fonts load from Google Fonts; without network access the app falls back to
  system fonts.
* On a phone, the lesson outline sits above the lesson rather than beside it.
* Library files are Markdown. PDFs can be added the same way once they exist.

---

## 7. Tests

```bash
python tests/test_academy.py       # 215 checks — content, validation, quiz, risk, progress, store
python tests/test_academy_api.py   #  56 checks — HTTP access policy, isolation, no answer key
python tests/test_academy_app.py   #  76 checks — every page and space renders, locking, writes per member
python tests/test_platform.py      #  39 checks — spaces registry, renderers, brand asset
python -m sensitor.academy.validate
```
