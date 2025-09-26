from __future__ import annotations

import json
from pathlib import Path

from tests._qt import install_stub_if_missing

install_stub_if_missing()

import pytest

try:
    from PyQt5.QtWidgets import QWidget
except ImportError:  # pragma: no cover - handled by pytest skip when Qt stub is active
    pytest.skip("PyQt5 QtWidgets is unavailable", allow_module_level=True)

from domain import Product


class _StubMessageBox:
    last_messages: list[tuple[str, tuple, dict]] = []

    @classmethod
    def _record(cls, kind: str, *args, **kwargs):
        cls.last_messages.append((kind, args, kwargs))

    @classmethod
    def information(cls, *args, **kwargs):
        cls._record("info", *args, **kwargs)

    @classmethod
    def warning(cls, *args, **kwargs):
        cls._record("warning", *args, **kwargs)

    @classmethod
    def critical(cls, *args, **kwargs):
        cls._record("critical", *args, **kwargs)


def test_active_models_serialization(tmp_path, monkeypatch):
    from ui import printing_models

    monkeypatch.setattr(printing_models, "PROJECT_ROOT", tmp_path)
    storage = tmp_path / "store" / "active_models.json"
    monkeypatch.setattr(printing_models, "ACTIVE_MODELS_PATH", storage)

    folder = tmp_path / "models"
    template = folder / "template.json"
    folder.mkdir()
    template.write_text("{}", encoding="utf-8")

    printing_models.save_active_models(
        {"ft_gestao_actual": {"folder": folder, "template": template}}
    )

    raw = json.loads(storage.read_text(encoding="utf-8"))
    assert raw == {
        "ft_gestao_actual": {
            "folder": "models",
            "template": "models/template.json",
        }
    }

    loaded = printing_models.load_active_models()
    assert loaded["ft_gestao_actual"]["folder"] == str(folder.resolve())
    assert loaded["ft_gestao_actual"]["template"] == str(template.resolve())

    resolved = printing_models.resolve_active_model_template("ft_gestao_actual")
    assert resolved == template.resolve()


def test_print_ft_gestao_uses_active_template(monkeypatch, tmp_path, qapp):
    import ui.ui_editor_fonte as ui_editor_fonte

    monkeypatch.delenv("FTV_USE_REPORTBRO", raising=False)
    monkeypatch.delenv("FTV_REPORTBRO_TEMPLATE", raising=False)

    _StubMessageBox.last_messages = []

    storage = tmp_path / "active_models.json"
    folder = tmp_path / "models"
    folder.mkdir()
    template = folder / "custom.json"
    template.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(ui_editor_fonte.printing_models, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ui_editor_fonte.printing_models, "ACTIVE_MODELS_PATH", storage)
    ui_editor_fonte.printing_models.save_active_model(
        "ft_gestao_actual", folder, template
    )

    fake_output = tmp_path / "output.pdf"

    def fake_generate_reportbro(product, *, template_path, parent):
        fake_output.write_text("conteúdo", encoding="utf-8")
        assert Path(template_path) == template.resolve()
        assert parent is ft_app
        return fake_output

    def fake_generate_legacy(*args, **kwargs):
        raise AssertionError("Fallback PDF generator must not be used")

    monkeypatch.setattr(
        ui_editor_fonte, "generate_ft_gestao_reportbro_pdf", fake_generate_reportbro
    )
    monkeypatch.setattr(ui_editor_fonte, "generate_ft_gestao_pdf", fake_generate_legacy)
    monkeypatch.setattr(ui_editor_fonte, "QMessageBox", _StubMessageBox)

    ft_app = ui_editor_fonte.FTApp.__new__(ui_editor_fonte.FTApp)
    QWidget.__init__(ft_app)
    ft_app.current_product = Product(
        code="PR-01", name="Produto", pvps=[], iva=23, ingredients=[]
    )

    ft_app._on_print_ft_gestao_actual()

    assert fake_output.exists()
    assert any(kind == "info" for kind, *_ in _StubMessageBox.last_messages)

    ft_app.deleteLater()


def test_active_models_dialog_lists_templates(monkeypatch, tmp_path, qapp):
    import ui.dialogs as dialogs_module

    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    template_a = template_dir / "ft_custom_a.json"
    template_b = template_dir / "ft_custom_b.json"
    for template in (template_a, template_b):
        template.write_text("{}", encoding="utf-8")

    discovered = [template_a, template_b]

    monkeypatch.setattr(dialogs_module, "discover_reportbro_templates", lambda: discovered)
    monkeypatch.setattr(dialogs_module.printing_models, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(dialogs_module.printing_models, "load_active_models", lambda: {})

    saved_calls: list[tuple[str, object, object]] = []

    def fake_save(identifier, folder, template):
        saved_calls.append((identifier, folder, template))

    monkeypatch.setattr(dialogs_module.printing_models, "save_active_model", fake_save)

    dialog = dialogs_module.ActiveModelsDialog()
    combos = dialog.combo_boxes

    assert set(combos) == {
        "ft_gestao_filtro",
        "ft_gestao_actual",
        "ft_operacionais_filtro",
        "ft_operacionais_actual",
    }

    expected_paths = {str(path.resolve()) for path in discovered}
    for combo in combos.values():
        item_data = {combo.itemData(index) for index in range(combo.count())}
        assert "" in item_data
        assert expected_paths <= item_data
        item_texts = {combo.itemText(index) for index in range(combo.count())}
        assert "FT Custom A" in item_texts
        assert "FT Custom B" in item_texts

    dialog.accept()
    assert len(saved_calls) == len(combos)
    for identifier, folder, template in saved_calls:
        assert identifier in combos
        if template is None:
            assert folder is None
        else:
            assert str(Path(template)) in expected_paths
            assert Path(template).exists()
