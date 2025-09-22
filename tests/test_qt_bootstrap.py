"""Tests for the Qt bootstrap helpers."""

from __future__ import annotations

import os

import qt_bootstrap


def test_homebrew_fallback_selected(monkeypatch, tmp_path, caplog):
    """Ensure Homebrew-style layouts are detected when PyQt lacks plugins."""

    monkeypatch.delenv("FTV_QT_PLUGIN_PATH", raising=False)
    monkeypatch.delenv("QT_QPA_PLATFORM_PLUGIN_PATH", raising=False)
    monkeypatch.delenv("QT_PLUGIN_PATH", raising=False)

    homebrew_prefix = tmp_path / "homebrew"
    platforms_dir = homebrew_prefix / "opt" / "qt" / "plugins" / "platforms"
    platforms_dir.mkdir(parents=True)
    (platforms_dir / "libqcocoa.dylib").touch()

    monkeypatch.setenv("HOMEBREW_PREFIX", str(homebrew_prefix))

    pyqt_root = tmp_path / "pyqt_stub"
    pyqt_root.mkdir()
    monkeypatch.setattr(qt_bootstrap, "_find_pyqt5_root", lambda: pyqt_root)

    caplog.clear()
    with caplog.at_level("INFO"):
        qt_bootstrap._ensure_qt_plugin_environment()

    assert os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] == str(platforms_dir)

    plugin_roots = os.environ["QT_PLUGIN_PATH"].split(os.pathsep)
    assert str(platforms_dir.parent) in plugin_roots

    assert any("Homebrew" in record.message for record in caplog.records)
