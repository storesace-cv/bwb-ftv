from __future__ import annotations

from pathlib import Path

import pytest

from ui.reportbro_stub import discover_reportbro_templates, resolve_reportbro_url


def test_discover_reportbro_templates_lists_existing_templates(tmp_path, monkeypatch):
    template_a = tmp_path / "a_template.json"
    template_b = tmp_path / "b_template.json"
    template_a.write_text("{}", encoding="utf-8")
    template_b.write_text("{}", encoding="utf-8")

    monkeypatch.setattr("ui.reportbro_stub.TEMPLATES_DIR", tmp_path)

    discovered = discover_reportbro_templates()
    assert discovered == [template_a, template_b]


def test_discover_reportbro_templates_default_directory_contains_fixture():
    discovered = discover_reportbro_templates()
    names = {path.name for path in discovered}
    assert "ft_gestao_reportbro.json" in names


def test_resolve_reportbro_url_accepts_directory(tmp_path):
    QtCore = pytest.importorskip("PyQt5.QtCore")
    if not hasattr(QtCore, "QUrl"):
        pytest.skip("QUrl não disponível no stub de PyQt5")

    html_dir = tmp_path / "reportbro"
    html_dir.mkdir()
    (html_dir / "index.html").write_text("<html></html>", encoding="utf-8")

    url = resolve_reportbro_url(str(html_dir))
    assert isinstance(url, QtCore.QUrl)
    assert url.isLocalFile()
    assert url.toLocalFile().endswith("index.html")


def test_resolve_reportbro_url_invalid_target_returns_none(monkeypatch):
    QtCore = pytest.importorskip("PyQt5.QtCore")
    if not hasattr(QtCore, "QUrl"):
        pytest.skip("QUrl não disponível no stub de PyQt5")

    assert resolve_reportbro_url("") is None
    assert resolve_reportbro_url("   ") is None

    # Force Path.exists to return False so the function goes through QUrl branch.
    monkeypatch.setattr(Path, "exists", lambda self: False)
    url = resolve_reportbro_url("ht!tp://broken")
    assert url is None
