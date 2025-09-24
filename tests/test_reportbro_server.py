from __future__ import annotations

import urllib.request

import pytest

from ui import reportbro_server


@pytest.fixture(autouse=True)
def _cleanup_server():
    yield
    reportbro_server.shutdown_reportbro_server()


def test_ensure_reportbro_server_serves_designer():
    endpoint = reportbro_server.ensure_reportbro_server(port=0)

    with urllib.request.urlopen(endpoint.url) as response:  # noqa: S310 - local server
        body = response.read().decode("utf-8")

    assert "ReportBro Designer Offline" in body
