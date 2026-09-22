#!/usr/bin/env python3

import argparse
import json
import sqlite3
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Inventory a SQLite database without modifying it")
    parser.add_argument("database", type=Path)
    return parser.parse_args()


def quote_identifier(identifier):
    return '"' + identifier.replace('"', '""') + '"'


def main():
    args = parse_args()
    database_uri = f"file:{args.database.resolve()}?mode=ro&immutable=1"
    connection = sqlite3.connect(database_uri, uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")

    tables = []
    table_rows = connection.execute(
        "SELECT name, sql FROM sqlite_master WHERE type = 'table' ORDER BY name"
    ).fetchall()
    for table_row in table_rows:
        table_name = table_row["name"]
        columns = connection.execute(
            f"PRAGMA table_info({quote_identifier(table_name)})"
        ).fetchall()
        foreign_keys = connection.execute(
            f"PRAGMA foreign_key_list({quote_identifier(table_name)})"
        ).fetchall()
        row_count = connection.execute(
            f"SELECT COUNT(*) FROM {quote_identifier(table_name)}"
        ).fetchone()[0]
        tables.append(
            {
                "name": table_name,
                "row_count": row_count,
                "columns": [dict(column) for column in columns],
                "foreign_keys": [dict(foreign_key) for foreign_key in foreign_keys],
                "sql": table_row["sql"],
            }
        )

    result = {
        "path": str(args.database),
        "sqlite_version": sqlite3.sqlite_version,
        "user_version": connection.execute("PRAGMA user_version").fetchone()[0],
        "application_id": connection.execute("PRAGMA application_id").fetchone()[0],
        "tables": tables,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
