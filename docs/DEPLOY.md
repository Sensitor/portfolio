# Deploying, and not losing your data

The short version: **on Streamlit Cloud, set `SENSITOR_DB_URL` to a PostgreSQL
database before you enter anything you would mind re-entering.**

---

## 1. Why the default loses data

The app stores everything in SQLite — your trades, your saved portfolios, and
the allocation you are currently editing. That is the right store on your own
machine, where the file sits on a disk that survives a reboot.

Streamlit Community Cloud gives a deployment **no persistent disk**. The
container is rebuilt on every redeploy, every restart, and every wake from
sleep — and an app with no visitors sleeps within hours. The SQLite file goes
with it. Nothing is corrupted and nothing warns you: you sign in and the
portfolio is simply not there.

The Account page says which of the two you are on, and turns red when the
answer is "this will be lost".

---

## 2. A free PostgreSQL, in about five minutes

Either provider works. Neither asks for a card on the free tier.

**[Neon](https://neon.tech)** — create a project, copy the connection string
from the dashboard. It looks like:

```
postgresql://user:password@ep-something.eu-central-1.aws.neon.tech/neondb?sslmode=require
```

**[Supabase](https://supabase.com)**: create a project, then the **Connect**
button at the top of the project, and copy the **Session pooler** string. It
looks like:

```
postgresql://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres
```

Not the « Direct connection » one (`db.<project-ref>.supabase.co`): that host
has only an IPv6 address, Streamlit Cloud cannot reach IPv6, and the app
reports the database as unavailable with the password and everything else
right. Replace `[YOUR-PASSWORD]` with the password you set. A password with
`@`, `:` or `/` in it can be pasted as it is: the app percent-encodes the user
name and password before connecting (`postgres.normalise_url`). When the
connection fails, the Account page says why under « Détail technique », with
the server's message and, for the two usual Supabase mistakes, what to change;
the password is never shown.

Pick a region near you; every page load makes a few queries and the round trip
is the whole latency.

### Give it to the app

On **Streamlit Cloud**: your app → ⋮ → *Settings* → *Secrets*, and paste:

```toml
SENSITOR_DB_URL = "postgresql://user:password@host/dbname?sslmode=require"
SENSITOR_AUTH = "multi"
```

Save. The app restarts and creates its own tables on first connection — there
is nothing to run by hand.

Streamlit Cloud has no way to set environment variables, only secrets, so the
entry point copies the ones it knows about into the environment before anything
reads them. An environment variable already set always wins, so running locally
is never overridden by a secrets file.

Running anywhere else, it is an ordinary environment variable:

```bash
export SENSITOR_DB_URL="postgresql://…"
streamlit run portfolio_optimizer_saas.py
```

### While you are there, set `SENSITOR_AUTH=multi`

A database reachable from the internet holding your net worth should be behind
a password. In `single` mode the email is a filing label and anyone who can
reach the app can open any of it — which is correct on your own laptop and
wrong on a public URL.

Since 30 October 2026, a deployment with a PostgreSQL `SENSITOR_DB_URL` and no
`SENSITOR_AUTH` runs in `multi` mode by default, and a value that is neither
`single` nor `multi` (a typo) means `multi` too: single-user mode, which has no
passwords, now has to be asked for in so many words. Set it anyway, so the
intent is written down.

---

## 3. Moving what you already have

If you have data in a local SQLite file and want it in Postgres:

```python
from sensitor.database import Store

old = Store("sensitor_data.db")
new = Store("postgresql://…")

data = old.export_user("you@example.com")
for entry in data["portfolios"]:
    portfolio = entry["portfolio"]
    pid = new.save_portfolio(
        "you@example.com", portfolio["name"], portfolio["holdings"],
        mode=portfolio["mode"], currency=portfolio["currency"],
        notes=portfolio["notes"], client_name=portfolio["client_name"])
    for snapshot in entry["snapshots"]:
        new.add_snapshot("you@example.com", pid,
                         total_value=snapshot["total_value"],
                         weights=snapshot["weights"],
                         metrics=snapshot["metrics"])

new.save_trades("you@example.com", old.list_trades("you@example.com"))

workspace = data["workspace"]
if workspace:
    new.save_workspace(
        "you@example.com", workspace["holdings"],
        mode=workspace["mode"], base_currency=workspace["base_currency"],
        profile=workspace["profile"], period=workspace["period"],
        quantities=workspace["quantities"],
        manual_prices=workspace["manual_prices"])
```

`export_user` reads through the same user-scoped methods as everything else, so
a migration cannot reach further than the app can.

---

## 4. The two backends are the same store

`Store` issues one set of SQL. `database/postgres.py` supplies a connection
object shaped like the `sqlite3` one, and translates the handful of places the
dialects differ — placeholders, auto-increment, `INSERT OR IGNORE`, and the
pragmas, which are answered rather than refused.

That is not tidiness. Two backends that drift apart are two answers to
"is this portfolio mine", and the whole isolation guarantee rests on there
being one. **The database suite runs against both** — the same 97 assertions,
SQLite by default and PostgreSQL when `SENSITOR_TEST_PG` is set:

```bash
python tests/test_database.py

createdb sensitor_test
SENSITOR_TEST_PG="postgresql://localhost/sensitor_test" python tests/test_database.py
```

There is no migration machinery on the Postgres side, and that is deliberate:
the SQLite migrations exist to carry databases written before a constraint
changed, and every Postgres database starts at the current schema. Added
columns are still applied, so one created by this code and later upgraded keeps
working.

---

## 5. Other hosts

Anywhere with a persistent disk, SQLite is still the simplest thing that works
— point `SENSITOR_DB_PATH` at a volume and there is nothing else to do:

| Host | What to attach | Then set |
|---|---|---|
| Railway | a volume, mounted at `/data` | `SENSITOR_DB_PATH=/data/sensitor.db` |
| Render | a disk, mounted at `/var/data` | `SENSITOR_DB_PATH=/var/data/sensitor.db` |
| Fly.io | a volume, mounted at `/data` | `SENSITOR_DB_PATH=/data/sensitor.db` |
| Your own machine | nothing | `SENSITOR_DB_PATH=$HOME/.sensitor/sensitor.db` |

**Set it absolutely, wherever you are.** The default is relative to the
directory the app was launched from, so `streamlit run` from two places gives
you two databases and one of them looks empty.

Put TLS in front of anything that leaves your own network: the app sends a
session token on every request.

---

## 6. Backups, and checking a deployment before it opens

**Backups.** `python -m sensitor.database.backup dump <file>.json.gz` writes every
row of every table to one gzipped JSON file, on either backend, with no
PostgreSQL client tools; `restore <file>` writes it back into an *empty*
database, in one transaction, and refuses a dump taken by a newer schema. Both
take `--db` to name another database than the app's. A PostgreSQL dump restores
into a SQLite file and the other way round, which is also how to inspect one.
Tested on both backends (`tests/test_backup.py`).

- Run it from a machine that can reach the database (your computer, with the
  same `SENSITOR_DB_URL` as the app), daily or before every deployment, and keep
  the files in encrypted storage, never in the repository (`.gitignore` covers
  `sensitor-backup-*`): they hold every member's personal and financial data.
- Your provider's own backups (Supabase, Neon) come in addition; check what your
  plan keeps and for how long.
- Restore once into a scratch database to know the procedure works:
  `python -m sensitor.database.backup restore <file> --db /tmp/essai.db`.

**Before opening to members.** `python -m sensitor.core.admin check`, run with
the production environment, lists what is still missing and exits 1 while
anything is: a durable PostgreSQL database that answers, `multi` mode, an e-mail
server, an `https` `SENSITOR_PUBLIC_URL`, and the legal pages' publisher details
and review (`content/legal/editeur.toml`).

**Connections.** The app keeps one PostgreSQL connection per process. If the
server closes it (Neon suspending, the Supabase pooler's idle timeout), the next
statement that opens a transaction reconnects and runs again; a drop in the
middle of a write is raised and rolled back, never replayed. Reads end their
transaction, so the shared connection never sits « idle in transaction ».
Tested against a real server (`tests/test_db_errors.py` with `SENSITOR_TEST_PG`).

**Speed.** Each page waits on the database a few times, and each wait costs a
network round trip between the app and the database. Reads run in autocommit
(one round trip each, not three), the session's « last seen » is written at
most every five minutes, and the member's level and roles are read once per
page. Measured with 80 ms of round trip: about 0.45 s per page, down from 2 to
2.5 s. Put the database in the region closest to the app (on Supabase, the
region is chosen when the project is created): the round trip is the cost that
remains.

**Fonts and usage statistics.** `.streamlit/config.toml` turns on static file
serving, so the fonts come from `static/fonts/` (built by
`scripts/build_fonts.py`) instead of Google, and turns off Streamlit's usage
statistics: no visitor data leaves for a third party.


**Administrators.** On Streamlit Cloud, with no command line, list them in the
secrets: `SENSITOR_ADMIN_EMAILS = "you@example.com"` (comma-separated for
several). The address becomes an administrator at its next sign-in, or at the
next page if it is already signed in, provided it has an account with a
password and, once e-mail is configured, a verified address. Elsewhere,
`python -m sensitor.core.admin set-role you@example.com admin` does the same
from a machine that reaches the database. The
« Membres et accès » page then appears in the platform's sidebar for that
account; it grants and revokes Premium (with a reason and an optional end) and
names coaches and other administrators. `check` reports a deployment with no
administrator.

---

## 7. The member area on its own domain (P1.7)

Streamlit Community Cloud is fine to start, but it sleeps after inactivity and
serves only `*.streamlit.app`. For `app.sensitor.fr`, run the same app on a host
that does not sleep:

| Host | Start command | Notes |
|---|---|---|
| Render (web service) | `streamlit run sensitor_app.py --server.port $PORT --server.address 0.0.0.0` | custom domain and TLS included; pick a paid instance so it does not sleep |
| Railway | the same | custom domain and TLS included |
| A VPS (Scaleway, OVH, Hetzner) | the same, behind Caddy or nginx | Caddy obtains the certificate by itself |

Environment, on any of them: `SENSITOR_DB_URL` (the Supabase « Session pooler »
URL), `SENSITOR_AUTH=multi`, `SENSITOR_PUBLIC_URL=https://app.sensitor.fr`, the
`SENSITOR_SMTP_*` settings, and `PYTHON_VERSION=3.11` where the host asks for it.
Point the domain with a `CNAME` record from `app` to the host's address. A
reverse proxy must pass WebSockets (`Upgrade` and `Connection` headers), which
Streamlit needs.

**The API** (`sensitor/api`, for the mobile app and later the payment webhook)
is a second service from the same repository:

    pip install -r requirements.txt "fastapi>=0.110" "uvicorn>=0.27"
    uvicorn sensitor.api.app:create_app --factory --host 0.0.0.0 --port $PORT

with the same `SENSITOR_DB_URL` and `SENSITOR_AUTH`, on `api.sensitor.fr`, and
`SENSITOR_CORS_ORIGINS` set to the origins allowed to call it. It shares the
accounts and the sessions of the platform.

---

## 8. The public site (P1.6)

`scripts/build_site.py` writes a static site from `content/` (articles in
`content/media/articles`, the Academy's programme, the free sheets, the legal
pages, `sitemap.xml`, `feed.xml`, `robots.txt`). It needs Python 3.11 and
nothing else: no dependency to install.

**GitHub Pages (built in).** `.github/workflows/site.yml` builds and publishes
the site on every push to `main`. Once, in the repository's settings:

1. *Settings > Pages > Build and deployment > Source*: « GitHub Actions ».
2. *Settings > Secrets and variables > Actions > Variables*: add
   `SENSITOR_APP_URL` with the member area's address (the Streamlit app), and,
   once the site has its own domain, `SENSITOR_SITE_URL`.
3. *Actions > Public site > Run workflow*, or push to `main`.

GitHub Pages on a private repository needs a paid GitHub plan.

**Any other static host** (Cloudflare Pages, Netlify), with the repository
connected:

| Setting | Value |
|---|---|
| Build command | `python scripts/build_site.py --base-url https://sensitor.fr --app-url https://app.sensitor.fr` |
| Output folder | `site` |
| Environment | `PYTHON_VERSION=3.11` | The site has no
script, no cookie and no third-party request; its fonts are the platform's own
files. The newsletter button opens the platform's form
(`?page=newsletter`). An article is published by setting `status = "published"`
in its file; `python -m sensitor.academy.validate` refuses one that breaks the
house rules (long dash, missing sources or review date, a tool or quiz block).

---

## 9. The newsletter and the logs

**Newsletter.** Subscriptions work as soon as e-mail is configured: the form
records the consent, sends a confirmation link valid 48 hours, and the
subscription is active once the member presses « Confirmer » on that page.
Every message carries a one-click unsubscribe link. To send campaigns, add a
Brevo list: `SENSITOR_BREVO_API_KEY` and `SENSITOR_BREVO_LIST_ID` (secrets
only). Confirmed addresses are then added to the list and removed on
unsubscription. Fill `newsletter` in `content/legal/editeur.toml` with the
provider's name; the privacy policy quotes it.

**Logs.** The app writes technical events to the standard error stream (the
host's log view): a page that raised, the database unreachable or reconnecting,
an e-mail not sent, a provider that refused a call, an account locked. Every
line is scrubbed of e-mail addresses, tokens, passwords and database URLs
before it is written. `SENSITOR_LOG_LEVEL` sets the level (INFO by default).

---

## 10. Accompaniment and statistics (P2.3 to P2.5)

**Cohorts.** In the platform, *Gestion > Cohortes et ateliers*: create a
cohort, enrol members by the address of their account, schedule workshops
(Paris time) with a video call link. A member sees the workshops and the link
only while they are Premium and the cohort is open; « Mon accompagnement »
appears in their sidebar. Closing a cohort hides its workshops and ends the
accompaniment requests for its members.

**Requests.** An accompanied member asks up to 4 questions a month
(`support.monthly_quota` in `core/permissions.py`). Coaches answer from
*Coaching > Demandes d'accompagnement*, under a pseudonym.

**Statistics.** *Gestion > Statistiques*: the funnel over a window, accounts by
month and by source, landing pages. To follow a campaign, add tags to its link:
`https://your-app/?utm_source=instagram&utm_campaign=launch`. The public site's
links carry `utm_source=site`. Visits are counted once per browser session,
with no cookie and no identifier.
