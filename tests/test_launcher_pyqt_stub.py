from __future__ import annotations

import importlib
import sys
from types import SimpleNamespace

from tests._qt import is_stub, load_pyqt5_stub


def test_launcher_imports_with_pyqt_stub(monkeypatch):
    original_pyqt_modules = {
        name: module
        for name, module in list(sys.modules.items())
        if name.startswith("PyQt5")
    }
    for name in original_pyqt_modules:
        monkeypatch.delitem(sys.modules, name, raising=False)

    original_path = list(sys.path)
    try:
        stub_pkg = load_pyqt5_stub()
        assert is_stub(stub_pkg)

        monkeypatch.setitem(sys.modules, "PyQt5", stub_pkg)
        monkeypatch.setitem(sys.modules, "PyQt5.QtCore", stub_pkg.QtCore)
        monkeypatch.setitem(sys.modules, "PyQt5.QtWidgets", stub_pkg.QtWidgets)
        monkeypatch.delitem(sys.modules, "bwb-fichas_tecnicas", raising=False)

        monkeypatch.setitem(
            sys.modules,
            "ui.app_launcher",
            SimpleNamespace(ensure_ftv_app=lambda: None, launch_ftv_app=lambda svc: 0),
        )
        monkeypatch.setitem(
            sys.modules,
            "ui.splashscreen",
            SimpleNamespace(SplashScreen=lambda: SimpleNamespace(show_message=lambda *a, **k: None, close=lambda: None)),
        )
        monkeypatch.setitem(
            sys.modules,
            "ui.qt_compat",
            SimpleNamespace(exec_modal=lambda widget: None),
        )

        module = importlib.import_module("bwb-fichas_tecnicas")

        qt_core = stub_pkg.QtCore
        assert (
            module._QT_MESSAGE_LEVELS[qt_core.QtMsgType.QtWarningMsg]
            == module.logging.WARNING
        )
    finally:
        sys.path[:] = original_path
