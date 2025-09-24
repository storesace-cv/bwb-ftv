"""Tests for the kiosk integration of the ReportBro Designer."""

from types import SimpleNamespace

from ui import reportbro_kiosk


def test_open_reportbro_kiosk_without_qwebengine(monkeypatch):
    """Return ``False`` when QtWebEngine is unavailable."""

    monkeypatch.setattr(reportbro_kiosk, "QWebEngineView", None)
    endpoint = SimpleNamespace(host="127.0.0.1", port=5000)
    assert reportbro_kiosk.open_reportbro_kiosk(None, endpoint) is False