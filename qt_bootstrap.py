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


def _platform_plugin_path(
    pyqt_root: Path,
) -> tuple[Optional[Path], list[Path], Optional[str], list[Path]]:
    """Locate the Qt platform plugin directory.

    The search first inspects the PyQt5 installation tree. When no bundled
    plugins are available (which happens for Homebrew-provided Qt), fallbacks are
    attempted based on environment variables and common Homebrew install
    prefixes.
    """

    attempted_paths: list[Path] = []
    skipped_pyqt_wheel_dirs: list[Path] = []

    def _register_attempt(candidate: Path) -> Path:
        attempted_paths.append(candidate)
        return candidate

    def _attempt_candidate(
        candidate: Path,
        source: str,
        *,
        require_cocoa: bool = False,
    ) -> tuple[Optional[Path], Optional[str]]:
        candidate = _register_attempt(candidate)
        if candidate.is_dir():
            if require_cocoa and sys.platform == "darwin":
                expected_plugin = candidate / "libqcocoa.dylib"
                if not expected_plugin.exists():
                    skipped_pyqt_wheel_dirs.append(candidate)
                    return None, None
            return candidate, source
        return None, None

    for runtime_dir in ("Qt", "Qt5"):
        candidate = pyqt_root / runtime_dir / "plugins" / "platforms"
        found, source = _attempt_candidate(
            candidate,
            "PyQt5 wheel",
            require_cocoa=True,
        )
        if found:
            return found, attempted_paths, source, skipped_pyqt_wheel_dirs

    legacy_candidate = pyqt_root / "plugins" / "platforms"
    found, source = _attempt_candidate(
        legacy_candidate,
        "PyQt5 wheel",
        require_cocoa=True,
    )
    if found:
        return found, attempted_paths, source, skipped_pyqt_wheel_dirs

    def _platform_candidates(root: Path) -> list[Path]:
        candidates: list[Path] = []
        if root.name == "platforms":
            candidates.append(root)
        candidates.append(root / "plugins" / "platforms")
        candidates.append(root / "platforms")
        seen: set[Path] = set()
        unique: list[Path] = []
        for path in candidates:
            if path not in seen:
                seen.add(path)
                unique.append(path)
        return unique

    env_override = os.environ.get("FTV_QT_PLUGIN_PATH")
    if env_override:
        override_root = Path(env_override)
        for candidate in _platform_candidates(override_root):
            found, source = _attempt_candidate(candidate, "Homebrew override")
            if found:
                return found, attempted_paths, source, skipped_pyqt_wheel_dirs

    homebrew_candidates: list[tuple[Path, str]] = []

    homebrew_prefix = os.environ.get("HOMEBREW_PREFIX")
    if homebrew_prefix:
        prefix_path = Path(homebrew_prefix)
        homebrew_candidates.extend(
            [
                (prefix_path / "opt" / "qt", "Homebrew prefix"),
                (prefix_path / "opt" / "qt@5", "Homebrew prefix"),
            ]
        )

    homebrew_candidates.extend(
        [
            (Path("/opt/homebrew/opt/qt"), "Homebrew default"),
            (Path("/opt/homebrew/opt/qt@5"), "Homebrew default"),
            (Path("/usr/local/opt/qt"), "Homebrew default"),
        ]
    )

    for root, label in homebrew_candidates:
        for candidate in _platform_candidates(root):
            found, source = _attempt_candidate(candidate, f"{label}: {root}")
            if found:
                return found, attempted_paths, source, skipped_pyqt_wheel_dirs

    return None, attempted_paths, None, skipped_pyqt_wheel_dirs


def _ensure_qt_plugin_environment() -> None:
    """Ensure Qt plugin environment variables point to the bundled plugins."""

    pyqt_root = _find_pyqt5_root()
    if pyqt_root is None:
        return

    platforms_dir, attempted_paths, source, skipped_pyqt_wheels = _platform_plugin_path(
        pyqt_root
    )

    if platforms_dir is None:
        attempted_display = ", ".join(str(path) for path in attempted_paths) or "(none)"
        logger.error(
            "[QT] Diretório de plugins Qt inexistente; caminhos verificados: %s",
            attempted_display,
        )
        return

    if skipped_pyqt_wheels and source and source != "PyQt5 wheel":
        skipped_display = ", ".join(str(path) for path in skipped_pyqt_wheels)
        logger.warning(
            "[QT] Diretório PyQt5 wheel sem libqcocoa.dylib (%s); usando fallback de %s",
            skipped_display,
            source,
        )

    if sys.platform == "darwin" and source == "PyQt5 wheel":
        expected_plugin = platforms_dir / "libqcocoa.dylib"
        if not expected_plugin.exists():
            logger.error(
                "[QT] Plataforma Cocoa ausente em %s; reinstale a wheel do PyQt5 para macOS arm64",
                expected_plugin,
            )
            return

    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(platforms_dir)
    source_display = source or "desconhecida"
    logger.info("[QT] Plataforma Qt configurada em %s (fonte: %s)", platforms_dir, source_display)

    plugin_root = platforms_dir.parent
    existing_plugin_path = os.environ.get("QT_PLUGIN_PATH")
    if existing_plugin_path:
        paths = existing_plugin_path.split(os.pathsep)
        if str(plugin_root) not in paths:
            os.environ["QT_PLUGIN_PATH"] = (
                existing_plugin_path + os.pathsep + str(plugin_root)
            )
    else:
        os.environ["QT_PLUGIN_PATH"] = str(plugin_root)

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
