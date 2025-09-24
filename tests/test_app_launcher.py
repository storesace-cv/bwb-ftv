"""Tests for the Qt application launcher helpers."""

import importlib.util
from types import SimpleNamespace

import pytest

if importlib.util.find_spec("PyQt5") is None:  # pragma: no cover - environment guard
    pytest.skip("PyQt5 não está disponível", allow_module_level=True)

from ui import app_launcher


def test_ensure_qtwebengine_attribute_without_instance(monkeypatch):
    """The shared OpenGL contexts attribute is set before creating the app."""

    flag = SimpleNamespace(value=None)

    class DummyCoreApplication:
        attribute_enabled = False

        @staticmethod
        def testAttribute(attribute):  # type: ignore[override]
            return DummyCoreApplication.attribute_enabled

        @staticmethod
        def setAttribute(attribute, enabled=True):  # type: ignore[override]
            DummyCoreApplication.attribute_enabled = enabled
            flag.value = (attribute, enabled)

        @staticmethod
        def instance():  # type: ignore[override]
            return None

    monkeypatch.setattr(app_launcher, "QCoreApplication", DummyCoreApplication)
    monkeypatch.setattr(
        app_launcher, "Qt", SimpleNamespace(AA_ShareOpenGLContexts="ShareContexts")
    )

    app_launcher._ensure_qtwebengine_shared_contexts()

    assert flag.value == ("ShareContexts", True)
