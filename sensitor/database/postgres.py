"""
The PostgreSQL backend.

**Why this exists.** SQLite is the right store on your own machine and the wrong
one on Streamlit Cloud, whose filesystem is wiped on every restart, redeploy and
sleep. The persistence layer worked; the file it wrote to did not survive. A
portfolio that has to be re-entered after every nap is not persisted.

**What it is not.** Not an ORM, and not a rewrite. `Store` still issues the same
SQL it always did; this module supplies a connection object shaped like the
`sqlite3` one — `execute`, `executemany`, `commit`, `rollback`, `close`, cursors
with `fetchall`/`fetchone`/`lastrowid`, rows addressable by name *and* by
position. Everything above `connection.connect()` is unaware there are two
backends, which is the only way two backends stay in agreement about what a
query means.

The differences that actually exist between the two dialects are small enough to
list in full, and they are all handled here:

* **Placeholders.** SQLite takes `?`, Postgres takes `%s`. Rewritten on the way
  through, skipping anything inside a quoted string.
* **Auto-increment.** `INTEGER PRIMARY KEY AUTOINCREMENT` becomes
  `SERIAL PRIMARY KEY`.
* **`INSERT OR IGNORE`** becomes a trailing `ON CONFLICT DO NOTHING`.
* **The schema version.** SQLite keeps it in `PRAGMA user_version`, a slot the
  file format provides; Postgres has no equivalent, so it goes in a one-row
  table.
* **`PRAGMA` anything else.** Meaningless here, and silently ignored rather than
  raising — foreign keys are always enforced in Postgres, which is what the
  pragma was asking for.

`INSERT ... ON CONFLICT ... DO UPDATE SET ... excluded.x` needs no translation:
SQLite borrowed the syntax from Postgres.
"""

from __future__ import annotations

import re

# Imported lazily by `connect` so the app runs with no Postgres driver installed.
# Most people will never need one.


def is_url(target: str) -> bool:
    """Whether a database target names a Postgres server rather than a file."""
    if not target:
        return False
    return str(target).startswith(("postgres://", "postgresql://"))


# =============================================================================
# TRANSLATION
# =============================================================================

def to_pg_params(sql: str) -> str:
    """
    Rewrite `?` placeholders as `%s`.

    Quoted stretches are skipped. No query in this codebase contains a literal
    question mark today, but a text default or a LIKE pattern one day would turn
    a silent corruption into the kind of bug that takes an afternoon.

    A literal `%` in the SQL is doubled, because psycopg2 runs the string
    through its own formatting once the parameters are bound.
    """
    out = []
    quote = None
    for char in sql:
        if quote:
            out.append("%%" if char == "%" else char)
            if char == quote:
                quote = None
            continue
        if char in ("'", '"'):
            quote = char
            out.append(char)
        elif char == "?":
            out.append("%s")
        elif char == "%":
            out.append("%%")
        else:
            out.append(char)
    return "".join(out)


_AUTOINCREMENT = re.compile(
    r"INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT", re.IGNORECASE)
_INSERT_OR_IGNORE = re.compile(r"\bINSERT\s+OR\s+IGNORE\s+INTO\b", re.IGNORECASE)


def to_pg_ddl(sql: str) -> str:
    """Rewrite one SQLite CREATE statement for Postgres."""
    return _AUTOINCREMENT.sub("SERIAL PRIMARY KEY", sql)


def to_pg_sql(sql: str) -> str:
    """
    Rewrite one SQLite statement for Postgres, placeholders included.

    `INSERT OR IGNORE` has no Postgres spelling, but `ON CONFLICT DO NOTHING`
    means the same thing and can simply be appended — the statement is rejected
    by Postgres if it already carries its own `ON CONFLICT`, which is louder
    than guessing.
    """
    statement = to_pg_ddl(sql)
    if _INSERT_OR_IGNORE.search(statement):
        statement = _INSERT_OR_IGNORE.sub("INSERT INTO", statement)
        if "ON CONFLICT" not in statement.upper():
            statement = statement.rstrip().rstrip(";") + " ON CONFLICT DO NOTHING"
    return to_pg_params(statement)


# =============================================================================
# THE CONNECTION
# =============================================================================

class Cursor:
    """A psycopg2 cursor wearing the two attributes `sqlite3` callers expect."""

    def __init__(self, cursor):
        self._cursor = cursor

    def fetchall(self):
        return self._cursor.fetchall() if self._cursor.description else []

    def fetchone(self):
        return self._cursor.fetchone() if self._cursor.description else None

    @property
    def lastrowid(self):
        """
        Always None.

        Postgres has no equivalent, and inventing one from `RETURNING` here
        would guess at which column the caller wanted. The two callers that
        needed an id ask for it explicitly with `RETURNING id`, which SQLite
        also supports — so the call sites are now identical rather than
        branching on the backend.
        """
        return None

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def __iter__(self):
        return iter(self.fetchall())


class Row(list):
    """
    A row addressable by position and by name, like `sqlite3.Row`.

    Used only for the canned pragma answers. `PRAGMA table_info` is read as
    `row["name"]` by the migration code, and a plain tuple would send it looking
    for a string key on a list.
    """

    def __init__(self, values, names=()):
        super().__init__(values)
        self._names = {name: i for i, name in enumerate(names)}

    def __getitem__(self, key):
        if isinstance(key, str):
            return list.__getitem__(self, self._names[key])
        return list.__getitem__(self, key)

    def keys(self):
        return list(self._names)


class StaticCursor:
    """Canned rows, for the pragmas Postgres answers without being asked."""

    def __init__(self, rows=()):
        self._rows = list(rows)

    def fetchall(self):
        return list(self._rows)

    def fetchone(self):
        return self._rows[0] if self._rows else None

    @property
    def lastrowid(self):
        return None

    @property
    def rowcount(self):
        return len(self._rows)

    def __iter__(self):
        return iter(self._rows)


_PRAGMA = re.compile(r"^\s*PRAGMA\s+(\w+)\s*(?:=\s*(\S+)|\(\s*(\w+)\s*\))?\s*;?\s*$",
                     re.IGNORECASE)


class Connection:
    """
    A `sqlite3.Connection` lookalike over psycopg2.

    Autocommit is off: `Store._write` commits or rolls back around each unit of
    work, exactly as it does on SQLite, so a half-applied change is impossible
    on either backend.
    """

    def __init__(self, dsn: str):
        import psycopg2
        import psycopg2.extras

        self._dsn = dsn
        # `DictCursor`, not `RealDictCursor`: its rows answer to both `row["n"]`
        # and `row[0]`, which is what `sqlite3.Row` does and what the callers
        # above this layer assume.
        self._conn = psycopg2.connect(dsn, cursor_factory=psycopg2.extras.DictCursor)
        self._conn.autocommit = False

    # ── The sqlite3 surface ──────────────────────────────────────────────────

    def execute(self, sql: str, params: tuple = ()):
        pragma = _PRAGMA.match(sql)
        if pragma:
            return self._pragma(pragma)
        cursor = self._conn.cursor()
        cursor.execute(to_pg_sql(sql), tuple(params))
        return Cursor(cursor)

    def _pragma(self, match):
        """
        Answer a SQLite pragma the way Postgres would if it had them.

        Not a curiosity: the point of this backend is that nothing above it
        branches on which database it is talking to, and raising on a pragma
        would force exactly that branch into the migration code and into the
        tests. Each one below has a real Postgres answer, and the answer is
        given rather than the question refused.
        """
        name = match.group(1).lower()
        value = match.group(2)
        argument = match.group(3)

        if name == "user_version":
            if value is None:
                return StaticCursor([Row([get_version(self)], ["user_version"])])
            set_version(self, int(value))
            return StaticCursor()

        # Foreign keys are always enforced here, which is what the pragma asks
        # for — so setting it is a no-op and *reading* it answers 1, because
        # that is the truth about this database and a caller checking the
        # guarantee deserves the real answer rather than silence.
        if name == "foreign_keys":
            return StaticCursor() if value is not None \
                else StaticCursor([Row([1], ["foreign_keys"])])

        # `legacy_alter_table` steers a SQLite rebuild that never runs here.
        if name == "legacy_alter_table":
            return StaticCursor() if value is not None \
                else StaticCursor([Row([0], ["legacy_alter_table"])])

        # The two checks the SQLite migration refuses to finish without.
        # Postgres enforces both continuously, so there is nothing to report.
        if name == "foreign_key_check":
            return StaticCursor()
        if name == "integrity_check":
            return StaticCursor([Row(["ok"], ["integrity_check"])])

        if name == "table_info" and argument:
            return StaticCursor([Row([i, column], ["cid", "name"]) for i, column
                                 in enumerate(columns(self, argument))])

        return StaticCursor()

    def executemany(self, sql: str, seq) -> Cursor:
        rows = [tuple(item) for item in seq]
        cursor = self._conn.cursor()
        if rows:
            cursor.executemany(to_pg_sql(sql), rows)
        return Cursor(cursor)

    def executescript(self, script: str) -> None:
        """
        Apply a multi-statement script.

        Split on semicolons at the top level, because psycopg2 will run several
        statements in one `execute` but then reports errors against the whole
        blob — and a schema that fails to apply should say which table.
        """
        for statement in _split(script):
            self.execute(statement)

    def commit(self) -> None:
        self._conn.commit()

    def rollback(self) -> None:
        self._conn.rollback()

    def close(self) -> None:
        self._conn.close()

    @property
    def closed(self) -> bool:
        return bool(self._conn.closed)


def _split(script: str) -> list[str]:
    """Statements of a script, ignoring semicolons inside quotes and comments."""
    statements, current, quote, comment = [], [], None, False
    for char in script:
        if comment:
            if char == "\n":
                comment = False
                current.append(char)
            continue
        if quote:
            current.append(char)
            if char == quote:
                quote = None
            continue
        if char in ("'", '"'):
            quote = char
            current.append(char)
        elif char == "-" and current and current[-1] == "-":
            current.pop()
            comment = True
        elif char == ";":
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
        else:
            current.append(char)
    tail = "".join(current).strip()
    if tail:
        statements.append(tail)
    return statements


# =============================================================================
# SCHEMA VERSION
# =============================================================================

VERSION_TABLE = """
CREATE TABLE IF NOT EXISTS schema_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
)"""


def get_version(conn) -> int:
    conn.execute(VERSION_TABLE)
    rows = conn.execute(
        "SELECT value FROM schema_meta WHERE key = ?", ("user_version",)).fetchall()
    if not rows:
        return 0
    try:
        return int(rows[0][0])
    except (TypeError, ValueError):
        return 0


def set_version(conn, version: int) -> None:
    conn.execute(VERSION_TABLE)
    conn.execute(
        """INSERT INTO schema_meta (key, value) VALUES (?, ?)
           ON CONFLICT(key) DO UPDATE SET value = excluded.value""",
        ("user_version", str(int(version))),
    )


def table_names(conn) -> set[str]:
    rows = conn.execute(
        "SELECT tablename FROM pg_tables WHERE schemaname = current_schema()"
    ).fetchall()
    return {row[0] for row in rows}


def columns(conn, table: str) -> list[str]:
    rows = conn.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = current_schema() AND table_name = ? "
        "ORDER BY ordinal_position",
        (table,),
    ).fetchall()
    return [row[0] for row in rows]
