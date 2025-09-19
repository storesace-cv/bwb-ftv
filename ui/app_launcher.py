"""Shared bootstrap helpers for launching the FTV Qt application."""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.QtWidgets import QApplication

from utils.paths import get_project_root

from .qt_compat import exec_app

if TYPE_CHECKING:  # pragma: no cover - import for type checking only
    from services.products import ProductService


logger = logging.getLogger(__name__)


def _apply_global_theme(app: QApplication) -> None:
    """Apply the shared font/theme configuration to *app*."""

    try:
        root = get_project_root()
        font_path = (
            root
            / "ui"
            / "fonts"
            / "Roboto-Italic-VariableFont_wdth,wght.ttf"
        )
        font_family = "Roboto"
        font_id = -1

        if font_path.exists():
            font_id = QFontDatabase.addApplicationFont(str(font_path))
            if font_id == -1:
                logger.warning(
                    "[THEME] Falha a carregar fonte variável Roboto-Italic a partir de %s",
                    font_path,
                )
            else:
                families = QFontDatabase.applicationFontFamilies(font_id)
                if families:
                    font_family = families[0]
        else:
            logger.warning(
                "[THEME] Fonte variável Roboto-Italic não encontrada em %s", font_path
            )

        if font_id == -1 and font_family not in QFontDatabase().families():
            logger.warning(
                "[THEME] Fonte variável Roboto-Italic indisponível; a usar tipografia padrão"
            )
            font_family = app.font().family()

        font = QFont(font_family)
        font.setPointSizeF(14)
        app.setFont(font)
    except Exception as exc:  # pragma: no cover - defensive log guard
        logger.warning("[THEME] Falha a aplicar fonte global: %s", exc)


def ensure_ftv_app() -> QApplication:
    """Return the process-wide :class:`QApplication` configured for FTV."""

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

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
