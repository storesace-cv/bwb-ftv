"""Database migration helpers."""

from __future__ import annotations

import logging
import os
from pathlib import Path
import sqlite3
from typing import List

from utils.paths import get_project_root

logger = logging.getLogger(__name__)

BASE_DIR = get_project_root()
MIGRATIONS_DIR = BASE_DIR / "data" / "migrations"

DEFAULT_VALIDADE = [(1, "24h"), (2, "48h")]
DEFAULT_TEMPERATURAS = [(1, "Quente"), (2, "Frio")]
DEFAULT_ALERGENIOS = [
    (1, "Glúten", "Gluten", None, None, None),
    (2, "Crustáceos", "Crustaceans", None, None, None),
    (3, "Ovos", "Eggs", None, None, None),
    (4, "Peixe", "Fish", None, None, None),
    (5, "Amendoins", "Peanuts", None, None, None),
    (6, "Soja", "Soy", None, None, None),
    (7, "Leite", "Milk", None, None, None),
    (8, "Frutos de casca rija", "Tree nuts", None, None, None),
    (9, "Aipo", "Celery", None, None, None),
    (10, "Mostarda", "Mustard", None, None, None),
    (11, "Sementes de sésamo", "Sesame seeds", None, None, None),
    (12, "Dióxido de enxofre e sulfitos", "Sulphur dioxide and sulphites", None, None, None),
    (13, "Tremoço", "Lupin", None, None, None),
    (14, "Moluscos", "Molluscs", None, None, None),
]

ALERGENIOS_SEED_FLAG = "FTV_SEED_ALERGENIOS"
_TRUTHY_VALUES = {"1", "true", "yes", "on"}

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
    DispLojas TEXT,
    TipoArtigo INTEGER,
    Validade INTEGER,
    Temperatura INTEGER
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
    Peso DECIMAL(10,2),
    Ordem INTEGER
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
        rows = list(conn.execute("PRAGMA table_info(Produtos)"))
        types = {r[1]: r[2].upper() for r in rows}
        existing = {r[1] for r in rows}
        need = False
        if "PCU" in types and "PCM" in types:
            if (
                types.get("PCU") != "DECIMAL(10,2)"
                or types.get("PCM") != "DECIMAL(10,2)"
            ):
                need = True
        if "UnInvVMMMPG" not in existing:
            try:
                conn.execute("ALTER TABLE Produtos ADD COLUMN UnInvVMMMPG TEXT")
            except sqlite3.OperationalError:
                need = True
        for col in ("TipoArtigo", "Validade", "Temperatura"):
            if col not in existing:
                try:
                    conn.execute(f"ALTER TABLE Produtos ADD COLUMN {col} INTEGER")
                except sqlite3.OperationalError:
                    need = True
        if need:
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
                "TipoArtigo",
                "Validade",
                "Temperatura",
            ]
            _recreate_table(conn, "Produtos", PRODUTOS_SCHEMA, cols)

    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='FichasTecnicas'"
    )
    if cur.fetchone():
        rows = list(conn.execute("PRAGMA table_info(FichasTecnicas)"))
        existing = {r[1] for r in rows}
        need = False
        for col, decl in [("Preco", "DECIMAL(10,2)"), ("Ordem", "INTEGER")]:
            if col not in existing:
                try:
                    conn.execute(
                        f"ALTER TABLE FichasTecnicas ADD COLUMN {col} {decl}"
                    )
                except sqlite3.OperationalError:
                    need = True
        if need:
            cols = [
                "FamiliaSubfamilia",
                "ProdutoCodigo",
                "ProdutoNome",
                "ComponenteCodigo",
                "ComponenteNome",
                "Qtd",
                "Unidade",
                "Ppu",
                "Preco",
                "Peso",
                "Ordem",
            ]
            _recreate_table(conn, "FichasTecnicas", FICHAS_TECNICAS_SCHEMA, cols)

    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='PrecosTaxas'"
    )
    if cur.fetchone():
        rows = list(conn.execute("PRAGMA table_info(PrecosTaxas)"))
        types = {r[1]: r[2].upper() for r in rows}
        pk_cols = [r[1] for r in rows if r[5] > 0]
        need = False
        if "Preco1_5" in types and "Preco1" not in types:
            try:
                conn.execute("ALTER TABLE PrecosTaxas RENAME COLUMN Preco1_5 TO Preco1")
                types["Preco1"] = types.pop("Preco1_5")
            except sqlite3.OperationalError:
                need = True
        col_defs = {
            "Preco1": "DECIMAL(10,2)",
            "Preco2": "DECIMAL(10,2)",
            "Preco3": "DECIMAL(10,2)",
            "Preco4": "DECIMAL(10,2)",
            "Preco5": "DECIMAL(10,2)",
            "Iva1": "DECIMAL(10,2)",
            "Iva2": "DECIMAL(10,2)",
            "Loja": "TEXT",
        }
        for col, decl in col_defs.items():
            if col not in types:
                try:
                    conn.execute(f"ALTER TABLE PrecosTaxas ADD COLUMN {col} {decl}")
                except sqlite3.OperationalError:
                    need = True
            elif types.get(col) != decl:
                need = True
        if pk_cols != ["Codigo", "Loja"]:
            need = True
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
            logger.exception(
                "Falha ao renomear coluna 'filename' para 'Filename' na tabela SchemaVersion."
            )
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
    applied: List[str] = []
    for path in pending:
        sql = path.read_text(encoding="utf-8")
        try:
            with conn:
                conn.executescript(sql)
        except sqlite3.OperationalError as exc:
            msg = str(exc).lower()
            if "no such table" in msg:
                logger.warning(
                    "Migração %s ignorada porque a tabela alvo não existe; "
                    "presume-se que o esquema já está atualizado.",
                    path.name,
                )
            elif "no such column" in msg:
                logger.warning(
                    "Migração %s ignorada porque a coluna alvo não existe; "
                    "presume-se que o esquema já está atualizado.",
                    path.name,
                )
            elif not any(
                err in msg
                for err in (
                    "another table or index",
                    "duplicate column name",
                )
            ):
                raise
        table = _ensure_schema_table(conn)
        with conn:
            conn.execute(f"INSERT INTO {table}(Filename) VALUES (?)", (path.name,))
        applied.append(path.name)
    return applied


def ensure_core_tables(conn: sqlite3.Connection) -> None:
    """Run migrations and create essential tables if missing."""

    apply_pending_migrations(conn)
    _upgrade_tables(conn)
    apply_pending_migrations(conn)

    statements = [
        (PRODUTOS_SCHEMA),
        (FICHAS_TECNICAS_SCHEMA),
        (PRECOS_TAXAS_SCHEMA),
        (
            """
            CREATE TABLE IF NOT EXISTS Alergenios (
                Id         INTEGER PRIMARY KEY,
                Nome       TEXT NOT NULL,
                NomeIngles TEXT NOT NULL,
                Descricao  TEXT,
                Exemplos   TEXT,
                Notas      TEXT
            )
            """
        ),
        (
            """
            CREATE TABLE IF NOT EXISTS ProdutoAlergenio (
                ProdutoCodigo TEXT NOT NULL,
                AlergenioId   INTEGER NOT NULL,
                PRIMARY KEY (ProdutoCodigo, AlergenioId),
                FOREIGN KEY (ProdutoCodigo) REFERENCES Produtos (Codigo)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE,
                FOREIGN KEY (AlergenioId) REFERENCES Alergenios (Id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
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
            CREATE TABLE IF NOT EXISTS FcostValues (
                Nivel      INTEGER PRIMARY KEY,
                Nome       TEXT NOT NULL,
                ValorMin   REAL NOT NULL,
                ValorMax   REAL NOT NULL,
                Comentario TEXT NOT NULL,
                CHECK (ValorMin < ValorMax),
                UNIQUE (Nivel)
            )
            """
        ),
        (
            """
            CREATE TABLE IF NOT EXISTS Uploads (
                Id INTEGER PRIMARY KEY AUTOINCREMENT,
                Filename TEXT NOT NULL,
                Content BLOB NOT NULL,
                UploadedAt TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        ),
        (
            """
            CREATE TABLE IF NOT EXISTS Config (
                Key   TEXT PRIMARY KEY,
                Value TEXT
            )
            """
        ),
    ]

    for stmt in statements:
        conn.execute(stmt)
    conn.commit()
    _seed_alergenios(conn)
    _seed_validade(conn)
    _seed_temperaturas(conn)


def _should_seed_alergenios() -> bool:
    """Return ``True`` if default allergen seeding should run."""

    value = os.getenv(ALERGENIOS_SEED_FLAG)
    if value is None:
        return False
    return value.strip().lower() in _TRUTHY_VALUES


def _seed_alergenios(conn: sqlite3.Connection) -> None:
    """Populate ``Alergenios`` with default records if empty."""

    if not _should_seed_alergenios():
        return

    try:
        cur = conn.execute("SELECT COUNT(*) FROM Alergenios")
        if cur.fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO Alergenios (Id, Nome, NomeIngles, Descricao, Exemplos, Notas) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                DEFAULT_ALERGENIOS,
            )
            conn.commit()
    except sqlite3.Error:
        logger.exception(
            "Falha a inserir registos predefinidos na tabela Alergenios."
        )
        raise


def _seed_validade(conn: sqlite3.Connection) -> None:
    """Populate ``Validade`` with default records if empty."""

    try:
        cur = conn.execute("SELECT COUNT(*) FROM Validade")
        if cur.fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO Validade (Cod, Descricao, Ativo) VALUES (?, ?, 1)",
                DEFAULT_VALIDADE,
            )
            conn.commit()
    except sqlite3.Error:
        logger.exception("Falha a inserir registos predefinidos na tabela Validade.")
        raise


def _seed_temperaturas(conn: sqlite3.Connection) -> None:
    """Populate ``Temperaturas`` with default records if empty."""

    try:
        cur = conn.execute("SELECT COUNT(*) FROM Temperaturas")
        if cur.fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO Temperaturas (Cod, Descricao, Ativo) VALUES (?, ?, 1)",
                DEFAULT_TEMPERATURAS,
            )
            conn.commit()
    except sqlite3.Error:
        logger.exception(
            "Falha a inserir registos predefinidos na tabela Temperaturas."
        )
        raise


def ensure_preparacao_table(conn: sqlite3.Connection) -> None:
    """Ensure table ``ProdutoPreparacao`` exists.

    If the table is missing, legacy SQL migrations ``preparacao.sql`` and
    ``rename_to_camelcase.sql`` are executed.  Errors from missing tables or
    columns are ignored so the function is safe against already-upgraded
    databases.
    """

    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='ProdutoPreparacao'"
    )
    if cur.fetchone():
        return

    pre_path = MIGRATIONS_DIR / "preparacao.sql"
    if pre_path.exists():
        sql = pre_path.read_text(encoding="utf-8")
        try:
            with conn:
                conn.executescript(sql)
        except sqlite3.OperationalError:
            pass
        finally:
            try:
                conn.execute("PRAGMA foreign_keys=OFF")
            except sqlite3.Error:
                pass

    ren_path = MIGRATIONS_DIR / "rename_to_camelcase.sql"
    if ren_path.exists():
        text = "\n".join(
            line
            for line in ren_path.read_text(encoding="utf-8").splitlines()
            if not line.strip().startswith("--")
        )
        for stmt in text.split(";"):
            stmt = stmt.strip()
            if not stmt:
                continue
            try:
                with conn:
                    conn.execute(stmt)
            except sqlite3.OperationalError as exc:
                msg = str(exc).lower()
                if any(
                    e in msg
                    for e in (
                        "no such table",
                        "no such column",
                        "already exists",
                        "another table or index",
                    )
                ):
                    continue
                raise


def setup_database(conn: sqlite3.Connection) -> None:
    """Run pending migrations and ensure essential tables exist."""

    ensure_core_tables(conn)
    ensure_preparacao_table(conn)
