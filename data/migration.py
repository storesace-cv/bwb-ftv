"""Database migration helpers."""

from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import List

from utils.paths import get_project_root

BASE_DIR = get_project_root()
MIGRATIONS_DIR = BASE_DIR / "data" / "migrations"

PRODUTOS_SCHEMA = """
CREATE TABLE IF NOT EXISTS Produtos (
    Codigo TEXT PRIMARY KEY,
    Produto TEXT,
    Familia TEXT,
    SubFamilia TEXT,
    AfetaStk TEXT,
    Menu TEXT,
    CodBarras TEXT,
    TipoMercad TEXT,
    TipoVenda TEXT,
    TipoProducao TEXT,
    TipoGener TEXT,
    UnStockVMPG TEXT,
    UnVendaVMV TEXT,
    UnInvVMMMPG TEXT,
    UnProduFtPV TEXT,
    CodAuxiliar TEXT,
    CodAuxiliar2 TEXT,
    PCU DECIMAL(10,2),
    PCM DECIMAL(10,2),
    Descontinuado TEXT,
    DispLojas TEXT
)
"""

FICHAS_TECNICAS_SCHEMA = """
CREATE TABLE IF NOT EXISTS FichasTecnicas (
    FamiliaSubfamilia TEXT,
    ProdutoCodigo TEXT,
    ProdutoNome TEXT,
    ComponenteCodigo TEXT,
    ComponenteNome TEXT,
    Qtd DECIMAL(10,2),
    Unidade TEXT,
    Ppu DECIMAL(10,2),
    Preco DECIMAL(10,2),
    Peso DECIMAL(10,2)
)
"""

PRECOS_TAXAS_SCHEMA = """
CREATE TABLE IF NOT EXISTS PrecosTaxas (
    Codigo TEXT NOT NULL,
    Loja TEXT NOT NULL,
    Ativo TEXT,
    Preco1 DECIMAL(10,2),
    Preco2 DECIMAL(10,2),
    Preco3 DECIMAL(10,2),
    Preco4 DECIMAL(10,2),
    Preco5 DECIMAL(10,2),
    Iva1 DECIMAL(10,2),
    Iva2 DECIMAL(10,2),
    IsencaoIva TEXT,
    NomeProdVenda TEXT,
    Familia TEXT,
    SubFamilia TEXT,
    PRIMARY KEY (Codigo, Loja)
)
"""


def _recreate_table(
    conn: sqlite3.Connection, name: str, schema: str, columns: list[str]
) -> None:
    tmp = f"{name}_old"
    with conn:
        conn.execute(f"ALTER TABLE {name} RENAME TO {tmp}")
        conn.execute(schema.replace("IF NOT EXISTS ", ""))
        cur = conn.execute(f"PRAGMA table_info({tmp})")
        existing = {r[1] for r in cur.fetchall()}
        copy_cols = [c for c in columns if c in existing]
        if copy_cols:
            cols = ",".join(copy_cols)
            conn.execute(f"INSERT INTO {name} ({cols}) SELECT {cols} FROM {tmp}")
        conn.execute(f"DROP TABLE {tmp}")


def _upgrade_tables(conn: sqlite3.Connection) -> None:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='Produtos'"
    )
    if cur.fetchone():
        info = {r[1]: r[2].upper() for r in conn.execute("PRAGMA table_info(Produtos)")}
        has_cols = "PCU" in info and "PCM" in info
        if has_cols and (
            info.get("PCU") != "DECIMAL(10,2)" or info.get("PCM") != "DECIMAL(10,2)"
        ):
            cols = [
                "Codigo",
                "Produto",
                "Familia",
                "SubFamilia",
                "AfetaStk",
                "Menu",
                "CodBarras",
                "TipoMercad",
                "TipoVenda",
                "TipoProducao",
                "TipoGener",
                "UnStockVMPG",
                "UnVendaVMV",
                "UnInvVMMMPG",
                "UnProduFtPV",
                "CodAuxiliar",
                "CodAuxiliar2",
                "PCU",
                "PCM",
                "Descontinuado",
                "DispLojas",
            ]
            _recreate_table(conn, "Produtos", PRODUTOS_SCHEMA, cols)

    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='PrecosTaxas'"
    )
    if cur.fetchone():
        rows = list(conn.execute("PRAGMA table_info(PrecosTaxas)"))
        types = {r[1]: r[2].upper() for r in rows}
        pk_cols = [r[1] for r in rows if r[5] > 0]
        required = [
            "Preco1",
            "Preco2",
            "Preco3",
            "Preco4",
            "Preco5",
            "Iva1",
            "Iva2",
            "Loja",
        ]
        has_cols = all(c in types for c in required)
        need = has_cols and pk_cols != ["Codigo", "Loja"]
        if has_cols:
            for c in required[:-1]:
                if types.get(c) != "DECIMAL(10,2)":
                    need = True
                    break
        if need:
            cols = [
                "Codigo",
                "Loja",
                "Ativo",
                "Preco1",
                "Preco2",
                "Preco3",
                "Preco4",
                "Preco5",
                "Iva1",
                "Iva2",
                "IsencaoIva",
                "NomeProdVenda",
                "Familia",
                "SubFamilia",
            ]
            _recreate_table(conn, "PrecosTaxas", PRECOS_TAXAS_SCHEMA, cols)


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

    _upgrade_tables(conn)

    statements = [
        (PRODUTOS_SCHEMA),
        (FICHAS_TECNICAS_SCHEMA),
        (PRECOS_TAXAS_SCHEMA),
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
    ]

    for stmt in statements:
        conn.execute(stmt)
    conn.commit()


def setup_database(conn: sqlite3.Connection) -> None:
    """Run pending migrations and ensure essential tables exist."""

    apply_pending_migrations(conn)
    ensure_core_tables(conn)
