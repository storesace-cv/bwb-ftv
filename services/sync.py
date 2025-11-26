"""Automatic synchronization helpers for remote catalog ingestion."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Sequence

import requests
from requests import Session

from data.datastore import DataStore
from data.source_registry import IngestionSource, SourceRegistry

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10


@dataclass(frozen=True)
class SyncResult:
    """Outcome for a single ingestion source."""

    source: IngestionSource
    success: bool
    status_code: int | None
    error: str | None = None


class OnlineSynchronizer:
    """Ping ingestion sources and report their status."""

    def __init__(
        self,
        registry: SourceRegistry,
        *,
        session: Session | None = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        self._registry = registry
        self._session = session or requests.Session()
        self._timeout = timeout

    def run(self, *, sources: Sequence[IngestionSource] | None = None) -> list[SyncResult]:
        """Execute synchronization for each source."""

        entries = list(sources or self._registry.get_active_sources())
        results: list[SyncResult] = []
        for source in entries:
            try:
                response = self._session.get(source.base_url, timeout=self._timeout)
                response.raise_for_status()
            except requests.RequestException as exc:  # pragma: no cover - network
                status = getattr(getattr(exc, "response", None), "status_code", None)
                message = str(exc)
                logger.warning(
                    "[Sync] Falha ao contactar '%s' (%s): %s",
                    source.name,
                    source.base_url,
                    message,
                )
                results.append(
                    SyncResult(
                        source=source,
                        success=False,
                        status_code=status,
                        error=message,
                    )
                )
                continue
            logger.info(
                "[Sync] Fonte '%s' respondeu com HTTP %s",
                source.name,
                response.status_code,
            )
            results.append(
                SyncResult(
                    source=source,
                    success=True,
                    status_code=response.status_code,
                    error=None,
                )
            )
        return results


def auto_sync_datastore(
    store: DataStore,
    *,
    session: Session | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> list[SyncResult]:
    """Run the online synchronizer when the feature is enabled."""

    if store.conn is None:
        return []
    if not store.auto_sync_enabled():
        logger.info("[Sync] Sincronização automática desativada; ignorar execução.")
        return []
    registry = SourceRegistry(store.conn)
    synchronizer = OnlineSynchronizer(registry, session=session, timeout=timeout)
    return synchronizer.run()


__all__ = [
    "OnlineSynchronizer",
    "SyncResult",
    "auto_sync_datastore",
]
