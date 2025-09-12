#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# --- Caminhos robustos ---
import sys
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont

from data.datastore import DataStore  # noqa: E402
from services.products import ProductService  # noqa: E402
from utils.autosave import wire_autosave_aux  # noqa: E402
from ui.ui_editor_fonte import FTApp  # noqa: E402
from ui.startup_dialog import StartupDialog  # noqa: E402


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
    wire_autosave_aux(FTApp, ds)

    win = FTApp(svc)
    win.show()

    # Loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
