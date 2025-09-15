#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# --- Caminhos robustos ---
import sys
import logging
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont

from data.datastore import DataStore  # noqa: E402
from services.allergens import import_allergens  # noqa: E402
from services.products import ProductService  # noqa: E402
from ui.ui_editor_fonte import FTApp  # noqa: E402
from ui.splashscreen import SplashScreen  # noqa: E402
from utils.paths import get_project_root  # noqa: E402
from utils.files import archive_with_timestamp  # noqa: E402


logger = logging.getLogger(__name__)
# --- UI principal ---


def _apply_global_theme(app):
    try:
        f = QFont()
        f.setPointSize(12)  # tamanho global 12pt
        app.setFont(f)
        # pode-se adicionar QSS leve aqui se precisares
    except Exception as e:
        logger.warning("[THEME] Falha a aplicar fonte global: %s", e)


def main():
    # Qt app
    app = QApplication(sys.argv)
    _apply_global_theme(app)

    splash = SplashScreen()
    pending = DataStore.pending_migrations()
    if pending:
        splash.show_message("A migrar base de dados…")
        QApplication.processEvents()
        DataStore.apply_migrations()
        splash.close()
    else:
        splash.exec_()

    # DataStore
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

    # Janela
    win = FTApp(svc)
    win.show()

    # Loop
    sys.exit(app.exec_())


def configure_logging():
    root = get_project_root()
    log_dir = root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    # ensure import directories exist alongside logging setup
    imports_dir = root / "imports"
    (imports_dir / "history").mkdir(parents=True, exist_ok=True)
    images_dir = root / "databases" / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    if os.getenv("debug") == "0":
        log_file = log_dir / "ftv.log"
        handlers = [
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ]
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=handlers,
            force=True,
        )
    else:
        logging.getLogger().addHandler(logging.NullHandler())


if __name__ == "__main__":
    configure_logging()
    main()
