"""Utilities to run the embedded ReportBro Designer server."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import threading
import time
import urllib.error
import urllib.request
from typing import Final

from werkzeug.serving import make_server

from app.server import create_app

logger = logging.getLogger(__name__)

DEFAULT_HOST: Final[str] = "127.0.0.1"
DEFAULT_PORT: Final[int] = 55255
_HEALTHCHECK_PATH: Final[str] = "/designer"
_HEALTHCHECK_TIMEOUT: Final[int] = 10


@dataclass(frozen=True)
class ReportBroEndpoint:
    """Details about the running embedded server."""

    host: str
    port: int

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}{_HEALTHCHECK_PATH}"


class _ServerHandle:
    """Wrap the Werkzeug development server lifecycle."""

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.requested_port = port
        self._server = make_server(host, port, create_app())
        self.port = self._server.server_port
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    def start(self) -> None:
        self._thread.start()
        if not _wait_for_healthcheck(self.host, self.port, _HEALTHCHECK_TIMEOUT):
            self.shutdown()
            raise RuntimeError("Servidor ReportBro não respondeu ao healthcheck")

    def shutdown(self) -> None:
        self._server.shutdown()
        self._thread.join(timeout=2)

    @property
    def endpoint(self) -> ReportBroEndpoint:
        return ReportBroEndpoint(host=self.host, port=self.port)


_SERVER_HANDLE: _ServerHandle | None = None


def _wait_for_healthcheck(host: str, port: int, timeout: int) -> bool:
    deadline = time.time() + timeout
    url = f"http://{host}:{port}{_HEALTHCHECK_PATH}"
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url) as response:  # noqa: S310 - local request
                if 200 <= response.status < 400:
                    return True
        except urllib.error.URLError:
            time.sleep(0.3)
        except Exception:  # pragma: no cover - defensive logging
            logger.exception("[ReportBro] Healthcheck inesperado")
            time.sleep(0.3)
    return False


def _check_existing_server(host: str, port: int) -> ReportBroEndpoint | None:
    if port <= 0:
        return None
    if _wait_for_healthcheck(host, port, 2):
        logger.info(
            "[ReportBro] Servidor existente detectado em %s:%s", host, port
        )
        return ReportBroEndpoint(host=host, port=port)
    return None


def ensure_reportbro_server(host: str | None = None, port: int | None = None) -> ReportBroEndpoint:
    """Ensure that the embedded ReportBro server is running."""

    global _SERVER_HANDLE

    resolved_host = host or DEFAULT_HOST
    resolved_port = port if port is not None else DEFAULT_PORT

    existing = _check_existing_server(resolved_host, resolved_port)
    if existing:
        return existing

    if _SERVER_HANDLE and _SERVER_HANDLE.host == resolved_host:
        if resolved_port in {0, _SERVER_HANDLE.port, _SERVER_HANDLE.requested_port}:
            return _SERVER_HANDLE.endpoint

    handle = _ServerHandle(resolved_host, resolved_port)
    try:
        handle.start()
    except Exception:
        logger.exception("[ReportBro] Falha ao iniciar servidor integrado")
        handle.shutdown()
        raise

    _SERVER_HANDLE = handle
    logger.info(
        "[ReportBro] Servidor integrado disponível em http://%s:%s",
        handle.endpoint.host,
        handle.endpoint.port,
    )
    return handle.endpoint


def shutdown_reportbro_server() -> None:
    """Terminate the embedded server (primarily for tests)."""

    global _SERVER_HANDLE
    if _SERVER_HANDLE is None:
        return
    _SERVER_HANDLE.shutdown()
    _SERVER_HANDLE = None


__all__ = [
    "ensure_reportbro_server",
    "shutdown_reportbro_server",
    "ReportBroEndpoint",
]
