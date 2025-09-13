"""Database migration helpers."""

from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import List

from utils.paths import get_project_root

BASE_DIR = get_project_root()
MIGRATIONS_DIR = BASE_DIR / "data" / "migrations"


def _ensure_schema_table(conn: sqlite3.Connection) -> str:
    """Ensure the migration tracking table ``SchemaVersion`` exists.

    If an old ``schema_version`` table is present it is automatically
    renamed to the new CamelCase variant along with its ``Filename``
    column.  The function always returns the name of the table used for
    tracking migrations.
    """

    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='SchemaVersion'"
    )
    if cur.fetchone():
        cols = [r[1] for r in conn.execute("PRAGMA table_info('SchemaVersion')")]
        if "filename" in [c.lower() for c in cols] and "Filename" not in cols:
            conn.execute("ALTER TABLE SchemaVersion RENAME COLUMN filename TO Filename")
        return "SchemaVersion"

    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
    )
    if cur.fetchone():
        conn.execute("ALTER TABLE schema_version RENAME TO SchemaVersion")
        try:
            conn.execute("ALTER TABLE SchemaVersion RENAME COLUMN filename TO Filename")
        except sqlite3.OperationalError:
            pass
        return "SchemaVersion"

    conn.execute("CREATE TABLE IF NOT EXISTS SchemaVersion (Filename TEXT PRIMARY KEY)")
    return "SchemaVersion"


def _applied_migrations(conn: sqlite3.Connection) -> set[str]:
    table = _ensure_schema_table(conn)
    cur = conn.execute(f"SELECT Filename FROM {table}")
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
        try:
            with conn:
                conn.executescript(sql)
        except sqlite3.OperationalError as exc:
            if "another table or index" not in str(exc) and "no such table" not in str(
                exc
            ):
                raise
        table = _ensure_schema_table(conn)
        with conn:
            conn.execute(f"INSERT INTO {table}(Filename) VALUES (?)", (path.name,))
    return [p.name for p in pending]


def ensure_core_tables(conn: sqlite3.Connection) -> None:
    """Create essential tables if they do not already exist."""

    statements = [
        (
            """
            CREATE TABLE IF NOT EXISTS Produtos (
                Codigo TEXT PRIMARY KEY
            )
            """
        ),
        (
            """
            CREATE TABLE IF NOT EXISTS FichasTecnicas (
                ProdutoCodigo TEXT
            )
            """
        ),
        (
            """
            CREATE TABLE IF NOT EXISTS PrecosTaxas (
                Codigo TEXT PRIMARY KEY,
                Loja TEXT,
                Ativo TEXT,
                Preco1 TEXT,
                Preco2 TEXT,
                Preco3 TEXT,
                Preco4 TEXT,
                Preco5 TEXT,
                Iva1 TEXT,
                Iva2 TEXT,
                IsencaoIva TEXT,
                NomeProdVenda TEXT,
                Familia TEXT,
                SubFamilia TEXT
            )
            """
        ),
        (
            """
            CREATE TABLE IF NOT EXISTS Alergenios (
                Id    INTEGER PRIMARY KEY,
                Nome  TEXT NOT NULL,
                Ativo INTEGER NOT NULL DEFAULT 1
            )
            """
        ),
        (
            """
            CREATE TABLE IF NOT EXISTS TiposArtigos (
                Cod       INTEGER PRIMARY KEY,
                Descricao TEXT NOT NULL,
                Ativo     INTEGER NOT NULL DEFAULT 1
            )
            """
        ),
        (
            """
            CREATE TABLE IF NOT EXISTS Validade (
                Cod       INTEGER PRIMARY KEY,
                Descricao TEXT NOT NULL,
                Ativo     INTEGER NOT NULL DEFAULT 1
            )
            """
        ),
        (
            """
            CREATE TABLE IF NOT EXISTS Temperaturas (
                Cod       INTEGER PRIMARY KEY,
                Descricao TEXT NOT NULL,
                Ativo     INTEGER NOT NULL DEFAULT 1
            )
            """
        ),
        (
            """
            CREATE TABLE IF NOT EXISTS ProdutoAuxiliar (
                ProdutoCodigo TEXT PRIMARY KEY,
                TipoArtigoId INTEGER,
                ValidadeId    INTEGER,
                TemperaturaId INTEGER
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
