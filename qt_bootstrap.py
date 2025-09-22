"""Minimal Qt bootstrap helpers for configuring PyQt5 plugin discovery."""

from __future__ import annotations

import importlib.util
import logging
import os
import sys
from pathlib import Path
from typing import Optional


logger = logging.getLogger(__name__)


def _find_pyqt5_root() -> Optional[Path]:
    """Return the root directory for the installed PyQt5 package."""

    spec = importlib.util.find_spec("PyQt5")
    if spec is None:
        logger.error(
            "[QT] Pacote PyQt5 não encontrado; configuração de plugins Qt indisponível"
        )
        return None

    locations = getattr(spec, "submodule_search_locations", None)
    if not locations:
        origin = getattr(spec, "origin", None)
        if origin:
            return Path(origin).parent
        logger.error("[QT] Localização de instalação do PyQt5 indefinida")
        return None

    return Path(next(iter(locations)))


def _platform_plugin_path(pyqt_root: Path) -> Path:
    """Compute the Qt platform plugin directory within *pyqt_root*."""

    return pyqt_root / "Qt" / "plugins" / "platforms"


def _ensure_qt_plugin_environment() -> None:
    """Ensure Qt plugin environment variables point to the bundled plugins."""

    pyqt_root = _find_pyqt5_root()
    if pyqt_root is None:
        return

    platforms_dir = _platform_plugin_path(pyqt_root)

    if not platforms_dir.exists():
        logger.error(
            "[QT] Diretório de plugins Qt inexistente: %s", platforms_dir
        )
        return

    if sys.platform == "darwin":
        expected_plugin = platforms_dir / "libqcocoa.dylib"
        if not expected_plugin.exists():
            logger.error(
                "[QT] Plataforma Cocoa ausente em %s; reinstale a wheel do PyQt5 para macOS arm64",
                expected_plugin,
            )
            return

    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(platforms_dir)
    logger.info("[QT] Plataforma Qt configurada em %s", platforms_dir)

    existing_plugin_path = os.environ.get("QT_PLUGIN_PATH")
    if existing_plugin_path:
        paths = existing_plugin_path.split(os.pathsep)
        if str(platforms_dir) not in paths:
            os.environ["QT_PLUGIN_PATH"] = (
                existing_plugin_path + os.pathsep + str(platforms_dir)
            )
    else:
        os.environ["QT_PLUGIN_PATH"] = str(platforms_dir)

    if os.environ.get("FTV_QT_DEBUG_PLUGINS") and "QT_DEBUG_PLUGINS" not in os.environ:
        os.environ["QT_DEBUG_PLUGINS"] = "1"
        logger.info("[QT] Depuração de plugins Qt ativada via FTV_QT_DEBUG_PLUGINS")


def log_qt_library_paths(app) -> None:
    """Log the Qt library paths associated with *app* to aid debugging."""

    try:
        paths = list(app.libraryPaths())
    except Exception as exc:  # pragma: no cover - defensive log guard
        logger.warning("[QT] Impossível obter caminhos de bibliotecas Qt: %s", exc)
        return

    logger.info("[QT] Caminhos de bibliotecas Qt: %s", paths)


_ensure_qt_plugin_environment()


__all__ = ["log_qt_library_paths"]
