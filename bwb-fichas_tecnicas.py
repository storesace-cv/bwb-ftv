#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# --- Caminhos robustos ---
import sys
import logging
import os

import qt_bootstrap  # noqa: F401  # ensure Qt environment variables are configured early
from PyQt5.QtCore import QtMsgType, qInstallMessageHandler

from data.datastore import DataStore  # noqa: E402
from data.migration import ALERGENIOS_SEED_FLAG  # noqa: E402
from services.allergens import import_allergens  # noqa: E402
from services.products import ProductService  # noqa: E402
from ui.qt_compat import exec_modal  # noqa: E402
from ui.app_launcher import ensure_ftv_app, launch_ftv_app  # noqa: E402
from ui.splashscreen import SplashScreen  # noqa: E402
from utils.paths import get_project_root  # noqa: E402
from utils.files import archive_with_timestamp  # noqa: E402


logger = logging.getLogger(__name__)


_QT_MESSAGE_LEVELS = {
    QtMsgType.QtDebugMsg: logging.DEBUG,
    QtMsgType.QtWarningMsg: logging.WARNING,
    QtMsgType.QtCriticalMsg: logging.ERROR,
    QtMsgType.QtFatalMsg: logging.CRITICAL,
}
if hasattr(QtMsgType, "QtInfoMsg"):
    _QT_MESSAGE_LEVELS[QtMsgType.QtInfoMsg] = logging.INFO


def _qt_message_handler(mode, context, message):
    """Redireciona mensagens do Qt para o logging Python."""

    qt_logger = logging.getLogger("qt")
    log_level = _QT_MESSAGE_LEVELS.get(mode, logging.INFO)

    context_parts = []
    if context is not None:
        file_name = getattr(context, "file", "")
        if file_name:
            line_info = getattr(context, "line", 0)
            if line_info:
                context_parts.append(f"{file_name}:{line_info}")
            else:
                context_parts.append(str(file_name))
        function_name = getattr(context, "function", "")
        if function_name:
            context_parts.append(str(function_name))
        category_name = getattr(context, "category", "")
        if category_name:
            context_parts.append(str(category_name))

    prefix = " - ".join(part for part in context_parts if part)
    formatted_message = f"{prefix} - {message}" if prefix else message

    qt_logger.log(log_level, formatted_message)

    if mode == QtMsgType.QtFatalMsg:
        sys.exit(1)
def main() -> int:
    # Qt app (also applies the shared theme)
    app = ensure_ftv_app()

    splash = SplashScreen()
    pending = DataStore.pending_migrations()
    if pending:
        splash.show_message("A migrar base de dados…")
        app.processEvents()
        DataStore.apply_migrations()
        splash.close()
    else:
        exec_modal(splash)

    # DataStore
    # Nota: deixamos FTV_SEED_ALERGENIOS indefinida para evitar dados fictícios
    # antes da importação de alergénios via JSON.
    # Note: keep FTV_SEED_ALERGENIOS unset to avoid placeholder data before
    # importing allergens from JSON.
    if os.getenv(ALERGENIOS_SEED_FLAG):
        logger.info(
            "[LAUNCHER] Seeding de alergénios ativo via %s",
            ALERGENIOS_SEED_FLAG,
        )
    else:
        logger.info(
            "[LAUNCHER] Seeding de alergénios desativado (defina %s para valores padrão)",
            ALERGENIOS_SEED_FLAG,
        )
    ds = DataStore()
    logger.info("[LAUNCHER] DataStore importado de: %s", DataStore.__module__)

    root = get_project_root()
    allergens_path = root / "databases" / "allergens.json"
    if allergens_path.exists():
        if ds.conn is None:
            logger.error(
                "[LAUNCHER] Ficheiro de alergénios encontrado mas ligação à BD indisponível"
            )
        else:
            logger.info("[LAUNCHER] A importar alergénios de %s", allergens_path)
            try:
                import_allergens(allergens_path, ds.conn, archive=False)
            except Exception as exc:  # pragma: no cover - defensive log guard
                logger.error(
                    "[LAUNCHER] Falha a importar alergénios: %s", exc, exc_info=True
                )
            else:
                logger.info("[LAUNCHER] Alergénios importados com sucesso")
                backups_dir = root / "databases" / "backups"
                try:
                    archived_path = archive_with_timestamp(
                        allergens_path,
                        backups_dir,
                        prefix="allergens",
                        suffix=".json",
                    )
                except Exception as exc:  # pragma: no cover - defensive log guard
                    logger.error(
                        "[LAUNCHER] Falha a arquivar ficheiro de alergénios: %s",
                        exc,
                        exc_info=True,
                    )
                else:
                    logger.info(
                        "[LAUNCHER] Ficheiro de alergénios arquivado em %s", archived_path
                    )

    svc = ProductService(ds)

    # Janela principal e ciclo de eventos
    return launch_ftv_app(svc)


def configure_logging():
    root = get_project_root()
    log_dir = root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    # ensure import directories exist alongside logging setup
    imports_dir = root / "imports"
    (imports_dir / "history").mkdir(parents=True, exist_ok=True)
    images_dir = root / "databases" / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    debug_flag = os.getenv("debug")
    log_file = log_dir / "ftv.log"
    handlers = [logging.FileHandler(log_file, encoding="utf-8")]

    if debug_flag and debug_flag != "0":
        handlers.append(logging.StreamHandler())
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
        force=True,
    )

    qInstallMessageHandler(_qt_message_handler)


if __name__ == "__main__":
    configure_logging()
    sys.exit(main())
