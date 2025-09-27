from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from tests._qt import require_real_qt_modules

require_real_qt_modules("PyQt5.QtWidgets")

import ui.ui_editor_fonte as ui_editor_fonte

from PyQt5.QtWidgets import QPushButton

from domain import Product


class TemplateUpdateService:
    """Service stub exposing the API required by :class:`FTApp`."""

    def __init__(self) -> None:
        aux_stub = SimpleNamespace(
            list_tipos_artigos_admin=lambda: [],
            add_tipo_artigo=lambda *args, **kwargs: None,
            set_tipo_artigo_ativo=lambda *args, **kwargs: None,
            update_tipo_artigo=lambda *args, **kwargs: None,
            list_validade_admin=lambda: [],
            add_validade=lambda *args, **kwargs: None,
            set_validade_ativo=lambda *args, **kwargs: None,
            update_validade=lambda *args, **kwargs: None,
            list_temperaturas_admin=lambda: [],
            add_temperatura=lambda *args, **kwargs: None,
            set_temperatura_ativo=lambda *args, **kwargs: None,
            update_temperatura=lambda *args, **kwargs: None,
            list_alergenios_admin=lambda: [],
            add_alergenio=lambda *args, **kwargs: None,
            set_alergenio_ativo=lambda *args, **kwargs: None,
            update_alergenio=lambda *args, **kwargs: None,
        )
        self.ds = SimpleNamespace(
            aux=aux_stub,
            fcost=None,
            get_preparacao_html=lambda _codigo: "",
            save_preparacao_html=lambda _codigo, _html: None,
            set_fcost_level=lambda _level: None,
            get_localizacao_ativa=lambda: {
                "currency": "EUR",
                "currency_code": "EUR",
                "currency_symbol": "€",
                "locale_code": "pt_PT",
            },
        )
        self._product = Product(
            code="PR-01",
            name="Produto",
            familia="Família",
            subfamilia="Subfamília",
            tipo_artigo_cod=1,
            validade_cod=2,
            temperatura_cod=3,
            informacao_adicional="",
            pvps=[10.0],
            iva=23,
            ingredients=[],
        )

    def total(self) -> int:
        return 1

    def codigo_at(self, _idx: int) -> str:
        return self._product.code

    def list_tipos_artigos(self):
        return [(1, "Tipo")]

    def list_validade(self):
        return [(2, "Validade")]

    def list_temperaturas(self):
        return [(3, "Temperatura")]

    def list_active_allergens(self):
        return []

    def get_allergen_details(self, _aid):
        return {}

    def get_product_info(self, _codigo):
        return self._product

    def calculate_cost(self, _product):
        return 0

    def get_product_allergens(self, _codigo):
        return []

    def set_product_allergens(self, *_args, **_kwargs):
        return True

    def set_tipo_artigo(self, *_args, **_kwargs):
        return True

    def set_validade(self, *_args, **_kwargs):
        return True

    def set_temperatura(self, *_args, **_kwargs):
        return True

    def get_image_path(self, _codigo):
        return Path("does-not-exist.png")

    def save_product_image(self, *_args, **_kwargs):
        return None

    def delete_product_image(self, *_args, **_kwargs):
        return None

    def get_preparacao_image_path(self, *_args, **_kwargs):
        return Path("does-not-exist.png")

    def save_preparacao_image(self, *_args, **_kwargs):
        return None

    def delete_preparacao_image(self, *_args, **_kwargs):
        return None


class RecordingMessageBox:
    """Replacement for :class:`QMessageBox` capturing the presented dialog."""

    Question = object()
    AcceptRole = object()
    RejectRole = object()
    Information = object()
    Warning = object()
    Critical = object()

    instances: list["RecordingMessageBox"] = []
    info_calls: list[tuple[tuple, dict]] = []
    warning_calls: list[tuple[tuple, dict]] = []
    critical_calls: list[tuple[tuple, dict]] = []
    next_result: str = "cancel"

    def __init__(self, *args, **kwargs) -> None:
        self.buttons: list[QPushButton] = []
        self.button_roles: list[object] = []
        self._clicked: QPushButton | None = None
        self.window_title = ""
        self.text = ""
        RecordingMessageBox.instances.append(self)

    def setIcon(self, _icon) -> None:
        return None

    def setWindowTitle(self, title: str) -> None:
        self.window_title = title

    def setText(self, text: str) -> None:
        self.text = text

    def addButton(self, button: QPushButton, role: object) -> QPushButton:
        self.buttons.append(button)
        self.button_roles.append(role)
        return button

    def setDefaultButton(self, _button: QPushButton) -> None:
        return None

    def exec_(self) -> int:
        if RecordingMessageBox.next_result == "accept" and self.buttons:
            self._clicked = self.buttons[0]
        elif RecordingMessageBox.next_result == "cancel" and self.buttons:
            self._clicked = self.buttons[-1]
        else:
            self._clicked = None
        return 0

    def clickedButton(self) -> QPushButton | None:
        return self._clicked

    @classmethod
    def reset(cls) -> None:
        cls.instances.clear()
        cls.info_calls.clear()
        cls.warning_calls.clear()
        cls.critical_calls.clear()
        cls.next_result = "cancel"

    @classmethod
    def information(cls, *args, **kwargs):
        cls.info_calls.append((args, kwargs))
        return 0

    @classmethod
    def warning(cls, *args, **kwargs):
        cls.warning_calls.append((args, kwargs))
        return 0

    @classmethod
    def critical(cls, *args, **kwargs):
        cls.critical_calls.append((args, kwargs))
        return 0


@pytest.fixture()
def template_app(qapp):
    service = TemplateUpdateService()
    ft_app = ui_editor_fonte.FTApp(service)
    try:
        yield ft_app
    finally:
        ft_app.close()


def _find_action(menu, text: str):
    for action in menu.actions():
        if action.text() == text:
            return action
        submenu = action.menu()
        if submenu is not None:
            found = _find_action(submenu, text)
            if found is not None:
                return found
    return None


def test_actualizar_documentos_action_opens_dialog(monkeypatch, template_app):
    monkeypatch.setattr(ui_editor_fonte, "QMessageBox", RecordingMessageBox)
    RecordingMessageBox.reset()
    calls: list[str] = []
    monkeypatch.setattr(
        template_app,
        "_update_reportbro_templates",
        lambda: calls.append("called"),
    )
    RecordingMessageBox.next_result = "cancel"

    action = _find_action(template_app.mnuRoot, "Actualizar Documentos")
    assert action is not None
    action.trigger()

    assert RecordingMessageBox.instances, "Dialog should have been displayed"
    dialog = RecordingMessageBox.instances[-1]
    assert dialog.window_title == "Actualizar Documentos"
    assert dialog.text == "Pretende actualizar os modelos de documentos?"
    assert [button.text() for button in dialog.buttons] == [
        "Actualizar",
        "Cancelar",
    ]
    assert "#c62828" in dialog.buttons[0].styleSheet()
    assert "#2e7d32" in dialog.buttons[1].styleSheet()
    assert calls == []


def test_update_helper_runs_only_after_confirmation(monkeypatch, template_app):
    monkeypatch.setattr(ui_editor_fonte, "QMessageBox", RecordingMessageBox)
    RecordingMessageBox.reset()
    calls: list[str] = []

    monkeypatch.setattr(
        template_app,
        "_update_reportbro_templates",
        lambda: calls.append("called"),
    )
    RecordingMessageBox.next_result = "cancel"
    template_app._on_update_templates()
    assert calls == []

    RecordingMessageBox.reset()
    monkeypatch.setattr(
        template_app,
        "_update_reportbro_templates",
        lambda: calls.append("called"),
    )
    RecordingMessageBox.next_result = "accept"
    template_app._on_update_templates()
    assert calls == ["called"]
