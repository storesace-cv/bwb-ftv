import sys
import types

import pytest


qt_module = types.ModuleType("PyQt5")
qt_core = types.ModuleType("PyQt5.QtCore")
qt_core.Qt = object()
qt_core.QSize = object
qt_core.QObject = object
qt_gui = types.ModuleType("PyQt5.QtGui")
qt_gui.QFont = object
qt_gui.QKeySequence = object
qt_widgets = types.ModuleType("PyQt5.QtWidgets")
for name in [
    "QApplication",
    "QWidget",
    "QVBoxLayout",
    "QHBoxLayout",
    "QGridLayout",
    "QGroupBox",
    "QLabel",
    "QLineEdit",
    "QComboBox",
    "QPushButton",
    "QSizePolicy",
    "QTableWidget",
    "QTableWidgetItem",
    "QMessageBox",
    "QScrollArea",
    "QShortcut",
    "QTextEdit",
    "QCheckBox",
]:
    setattr(qt_widgets, name, type(name, (), {}))
qt_module.QtCore = qt_core
qt_module.QtGui = qt_gui
qt_module.QtWidgets = qt_widgets
sys.modules.setdefault("PyQt5", qt_module)
sys.modules.setdefault("PyQt5.QtCore", qt_core)
sys.modules.setdefault("PyQt5.QtGui", qt_gui)
sys.modules.setdefault("PyQt5.QtWidgets", qt_widgets)

from ui.ui_editor_fonte import FTApp  # noqa: E402


class ServiceStub:
    def __init__(
        self,
        *,
        tipos: list[tuple[int, str]] | None = None,
        validades: list[tuple[int, str]] | None = None,
        temperaturas: list[tuple[int, str]] | None = None,
    ):
        self._tipos = tipos or []
        self._validades = validades or []
        self._temperaturas = temperaturas or []

    def list_tipos_artigos(self):
        return self._tipos

    def list_validade(self):
        return self._validades

    def list_temperaturas(self):
        return self._temperaturas


def _make_app(service):
    app = FTApp.__new__(FTApp)
    app.service = service
    return app


def test_aux_fetch_lists_returns_expected():
    app = _make_app(
        ServiceStub(
            tipos=[(1, "TipoA")],
            validades=[(1, "Val1"), (2, "Val2")],
            temperaturas=[(1, "Temp1"), (2, "Temp2")],
        )
    )

    assert app._aux_fetch_lists() == {
        "tipo_artigo": [(1, "TipoA")],
        "validade": [(1, "Val1"), (2, "Val2")],
        "temperatura": [(1, "Temp1"), (2, "Temp2")],
    }


def test_aux_fetch_lists_missing_methods():
    class PartialService:
        def list_tipos_artigos(self):
            return []

    app = _make_app(PartialService())

    with pytest.raises(AttributeError) as exc:
        app._aux_fetch_lists()

    message = str(exc.value)
    assert "missing required auxiliary list method" in message
    assert "list_validade" in message
    assert "list_temperaturas" in message
