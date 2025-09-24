from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.server import create_app


@pytest.fixture()
def flask_client():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def _load_template(name: str) -> dict:
    template_path = Path("app/templates_store/templates") / f"{name}.json"
    return json.loads(template_path.read_text(encoding="utf-8"))


def test_preview_endpoint_returns_pdf(flask_client):
    template = _load_template("exemplo_fatura")
    response = flask_client.post("/rb/preview", json={"templateJson": template})
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/pdf")
    assert len(response.data) > 0
