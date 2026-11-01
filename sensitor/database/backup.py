"""
A backup of the whole database, and its restoration, on either backend.

    python -m sensitor.database.backup dump  sensitor-backup-2026-10-30.json.gz
    python -m sensitor.database.backup restore sensitor-backup-2026-10-30.json.gz

The database is the one the app uses (`SENSITOR_DB_URL`, else
`SENSITOR_DB_PATH`), or the one given with `--db`. A dump is every row of every
table, as gzipped JSON, with the schema version it was taken at. It needs no
PostgreSQL client tools, so it runs anywhere Python and the app's dependencies
run, and it restores into either backend: a PostgreSQL dump can be restored into
a SQLite file to inspect it, and the other way round to move a deployment.

A restore writes into an empty database only, all of it in one transaction, and
refuses a dump taken by a newer version of the schema than this code knows. It
then brings the identifier counters of PostgreSQL up to the restored rows, so the
next portfolio or quiz attempt gets a new number.

The file holds every member's personal and financial data: keep it out of the
repository (`.gitignore` covers `sensitor-backup-*`), in encrypted storage, and
delete old ones.
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from datetime import datetime, timezone

from . import postgres as pg
from .models import SCHEMA_VERSION, TABLES

FORMAT = "sensitor-backup"
VERSION = 1


class BackupError(ValueError):
    """The file is not a backup this code can restore, or the target is not empty; the message says which."""


def _table_columns(store, table: str) -> list[str]:
    rows = store._read(f"PRAGMA table_info({table})")              # noqa: SLF001 - answered on both backends
    return [r["name"] for r in rows]


def dump(store) -> dict:
    """Every row of every table, in the order the tables reference each other."""
    tables = {}
    for table in TABLES:
        columns = _table_columns(store, table)
        rows = store._read(f"SELECT * FROM {table}")               # noqa: SLF001
        tables[table] = {"columns": columns, "rows": [[row[c] for c in columns] for row in rows]}
    return {"format": FORMAT, "version": VERSION, "schema_version": SCHEMA_VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "tables": tables}


def write(store, path: str) -> dict:
    """Dump to a gzipped JSON file; returns the number of rows per table."""
    data = dump(store)
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, default=str)
    return {t: len(v["rows"]) for t, v in data["tables"].items()}


def read(path: str) -> dict:
    try:
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise BackupError(f"fichier illisible : {exc}") from exc
    if data.get("format") != FORMAT:
        raise BackupError("ce fichier n'est pas une sauvegarde Sensitor")
    if int(data.get("schema_version", 0)) > SCHEMA_VERSION:
        raise BackupError(f"sauvegarde prise en version {data['schema_version']} du schéma, plus récente que "
                          f"celle de ce code ({SCHEMA_VERSION}) : mettez le code à jour d'abord")
    return data


def restore(store, data: dict) -> dict:
    """Write a dump into an empty database, in one transaction; returns the number of rows per table."""
    if store._read("SELECT COUNT(*) AS n FROM users")[0]["n"]:     # noqa: SLF001
        raise BackupError("la base cible n'est pas vide : une restauration n'écrit que dans une base neuve")
    written = {}
    # Read before the transaction: `_read` takes the store's lock, which `_write` holds.
    present_columns = {table: set(_table_columns(store, table)) for table in TABLES}
    with store._write() as conn:                                     # noqa: SLF001
        for table in TABLES:
            block = data["tables"].get(table) or {"columns": [], "rows": []}
            present = present_columns[table]
            keep = [i for i, c in enumerate(block["columns"]) if c in present]
            if not block["rows"] or not keep:
                written[table] = 0
                continue
            names = [block["columns"][i] for i in keep]
            sql = f"INSERT INTO {table} ({', '.join(names)}) VALUES ({', '.join('?' for _ in names)})"
            conn.executemany(sql, [[row[i] for i in keep] for row in block["rows"]])
            written[table] = len(block["rows"])
        if pg.is_url(store.path):
            for table in TABLES:
                if "AUTOINCREMENT" in TABLES[table].upper():
                    conn.execute(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                                 f"COALESCE(MAX(id), 1), MAX(id) IS NOT NULL) FROM {table}")
    return written


def main(argv: list[str] | None = None) -> int:
    from . import Store

    parser = argparse.ArgumentParser(prog="python -m sensitor.database.backup", description=__doc__.split("\n\n")[0])
    parser.add_argument("action", choices=("dump", "restore"))
    parser.add_argument("file")
    parser.add_argument("--db", help="base visée (adresse PostgreSQL ou fichier SQLite) ; par défaut celle de l'app")
    args = parser.parse_args(argv)
    store = Store(args.db) if args.db else Store()
    try:
        counts = write(store, args.file) if args.action == "dump" else restore(store, read(args.file))
    except BackupError as exc:
        print(f"Échec : {exc}.")
        return 1
    total = sum(counts.values())
    print(("Sauvegarde écrite" if args.action == "dump" else "Restauration faite") + f" : {total} lignes, "
          + ", ".join(f"{t} {n}" for t, n in counts.items() if n) + ".")
    return 0


if __name__ == "__main__":
    sys.exit(main())
