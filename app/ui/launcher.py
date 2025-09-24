"""Launch the desktop window embedding the ReportBro Designer."""

from __future__ import annotations

import os
import socket
import threading
import time
import urllib.request
from dataclasses import dataclass
from typing import Callable

import webview
from werkzeug.serving import make_server

from app.server import create_app

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 0  # Auto-select a free port
DEFAULT_TITLE = "Layouts de Impressão"
HEALTHCHECK_TIMEOUT = 30


def _find_free_port(host: str) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return sock.getsockname()[1]


@dataclass
class ServerConfig:
    host: str
    port: int
    title: str


class FlaskThread(threading.Thread):
    """Run the Flask development server in a background thread."""

    def __init__(self, host: str, port: int) -> None:
        super().__init__(daemon=True)
        self.app = create_app()
        self.server = make_server(host, port, self.app)

    def run(self) -> None:  # pragma: no cover - requires GUI runtime
        self.server.serve_forever()

    def shutdown(self) -> None:
        self.server.shutdown()


def _wait_for_server(url: str, timeout: int) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url) as response:  # noqa: S310 - trusted local URL
                if response.status == 200:
                    return True
        except Exception:  # pragma: no cover - polling
            time.sleep(0.3)
    return False


def _build_config() -> ServerConfig:
    host = os.getenv("FLASK_HOST", DEFAULT_HOST)
    port_env = os.getenv("FLASK_PORT")
    port = int(port_env) if port_env and port_env.isdigit() else DEFAULT_PORT
    if port == 0:
        port = _find_free_port(host)
    title = os.getenv("APP_TITLE", DEFAULT_TITLE)
    return ServerConfig(host=host, port=port, title=title)


def _start_webview(config: ServerConfig, on_exit: Callable[[], None]) -> None:
    window = webview.create_window(config.title, f"http://{config.host}:{config.port}/designer")

    def _on_closed() -> None:
        on_exit()

    window.events.closed += _on_closed
    webview.start()


def main() -> None:  # pragma: no cover - requires GUI runtime
    config = _build_config()
    server_thread = FlaskThread(config.host, config.port)
    server_thread.start()

    url = f"http://{config.host}:{config.port}/designer"
    if not _wait_for_server(url, HEALTHCHECK_TIMEOUT):
        server_thread.shutdown()
        raise RuntimeError("Servidor Flask não respondeu ao healthcheck.")

    try:
        _start_webview(config, server_thread.shutdown)
    finally:
        server_thread.shutdown()


if __name__ == "__main__":  # pragma: no cover - script entrypoint
    main()
