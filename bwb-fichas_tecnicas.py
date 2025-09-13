#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# --- Caminhos robustos ---
import sys
import logging
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont

from data.datastore import DataStore  # noqa: E402
from services.products import ProductService  # noqa: E402
from ui.ui_editor_fonte import FTApp  # noqa: E402
from ui.startup_dialog import StartupDialog  # noqa: E402
from utils.paths import get_project_root  # noqa: E402


logger = logging.getLogger(__name__)
# --- UI principal ---


def _apply_global_theme(app):
    try:
        f = QFont()
        f.setPointSize(12)  # tamanho global 12pt
        app.setFont(f)
        # pode-se adicionar QSS leve aqui se precisares
    except Exception as e:
        StartupDialog(f"[THEME] Falha a aplicar fonte global: {e}", ["OK"]).get_choice()


def main():
    # Qt app
    app = QApplication(sys.argv)
    _apply_global_theme(app)

    escolha = StartupDialog("Avisos iniciais", ["Continuar", "Sair"]).get_choice()
    if escolha != "Continuar":
        sys.exit(0)

    # DataStore
    ds = DataStore()
    logger.info("[LAUNCHER] DataStore importado de: %s", DataStore.__module__)
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
        )
    else:
        logging.getLogger().addHandler(logging.NullHandler())


if __name__ == "__main__":
    configure_logging()
    main()
