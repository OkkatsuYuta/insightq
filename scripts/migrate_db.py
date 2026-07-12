"""
Safe migration: adds any missing columns to existing tables.
Run once after updating the models. Safe to re-run — skips
columns that already exist.

Usage:
    python -m scripts.migrate_db
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "earnings_tracker.db"

MIGRATIONS = [
    # (table, column, definition)
    ("integrated_filings", "filing_type", "TEXT"),
    ("integrated_filings", "is_revision", "BOOLEAN DEFAULT 0"),
]


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    for table, column, definition in MIGRATIONS:
        cur.execute(f"PRAGMA table_info({table})")
        existing = {row[1] for row in cur.fetchall()}

        if column not in existing:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
            print(f"  Added column: {table}.{column}")
        else:
            print(f"  Already exists: {table}.{column} — skipped")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
