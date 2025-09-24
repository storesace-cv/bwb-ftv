"""Tests for the kiosk integration of the ReportBro Designer."""

from types import SimpleNamespace

from ui import reportbro_kiosk


def test_open_reportbro_kiosk_without_qwebengine(monkeypatch):
    """Return ``False`` when QtWebEngine is unavailable."""

    monkeypatch.setattr(reportbro_kiosk, "QWebEngineView", None)
    endpoint = SimpleNamespace(host="127.0.0.1", port=5000)
    assert reportbro_kiosk.open_reportbro_kiosk(None, endpoint) is False


def test_resolve_default_templates_dir_prefers_app(tmp_path):
    """Pick the templates directory under ``app/templates_store`` when available."""

    project_root = tmp_path
    app_dir = project_root / "app" / "templates_store" / "templates"
    app_dir.mkdir(parents=True)

    resolved = reportbro_kiosk._resolve_default_templates_dir(project_root)
    assert resolved == app_dir


def test_resolve_default_templates_dir_falls_back_to_reporting(tmp_path):
    """When the primary directory is missing, fall back to ``reporting/templates``."""

    project_root = tmp_path
    reporting_dir = project_root / "reporting" / "templates"
    reporting_dir.mkdir(parents=True)

    resolved = reportbro_kiosk._resolve_default_templates_dir(project_root)
    assert resolved == reporting_dir


def test_resolve_default_templates_dir_final_fallback(tmp_path):
    """Return the project root when no known directory exists."""

    project_root = tmp_path
    resolved = reportbro_kiosk._resolve_default_templates_dir(project_root)
    assert resolved == project_root


def test_build_template_injection_script_contains_payload_and_label():
    """Ensure the injection script references the report payload and label."""

    script = reportbro_kiosk._build_template_injection_script({"foo": "bar"}, "demo.json")
    assert "designerInstance.load" in script
    assert "foo" in script
    assert "demo.json" in script
