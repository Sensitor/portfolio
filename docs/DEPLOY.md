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

**[Supabase](https://supabase.com)** — create a project, then
*Project Settings → Database → Connection string → URI*. Replace
`[YOUR-PASSWORD]` with the password you set.

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
