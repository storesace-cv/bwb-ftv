"""Database migration helpers."""

from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import List

from utils.paths import get_project_root

BASE_DIR = get_project_root()
MIGRATIONS_DIR = BASE_DIR / "data" / "migrations"


def _ensure_schema_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_version (filename TEXT PRIMARY KEY)"
    )


def _applied_migrations(conn: sqlite3.Connection) -> set[str]:
    _ensure_schema_table(conn)
    cur = conn.execute("SELECT filename FROM schema_version")
    return {row[0] for row in cur.fetchall()}


def get_pending_migrations(conn: sqlite3.Connection) -> List[Path]:
    """Return migration files that have not yet been applied."""
    applied = _applied_migrations(conn)
    if not MIGRATIONS_DIR.exists():
        return []
    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    return [p for p in files if p.name not in applied]


def apply_pending_migrations(conn: sqlite3.Connection) -> List[str]:
    """Apply all pending SQL migrations.

    Returns a list with the filenames of the migrations that were applied.
    """
    pending = get_pending_migrations(conn)
    for path in pending:
        sql = path.read_text(encoding="utf-8")
        with conn:
            conn.executescript(sql)
            conn.execute(
                "INSERT INTO schema_version(filename) VALUES (?)", (path.name,)
            )
    return [p.name for p in pending]
