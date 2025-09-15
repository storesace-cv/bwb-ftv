"""Utilities for importing allergen metadata."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable

from utils.files import archive_with_timestamp
from utils.paths import get_project_root


def _normalise_optional_text(value: Any) -> str | None:
    """Return a cleaned text representation or ``None`` for empty values."""

    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text or None
    text = str(value).strip()
    return text or None


def _load_payload(path: Path) -> list[dict[str, Any]]:
    """Load and validate that the JSON file contains an array of objects."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:  # pragma: no cover - defensive guard
        raise FileNotFoundError(f"JSON file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON payload in {path}: {exc}") from exc

    if not isinstance(payload, list):
        raise ValueError(f"Expected a JSON array in {path}, got {type(payload).__name__}")
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(
                f"Entry {index} in {path} must be an object, got {type(item).__name__}"
            )
    return payload


def _ensure_table(conn, exemplos_type: str) -> None:
    """Ensure the ``Alergenicos`` table exists with the required columns."""

    columns: Iterable[tuple[str, str]] = (
        ("Id", "INTEGER PRIMARY KEY"),
        ("Nome", "TEXT NOT NULL"),
        ("NomeIngles", "TEXT NOT NULL"),
        ("Descricao", "TEXT"),
        ("Exemplos", exemplos_type),
        ("Notas", "TEXT"),
    )
    column_defs = ", ".join(f"{name} {definition}" for name, definition in columns)

    cur = conn.cursor()
    cur.execute(f"CREATE TABLE IF NOT EXISTS Alergenicos ({column_defs})")

    existing_columns: set[str]
    if isinstance(conn, sqlite3.Connection):
        cur.execute("PRAGMA table_info(Alergenicos)")
        existing_columns = {row[1] for row in cur.fetchall()}
    else:
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'alergenicos'
              AND table_schema = current_schema()
            """
        )
        existing_columns = {row[0] for row in cur.fetchall()}

    for name, definition in columns:
        if name in existing_columns:
            continue
        if name == "Id":
            # ``Id`` must be part of the original schema; adding it later is non-trivial.
            raise ValueError("Table Alergenicos exists without primary key column 'Id'")
        cur.execute(f"ALTER TABLE Alergenicos ADD COLUMN {name} {definition}")


def import_allergens(path: Path, conn) -> None:
    """Import allergen definitions from ``path`` into ``conn``.

    The JSON file is expected to contain an array of objects with the keys
    ``id``, ``nome``, ``nome_ingles``, ``descricao``, ``exemplos`` and ``notas``.
    The import is idempotent thanks to an ``ON CONFLICT`` upsert on ``Id``.
    """

    is_sqlite = isinstance(conn, sqlite3.Connection)
    exemplos_type = "TEXT" if is_sqlite else "JSONB"
    _ensure_table(conn, exemplos_type)

    payload = _load_payload(path)

    records: list[tuple[Any, ...]] = []
    for entry in payload:
        allergen_id = entry.get("id")
        if not isinstance(allergen_id, int) or allergen_id <= 0:
            raise ValueError(
                f"Invalid allergen id {allergen_id!r}; expected a positive integer"
            )

        nome = entry.get("nome")
        if not isinstance(nome, str) or not nome.strip():
            raise ValueError(
                f"Allergen {allergen_id}: 'nome' must be a non-empty string"
            )
        nome_ingles = entry.get("nome_ingles")
        if not isinstance(nome_ingles, str) or not nome_ingles.strip():
            raise ValueError(
                f"Allergen {allergen_id}: 'nome_ingles' must be a non-empty string"
            )

        descricao = _normalise_optional_text(entry.get("descricao"))
        notas = _normalise_optional_text(entry.get("notas"))

        exemplos_value = entry.get("exemplos")
        if exemplos_value is None:
            exemplos = None
        else:
            try:
                exemplos = json.dumps(exemplos_value, ensure_ascii=False)
            except TypeError as exc:
                raise ValueError(
                    f"Allergen {allergen_id}: 'exemplos' is not JSON serialisable"
                ) from exc

        records.append(
            (
                allergen_id,
                nome.strip(),
                nome_ingles.strip(),
                descricao,
                exemplos,
                notas,
            )
        )

    cur = conn.cursor()
    if records:
        if is_sqlite:
            insert_sql = (
                "INSERT INTO Alergenicos (Id, Nome, NomeIngles, Descricao, Exemplos, Notas) "
                "VALUES (?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(Id) DO UPDATE SET "
                "Nome=excluded.Nome, "
                "NomeIngles=excluded.NomeIngles, "
                "Descricao=excluded.Descricao, "
                "Exemplos=excluded.Exemplos, "
                "Notas=excluded.Notas"
            )
        else:
            insert_sql = (
                "INSERT INTO Alergenicos (Id, Nome, NomeIngles, Descricao, Exemplos, Notas) "
                "VALUES (%s, %s, %s, %s, %s::jsonb, %s) "
                "ON CONFLICT (Id) DO UPDATE SET "
                "Nome = EXCLUDED.Nome, "
                "NomeIngles = EXCLUDED.NomeIngles, "
                "Descricao = EXCLUDED.Descricao, "
                "Exemplos = EXCLUDED.Exemplos, "
                "Notas = EXCLUDED.Notas"
            )

        cur.executemany(insert_sql, records)

    conn.commit()

    backups_dir = get_project_root() / "databases" / "backups"
    archive_with_timestamp(
        path,
        backups_dir,
        prefix="allergens",
        suffix=".json",
    )
