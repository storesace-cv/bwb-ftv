"""Registry helpers for online ingestion sources."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence
from urllib.parse import urlparse, urlunparse

import sqlite3


@dataclass(frozen=True, slots=True)
class IngestionSource:
    """Simple value object representing an ingestion endpoint."""

    id: int
    name: str
    base_url: str
    country_code: str | None
    active: bool
    created_at: str


class SourceRegistry:
    """CRUD helper focused on the ``IngestionSources`` table."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    # -- public API -----------------------------------------------------
    def list_sources(self) -> list[IngestionSource]:
        """Return all registered sources ordered by name."""

        cur = self._conn.execute(
            "SELECT Id, Name, BaseUrl, CountryCode, Active, CreatedAt"
            " FROM IngestionSources ORDER BY Name COLLATE NOCASE"
        )
        return [self._row_to_source(row) for row in cur.fetchall()]

    def get_active_sources(self) -> list[IngestionSource]:
        """Return only sources marked as active."""

        cur = self._conn.execute(
            "SELECT Id, Name, BaseUrl, CountryCode, Active, CreatedAt"
            " FROM IngestionSources WHERE Active = 1"
            " ORDER BY Name COLLATE NOCASE"
        )
        return [self._row_to_source(row) for row in cur.fetchall()]

    def get_source(self, source_id: int) -> IngestionSource | None:
        """Return a source by identifier or ``None``."""

        cur = self._conn.execute(
            "SELECT Id, Name, BaseUrl, CountryCode, Active, CreatedAt"
            " FROM IngestionSources WHERE Id = ?",
            (source_id,),
        )
        row = cur.fetchone()
        return self._row_to_source(row) if row else None

    def add_source(
        self,
        name: str,
        base_url: str,
        *,
        country_code: str | None = None,
        active: bool = True,
    ) -> IngestionSource:
        """Insert a new ingestion source and return the created entry."""

        normalized_url = self._normalize_url(base_url)
        with self._conn:
            try:
                cur = self._conn.execute(
                    "INSERT INTO IngestionSources (Name, BaseUrl, CountryCode, Active)"
                    " VALUES (?, ?, ?, ?)",
                    (name.strip(), normalized_url, self._normalize_country(country_code), int(active)),
                )
            except sqlite3.IntegrityError as exc:  # pragma: no cover - wrapped
                raise ValueError(
                    f"Já existe uma fonte registada com o URL '{normalized_url}'."
                ) from exc
        return self.get_source(cur.lastrowid)

    def update_source(
        self,
        source_id: int,
        *,
        name: str | None = None,
        base_url: str | None = None,
        country_code: str | None = None,
        active: bool | None = None,
    ) -> IngestionSource:
        """Update a source and return the refreshed value."""

        fields: list[str] = []
        values: list[object] = []
        if name is not None:
            fields.append("Name = ?")
            values.append(name.strip())
        if base_url is not None:
            fields.append("BaseUrl = ?")
            values.append(self._normalize_url(base_url))
        if country_code is not None:
            fields.append("CountryCode = ?")
            values.append(self._normalize_country(country_code))
        if active is not None:
            fields.append("Active = ?")
            values.append(int(bool(active)))
        if not fields:
            current = self.get_source(source_id)
            if current is None:
                raise LookupError(f"Fonte {source_id} não encontrada.")
            return current
        values.append(source_id)
        with self._conn:
            cur = self._conn.execute(
                f"UPDATE IngestionSources SET {', '.join(fields)} WHERE Id = ?",
                values,
            )
        if cur.rowcount == 0:
            raise LookupError(f"Fonte {source_id} não encontrada.")
        return self.get_source(source_id)

    def set_active(self, source_id: int, active: bool) -> IngestionSource:
        """Toggle the ``Active`` flag of a source."""

        return self.update_source(source_id, active=active)

    def delete_source(self, source_id: int) -> None:
        """Remove a source; silent if the id does not exist."""

        with self._conn:
            self._conn.execute("DELETE FROM IngestionSources WHERE Id = ?", (source_id,))

    # -- helpers --------------------------------------------------------
    @staticmethod
    def _normalize_url(url: str) -> str:
        cleaned = (url or "").strip()
        if not cleaned:
            raise ValueError("URL da fonte não pode ser vazio.")
        parsed = urlparse(cleaned if "://" in cleaned else f"https://{cleaned}")
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("Apenas esquemas HTTP/HTTPS são suportados.")
        if not parsed.netloc:
            raise ValueError("URL inválido: domínio em falta.")
        normalized_netloc = parsed.netloc.lower()
        rebuilt = parsed._replace(netloc=normalized_netloc)
        return urlunparse(rebuilt)

    @staticmethod
    def _normalize_country(country_code: str | None) -> str | None:
        if country_code is None:
            return None
        cleaned = country_code.strip().upper()
        return cleaned or None

    @staticmethod
    def _row_to_source(row: sqlite3.Row | Sequence[object]) -> IngestionSource:
        if isinstance(row, sqlite3.Row):
            data = row
        else:
            data = {
                "Id": row[0],
                "Name": row[1],
                "BaseUrl": row[2],
                "CountryCode": row[3],
                "Active": row[4],
                "CreatedAt": row[5],
            }
        return IngestionSource(
            id=int(data["Id"]),
            name=str(data["Name"]),
            base_url=str(data["BaseUrl"]),
            country_code=(data["CountryCode"] or None),
            active=bool(data["Active"]),
            created_at=str(data["CreatedAt"]),
        )

