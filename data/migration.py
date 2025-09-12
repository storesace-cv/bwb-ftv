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


def ensure_core_tables(conn: sqlite3.Connection) -> None:
    """Create essential tables if they do not already exist."""

    statements = [
        (
            """
            CREATE TABLE IF NOT EXISTS produtos (
                codigo TEXT PRIMARY KEY
            )
            """
        ),
        (
            """
            CREATE TABLE IF NOT EXISTS fichas_tecnicas (
                produto_codigo TEXT
            )
            """
        ),
        (
            """
            CREATE TABLE IF NOT EXISTS alergenios (
                id    INTEGER PRIMARY KEY,
                nome  TEXT NOT NULL,
                ativo INTEGER NOT NULL DEFAULT 1
            )
            """
        ),
        (
            """
            CREATE TABLE IF NOT EXISTS tipos_artigos (
                cod       INTEGER PRIMARY KEY,
                descricao TEXT NOT NULL,
                ativo     INTEGER NOT NULL DEFAULT 1
            )
            """
        ),
        (
            """
            CREATE TABLE IF NOT EXISTS validade (
                cod       INTEGER PRIMARY KEY,
                descricao TEXT NOT NULL,
                ativo     INTEGER NOT NULL DEFAULT 1
            )
            """
        ),
        (
            """
            CREATE TABLE IF NOT EXISTS temperaturas (
                cod       INTEGER PRIMARY KEY,
                descricao TEXT NOT NULL,
                ativo     INTEGER NOT NULL DEFAULT 1
            )
            """
        ),
        (
            """
            CREATE TABLE IF NOT EXISTS produto_auxiliar (
                produto_codigo TEXT PRIMARY KEY,
                tipo_artigo_id INTEGER,
                validade_id    INTEGER,
                temperatura_id INTEGER
            )
            """
        ),
    ]

    for stmt in statements:
        conn.execute(stmt)
    conn.commit()


def setup_database(conn: sqlite3.Connection) -> None:
    """Run pending migrations and ensure essential tables exist."""

    apply_pending_migrations(conn)
    ensure_core_tables(conn)
