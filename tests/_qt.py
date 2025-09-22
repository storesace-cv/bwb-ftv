"""Helpers for working with optional PyQt5 dependencies in tests."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType

import pytest

_STUB_ATTR = "__STUB__"


def _stubs_dir() -> Path:
    return Path(__file__).with_name("stubs")


def load_pyqt5_stub() -> ModuleType:
    """Load the bundled PyQt5 stub package and return it."""

    stubs_dir = _stubs_dir()
    if str(stubs_dir) not in sys.path:
        sys.path.insert(0, str(stubs_dir))
    module = importlib.import_module("PyQt5")
    return module


def is_stub(module: ModuleType | None = None) -> bool:
    """Return ``True`` when *module* represents the test stub."""

    if module is None:
        try:
            module = importlib.import_module("PyQt5")
        except ImportError:
            return False
    return getattr(module, _STUB_ATTR, False)


def require_real_qt_modules(*module_names: str) -> list[ModuleType]:
    """Import *module_names* and skip the test when the stub is active."""

    imported: list[ModuleType] = []
    for name in module_names:
        mod = pytest.importorskip(name)
        imported.append(mod)
    package = importlib.import_module("PyQt5")
    if is_stub(package) or any(is_stub(mod) for mod in imported):
        pytest.skip(
            "PyQt5 stub active; this test requires the real Qt bindings",
            allow_module_level=True,
        )
    return imported


def ensure_pyqt5_available() -> ModuleType:
    """Ensure PyQt5 (real or stub) can be imported and return the module."""

    try:
        return importlib.import_module("PyQt5")
    except ImportError:
        return load_pyqt5_stub()


def install_stub_if_missing() -> ModuleType:
    """Install the stub package when the real library is unavailable."""

    try:
        return importlib.import_module("PyQt5")
    except ImportError:
        return load_pyqt5_stub()
