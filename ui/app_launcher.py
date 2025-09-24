"""Shared bootstrap helpers for launching the FTV Qt application."""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

import qt_bootstrap
from PyQt5.QtCore import QCoreApplication, Qt
from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.QtWidgets import QApplication

from .qt_compat import exec_app

if TYPE_CHECKING:  # pragma: no cover - import for type checking only
    from services.products import ProductService


logger = logging.getLogger(__name__)


def _ensure_qtwebengine_shared_contexts() -> None:
    """Enable the OpenGL sharing attribute required by QtWebEngine."""

    share_attribute = getattr(Qt, "AA_ShareOpenGLContexts", None)
    if share_attribute is None:
        return

    if QCoreApplication.testAttribute(share_attribute):
        return

    if QCoreApplication.instance() is not None:
        logger.warning(
            "[QT] QtWebEngine requer Qt.AA_ShareOpenGLContexts antes da criação da QApplication"
        )
        return

    QCoreApplication.setAttribute(share_attribute, True)


def _apply_global_theme(app: QApplication) -> None:
    """Apply the shared font/theme configuration to *app*."""

    try:
        base_font = app.font()
        if not base_font.family():
            base_font = QFontDatabase.systemFont(QFontDatabase.GeneralFont)

        font = QFont(base_font)
        font.setPointSizeF(14)
        app.setFont(font)
    except Exception as exc:  # pragma: no cover - defensive log guard
        logger.warning("[THEME] Falha a aplicar fonte global: %s", exc)


def ensure_ftv_app() -> QApplication:
    """Return the process-wide :class:`QApplication` configured for FTV."""

    app = QApplication.instance()
    if app is None:
        _ensure_qtwebengine_shared_contexts()
        app = QApplication(sys.argv)
        qt_bootstrap.log_qt_library_paths(app)

    _apply_global_theme(app)

    from .ui_editor_fonte import APP_STYLESHEET  # late import to avoid cycles

    app.setStyleSheet(APP_STYLESHEET)
    return app


def launch_ftv_app(product_service: "ProductService") -> int:
    """Launch the FTV UI using *product_service* and return the exit code."""

    app = ensure_ftv_app()

    from .ui_editor_fonte import FTApp  # late import to avoid cycles

    window = FTApp(product_service)
    window.show()

    return exec_app(app)
